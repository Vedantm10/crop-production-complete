'use client'

import { useMemo } from 'react'
import { RankingBarChart } from '@/components/charts/bar-chart'
import { BreakdownTable } from '@/components/dashboard/breakdown-table'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { useBreakdown } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { METRIC_LABEL } from '@/lib/format'

export function RegionsView() {
  const { filters, setFilter } = useFilters()
  const metric = filters?.metric ?? 'production'
  const allStates = useMemo(() => (filters ? { ...filters, state: 'all', district: 'all' } : null), [filters])
  const byState = useBreakdown(allStates, 'state')
  const byDistrict = useBreakdown(filters, 'district')
  const state = filters?.state ?? 'all'
  const sortByMetric = <T extends { production: number; area: number; yield: number | null }>(rows: T[]) =>
    [...rows].sort((a, b) => (b[metric] ?? 0) - (a[metric] ?? 0))

  return (
    <>
      <PageHeader
        title="State & district analysis"
        description="Rank states and drill down into the districts of a selected state."
        actions={<ExportButtons />}
      />
      <FilterBar />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard
          title="States"
          description="Click a state name to drill into its districts."
          isLoading={!byState.data && !byState.error}
          error={byState.error}
          isEmpty={byState.data?.length === 0}
          onRetry={() => byState.mutate()}
          bodyClassName="h-auto"
        >
          <BreakdownTable
            rows={byState.data ?? []}
            keyLabel="State"
            selected={state}
            onSelect={(s) => setFilter('state', s === state ? 'all' : s)}
            showCrops
            showDistricts
            caption="State breakdown"
          />
        </ChartCard>
        <ChartCard
          title={state === 'all' ? 'Top 15 districts nationally' : `Top 15 districts in ${state}`}
          description={`By ${METRIC_LABEL[metric].toLowerCase()}`}
          isLoading={!byDistrict.data && !byDistrict.error}
          error={byDistrict.error}
          isEmpty={byDistrict.data?.length === 0}
          bodyClassName="h-[420px]"
        >
          <RankingBarChart
            rows={sortByMetric(byDistrict.data ?? []).slice(0, 15)}
            metric={metric}
            highlight={filters?.district}
            onSelect={state === 'all' ? undefined : (d) => setFilter('district', d === filters?.district ? 'all' : d)}
            className="size-full"
            ariaLabel="Bar chart of top districts"
          />
        </ChartCard>
      </div>

      <ChartCard
        title={state === 'all' ? 'All districts' : `Districts of ${state}`}
        description={state === 'all' ? 'Select a state to narrow this list.' : 'Click a district to filter.'}
        isLoading={!byDistrict.data && !byDistrict.error}
        error={byDistrict.error}
        isEmpty={byDistrict.data?.length === 0}
        bodyClassName="h-auto"
      >
        <BreakdownTable
          rows={byDistrict.data ?? []}
          keyLabel="District"
          selected={filters?.district}
          onSelect={state === 'all' ? undefined : (d) => setFilter('district', d === filters?.district ? 'all' : d)}
          showCrops
          caption="District breakdown"
        />
      </ChartCard>
    </>
  )
}
