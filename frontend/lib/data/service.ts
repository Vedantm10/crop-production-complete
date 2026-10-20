
import {
  applyFilters,
  breakdown,
  buildMeta,
  buildQualityReport,
  cleanRecords,
  computeKpis,
  queryRecords,
  timeSeries,
} from './aggregate'
import { breakdownToCsv, recordsToCsv } from './csv'
import { generateDemoRecords } from './demo/demo-data'
import { PROCESSING_COMPONENTS } from './processing'
import type {
  BreakdownRow,
  DatasetMeta,
  Dimension,
  Filters,
  KpiSummary,
  Metric,
  ProcessingComponent,
  QualityReport,
  RecordPage,
  RecordQuery,
  TimeSeriesResult,
} from './types'

export interface AnalyticsService {
  mode: 'demo' | 'api'
  getMeta(): Promise<DatasetMeta>
  getKpis(filters: Filters): Promise<KpiSummary>
  getBreakdown(filters: Filters, dimension: Dimension): Promise<BreakdownRow[]>
  getTimeSeries(
    filters: Filters,
    metric: Metric,
    groupBy: Dimension | null,
    keys?: string[],
  ): Promise<TimeSeriesResult>
  getRecords(query: RecordQuery): Promise<RecordPage>
  getQuality(): Promise<QualityReport>
  getProcessingStatus(): Promise<ProcessingComponent[]>
  exportFilteredCsv(filters: Filters): Promise<string>
  exportAggregatedCsv(filters: Filters, dimension: Dimension): Promise<string>
}

export const GEOJSON_URL = '/geo/india_states.geojson'

function demoDataset() {
  const raw = generateDemoRecords()
  const { clean, duplicates } = cleanRecords(raw)
  return { raw, clean, duplicates }
}

async function loadGeoNames(): Promise<string[] | null> {
  try {
    const res = await fetch(GEOJSON_URL, { cache: 'no-store' })
    if (!res.ok) return null

    const geo = (await res.json()) as {
      features: { properties: { ST_NM: string } }[]
    }

    return geo.features.map((f) => f.properties.ST_NM)
  } catch {
    return null
  }
}

const demoService: AnalyticsService = {
  mode: 'demo',

  async getMeta() {
    return buildMeta(
      demoDataset().clean,
      'demo',
      'Demo dataset (synthetic values, generated in browser)',
      null,
    )
  },

  async getKpis(filters) {
    return computeKpis(demoDataset().clean, filters)
  },

  async getBreakdown(filters, dimension) {
    return breakdown(demoDataset().clean, dimension, filters)
  },

  async getTimeSeries(filters, metric, groupBy, keys) {
    return timeSeries(demoDataset().clean, filters, metric, groupBy, { keys })
  },

  async getRecords(query) {
    return queryRecords(demoDataset().clean, query)
  },

  async getQuality() {
    const { raw, clean, duplicates } = demoDataset()
    return buildQualityReport(raw, clean, duplicates, await loadGeoNames())
  },

  async getProcessingStatus() {
    return PROCESSING_COMPONENTS.map((c) => ({
      ...c,
      state: 'not_connected' as const,
    }))
  },

  async exportFilteredCsv(filters) {
    return recordsToCsv(applyFilters(demoDataset().clean, filters))
  },

  async exportAggregatedCsv(filters, dimension) {
    return breakdownToCsv(
      dimension,
      breakdown(demoDataset().clean, dimension, filters),
    )
  },
}

const EMPTY_FILTER_VALUES = new Set([
  '',
  'all',
  'all states',
  'all districts',
  'all crops',
  'all seasons',
])

function selected(value: string): string | undefined {
  const normalized = value.trim()

  return !normalized || EMPTY_FILTER_VALUES.has(normalized.toLowerCase())
    ? undefined
    : normalized
}

function yearList(filters: Filters): string | undefined {
  const years: number[] = []

  for (let year = filters.yearFrom; year <= filters.yearTo; year++) {
    years.push(year)
  }

  return years.length ? years.join(',') : undefined
}

function addParam(
  params: URLSearchParams,
  key: string,
  value: string | undefined,
) {
  if (value !== undefined) params.set(key, value)
}

function filtersToParams(filters: Filters) {
  const params = new URLSearchParams()

  addParam(params, 'years', yearList(filters))
  addParam(params, 'states', selected(filters.state))
  addParam(params, 'crops', selected(filters.crop))
  addParam(params, 'seasons', selected(filters.season))

  return params
}

function numberValue(value: unknown): number {
  const result = Number(value)
  return Number.isFinite(result) ? result : 0
}

function textValue(value: unknown): string {
  return value == null ? '' : String(value)
}

type ApiRecord = Record<string, unknown>

