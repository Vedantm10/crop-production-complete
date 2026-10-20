'use client'

import { FlaskConical, Server } from 'lucide-react'
import { dataMode } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { cn } from '@/lib/utils'

export function DataSourceBadge({ variant = 'default' }: { variant?: 'default' | 'sidebar' | 'compact' }) {
  const { meta } = useFilters()
  const isDemo = dataMode === 'demo'
  const Icon = isDemo ? FlaskConical : Server

  if (variant === 'compact') {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
          isDemo ? 'bg-warning/15 text-warning-foreground' : 'bg-secondary text-secondary-foreground',
        )}
      >
        <Icon className="size-3.5" aria-hidden="true" />
        {isDemo ? 'Demo Data' : 'Live API'}
      </span>
    )
  }

  if (variant === 'sidebar') {
    return (
      <div className="flex flex-col gap-1.5 text-xs">
        <span
          className={cn(
            'inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 font-medium',
            isDemo ? 'bg-warning/20 text-amber-200' : 'bg-sidebar-accent text-sidebar-accent-foreground',
          )}
        >
          <Icon className="size-3.5" aria-hidden="true" />
          {isDemo ? 'Demo Data' : 'Connected to API'}
        </span>
        <p className="leading-relaxed text-sidebar-foreground/70">
          {isDemo
            ? 'Values are synthetic and for UI demonstration only.'
            : meta?.lastUpdated
              ? `Last updated ${new Date(meta.lastUpdated).toLocaleString('en-IN')}`
              : 'Backend did not report a last-updated time.'}
        </p>
      </div>
    )
  }

  return null
}
