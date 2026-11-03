import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft, ArrowSquareOut, CircleNotch, MagnifyingGlass } from '@phosphor-icons/react'
import { api } from '../lib/api'
import { labelOf, useI18n } from '../lib/i18n'
import type { CatalogDocument, Health, Law, LawArticle } from '../lib/types'
import { PageHeader } from '../components/PageHeader'
import { ErrorPanel, SkeletonLines } from '../components/States'

const PAGE_SIZE = 40

function ArticleReader({ law, onBack }: { law: Law; onBack: () => void }) {
  const { s, lang } = useI18n()
  const hasFrench = law.count_fr > 0
  const [textLang, setTextLang] = useState<'ar' | 'fr'>(lang === 'ar' || !hasFrench ? 'ar' : 'fr')
  const [articles, setArticles] = useState<LawArticle[] | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [filter, setFilter] = useState('')
  const [limit, setLimit] = useState(PAGE_SIZE)

  useEffect(() => {
    const ctrl = new AbortController()
    setArticles(null)
    setError(null)
    api
      .law(law.slug, textLang, ctrl.signal)
      .then((res) => setArticles(res.articles))
      .catch((e) => {
        if (!(e instanceof DOMException && e.name === 'AbortError')) setError(e)
      })
    return () => ctrl.abort()
  }, [law.slug, textLang])

  const shown = useMemo(() => {
    if (!articles) return []
    const q = filter.trim().toLowerCase()
    if (!q) return articles
    return articles.filter((a) => a.number === q || a.text.toLowerCase().includes(q) || a.section.toLowerCase().includes(q))
  }, [articles, filter])

  const title = lang === 'ar' ? law.title_ar : law.title_fr
  const pdf = textLang === 'fr' ? law.url_fr : law.url_ar
  const consolidated = textLang === 'fr' ? law.consolidated_fr : law.consolidated_ar

  return (
    <div className="space-y-6">
      <button type="button" onClick={onBack} className="inline-flex items-center gap-2 text-sm font-medium text-ink-2 hover:text-ink">
        <ArrowLeft size={16} aria-hidden="true" className="rtl:rotate-180" />
        {s.laws.back}
      </button>
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-ink" dir="auto">
          {title}
        </h2>
        <p className="mt-1 font-mono text-xs text-ink-3" dir="auto">
          {law.law_number}
          {consolidated ? ` · ${s.laws.consolidated} ${consolidated}` : ''}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {hasFrench && (
          <div role="group" aria-label={s.ask.answerIn} className="flex gap-1">
            {(['ar', 'fr'] as const).map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={textLang === value}
                onClick={() => setTextLang(value)}
                className={
                  textLang === value
                    ? 'rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-page'
                    : 'rounded-md border border-line-strong px-3 py-1.5 text-sm text-ink-2 hover:text-ink'
                }
              >
                {value === 'ar' ? s.ask.textAr : s.ask.textFr}
              </button>
            ))}
          </div>
        )}
        <a href={pdf} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-sm font-medium text-accent underline-offset-4 hover:underline">
          <ArrowSquareOut size={16} aria-hidden="true" />
          {textLang === 'fr' ? s.laws.pdfFr : s.laws.pdfAr}
        </a>
      </div>
      <input
        className="field w-full"
        dir="auto"
        value={filter}
        placeholder={s.laws.filter}
        aria-label={s.laws.filter}
        onChange={(e) => {
          setFilter(e.target.value)
          setLimit(PAGE_SIZE)
        }}
      />
      {error != null && <ErrorPanel error={error} onRetry={() => setTextLang(textLang)} />}
      {!articles && error == null && <SkeletonLines rows={6} />}
      {articles && (
        <>
          <p className="text-sm text-ink-3">{s.laws.shown(Math.min(limit, shown.length), shown.length)}</p>
          {shown.length === 0 && <p className="text-ink-2">{s.laws.noMatch}</p>}
          <ol className="divide-y divide-line">
            {shown.slice(0, limit).map((a) => (
              <li key={a.number} className="py-5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                  <h3 className="font-semibold text-ink" dir={textLang === 'ar' ? 'rtl' : 'ltr'}>
                    {a.label}
                  </h3>
                  <a
                    href={`${pdf}#page=${a.page}`}
                    target="_blank"
                    rel="noreferrer"
                    className="font-mono text-xs text-ink-3 underline-offset-4 hover:text-ink hover:underline"
                  >
                    {s.ask.page} {a.page}
                  </a>
                </div>
                {a.section && (
                  <p className="mt-1 text-xs text-ink-3" dir="auto">
                    {a.section.split(' · ').slice(-1)[0]}
                  </p>
                )}
                <p
                  lang={textLang}
                  dir={textLang === 'ar' ? 'rtl' : 'ltr'}
                  className={`mt-3 whitespace-pre-line text-ink ${textLang === 'ar' ? 'statute-ar' : 'statute-fr'}`}
                >
                  {a.text}
                </p>
              </li>
            ))}
          </ol>
          {limit < shown.length && (
            <button type="button" className="btn-primary" onClick={() => setLimit(limit + PAGE_SIZE)}>
              {s.laws.showMore}
            </button>
          )}
        </>
      )}
    </div>
  )
}