async function fetchJson<T>(
  baseUrl: string,
  path: string,
  params?: URLSearchParams,
): Promise<T> {
  const query = params?.toString()
  const url = `${baseUrl.replace(/\/$/, '')}${path}${query ? `?${query}` : ''}`

  console.info('[Analytics API] Request:', url)

  let response: Response

  try {
    response = await fetch(url, {
      cache: 'no-store',
      headers: { Accept: 'application/json' },
    })
  } catch (error) {
    console.error('[Analytics API] Network/CORS error:', url, error)
    throw new Error(
      `Unable to connect to the analytics API at ${url}. Check the browser console and backend CORS configuration.`,
    )
  }

  if (!response.ok) {
    const bodyText = await response.text().catch(() => '')
    console.error(
      '[Analytics API] HTTP error:',
      response.status,
      url,
      bodyText,
    )

    let detail = ''

    try {
      const body = JSON.parse(bodyText) as { detail?: unknown }
      if (typeof body.detail === 'string') detail = `: ${body.detail}`
    } catch {
      if (bodyText) detail = `: ${bodyText.slice(0, 200)}`
    }

    throw new Error(`API ${path} returned ${response.status}${detail}`)
  }

  try {
    const data = (await response.json()) as T
    console.info('[Analytics API] Success:', path)
    return data
  } catch (error) {
    console.error('[Analytics API] Invalid JSON response:', url, error)
    throw new Error(`API ${path} returned an invalid JSON response`)
  }
}

function recordsFromApi(
  records: ApiRecord[],
  stateOverride?: string,
): import('./types').CropRecord[] {
  return records.map((row, index) => {
    const rawState = textValue(row.State_Name ?? row.state ?? stateOverride)
    const year = numberValue(row.Crop_Year ?? row.year)
    const areaValue = row.Area ?? row.area
    const productionValue = row.Production ?? row.production

    return {
      id: index + 1,
      rawState,
      state: rawState,
      district: textValue(row.District_Name ?? row.district),
      year,
      season: textValue(row.Season ?? row.season),
      crop: textValue(row.Crop ?? row.crop),
      area: areaValue == null ? null : numberValue(areaValue),
      production:
        productionValue == null ? null : numberValue(productionValue),
      dataType: year >= 2024 ? 'Synthetic' : 'Observed',
    }
  })
}

function normalizeBreakdown(
  rows: ApiRecord[],
  dimension: Dimension,
): BreakdownRow[] {
  const keyField: Record<Dimension, string> = {
    state: 'State_Name',
    district: 'District_Name',
    crop: 'Crop',
    season: 'Season',
  }

  return rows.map((row) => ({
    key: textValue(row[keyField[dimension]] ?? row.key ?? row[dimension]),
    production: numberValue(
      row.Total_Production ?? row.Production ?? row.production,
    ),
    area: numberValue(row.Total_Area ?? row.Area ?? row.area),
    yield:
      row.Yield_t_per_ha == null && row.yield == null
        ? null
        : numberValue(row.Yield_t_per_ha ?? row.yield),
    records: numberValue(row.Record_Count ?? row.records),
    cropCount: numberValue(row.cropCount),
    districtCount: numberValue(row.districtCount),
  }))
}

function normalizeTimeSeries(
  rows: ApiRecord[],
  metric: Metric,
  seriesName: string,
): TimeSeriesResult {
  const valueField =
    metric === 'production'
      ? 'Total_Production'
      : metric === 'area'
        ? 'Total_Area'
        : 'Yield_t_per_ha'

  const points = rows.map((row) => {
    const year = numberValue(row.Crop_Year ?? row.year)
    const rawValue = row[valueField] ?? row.value

    return {
      year,
      value: rawValue == null ? null : numberValue(rawValue),
      synthetic: year >= 2024,
    }
  })

  return {
    metric,
    series: [{ name: seriesName, points }],
    syntheticYears: [
      ...new Set(points.filter((p) => p.synthetic).map((p) => p.year)),
    ],
  }
}

function normalizeMeta(response: ApiRecord): DatasetMeta {
  const years = Array.isArray(response.years)
    ? response.years.map(numberValue)
    : []

  const states = Array.isArray(response.states)
    ? response.states.map(textValue)
    : []

  const crops = Array.isArray(response.crops)
    ? response.crops.map(textValue)
    : []

  const seasons = Array.isArray(response.seasons)
    ? response.seasons.map(textValue)
    : []

  const districtsByState =
    response.districts_by_state &&
    typeof response.districts_by_state === 'object'
      ? (response.districts_by_state as Record<string, string[]>)
      : {}

  const cropsByState =
    response.crops_by_state && typeof response.crops_by_state === 'object'
      ? (response.crops_by_state as Record<string, string[]>)
      : {}

  const seasonsByCrop =
    response.seasons_by_crop && typeof response.seasons_by_crop === 'object'
      ? (response.seasons_by_crop as Record<string, string[]>)
      : {}

  return {
    source: 'api',
    sourceLabel: 'Crop production dataset · FastAPI / Pandas',
    lastUpdated: null,
    recordCount: numberValue(
      response.record_count ?? response.records ?? 463847,
    ),
    columns: [
      'State_Name',
      'District_Name',
      'Crop_Year',
      'Season',
      'Crop',
      'Area',
      'Production',
      'Data_Type',
    ],
    yearMin: years.length ? Math.min(...years) : 1997,
    yearMax: years.length ? Math.max(...years) : 2025,
    states,
    crops,
    seasons,
    districtsByState,
    cropsByState,
    seasonsByCrop,
    syntheticYears: Array.isArray(response.potentially_extended_years)
      ? response.potentially_extended_years.map(numberValue)
      : [2024, 2025],
  }
}

