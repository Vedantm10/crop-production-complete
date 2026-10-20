'use client'

import { AlertTriangle, CheckCircle2, CopyX, FileWarning, MinusCircle, Rows3 } from 'lucide-react'
import { ChartCard } from '@/components/dashboard/chart-card'
import { KpiCard } from '@/components/dashboard/kpi-card'
import { PageHeader } from '@/components/layout/page-header'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useQuality } from '@/hooks/use-analytics'
import { formatNumber } from '@/lib/format'
import { Plot } from '@/components/charts/plot'
import { COLORS, baseLayout } from '@/components/charts/chart-theme'

export function QualityView() {
  const { data: q, error, isLoading, mutate } = useQuality()

  return (
    <>
      <PageHeader
        title="Data quality & provenance"
        description="What was cleaned, what was excluded and why, and which records are observed versus synthetic."
      />

      {q && (
        <p className="text-xs text-muted-foreground">
          Report computed by: <span className="font-medium text-foreground">{q.computedBy}</span>
        </p>
      )}

      <section aria-label="Quality summary" className="grid grid-cols-2 gap-4 lg:grid-cols-3 2xl:grid-cols-6">
        <KpiCard label="Raw rows" value={formatNumber(q?.totalRows)} icon={Rows3} isLoading={isLoading} />
        <KpiCard label="Clean rows" value={formatNumber(q?.cleanRows)} icon={CheckCircle2} isLoading={isLoading} />
        <KpiCard label="Duplicates removed" value={formatNumber(q?.duplicateRows)} icon={CopyX} isLoading={isLoading} />
        <KpiCard label="Negative values" value={formatNumber(q?.negativeValues)} icon={MinusCircle} isLoading={isLoading} />
        <KpiCard label="Missing production" value={formatNumber(q?.missingProduction)} icon={FileWarning} isLoading={isLoading} />
        <KpiCard label="Missing area" value={formatNumber(q?.missingArea)} icon={FileWarning} isLoading={isLoading} />
      </section>

      {error && (
        <ChartCard title="Quality report" error={error} onRetry={() => mutate()}>
          {null}
        </ChartCard>
      )}

      {q && q.warnings.length > 0 && (
        <Card className="border-warning/40 bg-warning/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <AlertTriangle className="size-4 text-warning" aria-hidden="true" />
              Warnings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex list-disc flex-col gap-1.5 pl-5 text-sm">
              {q.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {q && (
        <>
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <ChartCard
              className="xl:col-span-2"
              title="Records per year"
              description="Bars coloured by provenance: observed vs synthetic."
              isEmpty={q.yearCoverage.length === 0}
              bodyClassName="h-72"
            >
              <Plot
                data={(['Observed', 'Synthetic', 'Mixed'] as const)
                  .map((type) => {
                    const pts = q.yearCoverage.filter((y) => y.dataType === type)
                    return {
                      type: 'bar',
                      name: type,
                      x: pts.map((p) => p.year),
                      y: pts.map((p) => p.records),
                      marker: { color: type === 'Observed' ? COLORS.primary : type === 'Synthetic' ? COLORS.synthetic : COLORS.muted },
                      hovertemplate: `%{x}: %{y:,} records (${type})<extra></extra>`,
                    }
                  })
                  .filter((t) => t.x.length > 0)}
                layout={baseLayout({ barmode: 'stack', showlegend: true, legend: { orientation: 'h', y: 1.12 } })}
                className="size-full"
                ariaLabel="Bar chart of records per year by data type"
              />
            </ChartCard>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Provenance</CardTitle>
                <CardDescription className="text-xs">From the Data_Type column</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                {q.provenance.map((p) => {
                  const pct = q.cleanRows ? (p.records / q.cleanRows) * 100 : 0
                  return (
                    <div key={p.dataType} className="flex flex-col gap-1.5">
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-medium">{p.dataType}</span>
                        <span className="font-mono tabular-nums text-muted-foreground">
                          {formatNumber(p.records)} · {pct.toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 overflow-hidden rounded-full bg-muted" role="presentation">
                        <div
                          className={p.dataType === 'Synthetic' ? 'h-full bg-warning' : 'h-full bg-primary'}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Column profile</CardTitle>
                <CardDescription className="text-xs">Missing and invalid values per source column</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Column</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-right">Missing</TableHead>
                        <TableHead className="text-right">Missing %</TableHead>
                        <TableHead className="text-right">Invalid</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {q.columns.map((c) => (
                        <TableRow key={c.column}>
                          <TableCell className="font-mono text-xs">{c.column}</TableCell>
                          <TableCell className="text-xs text-muted-foreground">{c.dtype}</TableCell>
                          <TableCell className="text-right font-mono tabular-nums">{formatNumber(c.missing)}</TableCell>
                          <TableCell className="text-right font-mono tabular-nums">{c.missingPct.toFixed(2)}%</TableCell>
                          <TableCell className="text-right font-mono tabular-nums">{formatNumber(c.invalid)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Exclusions by analysis</CardTitle>
                <CardDescription className="text-xs">Records left out of a calculation and the reason</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Analysis</TableHead>
                        <TableHead className="text-right">Excluded</TableHead>
                        <TableHead>Reason</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {q.exclusions.map((e) => (
                        <TableRow key={e.analysis}>
                          <TableCell className="font-medium">{e.analysis}</TableCell>
                          <TableCell className="text-right font-mono tabular-nums">{formatNumber(e.excluded)}</TableCell>
                          <TableCell className="whitespace-normal text-xs text-muted-foreground">{e.reason}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">State name normalisation</CardTitle>
                <CardDescription className="text-xs">Source spellings mapped to GeoJSON ST_NM names</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                {q.stateNameMappings.length === 0 ? (
                  <p className="text-sm text-muted-foreground">All source state names already matched the map.</p>
                ) : (
                  <div className="max-h-72 overflow-auto rounded-lg border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Source name</TableHead>
                          <TableHead>Normalised</TableHead>
                          <TableHead className="text-right">Records</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {q.stateNameMappings.map((m) => (
                          <TableRow key={m.raw}>
                            <TableCell className="font-mono text-xs">{m.raw}</TableCell>
                            <TableCell>{m.normalized}</TableCell>
                            <TableCell className="text-right font-mono tabular-nums">{formatNumber(m.records)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
                <NameList title="Data states not found on the map" names={q.unmatchedStates} emptyText="Every state in the data matched a map region." />
                <NameList title="Map regions without data" names={q.geoRegionsWithoutData} emptyText="Every map region has data." />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Cleaning steps</CardTitle>
                <CardDescription className="text-xs">Applied in order before any aggregation</CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="flex flex-col gap-3">
                  {q.cleaningSteps.map((step, i) => (
                    <li key={step} className="flex gap-3 text-sm">
                      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-secondary font-mono text-xs text-secondary-foreground">
                        {i + 1}
                      </span>
                      <span className="pt-0.5 text-pretty">{step}</span>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </>
  )
}

function NameList({ title, names, emptyText }: { title: string; names: string[]; emptyText: string }) {
  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      {names.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyText}</p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {names.map((n) => (
            <Badge key={n} variant="outline">
              {n}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
