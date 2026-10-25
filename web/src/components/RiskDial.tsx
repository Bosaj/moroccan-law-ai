import { useEffect, useState } from 'react'
import type { AuditStatus } from '../lib/types'
import { useI18n } from '../lib/i18n'

const R = 54
const C = 2 * Math.PI * R

const STROKE: Record<AuditStatus, string> = {
  COMPLIANT: 'var(--ins)',
  REVIEW_REQUIRED: 'var(--sev-high)',
  NON_COMPLIANT_HIGH_RISK: 'var(--sev-crit)',
}

/** Ring gauge. The arc animates from empty to the score on mount (stroke-dashoffset only). */
export function RiskDial({ score, status }: { score: number; status: AuditStatus }) {
  const { s } = useI18n()
  const [shown, setShown] = useState(0)
  useEffect(() => {
    const id = requestAnimationFrame(() => setShown(score))
    return () => cancelAnimationFrame(id)
  }, [score])

  return (
    <div className="relative size-36 shrink-0" role="img" aria-label={`${s.audit.score}: ${score}/100, ${s.status[status]}`}>
      <svg viewBox="0 0 132 132" className="size-full -rotate-90">
        <circle cx="66" cy="66" r={R} fill="none" stroke="var(--line)" strokeWidth="10" />
        <circle
          cx="66"
          cy="66"
          r={R}
          fill="none"
          stroke={STROKE[status]}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={C * (1 - shown / 100)}
          style={{ transition: 'stroke-dashoffset 900ms cubic-bezier(0.16, 1, 0.3, 1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-4xl font-semibold tabular-nums tracking-tight text-ink">{score}</span>
        <span className="eyebrow mt-0.5">/ 100</span>
      </div>
    </div>
  )
}