function normalizeQuality(response: ApiRecord): QualityReport {
  const totalRows = numberValue(response.total_records)
  const missingProduction = numberValue(response.missing_production)
  const missingArea = numberValue(response.missing_area)
  const duplicateRows = numberValue(response.duplicate_rows_full)

  const yearRange = Array.isArray(response.year_range)
    ? response.year_range.map(numberValue)
    : [1997, 2025]

  const limitations = Array.isArray(response.limitations)
    ? response.limitations.map(textValue)
    : []

  const warnings = [
    ...limitations,
    textValue(response.provenance_note),
    textValue(response.coconut_unit_caveat),
  ].filter(Boolean)

  return {
    computed: true,
    computedBy: 'FastAPI / Pandas',
    totalRows,
    cleanRows: Math.max(0, totalRows - missingProduction),
    duplicateRows,
    negativeValues: 0,
    missingProduction,
    missingArea,
    columns: [],
    yearCoverage: yearRange.map((year) => ({
      year,
      records: 0,
      dataType: year >= 2024 ? 'Synthetic' : 'Observed',
    })),
    provenance: [{ dataType: 'Observed', records: totalRows }],
    stateNameMappings: [],
    unmatchedStates: [],
    geoRegionsWithoutData: [],
    exclusions: [
      {
        analysis: 'Production aggregations',
        excluded: missingProduction,
        reason:
          'Missing production values are excluded, not replaced with zero.',
      },
    ],
    warnings,
    cleaningSteps: [
      'Loaded and cleaned the source CSV with Python and Pandas.',
      'Missing production values are excluded from production calculations.',
      'Years 2024–2025 are flagged as potentially extrapolated.',
      'Coconut output is measured in nuts, not tonnes.',
    ],
  }
}

