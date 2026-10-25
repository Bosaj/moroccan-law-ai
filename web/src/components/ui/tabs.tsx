import * as React from 'react'
import { Tabs as TabsPrimitive } from 'radix-ui'
import { cn } from '../../lib/cn'

// Adapted from the shadcn/ui v4 Tabs source (Radix primitives), restyled with Mizan tokens:
// underline variant, brass indicator, logical properties so it mirrors in right-to-left.

export const Tabs = TabsPrimitive.Root

export function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn('inline-flex items-center gap-1 border-b border-line', className)}
      {...props}
    />
  )
}

export function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        'relative -mb-px inline-flex items-center px-3 py-2 text-sm font-medium text-ink-3 transition-colors',
        'hover:text-ink data-[state=active]:text-ink',
        'after:absolute after:inset-x-2 after:-bottom-px after:h-0.5 after:rounded-full after:bg-accent after:opacity-0 after:transition-opacity',
        'data-[state=active]:after:opacity-100',
        className,
      )}
      {...props}
    />
  )
}

export function TabsContent({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return <TabsPrimitive.Content className={cn('outline-none', className)} {...props} />
}
