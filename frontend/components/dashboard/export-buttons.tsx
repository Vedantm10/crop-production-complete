'use client'

import { Download, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuGroup } from '@/components/ui/dropdown-menu'
import { downloadText } from '@/lib/data/csv'
import { analyticsService } from '@/lib/data/service'
import type { Dimension } from '@/lib/data/types'
import { useFilters } from '@/lib/filters-context'

const AGG_OPTIONS: { dimension: Dimension; label: string }[] = [
  { dimension: 'state', label: 'Aggregated by state' },
  { dimension: 'district', label: 'Aggregated by district' },
  { dimension: 'crop', label: 'Aggregated by crop' },
  { dimension: 'season', label: 'Aggregated by season' },
]

export function ExportButtons() {
  const { filters } = useFilters()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(kind: 'records' | Dimension) {
    if (!filters) return
    setBusy(true)
    setError(null)
    try {
      const stamp = `${filters.yearFrom}-${filters.yearTo}`
      if (kind === 'records') {
        downloadText(`crop-records-${stamp}.csv`, await analyticsService.exportFilteredCsv(filters))
      } else {
        downloadText(`crop-by-${kind}-${stamp}.csv`, await analyticsService.exportAggregatedCsv(filters, kind))
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex items-center gap-2">
      {error && (
        <span className="text-xs text-destructive" role="alert">
          Export failed: {error}
        </span>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="outline" size="sm" disabled={!filters || busy} />}>
          {busy ? <Loader2 className="animate-spin" aria-hidden="true" /> : <Download aria-hidden="true" />}
          Export CSV
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuGroup>
            <DropdownMenuLabel>Current filters</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => run('records')}>Filtered records</DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            {AGG_OPTIONS.map((o) => (
              <DropdownMenuItem key={o.dimension} onClick={() => run(o.dimension)}>
                {o.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
