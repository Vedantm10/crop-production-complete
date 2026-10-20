'use client'

import useSWR from 'swr'
import { analyticsService } from '@/lib/data/service'
import type { Dimension, Filters, Metric, RecordQuery } from '@/lib/data/types'

const swrOptions = { keepPreviousData: true, revalidateOnFocus: false }

export function useMeta() {
  return useSWR('meta', () => analyticsService.getMeta(), swrOptions)
}

export function useKpis(filters: Filters | null) {
  return useSWR(filters ? ['kpis', filters] : null, ([, f]) => analyticsService.getKpis(f), swrOptions)
}

export function useBreakdown(filters: Filters | null, dimension: Dimension) {
  return useSWR(filters ? ['breakdown', filters, dimension] : null, ([, f, d]) => analyticsService.getBreakdown(f, d), swrOptions)
}

export function useTimeSeries(filters: Filters | null, metric: Metric, groupBy: Dimension | null, keys?: string[]) {
  return useSWR(
    filters ? ['timeseries', filters, metric, groupBy, keys ?? null] : null,
    ([, f, m, g, k]) => analyticsService.getTimeSeries(f, m, g, k ?? undefined),
    swrOptions,
  )
}

export function useRecords(query: RecordQuery | null) {
  return useSWR(query ? ['records', query] : null, ([, q]) => analyticsService.getRecords(q), swrOptions)
}

export function useQuality() {
  return useSWR('quality', () => analyticsService.getQuality(), swrOptions)
}

export function useProcessingStatus() {
  return useSWR('processing', () => analyticsService.getProcessingStatus(), swrOptions)
}

export const dataMode = analyticsService.mode