function DocumentSearch({ total, initial }: { total: number; initial: string }) {
  const { s } = useI18n()
  const [query, setQuery] = useState(initial)
  const [documents, setDocuments] = useState<CatalogDocument[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const abort = useRef<AbortController | null>(null)

  async function run(text = query) {
    const q = text.trim()
    if (!q) return
    abort.current?.abort()
    const ctrl = new AbortController()
    abort.current = ctrl
    setLoading(true)
    setError(null)
    try {
      const res = await api.catalog(q, ctrl.signal)
      setDocuments(res.documents)
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return
      setError(e)
    } finally {
      if (abort.current === ctrl) setLoading(false)
    }
  }

  useEffect(() => {
    if (initial) void run(initial)
    return () => abort.current?.abort()
    // Only the query the page opened with runs on its own
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <section aria-labelledby="docs-title" className="space-y-4">
      <h2 id="docs-title" className="text-lg font-semibold text-ink">
        {s.laws.searchDocs}
      </h2>
      <form
        className="flex gap-2"
        onSubmit={(e) => {
          e.preventDefault()
          void run()
        }}
      >
        <input
          className="field min-w-0 flex-1"
          dir="auto"
          value={query}
          placeholder={s.laws.searchPlaceholder}
          aria-label={s.laws.searchDocs}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="btn-primary shrink-0" disabled={loading || !query.trim()} aria-label={s.laws.searchDocs}>
          {loading ? <CircleNotch size={18} className="animate-spin" aria-hidden="true" /> : <MagnifyingGlass size={18} weight="bold" aria-hidden="true" />}
        </button>
      </form>
      {total > 0 && <p className="text-sm text-ink-3">{s.laws.searchHint(total)}</p>}
      {error != null && <ErrorPanel error={error} onRetry={() => void run()} />}
      {documents && (
        <div aria-live="polite">
          <p className="mb-2 text-sm text-ink-3">{documents.length ? s.laws.docsResults(documents.length) : s.laws.docsNone}</p>
          <ul className="divide-y divide-line border-y border-line empty:hidden">
            {documents.map((doc) => (
              <li key={doc.id}>
                <a href={doc.url} target="_blank" rel="noreferrer" className="block py-3 transition-colors hover:bg-surface">
                  <span dir="auto" className="block text-sm font-medium text-ink">
                    {doc.name}
                  </span>
                  <span dir="auto" className="mt-0.5 block text-xs text-ink-3">
                    {doc.trail}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  )
}

export function LawsView({ health }: { health: Health | null }) {
  const { s, lang } = useI18n()
  const [laws, setLaws] = useState<Law[] | null>(null)
  const [error, setError] = useState<unknown>(null)
  const [open, setOpen] = useState<Law | null>(null)
  const [attempt, setAttempt] = useState(0)
  const initialQuery = useMemo(() => new URLSearchParams(window.location.hash.split('?')[1] ?? '').get('q') ?? '', [])

  useEffect(() => {
    setError(null)
    api
      .laws()
      .then((res) => setLaws(res.laws))
      .catch(setError)
  }, [attempt])

  const groups = useMemo(() => {
    const byDomain = new Map<string, Law[]>()
    for (const law of laws ?? []) {
      byDomain.set(law.domain, [...(byDomain.get(law.domain) ?? []), law])
    }
    return [...byDomain.entries()]
  }, [laws])

  if (open) {
    return (
      <div className="space-y-10">
        <ArticleReader law={open} onBack={() => setOpen(null)} />
      </div>
    )
  }

  return (
    <div className="space-y-10">
      <PageHeader title={s.laws.title} sub={s.laws.sub} />
      <DocumentSearch total={health?.catalog_documents_count ?? 0} initial={initialQuery} />
      <section aria-labelledby="core-title" className="space-y-6">
        <h2 id="core-title" className="text-lg font-semibold text-ink">
          {s.laws.coreTitle}
        </h2>
        {error != null && <ErrorPanel error={error} onRetry={() => setAttempt(attempt + 1)} />}
        {!laws && error == null && <SkeletonLines rows={6} />}
        {groups.map(([domain, items]) => (
          <div key={domain}>
            <h3 className="eyebrow mb-2">{labelOf(s.domains, domain)}</h3>
            <ul className="divide-y divide-line border-y border-line">
              {items.map((law) => (
                <li key={law.slug}>
                  <button
                    type="button"
                    onClick={() => setOpen(law)}
                    className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4 py-3 text-start transition-colors hover:bg-surface"
                  >
                    <span className="min-w-0">
                      <span dir="auto" className="block font-medium text-ink">
                        {lang === 'ar' ? law.title_ar : law.title_fr}
                      </span>
                      <span dir="auto" className="mt-0.5 block font-mono text-xs text-ink-3">
                        {law.law_number}
                        {law.consolidated_ar ? ` · ${s.laws.consolidated} ${law.consolidated_ar}` : ''}
                        {law.count_fr === 0 ? ` · ${s.laws.onlyArabic}` : ''}
                      </span>
                    </span>
                    <span className="font-mono text-xs tabular-nums text-ink-3">
                      {Math.max(law.count_ar, law.count_fr)} {s.laws.articles}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>
    </div>
  )
}
