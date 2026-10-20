'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

interface PlotlyEventPoint {
  location?: string
  x?: unknown
  y?: unknown
  label?: unknown
  customdata?: unknown
}

interface PlotlyLike {
  react(el: HTMLElement, data: unknown[], layout: unknown, config: unknown): Promise<unknown>
  purge(el: HTMLElement): void
  Plots: { resize(el: HTMLElement): void }
}

type PlotElement = HTMLDivElement & {
  on?: (event: string, cb: (e: { points: PlotlyEventPoint[] }) => void) => void
  removeAllListeners?: (event: string) => void
}

let plotlyPromise: Promise<PlotlyLike> | null = null
function loadPlotly() {
  plotlyPromise ??= import('plotly.js-dist-min').then((mod) => ((mod as { default?: unknown }).default ?? mod) as PlotlyLike)
  return plotlyPromise
}

export interface PlotProps {
  data: Record<string, unknown>[]
  layout: Record<string, unknown>
  config?: Record<string, unknown>
  onPointClick?: (point: PlotlyEventPoint) => void
  className?: string
  ariaLabel: string
}

export function Plot({ data, layout, config, onPointClick, className, ariaLabel }: PlotProps) {
  const ref = useRef<PlotElement>(null)
  const [plotly, setPlotly] = useState<PlotlyLike | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const clickRef = useRef(onPointClick)
  clickRef.current = onPointClick
  const boundRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    loadPlotly()
      .then((p) => !cancelled && setPlotly(p))
      .catch((err: Error) => !cancelled && setLoadError(err.message))
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!plotly || !el) return
    plotly
      .react(el, data, layout, { displaylogo: false, responsive: true, modeBarButtonsToRemove: ['select2d', 'lasso2d'], ...config })
      .then(() => {
        if (!boundRef.current && el.on) {
          el.on('plotly_click', (e) => {
            const point = e.points?.[0]
            if (point) clickRef.current?.(point)
          })
          boundRef.current = true
        }
      })
  }, [plotly, data, layout, config])

  useEffect(() => {
    const el = ref.current
    if (!plotly || !el) return
    const observer = new ResizeObserver(() => plotly.Plots.resize(el))
    observer.observe(el)
    return () => {
      observer.disconnect()
      el.removeAllListeners?.('plotly_click')
      boundRef.current = false
      plotly.purge(el)
    }
  }, [plotly])

  if (loadError) {
    return (
      <div className={cn('flex items-center justify-center text-sm text-destructive', className)} role="alert">
        Chart library failed to load: {loadError}
      </div>
    )
  }

  return (
    <div className={cn('relative', className)} role="figure" aria-label={ariaLabel}>
      {!plotly && <Skeleton className="absolute inset-0" />}
      <div ref={ref} className="size-full" />
    </div>
  )
}
