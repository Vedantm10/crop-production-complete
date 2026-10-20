'use client'

import { useMemo } from 'react'
import type { BreakdownRow, Metric } from '@/lib/data/types'
import { METRIC_UNIT } from '@/lib/format'
import { PALETTE, baseLayout } from './chart-theme'
import { Plot } from './plot'

interface DonutChartProps {
  rows: BreakdownRow[]
  metric: Exclude<Metric, 'yield'>
  className?: string
  ariaLabel: string
  onSelect?: (key: string) => void
}

export function DonutChart({ rows, metric, className, ariaLabel, onSelect }: DonutChartProps) {
  const { data, layout } = useMemo(
    () => ({
      data: [
        {
          type: 'pie',
          hole: 0.62,
          labels: rows.map((r) => r.key),
          values: rows.map((r) => r[metric]),
          sort: false,
          marker: { colors: PALETTE, line: { color: '#ffffff', width: 2 } },
          textinfo: 'percent',
          textposition: 'inside',
          insidetextfont: { color: '#ffffff', size: 11 },
          hovertemplate: `<b>%{label}</b><br>%{value:,.0f} ${METRIC_UNIT[metric]}<br>%{percent}<extra></extra>`,
        },
      ],
      layout: baseLayout({
        margin: { l: 8, r: 8, t: 8, b: 8 },
        showlegend: true,
        legend: { orientation: 'v', x: 1, y: 0.5, font: { size: 11 } },
      }),
    }),
    [rows, metric],
  )
  return <Plot data={data} layout={layout} className={className} ariaLabel={ariaLabel} onPointClick={onSelect ? (p) => onSelect(String(p.label)) : undefined} />
}
