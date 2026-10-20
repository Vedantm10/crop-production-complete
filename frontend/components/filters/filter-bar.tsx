'use client'

import { RotateCcw } from 'lucide-react'
import { useMemo } from 'react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import type { DataTypeFilter, Filters, Metric } from '@/lib/data/types'
import { useFilters } from '@/lib/filters-context'
import { FilterSelect, type FilterOption } from './filter-select'

export type FilterKey = 'years' | 'state' | 'district' | 'crop' | 'season' | 'dataType' | 'metric'

const ALL_KEYS: FilterKey[] = ['years', 'state', 'district', 'crop', 'season', 'dataType', 'metric']

const withAll = (label: string, values: string[]): FilterOption[] => [
  { value: 'all', label },
  ...values.map((v) => ({ value: v, label: v })),
]

export function FilterBar({ show = ALL_KEYS }: { show?: FilterKey[] }) {
  const { meta, filters, setFilter, setYearRange, resetFilters, isDefault } = useFilters()

  const options = useMemo(() => {
    if (!meta || !filters) return null
    const years = Array.from({ length: meta.yearMax - meta.yearMin + 1 }, (_, i) => meta.yearMin + i)
    const yearLabel = (y: number) => (meta.syntheticYears.includes(y) ? `${y} (synthetic)` : String(y))
    const crops = filters.state === 'all' ? meta.crops : (meta.cropsByState[filters.state] ?? [])
    const seasons = filters.crop === 'all' ? meta.seasons : (meta.seasonsByCrop[filters.crop] ?? [])
    return {
      yearFrom: years.map((y) => ({ value: String(y), label: yearLabel(y), disabled: y > filters.yearTo })),
      yearTo: years.map((y) => ({ value: String(y), label: yearLabel(y), disabled: y < filters.yearFrom })),
      state: withAll('All states', meta.states),
      district:
        filters.state === 'all'
          ? [{ value: 'all', label: 'Select a state first' }]
          : withAll('All districts', meta.districtsByState[filters.state] ?? []),
      crop: withAll('All crops', crops),
      season: withAll('All seasons', seasons),
      dataType: [
        { value: 'all', label: 'Observed + Synthetic' },
        { value: 'Observed', label: 'Observed only' },
        { value: 'Synthetic', label: 'Synthetic only' },
      ],
      metric: [
        { value: 'production', label: 'Production (t)' },
        { value: 'area', label: 'Area (ha)' },
        { value: 'yield', label: 'Yield (t/ha)', disabled: filters.crop === 'all' },
      ],
    }
  }, [meta, filters])

  if (!options || !filters) {
    return (
      <div className="grid grid-cols-2 gap-3 rounded-xl border bg-card p-4 md:grid-cols-4 xl:grid-cols-8" aria-busy="true">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-14" />
        ))}
      </div>
    )
  }

  return (
    <section aria-label="Filters" className="rounded-xl border bg-card p-4">
      <div className="grid grid-cols-2 items-end gap-3 md:grid-cols-4 2xl:grid-cols-8">
        {show.includes('years') && (
          <>
            <FilterSelect
              label="Year from"
              value={String(filters.yearFrom)}
              options={options.yearFrom}
              onChange={(v) => setYearRange(Number(v), filters.yearTo)}
            />
            <FilterSelect
              label="Year to"
              value={String(filters.yearTo)}
              options={options.yearTo}
              onChange={(v) => setYearRange(filters.yearFrom, Number(v))}
            />
          </>
        )}
        {show.includes('state') && (
          <FilterSelect label="State" value={filters.state} options={options.state} onChange={(v) => setFilter('state', v)} />
        )}
        {show.includes('district') && (
          <FilterSelect
            label="District"
            value={filters.district}
            options={options.district}
            disabled={filters.state === 'all'}
            onChange={(v) => setFilter('district', v)}
          />
        )}
        {show.includes('crop') && (
          <FilterSelect label="Crop" value={filters.crop} options={options.crop} onChange={(v) => setFilter('crop', v)} />
        )}
        {show.includes('season') && (
          <FilterSelect label="Season" value={filters.season} options={options.season} onChange={(v) => setFilter('season', v)} />
        )}
        {show.includes('dataType') && (
          <FilterSelect
            label="Data type"
            value={filters.dataType}
            options={options.dataType}
            onChange={(v) => setFilter('dataType', v as DataTypeFilter)}
          />
        )}
        {show.includes('metric') && (
          <FilterSelect
            label="Metric"
            value={filters.metric}
            options={options.metric}
            hint="Yield requires a single crop to be selected"
            onChange={(v) => setFilter('metric', v as Metric)}
          />
        )}
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t pt-3">
        <ActiveFilterSummary filters={filters} />
        <Button variant="ghost" size="sm" onClick={resetFilters} disabled={isDefault}>
          <RotateCcw aria-hidden="true" />
          Reset filters
        </Button>
      </div>
    </section>
  )
}

function ActiveFilterSummary({ filters }: { filters: Filters }) {
  const parts = [
    filters.yearFrom === filters.yearTo ? String(filters.yearFrom) : `${filters.yearFrom}–${filters.yearTo}`,
    filters.state !== 'all' ? filters.state : 'All India',
    filters.district !== 'all' ? filters.district : null,
    filters.crop !== 'all' ? filters.crop : 'All crops',
    filters.season !== 'all' ? filters.season : null,
    filters.dataType !== 'all' ? `${filters.dataType} only` : null,
  ].filter(Boolean)
  return (
    <p className="text-xs text-muted-foreground">
      <span className="font-medium text-foreground">Showing:</span> {parts.join(' · ')}
      {filters.crop === 'all' && <span className="ml-2 text-muted-foreground">(select one crop to enable yield)</span>}
    </p>
  )
}
