'use client'

import { Layers, MapPinned, Sprout, Wheat } from 'lucide-react'
import Link from 'next/link'
import { useMemo } from 'react'
import { RankingBarChart } from '@/components/charts/bar-chart'
import { DonutChart } from '@/components/charts/donut-chart'
import { IndiaMap } from '@/components/charts/india-map'
import { TrendChart } from '@/components/charts/trend-chart'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { KpiCard } from '@/components/dashboard/kpi-card'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { buttonVariants } from '@/components/ui/button'
import { useBreakdown, useKpis, useTimeSeries } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { METRIC_LABEL, formatNumber, scaled } from '@/lib/format'

export function OverviewView() {
  const { filters, setFilter } = useFilters()
  const allStates = useMemo(() => (filters ? { ...filters, state: 'all', district: 'all' } : null), [filters])

  const kpis = useKpis(filters)
  const byState = useBreakdown(allStates, 'state')
  const byCrop = useBreakdown(filters, 'crop')
  const bySeason = useBreakdown(filters, 'season')
  const trend = useTimeSeries(filters, filters?.metric ?? 'production', null)

  const metric = filters?.metric ?? 'production'
  const shareMetric = metric === 'yield' ? 'production' : metric
  const k = kpis.data
  const prod = scaled(k?.totalProduction)
  const area = scaled(k?.totalArea)
  const changeLabel = k?.lastYear ? `${k.lastYear} vs ${k.lastYear - 1}` : 'needs 2+ years'

  const topCrops = useMemo(() => {
    const rows = byCrop.data ?? []
    if (rows.length <= 7) return rows
    const head = rows.slice(0, 6)
    const rest = rows.slice(6)
    return [
      ...head,
      {
        key: 'Other',
        production: rest.reduce((s, r) => s + r.production, 0),
        area: rest.reduce((s, r) => s + r.area, 0),
        yield: null,
        records: rest.reduce((s, r) => s + r.records, 0),
        cropCount: rest.length,
        districtCount: 0,
      },
    ]
  }, [byCrop.data])

  return (
    <>
      <PageHeader
        title="National overview"
        description="Production, cultivated area and crop mix across Indian states. Filters apply to every panel on this page."
        actions={<ExportButtons />}
      />
      <FilterBar />

      <section aria-label="Key indicators" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Total production"
          value={prod.value}
          unit={prod.suffix ? `${prod.suffix} tonnes` : 'tonnes'}
          icon={Wheat}
          changePct={k ? k.productionChangePct : undefined}
          changeLabel={changeLabel}
          isLoading={kpis.isLoading || (!kpis.data && !kpis.error)}
          error={kpis.error}
          onRetry={() => kpis.mutate()}
        />
        <KpiCard
          label="Cultivated area"
          value={area.value}
          unit={area.suffix ? `${area.suffix} hectares` : 'hectares'}
          icon={Layers}
          changePct={k ? k.areaChangePct : undefined}
          changeLabel={changeLabel}
          isLoading={kpis.isLoading || (!kpis.data && !kpis.error)}
          error={kpis.error}
          onRetry={() => kpis.mutate()}
        />
        <KpiCard
          label="Crops"
          value={formatNumber(k?.cropCount)}
          icon={Sprout}
          caption={k ? `${formatNumber(k.recordCount)} records in ${k.yearLabel}` : undefined}
          isLoading={kpis.isLoading || (!kpis.data && !kpis.error)}
          error={kpis.error}
          onRetry={() => kpis.mutate()}
        />
        <KpiCard
          label="States · Districts"
          value={k ? `${k.stateCount} · ${formatNumber(k.districtCount)}` : '—'}
          icon={MapPinned}
          caption={k && k.excludedRecords > 0 ? `${formatNumber(k.excludedRecords)} records excluded (invalid values)` : 'All records valid'}
          isLoading={kpis.isLoading || (!kpis.data && !kpis.error)}
          error={kpis.error}
          onRetry={() => kpis.mutate()}
        />
      </section>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
        <ChartCard
          className="xl:col-span-3"
          title={`${METRIC_LABEL[metric]} by state`}
          description="Click a state to filter the dashboard. Grey states have no data for the current filters."
          action={
            <Link href="/map" className={buttonVariants({ variant: 'ghost', size: 'sm' })}>
              Full map
            </Link>
          }
          isLoading={byState.isLoading || (!byState.data && !byState.error)}
          error={byState.error}
          onRetry={() => byState.mutate()}
          bodyClassName="h-[460px]"
        >
          <IndiaMap
            rows={byState.data ?? []}
            metric={metric}
            selected={filters?.state ?? 'all'}
            onSelect={(s) => setFilter('state', s)}
            className="size-full"
          />
        </ChartCard>
        <ChartCard
          className="xl:col-span-2"
          title="Top 10 states"
          description={`Ranked by ${METRIC_LABEL[metric].toLowerCase()}`}
          isLoading={byState.isLoading || (!byState.data && !byState.error)}
          error={byState.error}
          isEmpty={byState.data?.length === 0}
          onRetry={() => byState.mutate()}
          bodyClassName="h-[460px]"
        >
          <RankingBarChart
            rows={[...(byState.data ?? [])].sort((a, b) => (b[metric] ?? 0) - (a[metric] ?? 0)).slice(0, 10)}
            metric={metric}
            highlight={filters?.state}
            onSelect={(s) => setFilter('state', s === filters?.state ? 'all' : s)}
            className="size-full"
            ariaLabel="Horizontal bar chart of the top 10 states"
          />
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard
          className="xl:col-span-2"
          title={`${METRIC_LABEL[metric]} over time`}
          description="Dashed segments and the shaded band mark synthetic (estimated) years."
          isLoading={trend.isLoading || (!trend.data && !trend.error)}
          error={trend.error}
          isEmpty={!trend.data || trend.data.series.length === 0 || trend.data.series.every((s) => s.points.every((p) => p.value === null))}
          onRetry={() => trend.mutate()}
        >
          {trend.data && <TrendChart result={trend.data} metric={metric} className="size-full" ariaLabel="Line chart of the selected metric by year" />}
        </ChartCard>
        <ChartCard
          title="Crop mix"
          description={`Share of ${shareMetric === 'area' ? 'cultivated area' : 'production'}`}
          isLoading={byCrop.isLoading || (!byCrop.data && !byCrop.error)}
          error={byCrop.error}
          isEmpty={topCrops.length === 0}
          onRetry={() => byCrop.mutate()}
        >
          <DonutChart
            rows={topCrops}
            metric={shareMetric}
            className="size-full"
            ariaLabel="Donut chart of crop share"
            onSelect={(c) => c !== 'Other' && setFilter('crop', c === filters?.crop ? 'all' : c)}
          />
        </ChartCard>
      </div>

      <ChartCard
        title="By season"
        description={`${METRIC_LABEL[metric]} for each cropping season`}
        isLoading={bySeason.isLoading || (!bySeason.data && !bySeason.error)}
        error={bySeason.error}
        isEmpty={bySeason.data?.length === 0}
        onRetry={() => bySeason.mutate()}
        bodyClassName="h-64"
      >
        <RankingBarChart
          rows={bySeason.data ?? []}
          metric={metric}
          highlight={filters?.season}
          orientation="v"
          onSelect={(s) => setFilter('season', s === filters?.season ? 'all' : s)}
          className="size-full"
          ariaLabel="Bar chart of the selected metric by season"
        />
      </ChartCard>
    </>
  )
}
