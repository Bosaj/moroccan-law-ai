export type RedlineSegment = { kind: 'same' | 'del' | 'ins'; text: string }

/**
 * Parses the server's `redline_markdown` (`[-removed-]` and `{+added+}`) into segments.
 * The UI renders segments as text nodes, so no server-supplied HTML is ever injected.
 */
export function parseRedlineMarkdown(markdown: string): RedlineSegment[] {
  const segments: RedlineSegment[] = []
  const pattern = /\[-([\s\S]*?)-\]|\{\+([\s\S]*?)\+\}/g
  let cursor = 0
  for (const match of markdown.matchAll(pattern)) {
    const index = match.index ?? 0
    if (index > cursor) segments.push({ kind: 'same', text: markdown.slice(cursor, index) })
    if (match[1] !== undefined) segments.push({ kind: 'del', text: match[1] })
    else if (match[2] !== undefined) segments.push({ kind: 'ins', text: match[2] })
    cursor = index + match[0].length
  }
  if (cursor < markdown.length) segments.push({ kind: 'same', text: markdown.slice(cursor) })
  return segments
}

/** Removes leading warning glyphs/emoji the API puts in its disclaimers; the UI draws its own icon. */
export function stripLeadingSymbols(text: string): string {
  return text.replace(/^[^\p{L}\p{N}]+/u, '').trim()
}

/** Formats an ISO date with Latin digits in every UI language. */
export function formatDate(iso: string, locale: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const tag = locale === 'ar' ? 'ar-MA-u-nu-latn' : locale
  return new Intl.DateTimeFormat(tag, { day: 'numeric', month: 'short', year: 'numeric' }).format(d)
}

/** Direction of a piece of statutory text, so Arabic articles read right-to-left in any UI language. */
export function textDir(lang: 'fr' | 'ar' | 'en' | 'darija'): 'rtl' | 'ltr' {
  return lang === 'ar' || lang === 'darija' ? 'rtl' : 'ltr'
}
