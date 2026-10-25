import { useCallback, useEffect, useMemo, useState } from 'react'
import { DICTIONARIES, I18nContext, type I18nValue } from './lib/i18n'
import { viewFromHash, type ViewId } from './lib/route'
import { ApiError } from './lib/api'
import type { UiLang } from './lib/types'
import { useHealth } from './lib/useHealth'
import { Shell } from './components/Shell'
import { AskView } from './views/AskView'
import { GazetteView } from './views/GazetteView'
import { CompareView } from './views/CompareView'
import { AuditView } from './views/AuditView'

type Theme = 'dark' | 'light'

function initialLang(): UiLang {
  try {
    const saved = localStorage.getItem('mizan.lang')
    if (saved === 'fr' || saved === 'ar' || saved === 'en') return saved
  } catch {
    // storage unavailable: fall through to the default
  }
  return 'fr'
}

function initialTheme(): Theme {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'
}

export function App() {
  const [lang, setLangState] = useState<UiLang>(initialLang)
  const [theme, setTheme] = useState<Theme>(initialTheme)
  const [view, setView] = useState<ViewId>(() => viewFromHash(window.location.hash))
  const { health, error } = useHealth()

  useEffect(() => {
    const onHash = () => {
      setView(viewFromHash(window.location.hash))
      window.scrollTo({ top: 0 })
    }
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  // Real right-to-left: the whole document flips, not only the text.
  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  }, [lang])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const setLang = useCallback((next: UiLang) => {
    setLangState(next)
    try {
      localStorage.setItem('mizan.lang', next)
    } catch {
      // not persisted; the choice still applies for this session
    }
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next: Theme = t === 'dark' ? 'light' : 'dark'
      try {
        localStorage.setItem('mizan.theme', next)
      } catch {
        // not persisted
      }
      return next
    })
  }, [])

  const i18n = useMemo<I18nValue>(() => ({ lang, s: DICTIONARIES[lang], setLang }), [lang, setLang])
  const online = !(error instanceof ApiError && error.status === 0)

  return (
    <I18nContext.Provider value={i18n}>
      <Shell view={view} theme={theme} onToggleTheme={toggleTheme} health={health} online={online}>
        {view === 'ask' && <AskView />}
        {view === 'gazette' && <GazetteView />}
        {view === 'compare' && <CompareView />}
        {view === 'audit' && <AuditView />}
      </Shell>
    </I18nContext.Provider>
  )
}
