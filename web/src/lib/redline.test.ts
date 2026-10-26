import { describe, expect, it } from 'vitest'
import { formatDate, parseRedlineMarkdown, stripLeadingSymbols, textDir } from './redline'

describe('redline utility functions', () => {
  describe('parseRedlineMarkdown', () => {
    it('returns a single "same" segment when text has no diff markers', () => {
      const text = 'Article 1 : Le contrat est conclu pour une durée indéterminée.'
      const segments = parseRedlineMarkdown(text)
      expect(segments).toEqual([{ kind: 'same', text }])
    })

    it('returns empty array for empty string', () => {
      expect(parseRedlineMarkdown('')).toEqual([])
    })

    it('parses deleted and inserted tokens', () => {
      const markdown = 'Capital de [-100.000 DH-] {+librement fixé+}.'
      const segments = parseRedlineMarkdown(markdown)
      expect(segments).toHaveLength(5)
      expect(segments[0]).toEqual({ kind: 'same', text: 'Capital de ' })
      expect(segments[1]).toEqual({ kind: 'del', text: '100.000 DH' })
      expect(segments[2]).toEqual({ kind: 'same', text: ' ' })
      expect(segments[3]).toEqual({ kind: 'ins', text: 'librement fixé' })
      expect(segments[4]).toEqual({ kind: 'same', text: '.' })
    })

    it('handles consecutive del and ins blocks', () => {
      const markdown = '[-ancien-]{+nouveau+}'
      const segments = parseRedlineMarkdown(markdown)
      expect(segments).toEqual([
        { kind: 'del', text: 'ancien' },
        { kind: 'ins', text: 'nouveau' },
      ])
    })

    it('parses multiline text changes', () => {
      const multiline = `[-Ligne 1 ancienne
Ligne 2 ancienne-]{+Ligne 1 nouvelle
Ligne 2 nouvelle+}`
      const segments = parseRedlineMarkdown(multiline)
      expect(segments).toHaveLength(2)
      expect(segments[0].kind).toBe('del')
      expect(segments[0].text).toContain('Ligne 1 ancienne')
      expect(segments[1].kind).toBe('ins')
      expect(segments[1].text).toContain('Ligne 2 nouvelle')
    })
  })

  describe('stripLeadingSymbols', () => {
    it('removes warning and emoji symbols from start of text', () => {
      expect(stripLeadingSymbols('⚠️ Avertissement légal officiel.')).toBe('Avertissement légal officiel.')
      expect(stripLeadingSymbols('⛔ Attention aux clauses nulles.')).toBe('Attention aux clauses nulles.')
      expect(stripLeadingSymbols('🚨 Important :')).toBe('Important :')
    })

    it('leaves standard text with no symbols untouched', () => {
      expect(stripLeadingSymbols('Information juridique officielle.')).toBe('Information juridique officielle.')
      expect(stripLeadingSymbols('المعلومات القانونية الرسمية.')).toBe('المعلومات القانونية الرسمية.')
    })
  })

  describe('formatDate', () => {
    it('formats ISO dates correctly', () => {
      const formattedFr = formatDate('2025-04-10', 'fr')
      expect(formattedFr).toContain('2025')
      expect(formattedFr).toContain('10')

      const formattedEn = formatDate('2025-04-10', 'en')
      expect(formattedEn).toContain('2025')
      expect(formattedEn).toContain('10')
    })

    it('returns raw string when date is invalid', () => {
      expect(formatDate('not-a-valid-date', 'fr')).toBe('not-a-valid-date')
    })
  })

  describe('textDir', () => {
    it('returns rtl for Arabic and Darija', () => {
      expect(textDir('ar')).toBe('rtl')
      expect(textDir('darija')).toBe('rtl')
    })

    it('returns ltr for French and English', () => {
      expect(textDir('fr')).toBe('ltr')
      expect(textDir('en')).toBe('ltr')
    })
  })
})
