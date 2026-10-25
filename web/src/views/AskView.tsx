import { useEffect, useRef, useState } from 'react'
import { CircleNotch, MagnifyingGlass, Quotes, SealCheck, Warning } from '@phosphor-icons/react'
import { api } from '../lib/api'
import { labelOf, useI18n } from '../lib/i18n'
import { formatDate, textDir } from '../lib/redline'
import type { AnswerLang, Citation, QueryResult } from '../lib/types'
import { PageHeader } from '../components/PageHeader'
import { Segmented } from '../components/ui/Segmented'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { BlurFade } from '../components/ui/BlurFade'
import { ErrorPanel, SkeletonLines } from '../components/States'
import { Disclaimer } from '../components/Disclaimer'
import { cn } from '../lib/cn'

const EXAMPLES: Array<{ tag: string; text: string }> = [
  { tag: 'Darija', text: 'جراو عليا من الخدمة بلا سابق إنذار' },
  { tag: 'Arabizi', text: 'moul dar bgha ykhrjni mn lkra bla ma y3lemni' },
  { tag: 'Français', text: 'Puis-je installer des caméras de surveillance sans déclaration CNDP ?' },
  { tag: 'العربية', text: 'ما هي شروط النفقة بعد الطلاق؟' },
]

type Phase = 'idle' | 'loading' | 'done' | 'error'

function defaultAnswerLang(ui: 'fr' | 'ar' | 'en'): AnswerLang {
  return ui === 'ar' ? 'ar' : 'fr'
}

