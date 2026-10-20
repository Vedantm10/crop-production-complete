'use client'

import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { useDeferredValue, useMemo, useState } from 'react'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useRecords } from '@/hooks/use-analytics'
import type { CropRecord, RecordQuery } from '@/lib/data/types'
import { useFilters } from '@/lib/filters-context'
import { formatNumber } from '@/lib/format'

const COLUMNS: { key: keyof CropRecord; label: string; numeric?: boolean }[] = [
  { key: 'state', label: 'State' },
  { key: 'district', label: 'District' },
  { key: 'year', label: 'Year', numeric: true },
  { key: 'season', label: 'Season' },
  { key: 'crop', label: 'Crop' },
  { key: 'area', label: 'Area (ha)', numeric: true },
  { key: 'production', label: 'Production (t)', numeric: true },
  { key: 'dataType', label: 'Data type' },
]

const PAGE_SIZE = 25

export function ExplorerView() {
  const { filters } = useFilters()
  const [search, setSearch] = useState('')
  const deferredSearch = useDeferredValue(search)
  const [sortBy, setSortBy] = useState<keyof CropRecord>('year')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [page, setPage] = useState(1)

  const query = useMemo<RecordQuery | null>(
    () => (filters ? { filters, search: deferredSearch, sortBy, sortDir, page, pageSize: PAGE_SIZE } : null),
    [filters, deferredSearch, sortBy, sortDir, page],
  )
  const { data, error, isLoading, mutate } = useRecords(query)
  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1
  const safePage = Math.min(page, totalPages)

  function toggleSort(key: keyof CropRecord) {
    setPage(1)
    if (key === sortBy) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortBy(key)
      setSortDir(key === 'production' || key === 'area' || key === 'year' ? 'desc' : 'asc')
    }
  }

  return (
    <>
      <PageHeader
        title="Data explorer"
        description="Browse the cleaned record-level dataset. Filters, search and sorting combine; exports respect the current filters."
        actions={<ExportButtons />}
      />
      <FilterBar />

      <ChartCard
        title="Records"
        description={data ? `${formatNumber(data.total)} matching records` : 'Loading records…'}
        action={
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
              placeholder="Search state, district, crop…"
              aria-label="Search records"
              className="pl-8"
            />
          </div>
        }
        isLoading={isLoading && !data}
        error={error}
        onRetry={() => mutate()}
        isEmpty={data?.total === 0}
        bodyClassName="h-auto min-h-64"
        footer={
          data && data.total > 0 ? (
            <nav aria-label="Pagination" className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
              <span>
                Showing {formatNumber((safePage - 1) * PAGE_SIZE + 1)}–{formatNumber(Math.min(safePage * PAGE_SIZE, data.total))} of{' '}
                {formatNumber(data.total)}
              </span>
              <div className="flex items-center gap-1">
                <Button variant="outline" size="icon-sm" onClick={() => setPage(safePage - 1)} disabled={safePage <= 1} aria-label="Previous page">
                  <ChevronLeft aria-hidden="true" />
                </Button>
                <span className="px-2 tabular-nums">
                  Page {safePage} of {formatNumber(totalPages)}
                </span>
                <Button variant="outline" size="icon-sm" onClick={() => setPage(safePage + 1)} disabled={safePage >= totalPages} aria-label="Next page">
                  <ChevronRight aria-hidden="true" />
                </Button>
              </div>
            </nav>
          ) : null
        }
      >
        <div className="overflow-x-auto rounded-lg border">
          <Table>
            <caption className="sr-only">Crop production records</caption>
            <TableHeader>
              <TableRow>
                {COLUMNS.map((c) => {
                  const active = sortBy === c.key
                  const Icon = !active ? ArrowUpDown : sortDir === 'asc' ? ArrowUp : ArrowDown
                  return (
                    <TableHead
                      key={c.key}
                      className={c.numeric ? 'text-right' : undefined}
                      aria-sort={active ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
                    >
                      <button
                        type="button"
                        onClick={() => toggleSort(c.key)}
                        className="inline-flex items-center gap-1 hover:text-foreground"
                      >
                        {c.label}
                        <Icon className="size-3.5 opacity-60" aria-hidden="true" />
                      </button>
                    </TableHead>
                  )
                })}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.rows.map((r) => (
                <TableRow key={r.id}>
                  <TableCell className="font-medium">
                    {r.state}
                    {r.rawState !== r.state && <span className="block text-xs font-normal text-muted-foreground">source: {r.rawState}</span>}
                  </TableCell>
                  <TableCell>{r.district}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">{r.year}</TableCell>
                  <TableCell>{r.season}</TableCell>
                  <TableCell>{r.crop}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">{r.area === null ? <Missing /> : formatNumber(r.area)}</TableCell>
                  <TableCell className="text-right font-mono tabular-nums">{r.production === null ? <Missing /> : formatNumber(r.production)}</TableCell>
                  <TableCell>
                    <Badge variant={r.dataType === 'Synthetic' ? 'outline' : 'secondary'} className={r.dataType === 'Synthetic' ? 'border-warning/60 text-warning-foreground' : undefined}>
                      {r.dataType}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </ChartCard>
    </>
  )
}

function Missing() {
  return <span className="text-xs italic text-muted-foreground">missing</span>
}
