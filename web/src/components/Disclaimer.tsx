import { Warning } from '@phosphor-icons/react'
import { stripLeadingSymbols } from '../lib/redline'
import { useI18n } from '../lib/i18n'

/** Standing disclaimer. Prefers the server text for the current result, else the UI default. */
export function Disclaimer({ text }: { text?: string }) {
  const { s } = useI18n()
  const clean = text ? stripLeadingSymbols(text) : s.disclaimer
  return (
    <p className="flex items-start gap-2 text-xs leading-relaxed text-ink-3">
      <Warning size={14} weight="bold" className="mt-0.5 shrink-0" aria-hidden="true" />
      <span dir="auto">{clean}</span>
    </p>
  )
}
