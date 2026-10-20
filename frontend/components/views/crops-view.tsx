'use client'

import { Info } from 'lucide-react'
import { RankingBarChart } from '@/components/charts/bar-chart'
import { TrendChart } from '@/components/charts/trend-chart'
import { BreakdownTable } from '@/components/dashboard/breakdown-table'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { useBreakdown, useTimeSeries } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { METRIC_LABEL } from '@/lib/format'

export function CropsView() {
  const { filters, setFilter } = useFilters()
  const metric = filters?.metric ?? 'production'
  const byCrop = useBreakdown(filters, 'crop')
  const trend = useTimeSeries(filters, metric, 'crop')
  const yieldTrend = useTimeSeries(filters, 'yield', 'crop')
  const bySeason = useBreakdown(filters, 'season')
  const selectCrop = (c: string) => setFilter('crop', c === filters?.crop ? 'all' : c)

  return (
    <>
      <PageHeader
        title="Crop analytics"
        description="Compare crops by production, area and yield, and see how the leading crops have moved over time."
        actions={<ExportButtons />}
      />
      <FilterBar />

      <p className="flex items-start gap-2 rounded-lg bg-secondary/60 px-4 py-3 text-xs text-secondary-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
        Yield (tonnes per hectare) is computed per crop only. Summing production of different crops — for example
        coconuts counted in nuts and rice in tonnes — and dividing by total area would be misleading, so mixed-crop yields
        are not shown.
      </p>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <ChartCard
          title={`Crops ranked by ${METRIC_LABEL[metric].toLowerCase()}`}
          description="Top 15 crops. Click a bar to filter."
          isLoading={!byCrop.data && !byCrop.error}
          error={byCrop.error}
          isEmpty={byCrop.data?.length === 0}
          bodyClassName="h-[460px]"
        >
          <RankingBarChart
            rows={[...(byCrop.data ?? [])].sort((a, b) => (b[metric] ?? 0) - (a[metric] ?? 0)).slice(0, 15)}
            metric={metric}
            highlight={filters?.crop}
            onSelect={selectCrop}
            className="size-full"
            ariaLabel="Bar chart ranking crops"
          />
        </ChartCard>
        <ChartCard
          title={`${METRIC_LABEL[metric]} of leading crops over time`}
          description="Top 6 crops for the current filters. Dashed = synthetic years."
          isLoading={!trend.data && !trend.error}
          error={trend.error}
          isEmpty={trend.data?.series.length === 0}
          bodyClassName="h-[460px]"
        >
          {trend.data && <TrendChart result={trend.data} metric={metric} className="size-full" ariaLabel="Multi-line chart of leading crops by year" />}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard
          className="xl:col-span-2"
          title="Yield trend by crop"
          description="Tonnes per hectare for the top 6 crops."
          isLoading={!yieldTrend.data && !yieldTrend.error}
          error={yieldTrend.error}
          isEmpty={yieldTrend.data?.series.length === 0}
        >
          {yieldTrend.data && <TrendChart result={yieldTrend.data} metric="yield" className="size-full" ariaLabel="Yield trend by crop" />}
        </ChartCard>
        <ChartCard
          title="Season split"
          description={`${METRIC_LABEL[metric]} by season`}
          isLoading={!bySeason.data && !bySeason.error}
          error={bySeason.error}
          isEmpty={bySeason.data?.length === 0}
        >
          <RankingBarChart
            rows={bySeason.data ?? []}
            metric={metric === 'yield' ? 'production' : metric}
            orientation="v"
            highlight={filters?.season}
            onSelect={(s) => setFilter('season', s === filters?.season ? 'all' : s)}
            className="size-full"
            ariaLabel="Bar chart by season"
          />
        </ChartCard>
      </div>

      <ChartCard
        title="All crops"
        description="Full crop breakdown for the current filters."
        isLoading={!byCrop.data && !byCrop.error}
        error={byCrop.error}
        isEmpty={byCrop.data?.length === 0}
        bodyClassName="h-auto"
      >
        <BreakdownTable rows={byCrop.data ?? []} keyLabel="Crop" selected={filters?.crop} onSelect={selectCrop} showDistricts caption="Crop breakdown" />
      </ChartCard>
    </>
  )
}