function CitationItem({ c, index, answerLang }: { c: Citation; index: number; answerLang: AnswerLang }) {
  const { s, lang } = useI18n()
  const initial = answerLang === 'fr' ? 'fr' : 'ar'
  return (
    <article className="grid grid-cols-[2.25rem_minmax(0,1fr)] gap-x-3 border-t border-line py-6 first:border-t-0 first:pt-0">
      <span className="pt-0.5 font-mono text-sm tabular-nums text-accent">{String(index + 1).padStart(2, '0')}</span>
      <div className="min-w-0">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h3 className="font-semibold text-ink" dir="auto">
            {c.code}
          </h3>
          {typeof c.rrf_score === 'number' && (
            <span className="font-mono text-xs tabular-nums text-ink-3" title={s.ask.relevance}>
              {s.ask.relevance} {c.rrf_score.toFixed(4)}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm font-medium text-ink-2" dir="auto">
          {c.article}
        </p>
        <dl className="mt-2 flex flex-wrap gap-x-5 gap-y-1 font-mono text-xs text-ink-3">
          <div className="flex gap-1.5">
            <dt>{s.ask.law}</dt>
            <dd className="text-ink-2">{c.law_number}</dd>
          </div>
          <div className="flex gap-1.5">
            <dt>{c.bo_issue.split(' ')[0]}</dt>
            <dd className="text-ink-2">{c.bo_issue.replace(/^BO\s*/, '')}</dd>
          </div>
          <div className="flex gap-1.5">
            <dt>{s.ask.published}</dt>
            <dd className="text-ink-2">{formatDate(c.publication_date, lang)}</dd>
          </div>
        </dl>
        <p className="mt-1 font-mono text-xs text-ink-3" dir="auto">
          {c.dahir}
        </p>

        <Tabs defaultValue={initial} className="mt-4">
          <TabsList>
            <TabsTrigger value="fr" lang="fr">
              {s.ask.textFr}
            </TabsTrigger>
            <TabsTrigger value="ar" lang="ar">
              {s.ask.textAr}
            </TabsTrigger>
          </TabsList>
          <TabsContent value="fr" className="pt-4">
            <blockquote lang="fr" dir="ltr" className="statute-fr border-s-2 border-accent/60 ps-4 text-ink">
              {c.text_fr}
            </blockquote>
          </TabsContent>
          <TabsContent value="ar" className="pt-4">
            <blockquote lang="ar" dir="rtl" className="statute-ar border-s-2 border-accent/60 ps-4 text-ink">
              {c.text_ar}
            </blockquote>
          </TabsContent>
        </Tabs>
      </div>
    </article>
  )
}

function Results({ result, answerLang }: { result: QueryResult; answerLang: AnswerLang }) {
  const { s } = useI18n()
  const t = result.query_translation
  const commentary = result.ai_commentary[answerLang]
  const terms = t.expanded_terms.slice(0, 6)

  return (
    <div className="space-y-10">
      <BlurFade>
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
          <div>
            <span className="eyebrow me-2">{s.ask.domain}</span>
            <span className="font-medium text-ink">{labelOf(s.domains, result.domain)}</span>
          </div>
          {result.verbatim_citations.length > 0 &&
            (result.citation_verified ? (
              <span className="inline-flex items-center gap-1.5 font-medium text-ins">
                <SealCheck size={18} weight="fill" aria-hidden="true" />
                {s.ask.verified}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 font-medium text-sev-high">
                <Warning size={18} weight="fill" aria-hidden="true" />
                {s.ask.notVerified}
              </span>
            ))}
        </div>
        {terms.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="eyebrow">{s.ask.understood}</span>
            {terms.map((term) => (
              <span
                key={term}
                dir="auto"
                className="rounded-full border border-line-strong px-2.5 py-0.5 text-xs text-ink-2"
              >
                {term}
              </span>
            ))}
          </div>
        )}
      </BlurFade>

      <BlurFade delay={0.06}>
        <section aria-labelledby="sources-title">
          <div className="mb-5 flex items-center gap-2">
            <Quotes size={18} weight="fill" className="text-accent" aria-hidden="true" />
            <h2 id="sources-title" className="text-lg font-semibold text-ink">
              {s.ask.sources}
            </h2>
          </div>
          <p className="-mt-3 mb-6 text-sm text-ink-3">{s.ask.sourcesNote}</p>
          {result.verbatim_citations.length === 0 ? (
            <p className="text-ink-2">{s.ask.noResults}</p>
          ) : (
            <div>
              {result.verbatim_citations.map((c, i) => (
                <CitationItem key={c.id} c={c} index={i} answerLang={answerLang} />
              ))}
            </div>
          )}
        </section>
      </BlurFade>

      {commentary && (
        <BlurFade delay={0.12}>
          <section
            aria-labelledby="commentary-title"
            className="rounded-xl border border-dashed border-line-strong bg-surface/60 p-5"
          >
            <h2 id="commentary-title" className="text-sm font-semibold text-ink">
              {s.ask.commentary}
            </h2>
            <p className="mt-1 text-xs text-ink-3">{s.ask.commentaryNote}</p>
            <p
              lang={answerLang === 'fr' ? 'fr' : 'ar'}
              dir={textDir(answerLang)}
              className={cn('mt-3 text-ink-2', answerLang === 'fr' ? 'statute-fr' : 'statute-ar !text-base')}
            >
              {commentary}
            </p>
          </section>
        </BlurFade>
      )}

      <BlurFade delay={0.18}>
        <div className="space-y-2">
          <p className="text-xs text-ink-3">{s.ask.corpusLimit}</p>
          <Disclaimer text={result.legal_disclaimer} />
        </div>
      </BlurFade>
    </div>
  )
}

export function AskView() {
  const { s, lang } = useI18n()
  const [query, setQuery] = useState('')
  const [answerLang, setAnswerLang] = useState<AnswerLang>(defaultAnswerLang(lang))
  const [touched, setTouched] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<unknown>(null)
  const abort = useRef<AbortController | null>(null)

  // Follow the interface language until the user picks an answer language themselves.
  useEffect(() => {
    if (!touched) setAnswerLang(defaultAnswerLang(lang))
  }, [lang, touched])

  useEffect(() => () => abort.current?.abort(), [])

  async function run(text = query) {
    const q = text.trim()
    if (!q) return
    abort.current?.abort()
    const ctrl = new AbortController()
    abort.current = ctrl
    setPhase('loading')
    setError(null)
    try {
      const res = await api.query(q, answerLang, ctrl.signal)
      setResult(res)
      setPhase('done')
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return
      setError(e)
      setPhase('error')
    }
  }

  return (
    <div className="space-y-10">
      <PageHeader title={s.ask.title} sub={s.ask.sub} />

      <div className="grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-14">
        <form
          className="space-y-5 lg:sticky lg:top-24 lg:self-start"
          onSubmit={(e) => {
            e.preventDefault()
            void run()
          }}
        >
          <div className="flex flex-col gap-2">
            <label htmlFor="question" className="text-sm font-medium text-ink">
              {s.ask.label}
            </label>
            <textarea
              id="question"
              className="field min-h-36 resize-y"
              dir="auto"
              value={query}
              placeholder={s.ask.placeholder}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') void run()
              }}
            />
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-ink">{s.ask.answerIn}</span>
            <Segmented<AnswerLang>
              label={s.ask.answerIn}
              value={answerLang}
              onChange={(v) => {
                setTouched(true)
                setAnswerLang(v)
              }}
              options={[
                { value: 'fr', label: s.ask.langs.fr, lang: 'fr' },
                { value: 'ar', label: s.ask.langs.ar, lang: 'ar' },
                { value: 'darija', label: s.ask.langs.darija, lang: 'ar' },
              ]}
            />
          </div>

          <button type="submit" className="btn-primary w-full sm:w-auto" disabled={phase === 'loading' || !query.trim()}>
            {phase === 'loading' ? (
              <CircleNotch size={18} className="animate-spin" aria-hidden="true" />
            ) : (
              <MagnifyingGlass size={18} weight="bold" aria-hidden="true" />
            )}
            {phase === 'loading' ? s.ask.submitting : s.ask.submit}
          </button>

          <div className="pt-4">
            <p className="eyebrow mb-2">{s.ask.examples}</p>
            <ul className="divide-y divide-line border-y border-line">
              {EXAMPLES.map((ex) => (
                <li key={ex.text}>
                  <button
                    type="button"
                    className="flex w-full items-baseline gap-3 py-2.5 text-start transition-colors hover:bg-surface"
                    onClick={() => {
                      setQuery(ex.text)
                      void run(ex.text)
                    }}
                  >
                    <span className="eyebrow w-16 shrink-0">{ex.tag}</span>
                    <span dir="auto" className="min-w-0 flex-1 text-sm text-ink-2">
                      {ex.text}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </form>

        <section aria-live="polite" aria-busy={phase === 'loading'} className="min-w-0">
          {phase === 'idle' && (
            <div className="flex min-h-72 items-center rounded-2xl border border-dashed border-line-strong p-8">
              <p className="max-w-[40ch] text-ink-3">{s.ask.empty}</p>
            </div>
          )}
          {phase === 'loading' && (
            <div className="space-y-8">
              <SkeletonLines rows={2} />
              <SkeletonLines rows={4} />
              <SkeletonLines rows={4} />
            </div>
          )}
          {phase === 'error' && <ErrorPanel error={error} onRetry={() => void run()} />}
          {phase === 'done' && result && <Results result={result} answerLang={answerLang} />}
        </section>
      </div>
    </div>
  )
}
