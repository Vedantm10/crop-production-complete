
'use client'

import { useMemo } from 'react'
import useSWR from 'swr'
import { Skeleton } from '@/components/ui/skeleton'
import { GEOJSON_URL } from '@/lib/data/service'
import { csvStateToGeoName, geoStateToCsvName } from '@/lib/data/state-names'
import type { BreakdownRow, Metric } from '@/lib/data/types'
import { METRIC_LABEL, METRIC_UNIT } from '@/lib/format'
import { COLORS, SEQUENTIAL_GREENS, baseLayout } from './chart-theme'
import { Plot } from './plot'

interface GeoFeature {
  properties: { NAME_1: string }
}

interface GeoCollection {
  type: 'FeatureCollection'
  features: GeoFeature[]
}

const fetchGeo = async (url: string): Promise<GeoCollection> => {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`GeoJSON request failed (${res.status})`)
  return res.json()
}

export function useIndiaGeo() {
  return useSWR(GEOJSON_URL, fetchGeo, {
    revalidateOnFocus: false,
    revalidateIfStale: false,
  })
}

interface IndiaMapProps {
  rows: BreakdownRow[]
  metric: Metric
  selected: string
  onSelect: (state: string) => void
  className?: string
}

export function IndiaMap({
  rows,
  metric,
  selected,
  onSelect,
  className,
}: IndiaMapProps) {
  const { data: geo, error } = useIndiaGeo()

  const { data, layout } = useMemo(() => {
    if (!geo) return { data: [], layout: {} }

    const geoNames = geo.features.map((f) => f.properties.NAME_1)
    const selectedGeo = selected !== 'all' ? csvStateToGeoName(selected) : 'all'

    // Map rows to GeoJSON locations
    const rowByGeo = new Map<string, BreakdownRow & { displayName: string }>()
    for (const r of rows) {
      if (r[metric] === null) continue
      const geoKey = csvStateToGeoName(r.key)
      if (!geoNames.includes(geoKey)) continue

      const existing = rowByGeo.get(geoKey)
      if (existing) {
        // Aggregate if multiple dataset rows map to the same geometry (e.g., Ladakh + J&K)
        const combinedProd = (existing.production ?? 0) + (r.production ?? 0)
        const combinedArea = (existing.area ?? 0) + (r.area ?? 0)
        existing.production = combinedProd
        existing.area = combinedArea
        existing.records = (existing.records ?? 0) + (r.records ?? 0)
        existing.cropCount = Math.max(existing.cropCount, r.cropCount)
        existing.districtCount = (existing.districtCount ?? 0) + (r.districtCount ?? 0)
        existing.yield = combinedArea > 0 ? combinedProd / combinedArea : null
      } else {
        rowByGeo.set(geoKey, {
          ...r,
          displayName: r.key,
        })
      }
    }

    const valuedGeoNames = Array.from(rowByGeo.keys())
    const valuedRows = Array.from(rowByGeo.values())
    const valuedSet = new Set(valuedGeoNames)
    const missing = geoNames.filter((name) => !valuedSet.has(name))

    const unit = METRIC_UNIT[metric]
    const valueFormat = metric === 'yield' ? '.2f' : ',.0f'
    const lineWidth = (name: string) => (name === selectedGeo ? 2.5 : 0.6)
    const lineColor = (name: string) =>
      name === selectedGeo ? COLORS.highlight : '#ffffff'

    const traces: Record<string, unknown>[] = [
      {
        type: 'choropleth',
        geojson: geo,
        featureidkey: 'properties.NAME_1',
        locations: missing,
        z: missing.map(() => 0),
        customdata: missing.map((name) => [geoStateToCsvName(name)]),
        colorscale: [
          [0, COLORS.noData],
          [1, COLORS.noData],
        ],
        showscale: false,
        marker: {
          line: {
            color: missing.map(lineColor),
            width: missing.map(lineWidth),
          },
        },
        hovertemplate:
          '<b>%{customdata[0]}</b><br>No data for current filters<extra></extra>',
      },
      {
        type: 'choropleth',
        geojson: geo,
        featureidkey: 'properties.NAME_1',
        locations: valuedGeoNames,
        z: valuedRows.map((r) => r[metric]),
        customdata: valuedRows.map((r) => [
          r.production,
          r.area,
          r.cropCount,
          r.districtCount,
          r.displayName,
        ]),
        colorscale: SEQUENTIAL_GREENS,
        marker: {
          line: {
            color: valuedGeoNames.map(lineColor),
            width: valuedGeoNames.map(lineWidth),
          },
        },
        colorbar: {
          title: {
            text: `${METRIC_LABEL[metric]}<br>(${unit})`,
            font: { size: 11, color: COLORS.muted },
          },
          thickness: 12,
          len: 0.6,
          tickformat: metric === 'yield' ? '.1f' : '.2s',
          tickfont: { size: 10, color: COLORS.muted },
          outlinewidth: 0,
        },
        hovertemplate:
          `<b>%{customdata[4]}</b><br>${METRIC_LABEL[metric]}: %{z:${valueFormat}} ${unit}` +
          '<br>Production: %{customdata[0]:,.0f} t<br>Area: %{customdata[1]:,.0f} ha' +
          '<br>Crops: %{customdata[2]} · Districts: %{customdata[3]}<extra></extra>',
      },
    ]

    return {
      data: traces,
      layout: baseLayout({
        margin: { l: 0, r: 0, t: 0, b: 0 },
        dragmode: false,
        geo: {
          fitbounds: 'locations',
          visible: false,
          projection: { type: 'mercator' },
          bgcolor: 'rgba(0,0,0,0)',
        },
      }),
    }
  }, [geo, rows, metric, selected])

  if (error) {
    return (
      <div
        className="flex size-full items-center justify-center text-sm text-destructive"
        role="alert"
      >
        Map boundaries failed to load: {error.message}
      </div>
    )
  }

  if (!geo) return <Skeleton className="size-full" />

  return (
    <Plot
      data={data}
      layout={layout}
      config={{ scrollZoom: false }}
      className={className}
      ariaLabel={`Choropleth map of India by state showing ${METRIC_LABEL[metric].toLowerCase()}. Click a state to filter.`}
      onPointClick={(p) => {
        if (p.location) {
          const csvName = geoStateToCsvName(p.location)
          onSelect(csvName === selected ? 'all' : csvName)
        }
      }}
    />
  )
}
