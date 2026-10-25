import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ArrowUpRight, MagnifyingGlass } from '@phosphor-icons/react'
import { api } from '../lib/api'
import { labelOf, useI18n } from '../lib/i18n'
import { formatDate } from '../lib/redline'
import type { Amendment, AnswerLang, BoIssue } from '../lib/types'
import { PageHeader } from '../components/PageHeader'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { ErrorPanel, SkeletonLines } from '../components/States'
import { Redline } from '../components/Redline'
import { SeverityBadge } from '../components/SeverityBadge'
import { BlurFade } from '../components/ui/BlurFade'
import { cn } from '../lib/cn'

type TypeFilter = 'all' | 'curated' | 'index'

function hasProvenance(issue: BoIssue, kind: Amendment['provenance']): boolean {
  return issue.amendments.some((a) => a.provenance === kind)
}

function AmendmentBlock({ am }: { am: Amendment }) {
  const { s, lang } = useI18n()
  const initial: AnswerLang = lang === 'ar' ? 'ar' : 'fr'
  const diff = am.redline_diff

  return (
    <article className="space-y-4 border-t border-line pt-6 first:border-t-0 first:pt-0">
      <div>
        <h3 className="font-semibold text-ink" dir="auto">
          {am.article_ref}
        </h3>
        <p className="mt-0.5 text-sm text-ink-3" dir="auto">
          {am.code}
        </p>
      </div>

      <Tabs defaultValue={initial}>
        <TabsList aria-label={s.gazette.summary}>
          <TabsTrigger value="fr" lang="fr">
            {s.gazette.langs.fr}
          </TabsTrigger>
          <TabsTrigger value="ar" lang="ar">
            {s.gazette.langs.ar}
          </TabsTrigger>
          <TabsTrigger value="darija" lang="ar">
            {s.gazette.langs.darija}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="fr" className="pt-4">
          <p lang="fr" className="statute-fr text-ink-2">
            {am.summary_fr}
          </p>
        </TabsContent>
        <TabsContent value="ar" className="pt-4">
          <p lang="ar" dir="rtl" className="statute-ar text-ink-2">
            {am.summary_ar}
          </p>
        </TabsContent>
        <TabsContent value="darija" className="pt-4">
          <p lang="ar" dir="rtl" className="statute-ar text-ink-2">
            {am.summary_darija}
          </p>
        </TabsContent>
      </Tabs>

      {diff ? (
        <div className="space-y-3 rounded-xl border border-line bg-surface p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="eyebrow">
              {s.gazette.before} / {s.gazette.after}
            </span>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs tabular-nums text-ink-3">
                {s.compare.changed} {Math.round(diff.change_ratio * 100)}%
              </span>
              <SeverityBadge severity={diff.compliance_severity} />
            </div>
          </div>
          <Redline markdown={diff.redline_markdown} />
          <p className="text-xs text-ink-3">{s.gazette.curatedNote}</p>
        </div>
      ) : (
        <p className="rounded-lg bg-surface-2 px-3 py-2 text-xs text-ink-3">{s.gazette.indexNote}</p>
      )}
    </article>
  )
}

function IssueDetail({ issue }: { issue: BoIssue }) {
  const { s, lang } = useI18n()
  const titleMain = lang === 'ar' ? issue.title_ar : issue.title_fr
  const titleOther = lang === 'ar' ? issue.title_fr : issue.title_ar
  return (
    <BlurFade key={issue.bo_number}>
      <div className="space-y-6">
        <div>
          <p className="font-mono text-sm tabular-nums text-accent">{issue.bo_number}</p>
          <h2 className="mt-1 text-xl font-semibold leading-snug tracking-tight text-ink" dir="auto">
            {titleMain}
          </h2>
          <p
            className="mt-2 text-sm text-ink-3"
            lang={lang === 'ar' ? 'fr' : 'ar'}
            dir={lang === 'ar' ? 'ltr' : 'rtl'}
          >
            {titleOther}
          </p>
        </div>

        <dl className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
          <div>
            <dt className="eyebrow">{s.ask.published}</dt>
            <dd className="mt-0.5 font-mono tabular-nums text-ink">{formatDate(issue.publication_date, lang)}</dd>
          </div>
          {issue.total_pages ? (
            <div>
              <dt className="eyebrow">{s.gazette.pages}</dt>
              <dd className="mt-0.5 font-mono tabular-nums text-ink">{issue.total_pages}</dd>
            </div>
          ) : null}
          <div>
            <dt className="eyebrow">{s.gazette.audience}</dt>
            <dd className="mt-0.5 text-ink">
              {issue.target_audiences.map((a) => labelOf(s.audiences, a)).join(' · ')}
            </dd>
          </div>
        </dl>

        <a
          href={issue.source_url}
          target="_blank"
          rel="noreferrer noopener"
          className="btn-quiet inline-flex"
        >
          {s.gazette.open}
          <ArrowUpRight size={14} aria-hidden="true" />
        </a>

        <section className="space-y-6">
          <h3 className="eyebrow">{s.gazette.amendments}</h3>
          {issue.amendments.map((am, i) => (
            <AmendmentBlock key={`${am.article_ref}-${i}`} am={am} />
          ))}
        </section>
      </div>
    </BlurFade>
  )
}

