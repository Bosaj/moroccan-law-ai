import { useMemo } from 'react'
import { parseRedlineMarkdown } from '../lib/redline'

/** Renders a redline as plain text nodes; `dir="auto"` lets Arabic articles read right-to-left. */
export function Redline({ markdown }: { markdown: string }) {
  const segments = useMemo(() => parseRedlineMarkdown(markdown), [markdown])
  return (
    <p dir="auto" className="statute-fr whitespace-pre-wrap text-ink">
      {segments.map((seg, i) =>
        seg.kind === 'same' ? (
          <span key={i}>{seg.text}</span>
        ) : seg.kind === 'del' ? (
          <del key={i} className="mark-del">
            {seg.text}
          </del>
        ) : (
          <ins key={i} className="mark-ins">
            {seg.text}
          </ins>
        ),
      )}
    </p>
  )
}
