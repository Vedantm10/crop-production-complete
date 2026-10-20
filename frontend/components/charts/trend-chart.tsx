'use client'

import { useMemo } from 'react'
import type { Metric, TimeSeriesResult } from '@/lib/data/types'
import { METRIC_LABEL, METRIC_UNIT } from '@/lib/format'
import { COLORS, METRIC_TICKFORMAT, PALETTE, baseLayout } from './chart-theme'
import { Plot } from './plot'

interface TrendChartProps {
  result: TimeSeriesResult
  metric: Metric
  className?: string
  ariaLabel: string
  showMarkers?: boolean
}

/**
 * Each series is split into an observed (solid) and a synthetic (dashed) trace
 * that share the boundary point, so estimated years are never visually mistaken
 * for observed history.
 */
export function TrendChart({ result, metric, className, ariaLabel, showMarkers = false }: TrendChartProps) {
  const { data, layout } = useMemo(() => {
    const synthetic = new Set(result.syntheticYears)
    const unit = METRIC_UNIT[metric]
    const valueFormat = metric === 'yield' ? '.2f' : ',.0f'
    const traces: Record<string, unknown>[] = []

    result.series.forEach((s, i) => {
      const color = PALETTE[i % PALETTE.length]
      const firstSynthIdx = s.points.findIndex((p) => synthetic.has(p.year))
      const observed = firstSynthIdx === -1 ? s.points : s.points.slice(0, firstSynthIdx)
      const estimated = firstSynthIdx === -1 ? [] : s.points.slice(Math.max(0, firstSynthIdx - 1))
      const common = {
        type: 'scatter',
        mode: showMarkers ? 'lines+markers' : 'lines',
        legendgroup: s.name,
        connectgaps: false,
        hovertemplate: `<b>${s.name}</b><br>%{x}: %{y:${valueFormat}} ${unit}%{customdata}<extra></extra>`,
      }
      if (observed.length) {
        traces.push({
          ...common,
          name: s.name,
          x: observed.map((p) => p.year),
          y: observed.map((p) => p.value),
          customdata: observed.map(() => ''),
          line: { color, width: 2.25, shape: 'spline', smoothing: 0.4 },
          marker: { size: 5, color },
        })
      }
      if (estimated.length) {
        traces.push({
          ...common,
          name: `${s.name} (synthetic)`,
          showlegend: observed.length === 0 || i === 0,
          x: estimated.map((p) => p.year),
          y: estimated.map((p) => p.value),
          customdata: estimated.map((p) => (synthetic.has(p.year) ? '<br><i>Synthetic / estimated</i>' : '')),
          line: { color, width: 2.25, dash: 'dash' },
          marker: { size: 5, color, symbol: 'circle-open' },
        })
      }
    })

    const shapes =
      result.syntheticYears.length > 0
        ? [
            {
              type: 'rect',
              xref: 'x',
              yref: 'paper',
              x0: Math.min(...result.syntheticYears) - 0.5,
              x1: Math.max(...result.syntheticYears) + 0.5,
              y0: 0,
              y1: 1,
              fillcolor: COLORS.synthetic,
              opacity: 0.08,
              line: { width: 0 },
              layer: 'below',
            },
          ]
        : []

    const annotations =
      result.syntheticYears.length > 0
        ? [
            {
              xref: 'x',
              yref: 'paper',
              x: (Math.min(...result.syntheticYears) + Math.max(...result.syntheticYears)) / 2,
              y: 1,
              yanchor: 'bottom',
              text: 'Synthetic',
              showarrow: false,
              font: { size: 10, color: '#9a6a08' },
            },
          ]
        : []

    return {
      data: traces,
      layout: baseLayout({
        margin: { l: 56, r: 16, t: 24, b: 40 },
        hovermode: 'x unified',
        shapes,
        annotations,
        showlegend: result.series.length > 1 || result.syntheticYears.length > 0,
        yaxis: {
          ...(baseLayout().yaxis as object),
          title: { text: `${METRIC_LABEL[metric]} (${unit})`, font: { size: 11, color: COLORS.muted } },
          tickformat: METRIC_TICKFORMAT[metric],
          rangemode: 'tozero',
        },
        xaxis: { ...(baseLayout().xaxis as object), dtick: 2, tickangle: 0 },
      }),
    }
  }, [result, metric, showMarkers])

  return <Plot data={data} layout={layout} className={className} ariaLabel={ariaLabel} />
}
