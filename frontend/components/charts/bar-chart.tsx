'use client'

import { useMemo } from 'react'
import type { BreakdownRow, Metric } from '@/lib/data/types'
import { METRIC_LABEL, METRIC_UNIT } from '@/lib/format'
import { COLORS, METRIC_TICKFORMAT, baseLayout } from './chart-theme'
import { Plot } from './plot'

interface RankingBarChartProps {
  rows: BreakdownRow[]
  metric: Metric
  highlight?: string
  onSelect?: (key: string) => void
  className?: string
  ariaLabel: string
  orientation?: 'h' | 'v'
}

export function RankingBarChart({ rows, metric, highlight, onSelect, className, ariaLabel, orientation = 'h' }: RankingBarChartProps) {
  const { data, layout } = useMemo(() => {
    const ordered = orientation === 'h' ? [...rows].reverse() : rows
    const keys = ordered.map((r) => r.key)
    const values = ordered.map((r) => r[metric])
    const colors = ordered.map((r) => (highlight && highlight !== 'all' ? (r.key === highlight ? COLORS.primaryDark : '#9fcfb1') : COLORS.primary))
    const valueFormat = metric === 'yield' ? '.2f' : ',.0f'
    const trace: Record<string, unknown> = {
      type: 'bar',
      orientation,
      x: orientation === 'h' ? values : keys,
      y: orientation === 'h' ? keys : values,
      marker: { color: colors, line: { width: 0 } },
      hovertemplate: `<b>%{${orientation === 'h' ? 'y' : 'x'}}</b><br>${METRIC_LABEL[metric]}: %{${orientation === 'h' ? 'x' : 'y'}:${valueFormat}} ${METRIC_UNIT[metric]}<extra></extra>`,
    }
    const valueAxis = { ...(baseLayout().xaxis as object), tickformat: METRIC_TICKFORMAT[metric], rangemode: 'tozero' }
    const categoryAxis = { ...(baseLayout().yaxis as object), gridcolor: 'rgba(0,0,0,0)', ticksuffix: '  ' }
    return {
      data: [trace],
      layout: baseLayout({
        bargap: 0.28,
        margin: orientation === 'h' ? { l: 8, r: 16, t: 8, b: 32 } : { l: 48, r: 8, t: 8, b: 64 },
        xaxis: orientation === 'h' ? valueAxis : { ...categoryAxis, tickangle: -35 },
        yaxis: orientation === 'h' ? categoryAxis : valueAxis,
        showlegend: false,
      }),
    }
  }, [rows, metric, highlight, orientation])

  return (
    <Plot
      data={data}
      layout={layout}
      className={className}
      ariaLabel={ariaLabel}
      onPointClick={onSelect ? (p) => onSelect(String(orientation === 'h' ? p.y : p.x)) : undefined}
    />
  )
}
