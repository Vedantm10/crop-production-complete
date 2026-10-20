'use client'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { BreakdownRow } from '@/lib/data/types'
import { formatNumber, formatYield } from '@/lib/format'
import { cn } from '@/lib/utils'

interface BreakdownTableProps {
  rows: BreakdownRow[]
  keyLabel: string
  selected?: string
  onSelect?: (key: string) => void
  showCrops?: boolean
  showDistricts?: boolean
  caption: string
}

export function BreakdownTable({ rows, keyLabel, selected, onSelect, showCrops, showDistricts, caption }: BreakdownTableProps) {
  const total = rows.reduce((s, r) => s + r.production, 0)
  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border">
      <Table>
        <caption className="sr-only">{caption}</caption>
        <TableHeader className="sticky top-0 bg-card">
          <TableRow>
            <TableHead>{keyLabel}</TableHead>
            <TableHead className="text-right">Production (t)</TableHead>
            <TableHead className="text-right">Share</TableHead>
            <TableHead className="text-right">Area (ha)</TableHead>
            <TableHead className="text-right">Yield (t/ha)</TableHead>
            {showCrops && <TableHead className="text-right">Crops</TableHead>}
            {showDistricts && <TableHead className="text-right">Districts</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.key} className={cn(selected === r.key && 'bg-secondary/60')}>
              <TableCell className="font-medium">
                {onSelect ? (
                  <button
                    type="button"
                    className="text-left underline-offset-4 hover:underline focus-visible:underline"
                    onClick={() => onSelect(r.key)}
                    aria-pressed={selected === r.key}
                  >
                    {r.key}
                  </button>
                ) : (
                  r.key
                )}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">{formatNumber(r.production)}</TableCell>
              <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                {total > 0 ? `${((r.production / total) * 100).toFixed(1)}%` : '—'}
              </TableCell>
              <TableCell className="text-right font-mono tabular-nums">{formatNumber(r.area)}</TableCell>
              <TableCell className="text-right font-mono tabular-nums">{r.yield === null ? '—' : formatYield(r.yield).replace(/\s*t\/ha$/, '')}</TableCell>
              {showCrops && <TableCell className="text-right font-mono tabular-nums">{r.cropCount}</TableCell>}
              {showDistricts && <TableCell className="text-right font-mono tabular-nums">{r.districtCount}</TableCell>}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
