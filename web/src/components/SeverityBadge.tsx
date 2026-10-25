import { Info, Minus, Warning, WarningOctagon } from '@phosphor-icons/react'
import type { Severity } from '../lib/types'
import { useI18n } from '../lib/i18n'
import { cn } from '../lib/cn'

const TONE: Record<Severity, string> = {
  CRITICAL: 'text-sev-crit',
  HIGH: 'text-sev-high',
  MEDIUM: 'text-ink-2',
  LOW: 'text-ink-3',
}

const ICON = {
  CRITICAL: WarningOctagon,
  HIGH: Warning,
  MEDIUM: Info,
  LOW: Minus,
} as const

/** Severity is conveyed by icon shape and label as well as colour. */
export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const { s } = useI18n()
  const Icon = ICON[severity]
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border border-current/30 px-2 py-0.5 text-xs font-medium',
        TONE[severity],
        className,
      )}
    >
      <Icon size={13} weight="bold" aria-hidden="true" />
      {s.severity[severity]}
    </span>
  )
}
