import { cn } from '../../lib/cn'

interface Option<T extends string> {
  value: T
  label: string
  /** Set on options whose label is in another script, e.g. Arabic inside a French UI. */
  lang?: string
}

interface Props<T extends string> {
  value: T
  onChange: (value: T) => void
  options: Array<Option<T>>
  label: string
  className?: string
}

export function Segmented<T extends string>({ value, onChange, options, label, className }: Props<T>) {
  return (
    <div
      role="radiogroup"
      aria-label={label}
      className={cn('inline-flex rounded-lg border border-line-strong bg-surface p-0.5', className)}
    >
      {options.map((o) => {
        const active = o.value === value
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={active}
            lang={o.lang}
            onClick={() => onChange(o.value)}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              active ? 'bg-accent text-accent-ink' : 'text-ink-2 hover:text-ink',
            )}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
