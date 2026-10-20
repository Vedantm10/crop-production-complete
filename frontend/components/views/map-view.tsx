'use client'

import { X } from 'lucide-react'
import { useMemo } from 'react'
import { RankingBarChart } from '@/components/charts/bar-chart'
import { IndiaMap } from '@/components/charts/india-map'
import { ChartCard } from '@/components/dashboard/chart-card'
import { ExportButtons } from '@/components/dashboard/export-buttons'
import { FilterBar } from '@/components/filters/filter-bar'
import { PageHeader } from '@/components/layout/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useBreakdown, useKpis } from '@/hooks/use-analytics'
import { useFilters } from '@/lib/filters-context'
import { METRIC_LABEL, formatHectares, formatMetric, formatNumber, formatPct, formatTonnes } from '@/lib/format'

export function MapView() {
  const { filters, setFilter } = useFilters()
  const allStates = useMemo(() => (filters ? { ...filters, state: 'all', district: 'all' } : null), [filters])
  const byState = useBreakdown(allStates, 'state')
  const metric = filters?.metric ?? 'production'
  const selected = filters?.state ?? 'all'

  return (
    <>
      <PageHeader
        title="India state map"
        description="Choropleth of the selected metric by state. Click a state to drill into it; click again to clear."
        actions={<ExportButtons />}
      />
      <FilterBar />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <ChartCard
          className="xl:col-span-2"
          title={`${METRIC_LABEL[metric]} by state`}
          description="Light grey regions have no records for the current filters — they are not zero production."
          isLoading={!byState.data && !byState.error}
          error={byState.error}
          onRetry={() => byState.mutate()}
          bodyClassName="h-[560px] md:h-[680px]"
        >
          <IndiaMap
            rows={byState.data ?? []}
            metric={metric}
            selected={selected}
            onSelect={(s) => setFilter('state', s)}
            className="size-full"
          />
        </ChartCard>
        <div className="flex flex-col gap-4">
          {selected === 'all' ? (
            <ChartCard
              title="State ranking"
              description={`All states by ${METRIC_LABEL[metric].toLowerCase()}`}
              isLoading={!byState.data && !byState.error}
              error={byState.error}
              isEmpty={byState.data?.length === 0}
              bodyClassName="h-[680px]"
            >
              <RankingBarChart
                rows={[...(byState.data ?? [])].sort((a, b) => (b[metric] ?? 0) - (a[metric] ?? 0)).slice(0, 20)}
                metric={metric}
                onSelect={(s) => setFilter('state', s)}
                className="size-full"
                ariaLabel="Bar chart ranking the top 20 states"
              />
            </ChartCard>
          ) : (
            <StateDetail state={selected} onClear={() => setFilter('state', 'all')} />
          )}
        </div>
      </div>
    </>
  )
}

function StateDetail({ state, onClear }: { state: string; onClear: () => void }) {
  const { filters } = useFilters()
  const kpis = useKpis(filters)
  const crops = useBreakdown(filters, 'crop')
  const districts = useBreakdown(filters, 'district')
  const metric = filters?.metric ?? 'production'
  const k = kpis.data

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-2">
          <div className="flex flex-col gap-1">
            <CardDescription className="text-xs uppercase tracking-wide">Selected state</CardDescription>
            <CardTitle className="text-xl">{state}</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={onClear}>
            <X aria-hidden="true" />
            Clear
          </Button>
        </CardHeader>
        <CardContent>
          {kpis.isLoading || !k ? (
            <Skeleton className="h-28 w-full" />
          ) : (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <Stat label="Production" value={formatTonnes(k.totalProduction)} />
              <Stat label="Area" value={formatHectares(k.totalArea)} />
              <Stat label="Crops" value={formatNumber(k.cropCount)} />
              <Stat label="Districts" value={formatNumber(k.districtCount)} />
              <Stat label="Records" value={formatNumber(k.recordCount)} />
              <Stat label={k.lastYear ? `Δ ${k.lastYear}` : 'YoY change'} value={formatPct(k.productionChangePct)} />
            </dl>
          )}
        </CardContent>
      </Card>
      <ChartCard
        title="Top crops"
        description={`In ${state}, by ${METRIC_LABEL[metric].toLowerCase()}`}
        isLoading={!crops.data && !crops.error}
        error={crops.error}
        isEmpty={crops.data?.length === 0}
        bodyClassName="h-64"
      >
        <RankingBarChart rows={(crops.data ?? []).slice(0, 8)} metric={metric} className="size-full" ariaLabel={`Top crops in ${state}`} />
      </ChartCard>
      <ChartCard
        title="Top districts"
        description={`In ${state}, by ${METRIC_LABEL[metric].toLowerCase()}`}
        isLoading={!districts.data && !districts.error}
        error={districts.error}
        isEmpty={districts.data?.length === 0}
        bodyClassName="h-64"
        footer={
          districts.data && districts.data.length > 0 ? (
            <p className="text-xs text-muted-foreground">
              Leading district: <span className="font-medium text-foreground">{districts.data[0].key}</span> ·{' '}
              {formatMetric(metric, districts.data[0][metric])}
            </p>
          ) : null
        }
      >
        <RankingBarChart rows={(districts.data ?? []).slice(0, 8)} metric={metric} className="size-full" ariaLabel={`Top districts in ${state}`} />
      </ChartCard>
    </>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-mono font-medium tabular-nums">{value}</dd>
    </div>
  )
}
