import type { Metric } from './data/types'

const compact = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 })
const integer = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 })

export function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return integer.format(value)
}

/** Returns a value scaled to million / thousand with a unit suffix. */
export function scaled(value: number | null | undefined): { value: string; suffix: string } {
  if (value === null || value === undefined || Number.isNaN(value)) return { value: '—', suffix: '' }
  const abs = Math.abs(value)
  if (abs >= 1e6) return { value: compact.format(value / 1e6), suffix: 'M' }
  if (abs >= 1e3) return { value: compact.format(value / 1e3), suffix: 'K' }
  return { value: compact.format(value), suffix: '' }
}

export function formatTonnes(value: number | null | undefined) {
  const s = scaled(value)
  return s.value === '—' ? '—' : `${s.value}${s.suffix ? ` ${s.suffix}` : ''} t`
}

export function formatHectares(value: number | null | undefined) {
  const s = scaled(value)
  return s.value === '—' ? '—' : `${s.value}${s.suffix ? ` ${s.suffix}` : ''} ha`
}

export function formatYield(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  return `${value.toFixed(2)} t/ha`
}

export const METRIC_LABEL: Record<Metric, string> = {
  production: 'Production',
  area: 'Cultivated area',
  yield: 'Yield',
}

export const METRIC_UNIT: Record<Metric, string> = {
  production: 'tonnes',
  area: 'hectares',
  yield: 't/ha',
}

export function formatMetric(metric: Metric, value: number | null | undefined) {
  if (metric === 'production') return formatTonnes(value)
  if (metric === 'area') return formatHectares(value)
  return formatYield(value)
}

export function formatPct(value: number | null) {
  if (value === null) return '—'
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
}
