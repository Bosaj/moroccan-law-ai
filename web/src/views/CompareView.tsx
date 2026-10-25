import { useEffect, useRef, useState } from 'react'
import { CircleNotch, GitDiff } from '@phosphor-icons/react'
import { api } from '../lib/api'
import { useI18n } from '../lib/i18n'
import type { RedlineDiff } from '../lib/types'
import { PageHeader } from '../components/PageHeader'
import { ErrorPanel, SkeletonLines } from '../components/States'
import { Redline } from '../components/Redline'
import { SeverityBadge } from '../components/SeverityBadge'
import { BlurFade } from '../components/ui/BlurFade'
import { Disclaimer } from '../components/Disclaimer'

// Illustrative wording of Loi 19-20 (SARL), the same hand-written paraphrase used in the Gazette view.
const EXAMPLE = {
  ref: 'Loi 5-96, article 71',
  old: 'Les associés doivent se réunir physiquement au siège social pour délibérer en assemblée générale, sans possibilité de vote par visioconférence pour les décisions statutaires.',
  next: 'Sont réputés présents pour le calcul du quorum et de la majorité les associés qui participent à l’assemblée générale par des moyens de visioconférence permettant leur identification.',
}

type Phase = 'idle' | 'loading' | 'done' | 'error'

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-5 first:ps-0">
      <dt className="eyebrow">{label}</dt>
      <dd className="mt-1 font-mono text-2xl font-semibold tabular-nums tracking-tight text-ink">{value}</dd>
    </div>
  )
}

export function CompareView() {
  const { s } = useI18n()
  const [ref, setRef] = useState('')
  const [oldText, setOldText] = useState('')
  const [newText, setNewText] = useState('')
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<RedlineDiff | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [hint, setHint] = useState('')
  const abort = useRef<AbortController | null>(null)

  useEffect(() => () => abort.current?.abort(), [])

  async function run(o = oldText, n = newText, r = ref) {
    if (!o.trim() || !n.trim()) {
      setHint(s.compare.needBoth)
      return
    }
    setHint('')
    abort.current?.abort()
    const ctrl = new AbortController()
    abort.current = ctrl
    setPhase('loading')
    try {
      setResult(await api.diff(o, n, r, ctrl.signal))
      setPhase('done')
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return
      setError(e)
      setPhase('error')
    }
  }

  return (
    <div className="space-y-10">
      <PageHeader title={s.compare.title} sub={s.compare.sub} />

      <form
        className="space-y-5"
        onSubmit={(e) => {
          e.preventDefault()
          void run()
        }}
      >
        <div className="flex max-w-md flex-col gap-2">
          <label htmlFor="cmp-ref" className="text-sm font-medium text-ink">
            {s.compare.ref}
          </label>
          <input
            id="cmp-ref"
            className="field"
            dir="auto"
            value={ref}
            placeholder={s.compare.refPlaceholder}
            onChange={(e) => setRef(e.target.value)}
          />
        </div>

        <div className="grid gap-5 md:grid-cols-2">
          <div className="flex flex-col gap-2">
            <label htmlFor="cmp-old" className="text-sm font-medium text-ink">
              {s.compare.oldLabel}
            </label>
            <textarea
              id="cmp-old"
              className="field min-h-48 resize-y"
              dir="auto"
              value={oldText}
              onChange={(e) => setOldText(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="cmp-new" className="text-sm font-medium text-ink">
              {s.compare.newLabel}
            </label>
            <textarea
              id="cmp-new"
              className="field min-h-48 resize-y"
              dir="auto"
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button type="submit" className="btn-primary" disabled={phase === 'loading'}>
            {phase === 'loading' ? (
              <CircleNotch size={18} className="animate-spin" aria-hidden="true" />
            ) : (
              <GitDiff size={18} weight="bold" aria-hidden="true" />
            )}
            {phase === 'loading' ? s.compare.submitting : s.compare.submit}
          </button>
          <button
            type="button"
            className="btn-quiet"
            onClick={() => {
              setRef(EXAMPLE.ref)
              setOldText(EXAMPLE.old)
              setNewText(EXAMPLE.next)
              void run(EXAMPLE.old, EXAMPLE.next, EXAMPLE.ref)
            }}
          >
            {s.compare.example}
          </button>
          {hint && (
            <p role="alert" className="text-sm text-sev-crit">
              {hint}
            </p>
          )}
        </div>
      </form>

      <section aria-live="polite" aria-busy={phase === 'loading'}>
        {phase === 'idle' && (
          <div className="rounded-2xl border border-dashed border-line-strong p-8">
            <p className="text-ink-3">{s.compare.empty}</p>
          </div>
        )}
        {phase === 'loading' && <SkeletonLines rows={4} />}
        {phase === 'error' && <ErrorPanel error={error} onRetry={() => void run()} />}
        {phase === 'done' && result && (
          <BlurFade>
            <div className="space-y-6">
              <dl className="flex flex-wrap items-end divide-x divide-line rtl:divide-x-reverse">
                <Stat label={s.compare.removed} value={String(result.removed_tokens.length)} />
                <Stat label={s.compare.added} value={String(result.added_tokens.length)} />
                <Stat label={s.compare.changed} value={`${Math.round(result.change_ratio * 100)}%`} />
                <div className="px-5">
                  <dt className="eyebrow">{s.compare.severity}</dt>
                  <dd className="mt-2">
                    <SeverityBadge severity={result.compliance_severity} />
                  </dd>
                </div>
              </dl>

              <div className="rounded-2xl border border-line bg-surface p-6">
                <div className="mb-4 flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-ink-3">
                  <span className="eyebrow">{s.compare.legend}</span>
                  <span>
                    <del className="mark-del">abc</del> {s.compare.legendDel}
                  </span>
                  <span>
                    <ins className="mark-ins">abc</ins> {s.compare.legendIns}
                  </span>
                </div>
                <Redline markdown={result.redline_markdown} />
              </div>
              <p className="text-xs text-ink-3">{s.compare.severityNote}</p>
              <Disclaimer />
            </div>
          </BlurFade>
        )}
      </section>
    </div>
  )
}
