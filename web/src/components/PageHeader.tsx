import type { ReactNode } from 'react'

export function PageHeader({ title, sub, aside }: { title: string; sub: string; aside?: ReactNode }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-6">
      <div className="max-w-[62ch]">
        <h1 className="text-2xl font-semibold tracking-tight text-ink md:text-3xl">{title}</h1>
        <p className="mt-2 text-ink-2">{sub}</p>
      </div>
      {aside}
    </header>
  )
}
