import { ClipboardText, GitDiff, Moon, Newspaper, Scales, Sun } from '@phosphor-icons/react'
import type { ReactNode } from 'react'
import { LogoMark } from './Logo'
import { Segmented } from './ui/Segmented'
import { DICTIONARIES, UI_LANGS, useI18n } from '../lib/i18n'
import type { Health, UiLang } from '../lib/types'
import { VIEW_IDS, type ViewId } from '../lib/route'
import { cn } from '../lib/cn'

const ICONS = { ask: Scales, gazette: Newspaper, compare: GitDiff, audit: ClipboardText } as const

interface ShellProps {
  view: ViewId
  theme: 'dark' | 'light'
  onToggleTheme: () => void
  health: Health | null
  online: boolean
  children: ReactNode
}

function EngineStatus({ health, online }: { health: Health | null; online: boolean }) {
  const { s } = useI18n()
  return (
    <section aria-label={s.engine.title} className="space-y-3 border-t border-line pt-5">
      <div className="flex items-center gap-2">
        <span className="pulse-dot" data-off={!online} aria-hidden="true" />
        <span className="eyebrow">{online ? s.engine.online : s.engine.offline}</span>
      </div>
      {health && (
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-3">
            <dt className="text-ink-3">{s.engine.corpus}</dt>
            <dd className="font-mono tabular-nums text-ink">{health.corpus_articles_count}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-ink-3">{s.engine.issues}</dt>
            <dd className="font-mono tabular-nums text-ink">{health.bo_issues_count}</dd>
          </div>
          <div className="flex justify-between gap-3">
            <dt className="text-ink-3">{s.engine.consultations}</dt>
            <dd className="font-mono tabular-nums text-ink">{health.consultations_logged}</dd>
          </div>
          <div className="pt-1">
            <dt className="text-ink-3">{s.engine.retrieval}</dt>
            <dd className="mt-0.5 text-xs text-ink-2">{s.engine.retrievalValue}</dd>
          </div>
        </dl>
      )}
    </section>
  )
}

export function Shell({ view, theme, onToggleTheme, health, online, children }: ShellProps) {
  const { s, lang, setLang } = useI18n()

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[17rem_minmax(0,1fr)]">
      <aside className="hidden border-e border-line lg:block">
        <div className="sticky top-0 flex h-dvh flex-col justify-between gap-8 px-6 py-8">
          <div className="space-y-10">
            <a href="#/ask" className="flex items-center gap-3 text-accent" aria-label={s.brand}>
              <LogoMark size={40} />
              <span className="leading-none">
                <span className="block text-xl font-semibold tracking-tight text-ink">{s.brand}</span>
                <span lang="ar" className="mt-1 block font-maghribi text-lg text-accent">
                  {s.brandAr}
                </span>
              </span>
            </a>
            <nav aria-label={s.navLabel} className="space-y-1">
              {VIEW_IDS.map((id) => {
                const Icon = ICONS[id]
                const active = id === view
                return (
                  <a
                    key={id}
                    href={`#/${id}`}
                    aria-current={active ? 'page' : undefined}
                    className={cn(
                      'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                      active ? 'bg-accent-soft text-ink' : 'text-ink-2 hover:bg-surface hover:text-ink',
                    )}
                  >
                    <Icon
                      size={20}
                      weight={active ? 'fill' : 'regular'}
                      className={active ? 'text-accent' : 'text-ink-3 group-hover:text-ink-2'}
                      aria-hidden="true"
                    />
                    {s.nav[id]}
                  </a>
                )
              })}
            </nav>
          </div>
          <EngineStatus health={health} online={online} />
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <div className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-line bg-canvas/85 px-4 py-3 backdrop-blur md:px-8">
          <a href="#/ask" className="flex items-center gap-2 text-accent lg:invisible" aria-label={s.brand}>
            <LogoMark size={28} />
            <span className="text-base font-semibold tracking-tight text-ink">{s.brand}</span>
          </a>
          <div className="flex items-center gap-2">
            <Segmented<UiLang>
              label={s.uiLang}
              value={lang}
              onChange={setLang}
              options={UI_LANGS.map((l) => ({ value: l.code, label: l.label, lang: l.code }))}
            />
            <button
              type="button"
              onClick={onToggleTheme}
              className="btn-quiet !p-2"
              aria-label={theme === 'dark' ? DICTIONARIES[lang].theme.toLight : DICTIONARIES[lang].theme.toDark}
            >
              {theme === 'dark' ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
            </button>
          </div>
        </div>

        <main id="main" className="mx-auto w-full max-w-[1180px] flex-1 px-4 pb-28 pt-8 md:px-8 lg:pb-16">
          {children}
        </main>

        <nav
          aria-label={s.navLabel}
          className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-4 border-t border-line bg-canvas/95 backdrop-blur lg:hidden"
        >
          {VIEW_IDS.map((id) => {
            const Icon = ICONS[id]
            const active = id === view
            return (
              <a
                key={id}
                href={`#/${id}`}
                aria-current={active ? 'page' : undefined}
                className={cn(
                  'flex flex-col items-center gap-1 px-1 py-2.5 text-[0.6875rem] font-medium',
                  active ? 'text-accent' : 'text-ink-3',
                )}
              >
                <Icon size={22} weight={active ? 'fill' : 'regular'} aria-hidden="true" />
                <span className="max-w-full truncate">{s.nav[id]}</span>
              </a>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
