import { describe, expect, it } from 'vitest'
import { DICTIONARIES, UI_LANGS, labelOf } from './i18n'

describe('i18n and dictionary integrity', () => {
  it('defines dictionaries for fr, ar, and en', () => {
    expect(DICTIONARIES.fr).toBeDefined()
    expect(DICTIONARIES.ar).toBeDefined()
    expect(DICTIONARIES.en).toBeDefined()
  })

  it('has consistent top-level navigation, engine, ask, gazette, compare, audit keys across all languages', () => {
    const requiredSections = ['brand', 'nav', 'engine', 'ask', 'gazette', 'compare', 'audit', 'status', 'severity', 'domains', 'audiences'] as const

    for (const lang of ['fr', 'ar', 'en'] as const) {
      const dict = DICTIONARIES[lang]
      for (const section of requiredSections) {
        expect(dict[section as keyof typeof dict], `Missing ${section} in ${lang}`).toBeDefined()
      }
    }
  })

  it('contains Arabic script in Arabic dictionary brand and navigation', () => {
    const arabicRegex = /[\u0600-\u06FF]/
    const ar = DICTIONARIES.ar
    expect(arabicRegex.test(ar.brandAr)).toBe(true)
    expect(arabicRegex.test(ar.nav.ask)).toBe(true)
    expect(arabicRegex.test(ar.nav.gazette)).toBe(true)
    expect(arabicRegex.test(ar.nav.compare)).toBe(true)
    expect(arabicRegex.test(ar.nav.audit)).toBe(true)
  })

  it('UI_LANGS lists all supported language codes and readable labels', () => {
    const codes = UI_LANGS.map((l) => l.code)
    expect(codes).toEqual(['fr', 'ar', 'en'])
    for (const item of UI_LANGS) {
      expect(item.label.trim().length).toBeGreaterThan(0)
    }
  })

  describe('labelOf', () => {
    it('returns the mapped value when key exists', () => {
      const map = { labor_law: 'Droit du travail', family_law: 'Droit de la famille' }
      expect(labelOf(map, 'labor_law')).toBe('Droit du travail')
      expect(labelOf(map, 'family_law')).toBe('Droit de la famille')
    })

    it('falls back to replacing underscores with spaces when key is unmapped', () => {
      const map = { known_key: 'Known' }
      expect(labelOf(map, 'custom_statutory_code')).toBe('custom statutory code')
    })
  })
})