function createApiService(baseUrl: string): AnalyticsService {
  return {
    mode: 'api',

    async getMeta() {
      return normalizeMeta(
        await fetchJson<ApiRecord>(baseUrl, '/api/metadata'),
      )
    },

    async getKpis(filters) {
      const stateParams = filtersToParams(filters)
      const yearParams = filtersToParams(filters)
      const cropParams = filtersToParams(filters)
      cropParams.set('n', '115')

      const [stateResponse, yearResponse, cropResponse] = await Promise.all([
        fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/statewise',
          stateParams,
        ),
        fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/yearwise',
          yearParams,
        ),
        fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/cropwise',
          cropParams,
        ),
      ])

      const stateRows = stateResponse.data ?? []
      const yearRows = yearResponse.data ?? []
      const cropRows = cropResponse.data ?? []

      const lastYear = yearRows.length
        ? Math.max(...yearRows.map((r) => numberValue(r.Crop_Year)))
        : null

      const currentYear = yearRows.find(
        (r) => numberValue(r.Crop_Year) === lastYear,
      )

      const previousYear = yearRows.find(
        (r) => numberValue(r.Crop_Year) === (lastYear ?? 0) - 1,
      )

      const pctChange = (current: unknown, previous: unknown) => {
        const a = numberValue(current)
        const b = numberValue(previous)
        return previous == null || b === 0 ? null : ((a - b) / b) * 100
      }

      return {
        totalProduction: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Total_Production),
          0,
        ),
        totalArea: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Total_Area),
          0,
        ),
        cropCount: cropRows.length,
        stateCount: stateRows.length,
        districtCount: 0,
        recordCount: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Record_Count),
          0,
        ),
        excludedRecords: 0,
        yearLabel: `${filters.yearFrom}–${filters.yearTo}`,
        productionChangePct: pctChange(
          currentYear?.Total_Production,
          previousYear?.Total_Production,
        ),
        areaChangePct: pctChange(
          currentYear?.Total_Area,
          previousYear?.Total_Area,
        ),
        lastYear,
      } satisfies KpiSummary
    },

    async getBreakdown(filters, dimension) {
      const params = filtersToParams(filters)

      if (dimension === 'state') {
        const result = await fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/statewise',
          params,
        )
        return normalizeBreakdown(result.data ?? [], dimension)
      }

      if (dimension === 'crop') {
        params.set('n', '115')
        const result = await fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/cropwise',
          params,
        )
        return normalizeBreakdown(result.data ?? [], dimension)
      }

      if (dimension === 'season') {
        const result = await fetchJson<{ data: ApiRecord[] }>(
          baseUrl,
          '/api/seasonal',
          params,
        )
        return normalizeBreakdown(result.data ?? [], dimension)
      }

      const result = await fetchJson<{ data: ApiRecord[] }>(
        baseUrl,
        '/api/districts',
        params,
      )
      return normalizeBreakdown(result.data ?? [], dimension)
    },

    async getTimeSeries(filters, metric, groupBy, keys) {
      const params = filtersToParams(filters)
      let path = '/api/yearwise'
      let seriesName = 'India'

      if (selected(filters.state)) {
        params.set('state', filters.state)
        path = '/api/state-trend'
        seriesName = filters.state
      } else if (selected(filters.crop)) {
        params.set('crop', filters.crop)
        path = '/api/crop-trend'
        seriesName = filters.crop
      }

      const response = await fetchJson<ApiRecord>(baseUrl, path, params)
      const rows = Array.isArray(response.data)
        ? (response.data as ApiRecord[])
        : []

      return normalizeTimeSeries(rows, metric, seriesName)
    },

    async getRecords(query: RecordQuery): Promise<RecordPage> {
      const params = new URLSearchParams()
      const filters = query.filters

      if (filters.yearFrom) params.set('year_from', String(filters.yearFrom))
      if (filters.yearTo) params.set('year_to', String(filters.yearTo))

      const s = selected(filters.state)
      const d = selected(filters.district)
      const c = selected(filters.crop)
      const sn = selected(filters.season)
      const dt = filters.dataType !== 'all' ? filters.dataType : undefined

      if (s) params.set('state', s)
      if (d) params.set('district', d)
      if (c) params.set('crop', c)
      if (sn) params.set('season', sn)
      if (dt) params.set('data_type', dt)

      if (query.search) params.set('search', query.search)
      params.set('sort_by', query.sortBy)
      params.set('sort_order', query.sortDir)
      params.set('page', String(query.page))
      params.set('page_size', String(Math.min(query.pageSize, 100)))

      const response = await fetchJson<ApiRecord>(
        baseUrl,
        '/api/records',
        params,
      )

      const rawRecords = Array.isArray(response.records)
        ? (response.records as ApiRecord[])
        : []

      return {
        rows: recordsFromApi(rawRecords),
        total: numberValue(response.total),
        page: numberValue(response.page),
        pageSize: numberValue(response.page_size),
      }
    },

    async getQuality() {
      return normalizeQuality(
        await fetchJson<ApiRecord>(baseUrl, '/api/quality'),
      )
    },

    async getProcessingStatus() {
      return PROCESSING_COMPONENTS.map((component) => ({
        ...component,
        state: 'not_connected' as const,
        error: 'The backend does not currently expose processing status.',
      }))
    },

    async exportFilteredCsv(filters: Filters) {
      const params = new URLSearchParams()

      if (filters.yearFrom) params.set('year_from', String(filters.yearFrom))
      if (filters.yearTo) params.set('year_to', String(filters.yearTo))

      const s = selected(filters.state)
      const d = selected(filters.district)
      const c = selected(filters.crop)
      const sn = selected(filters.season)
      const dt = filters.dataType !== 'all' ? filters.dataType : undefined

      if (s) params.set('state', s)
      if (d) params.set('district', d)
      if (c) params.set('crop', c)
      if (sn) params.set('season', sn)
      if (dt) params.set('data_type', dt)

      const query = params.toString()
      const url = `${baseUrl.replace(/\/$/, '')}/api/export/records${query ? `?${query}` : ''}`

      console.info('[Analytics API] CSV export:', url)

      let response: Response

      try {
        response = await fetch(url, { cache: 'no-store' })
      } catch (error) {
        console.error('[Analytics API] CSV export network error:', error)
        throw new Error('Unable to connect to the API for CSV export.')
      }

      if (!response.ok) {
        const bodyText = await response.text().catch(() => '')
        console.error(
          '[Analytics API] CSV export failed:',
          response.status,
          bodyText,
        )
        throw new Error(`Export failed (${response.status})`)
      }

      return response.text()
    },

    async exportAggregatedCsv(filters, dimension) {
      const rows = await this.getBreakdown(filters, dimension)
      return breakdownToCsv(dimension, rows)
    },
  }
}

const apiUrl = process.env.NEXT_PUBLIC_ANALYTICS_API_URL?.trim()

export const analyticsService: AnalyticsService = apiUrl
  ? createApiService(apiUrl.replace(/\/+$/, ''))
  : demoService
