'use client'

import { FlaskConical } from 'lucide-react'
import type { ReactNode } from 'react'
import { dataMode } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { formatNumber } from '@/lib/format'

interface PageHeaderProps {
  title: string
  description: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  const { meta } = useFilters()
  return (
    <div className="flex flex-col gap-4">
      {dataMode === 'demo' && (
        <div
          role="note"
          className="flex items-start gap-3 rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-sm text-warning-foreground"
        >
          <FlaskConical className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p>
            <span className="font-semibold">Demo Data.</span> All production and area values on this page are generated
            synthetic numbers for interface demonstration — they are not official agricultural statistics. Set{' '}
            <code className="rounded bg-warning/15 px-1 font-mono text-xs">NEXT_PUBLIC_ANALYTICS_API_URL</code> to connect the
            real dataset.
          </p>
        </div>
      )}
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-balance text-2xl font-semibold tracking-tight md:text-3xl">{title}</h1>
          <p className="text-pretty text-sm text-muted-foreground">{description}</p>
          {meta && (
            <p className="text-xs text-muted-foreground">
              Source: {meta.sourceLabel} · {formatNumber(meta.recordCount)} records · {meta.yearMin}–{meta.yearMax}
              {meta.lastUpdated ? ` · Updated ${new Date(meta.lastUpdated).toLocaleDateString('en-IN')}` : ''}
            </p>
          )}
        </div>
        {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
      </div>
    </div>
  )
}
