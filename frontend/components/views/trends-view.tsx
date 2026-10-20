'use client'

import { AreaProductionChart } from '@/components/charts/area-production-chart'
import { TrendChart } from '@/components/charts/trend-chart'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { useTimeSeries } from '@/hooks/use-analytics'
import type { TimeSeriesResult } from '@/lib/data/types'
import { useFilters } from '@/lib/filters-context'
import { METRIC_LABEL } from '@/lib/format'

const isEmpty = (r?: TimeSeriesResult) => !!r && r.series.every((s) => s.points.every((p) => p.value === null))

export function TrendsView() {
  const { filters } = useFilters()
  const metric = filters?.metric ?? 'production'
  const area = useTimeSeries(filters, 'area', null)
  const production = useTimeSeries(filters, 'production', null)
  const byState = useTimeSeries(filters, metric, 'state')
  const bySeason = useTimeSeries(filters, metric, 'season')
  const synthetic = production.data?.syntheticYears ?? []

  return (
    <>
      <PageHeader
        title="Trends 1997–2025"
        description="Year-over-year movement in area, production and yield. Synthetic years are always drawn dashed and shaded."
        actions={<ExportButtons />}
      />
      <FilterBar />

      {synthetic.length > 0 && (
        <p className="rounded-lg border border-warning/40 bg-warning/10 px-4 py-3 text-xs text-warning-foreground" role="note">
          <span className="font-semibold">Synthetic years in range:</span> {synthetic[0]}
          {synthetic.length > 1 ? `–${synthetic[synthetic.length - 1]}` : ''}. These values are estimates, not observed
          statistics. Use the Data type filter to view observed records only.
        </p>
      )}

      <ChartCard
        title="Area vs production"
        description="Bars: cultivated area (left axis). Line: production (right axis)."
        isLoading={(!area.data && !area.error) || (!production.data && !production.error)}
        error={area.error ?? production.error}
        isEmpty={isEmpty(production.data) && isEmpty(area.data)}
        bodyClassName="h-96"
      >
        {area.data && production.data && (
          <AreaProductionChart area={area.data} production={production.data} className="size-full" ariaLabel="Dual-axis chart of area and production by year" />
        )}
      </ChartCard>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard
          title={`${METRIC_LABEL[metric]} — leading states`}
          description="Top 6 states for the current filters."
          isLoading={!byState.data && !byState.error}
          error={byState.error}
          isEmpty={isEmpty(byState.data)}
          bodyClassName="h-96"
        >
          {byState.data && <TrendChart result={byState.data} metric={metric} className="size-full" ariaLabel="State trend lines" />}
        </ChartCard>
        <ChartCard
          title={`${METRIC_LABEL[metric]} — by season`}
          description="Each cropping season as a separate line."
          isLoading={!bySeason.data && !bySeason.error}
          error={bySeason.error}
          isEmpty={isEmpty(bySeason.data)}
          bodyClassName="h-96"
        >
          {bySeason.data && <TrendChart result={bySeason.data} metric={metric} className="size-full" ariaLabel="Season trend lines" />}
        </ChartCard>
      </div>
    </>
  )
}
