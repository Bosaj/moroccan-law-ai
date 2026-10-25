import { useEffect, useRef, useState } from 'react'
import { CircleNotch, ClipboardText, SealCheck } from '@phosphor-icons/react'
import { api } from '../lib/api'
import { useI18n } from '../lib/i18n'
import type { AuditResult } from '../lib/types'
import { PageHeader } from '../components/PageHeader'
import { Segmented } from '../components/ui/Segmented'
import { ErrorPanel, SkeletonLines } from '../components/States'
import { RiskDial } from '../components/RiskDial'
import { SeverityBadge } from '../components/SeverityBadge'
import { BlurFade } from '../components/ui/BlurFade'
import { Disclaimer } from '../components/Disclaimer'

const EXAMPLE_CONTRACT = `CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE (CDI)

Article 1 : La période d'essai pour l'employé est fixée à 12 mois renouvelable deux fois.
Article 2 : Le salarié renonce par avance à toute indemnité de licenciement abusif.
Article 3 : Les données biométriques du salarié sont collectées sans déclaration préalable à la CNDP.`

type Phase = 'idle' | 'loading' | 'done' | 'error'

export function AuditView() {
  const { s, lang } = useI18n()
  const [text, setText] = useState('')
  const [reportLang, setReportLang] = useState<'fr' | 'ar'>(lang === 'ar' ? 'ar' : 'fr')
  const [touched, setTouched] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<AuditResult | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [hint, setHint] = useState('')
  const abort = useRef<AbortController | null>(null)

  useEffect(() => {
    if (!touched) setReportLang(lang === 'ar' ? 'ar' : 'fr')
  }, [lang, touched])

  useEffect(() => () => abort.current?.abort(), [])

  async function run(contract = text) {
    if (!contract.trim()) {
      setHint(s.audit.needText)
      return
    }
    setHint('')
    abort.current?.abort()
    const ctrl = new AbortController()
    abort.current = ctrl
    setPhase('loading')
    try {
      setResult(await api.auditContract(contract, reportLang, ctrl.signal))
      setPhase('done')
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return
      setError(e)
      setPhase('error')
    }
  }

  return (
    <div className="space-y-10">
      <PageHeader title={s.audit.title} sub={s.audit.sub} />

      <div className="grid gap-10 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:gap-14">
        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault()
            void run()
          }}
        >
          <div className="flex flex-col gap-2">
            <label htmlFor="contract" className="text-sm font-medium text-ink">
              {s.audit.label}
            </label>
            <textarea
              id="contract"
              className="field min-h-72 resize-y"
              dir="auto"
              value={text}
              placeholder={s.audit.placeholder}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="text-xs text-ink-3">{s.audit.scope}</p>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-ink">{s.audit.answerIn}</span>
            <Segmented<'fr' | 'ar'>
              label={s.audit.answerIn}
              value={reportLang}
              onChange={(v) => {
                setTouched(true)
                setReportLang(v)
              }}
              options={[
                { value: 'fr', label: 'Français', lang: 'fr' },
                { value: 'ar', label: 'العربية', lang: 'ar' },
              ]}
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button type="submit" className="btn-primary" disabled={phase === 'loading'}>
              {phase === 'loading' ? (
                <CircleNotch size={18} className="animate-spin" aria-hidden="true" />
              ) : (
                <ClipboardText size={18} weight="bold" aria-hidden="true" />
              )}
              {phase === 'loading' ? s.audit.submitting : s.audit.submit}
            </button>
            <button
              type="button"
              className="btn-quiet"
              onClick={() => {
                setText(EXAMPLE_CONTRACT)
                void run(EXAMPLE_CONTRACT)
              }}
            >
              {s.audit.example}
            </button>
            {hint && (
              <p role="alert" className="text-sm text-sev-crit">
                {hint}
              </p>
            )}
          </div>
        </form>

        <section aria-live="polite" aria-busy={phase === 'loading'} className="min-w-0">
          {phase === 'idle' && (
            <div className="flex min-h-72 items-center rounded-2xl border border-dashed border-line-strong p-8">
              <p className="max-w-[38ch] text-ink-3">{s.audit.empty}</p>
            </div>
          )}
          {phase === 'loading' && <SkeletonLines rows={5} />}
          {phase === 'error' && <ErrorPanel error={error} onRetry={() => void run()} />}
          {phase === 'done' && result && (
            <div className="space-y-8">
              <BlurFade>
                <div className="flex items-center gap-6">
                  <RiskDial score={result.risk_score} status={result.status} />
                  <div className="min-w-0">
                    <p className="eyebrow">{s.audit.score}</p>
                    <p className="mt-1 text-xl font-semibold tracking-tight text-ink">{s.status[result.status]}</p>
                    <p className="mt-1 font-mono text-xs tabular-nums text-ink-3">
                      {s.audit.flagged(result.violations_count)} · {s.audit.rules(result.rules_checked)}
                    </p>
                  </div>
                </div>
              </BlurFade>

              {result.violations.length === 0 ? (
                <BlurFade delay={0.08}>
                  <div className="flex items-start gap-3 rounded-xl border border-line bg-surface p-4">
                    <SealCheck size={22} weight="fill" className="mt-0.5 shrink-0 text-ins" aria-hidden="true" />
                    <div>
                      <p className="font-medium text-ink">{s.audit.cleanTitle}</p>
                      <p className="mt-1 text-sm text-ink-2">{s.audit.cleanBody}</p>
                    </div>
                  </div>
                </BlurFade>
              ) : (
                <ol className="divide-y divide-line border-y border-line">
                  {result.violations.map((v, i) => (
                    <li key={v.rule_id}>
                      <BlurFade delay={0.08 + i * 0.06} className="space-y-3 py-5">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <h3 className="max-w-[40ch] font-semibold leading-snug text-ink" dir="auto">
                            {v.title}
                          </h3>
                          <SeverityBadge severity={v.severity} />
                        </div>
                        <div>
                          <p className="eyebrow">{s.audit.reference}</p>
                          <p className="mt-1 font-mono text-xs text-ink-2" dir="auto">
                            {v.statutory_reference}
                          </p>
                        </div>
                        <div>
                          <p className="eyebrow">{s.audit.fix}</p>
                          <p className="mt-1 text-sm text-ink-2" dir="auto">
                            {v.remediation}
                          </p>
                        </div>
                      </BlurFade>
                    </li>
                  ))}
                </ol>
              )}
              <Disclaimer text={result.disclaimer} />
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
