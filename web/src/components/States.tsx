import { ArrowClockwise, WifiSlash, Warning } from '@phosphor-icons/react'
import { ApiError } from '../lib/api'
import { useI18n } from '../lib/i18n'

export function ErrorPanel({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { s } = useI18n()
  const offline = error instanceof ApiError && error.status === 0
  const Icon = offline ? WifiSlash : Warning
  const title = offline ? s.offline.title : s.error.generic
  const body = offline ? s.offline.body : error instanceof Error ? error.message : ''
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-line-strong bg-surface p-4">
      <Icon size={22} weight="duotone" className="mt-0.5 shrink-0 text-sev-crit" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="font-medium text-ink">{title}</p>
        {body && <p className="mt-1 text-sm text-ink-2">{body}</p>}
        {onRetry && (
          <button type="button" className="btn-quiet mt-3" onClick={onRetry}>
            <ArrowClockwise size={14} aria-hidden="true" />
            {offline ? s.offline.retry : s.error.retry}
          </button>
        )}
      </div>
    </div>
  )
}

export function SkeletonLines({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton h-4" style={{ width: `${92 - i * 14}%` }} />
      ))}
    </div>
  )
}