export function GazetteView() {
  const { s, lang } = useI18n()
  const [issues, setIssues] = useState<BoIssue[] | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [search, setSearch] = useState('')
  const [audience, setAudience] = useState('all')
  const [type, setType] = useState<TypeFilter>('all')
  const [selected, setSelected] = useState<string | null>(null)
  const detailRef = useRef<HTMLDivElement>(null)

  const load = useCallback(async () => {
    setError(null)
    setIssues(null)
    try {
      const list = await api.boIssues()
      setIssues([...list].sort((a, b) => b.publication_date.localeCompare(a.publication_date)))
    } catch (e) {
      setError(e)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const audiences = useMemo(
    () => Array.from(new Set((issues ?? []).flatMap((i) => i.target_audiences))).sort(),
    [issues],
  )

  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    return (issues ?? []).filter((i) => {
      if (audience !== 'all' && !i.target_audiences.includes(audience)) return false
      if (type === 'curated' && !hasProvenance(i, 'curated_paraphrase')) return false
      if (type === 'index' && !hasProvenance(i, 'gazette_index_summary')) return false
      if (!q) return true
      const haystack = [
        i.bo_number,
        i.title_fr,
        i.title_ar,
        ...i.amendments.flatMap((a) => [a.article_ref, a.summary_fr, a.summary_ar, a.summary_darija]),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [issues, search, audience, type])

  const current = visible.find((i) => i.bo_number === selected) ?? visible[0] ?? null

  const typeOptions: Array<{ value: TypeFilter; label: string }> = [
    { value: 'all', label: s.gazette.typeAll },
    { value: 'curated', label: s.gazette.typeCurated },
    { value: 'index', label: s.gazette.typeIndex },
  ]

  return (
    <div className="space-y-8">
      <PageHeader title={s.gazette.title} sub={s.gazette.sub} />

      <div className="space-y-4">
        <div className="relative max-w-xl">
          <label htmlFor="gazette-search" className="sr-only">
            {s.gazette.search}
          </label>
          <MagnifyingGlass
            size={18}
            className="pointer-events-none absolute start-3.5 top-1/2 -translate-y-1/2 text-ink-3"
            aria-hidden="true"
          />
          <input
            id="gazette-search"
            type="search"
            className="field ps-10"
            placeholder={s.gazette.search}
            value={search}
            dir="auto"
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
          <div className="flex flex-wrap items-center gap-2" role="group" aria-label={s.gazette.audience}>
            <span className="eyebrow me-1">{s.gazette.audience}</span>
            {['all', ...audiences].map((a) => (
              <button
                key={a}
                type="button"
                aria-pressed={audience === a}
                onClick={() => setAudience(a)}
                className={cn(
                  'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                  audience === a
                    ? 'border-accent bg-accent-soft text-ink'
                    : 'border-line-strong text-ink-2 hover:text-ink',
                )}
              >
                {a === 'all' ? s.gazette.all : labelOf(s.audiences, a)}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2" role="group" aria-label={s.gazette.type}>
            <span className="eyebrow me-1">{s.gazette.type}</span>
            {typeOptions.map((o) => (
              <button
                key={o.value}
                type="button"
                aria-pressed={type === o.value}
                onClick={() => setType(o.value)}
                className={cn(
                  'rounded-full border px-3 py-1 text-xs font-medium transition-colors',
                  type === o.value
                    ? 'border-accent bg-accent-soft text-ink'
                    : 'border-line-strong text-ink-2 hover:text-ink',
                )}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {error ? (
        <ErrorPanel error={error} onRetry={() => void load()} />
      ) : !issues ? (
        <div className="grid gap-10 lg:grid-cols-[minmax(0,4fr)_minmax(0,7fr)]">
          <SkeletonLines rows={6} />
          <SkeletonLines rows={5} />
        </div>
      ) : (
        <div className="grid gap-10 lg:grid-cols-[minmax(0,4fr)_minmax(0,7fr)] lg:gap-14">
          <div className="min-w-0">
            <p className="eyebrow mb-3" aria-live="polite">
              {s.gazette.results(visible.length)}
            </p>
            {visible.length === 0 ? (
              <p className="text-ink-2">{s.gazette.none}</p>
            ) : (
              <ul className="max-h-[68dvh] divide-y divide-line overflow-y-auto border-y border-line">
                {visible.map((i) => {
                  const active = current?.bo_number === i.bo_number
                  return (
                    <li key={i.bo_number}>
                      <button
                        type="button"
                        aria-current={active ? 'true' : undefined}
                        onClick={() => {
                          setSelected(i.bo_number)
                          if (window.matchMedia('(max-width: 1023px)').matches) {
                            detailRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                          }
                        }}
                        className={cn(
                          'block w-full px-3 py-3 text-start transition-colors',
                          active ? 'bg-accent-soft' : 'hover:bg-surface',
                        )}
                      >
                        <span className="flex items-baseline justify-between gap-3">
                          <span className="font-mono text-sm tabular-nums text-accent">{i.bo_number}</span>
                          <span className="font-mono text-xs tabular-nums text-ink-3">
                            {formatDate(i.publication_date, lang)}
                          </span>
                        </span>
                        <span className="mt-1 line-clamp-2 block text-sm text-ink-2" dir="auto">
                          {lang === 'ar' ? i.title_ar : i.title_fr}
                        </span>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          <div ref={detailRef} className="min-w-0 scroll-mt-24">
            {current ? (
              <IssueDetail issue={current} />
            ) : (
              <p className="text-ink-3">{s.gazette.select}</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
