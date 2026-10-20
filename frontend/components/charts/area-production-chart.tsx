'use client'

import { useMemo } from 'react'
import type { TimeSeriesResult } from '@/lib/data/types'
import { COLORS, baseLayout } from './chart-theme'
import { Plot } from './plot'

interface AreaProductionChartProps {
  area: TimeSeriesResult
  production: TimeSeriesResult
  className?: string
  ariaLabel: string
}

/** Dual-axis view: area as bars (left axis), production as a line (right axis). */
export function AreaProductionChart({ area, production, className, ariaLabel }: AreaProductionChartProps) {
  const { data, layout } = useMemo(() => {
    const areaPoints = area.series[0]?.points ?? []
    const prodPoints = production.series[0]?.points ?? []
    return {
      data: [
        {
          type: 'bar',
          name: 'Area (ha)',
          x: areaPoints.map((p) => p.year),
          y: areaPoints.map((p) => p.value),
          marker: { color: areaPoints.map((p) => (p.synthetic ? '#f1d89b' : '#bfe0c9')) },
          hovertemplate: '%{x}: %{y:,.0f} ha<extra>Area</extra>',
        },
        {
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Production (t)',
          yaxis: 'y2',
          x: prodPoints.map((p) => p.year),
          y: prodPoints.map((p) => p.value),
          line: { color: COLORS.primaryDark, width: 2.25 },
          marker: { size: 5, color: prodPoints.map((p) => (p.synthetic ? COLORS.synthetic : COLORS.primaryDark)) },
          hovertemplate: '%{x}: %{y:,.0f} t<extra>Production</extra>',
        },
      ],
      layout: baseLayout({
        margin: { l: 56, r: 56, t: 12, b: 40 },
        bargap: 0.25,
        hovermode: 'x unified',
        yaxis: { ...(baseLayout().yaxis as object), title: { text: 'Area (ha)', font: { size: 11, color: COLORS.muted } }, tickformat: '.3s' },
        yaxis2: {
          overlaying: 'y',
          side: 'right',
          showgrid: false,
          tickformat: '.3s',
          tickfont: { color: COLORS.muted },
          title: { text: 'Production (t)', font: { size: 11, color: COLORS.muted } },
        },
        xaxis: { ...(baseLayout().xaxis as object), dtick: 2 },
      }),
    }
  }, [area, production])

  return <Plot data={data} layout={layout} className={className} ariaLabel={ariaLabel} />
}
