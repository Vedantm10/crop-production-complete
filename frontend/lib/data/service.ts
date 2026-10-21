
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
      features: { properties: { NAME_1?: string; ST_NM?: string } }[]
    }

    return geo.features.map((f) => f.properties.NAME_1 ?? f.properties.ST_NM ?? '')
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
  if (filters.yearFrom <= 1997 && filters.yearTo >= 2025) {
    return undefined
  }
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
  addParam(params, 'district', selected(filters.district))
  addParam(params, 'crops', selected(filters.crop))
  addParam(params, 'seasons', selected(filters.season))
  if (filters.dataType && filters.dataType !== 'all') {
    params.set('data_type', filters.dataType)
  }

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

const inFlightRequests = new Map<string, Promise<unknown>>()
const responseCache = new Map<string, { data: unknown; expiry: number }>()
const CACHE_TTL_MS = 30_000

async function fetchJson<T>(
  baseUrl: string,
  path: string,
  params?: URLSearchParams,
  maxRetries = 5,
): Promise<T> {
  const query = params?.toString()
  const url = `${baseUrl.replace(/\/$/, '')}${path}${query ? `?${query}` : ''}`

  // Check client response cache
  const cached = responseCache.get(url)
  if (cached && Date.now() < cached.expiry) {
    return cached.data as T
  }

  // Deduplicate concurrent in-flight requests for the exact same URL
  const inFlight = inFlightRequests.get(url)
  if (inFlight) {
    return inFlight as Promise<T>
  }

  const promise = (async () => {
    console.info('[Analytics API] Request:', url)

    let lastError: unknown = null
    const retryDelays = [2000, 3000, 5000, 7000, 10000, 10000]

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      let response: Response

      try {
        response = await fetch(url, {
          cache: 'no-store',
          headers: { Accept: 'application/json' },
        })
      } catch (error) {
        lastError = error
        if (attempt < maxRetries) {
          const delay = retryDelays[attempt] || 4000
          console.warn(
            `[Analytics API] Request attempt ${attempt + 1} failed (${url}). Retrying in ${delay / 1000}s (server cold start / waking up)...`,
          )
          await new Promise((res) => setTimeout(res, delay))
          continue
        }
        console.error('[Analytics API] Network/CORS error:', url, error)
        throw new Error(
          `Unable to connect to the analytics API at ${url}. Check browser console and ensure the backend is active.`,
        )
      }

      if (!response.ok) {
        if (response.status === 404 && path !== '/api/metadata' && path !== '/api/health') {
          console.warn('[Analytics API] No data matches (404), returning empty structure:', url)
          return {
            data: [],
            records: [],
            total: 0,
            page: 1,
            page_size: 25,
            total_pages: 1,
          } as unknown as T
        }

        if (
          (response.status === 502 || response.status === 503 || response.status === 504) &&
          attempt < maxRetries
        ) {
          const delay = retryDelays[attempt] || 4000
          console.warn(
            `[Analytics API] Server returned ${response.status} for ${url}. Retrying in ${delay / 1000}s (backend warming up)...`,
          )
          await new Promise((res) => setTimeout(res, delay))
          continue
        }

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
        responseCache.set(url, { data, expiry: Date.now() + CACHE_TTL_MS })
        console.info('[Analytics API] Success:', path)
        return data
      } catch (error) {
        console.error('[Analytics API] Invalid JSON response:', url, error)
        throw new Error(`API ${path} returned an invalid JSON response`)
      }
    }

    throw lastError || new Error(`Failed to fetch ${url}`)
  })()

  inFlightRequests.set(url, promise)
  try {
    return (await promise) as T
  } finally {
    inFlightRequests.delete(url)
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
    cropCount: numberValue(row.Crop_Count ?? row.cropCount),
    districtCount: numberValue(row.District_Count ?? row.districtCount),
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

  const columns = Array.isArray(response.columns)
    ? (response.columns as ApiRecord[]).map((c) => ({
        column: textValue(c.column),
        dtype: textValue(c.dtype),
        missing: numberValue(c.missing),
        missingPct: numberValue(c.missingPct),
        invalid: numberValue(c.invalid),
      }))
    : []

  const yearCoverage = Array.isArray(response.year_coverage)
    ? (response.year_coverage as ApiRecord[]).map((y) => ({
        year: numberValue(y.year),
        records: numberValue(y.records),
        dataType: (y.dataType === 'Synthetic' ? 'Synthetic' : 'Observed') as import('./types').DataType,
      }))
    : yearRange.map((year) => ({
        year,
        records: 0,
        dataType: (year >= 2024 ? 'Synthetic' : 'Observed') as import('./types').DataType,
      }))

  const provenance = Array.isArray(response.provenance)
    ? (response.provenance as ApiRecord[]).map((p) => ({
        dataType: (p.dataType === 'Synthetic' ? 'Synthetic' : 'Observed') as import('./types').DataType,
        records: numberValue(p.records),
      }))
    : [{ dataType: 'Observed' as const, records: totalRows }]

  const stateNameMappings = Array.isArray(response.state_name_mappings)
    ? (response.state_name_mappings as ApiRecord[]).map((m) => ({
        raw: textValue(m.raw),
        normalized: textValue(m.normalized),
        records: numberValue(m.records),
      }))
    : []

  const unmatchedStates = Array.isArray(response.unmatched_states)
    ? response.unmatched_states.map(textValue)
    : []

  const geoRegionsWithoutData = Array.isArray(response.geo_regions_without_data)
    ? response.geo_regions_without_data.map(textValue)
    : []

  return {
    computed: true,
    computedBy: 'FastAPI / Pandas',
    totalRows,
    cleanRows: Math.max(0, totalRows - missingProduction),
    duplicateRows,
    negativeValues: 0,
    missingProduction,
    missingArea,
    columns,
    yearCoverage,
    provenance,
    stateNameMappings,
    unmatchedStates,
    geoRegionsWithoutData,
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
      const params = filtersToParams(filters)

      try {
        const kpiResp = await fetchJson<ApiRecord>(baseUrl, '/api/kpis', params)
        if (kpiResp && typeof kpiResp.totalProduction === 'number') {
          return {
            totalProduction: numberValue(kpiResp.totalProduction),
            totalArea: numberValue(kpiResp.totalArea),
            cropCount: numberValue(kpiResp.cropCount),
            stateCount: numberValue(kpiResp.stateCount),
            districtCount: numberValue(kpiResp.districtCount),
            recordCount: numberValue(kpiResp.recordCount),
            excludedRecords: numberValue(kpiResp.excludedRecords),
            yearLabel: textValue(kpiResp.yearLabel || `${filters.yearFrom}–${filters.yearTo}`),
            productionChangePct: kpiResp.productionChangePct == null ? null : numberValue(kpiResp.productionChangePct),
            areaChangePct: kpiResp.areaChangePct == null ? null : numberValue(kpiResp.areaChangePct),
            lastYear: kpiResp.lastYear == null ? null : numberValue(kpiResp.lastYear),
          } satisfies KpiSummary
        }
      } catch {
        // Fall back to legacy endpoints if /api/kpis is unavailable
      }

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

      const stateRows = Array.isArray(stateResponse.data) ? stateResponse.data : []
      const yearRows = Array.isArray(yearResponse.data) ? yearResponse.data : []
      const cropRows = Array.isArray(cropResponse.data) ? cropResponse.data : []

      const lastYear = yearRows.length
        ? Math.max(...yearRows.map((r) => numberValue(r.Crop_Year ?? r.year)))
        : null

      const currentYear = yearRows.find(
        (r) => numberValue(r.Crop_Year ?? r.year) === lastYear,
      )

      const previousYear = yearRows.find(
        (r) => numberValue(r.Crop_Year ?? r.year) === (lastYear ?? 0) - 1,
      )

      const pctChange = (current: unknown, previous: unknown) => {
        const a = numberValue(current)
        const b = numberValue(previous)
        return previous == null || b === 0 ? null : ((a - b) / b) * 100
      }

      // Compute actual district count from state aggregations
      const calculatedDistrictCount = stateRows.reduce(
        (sum, r) => sum + numberValue(r.District_Count ?? r.districtCount),
        0,
      )

      return {
        totalProduction: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Total_Production ?? r.Production ?? r.production),
          0,
        ),
        totalArea: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Total_Area ?? r.Area ?? r.area),
          0,
        ),
        cropCount: cropRows.length,
        stateCount: stateRows.length,
        districtCount: calculatedDistrictCount,
        recordCount: yearRows.reduce(
          (sum, r) => sum + numberValue(r.Record_Count ?? r.records ?? r.count),
          0,
        ),
        excludedRecords: 0,
        yearLabel: `${filters.yearFrom}–${filters.yearTo}`,
        productionChangePct: pctChange(
          currentYear?.Total_Production ?? currentYear?.Production ?? currentYear?.production,
          previousYear?.Total_Production ?? previousYear?.Production ?? previousYear?.production,
        ),
        areaChangePct: pctChange(
          currentYear?.Total_Area ?? currentYear?.Area ?? currentYear?.area,
          previousYear?.Total_Area ?? previousYear?.Area ?? previousYear?.area,
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

      // District breakdown
      params.set('n', '100')
      if (selected(filters.state)) {
        params.set('state', filters.state)
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

      if (groupBy === 'crop') {
        const topCrops = keys?.length
          ? keys
          : (await this.getBreakdown(filters, 'crop')).slice(0, 6).map((r) => r.key)

        if (!topCrops.length) {
          return { metric, series: [], syntheticYears: [2024, 2025] }
        }

        const seriesList = await Promise.all(
          topCrops.map(async (crop) => {
            const p = new URLSearchParams(params)
            p.set('crop', crop)
            const resp = await fetchJson<ApiRecord>(baseUrl, '/api/crop-trend', p)
            const rows = Array.isArray(resp.data) ? (resp.data as ApiRecord[]) : []
            return normalizeTimeSeries(rows, metric, crop).series[0]
          }),
        )

        return {
          metric,
          series: seriesList.filter(Boolean),
          syntheticYears: [2024, 2025],
        }
      }

      if (groupBy === 'state') {
        const topStates = keys?.length
          ? keys
          : (await this.getBreakdown(filters, 'state')).slice(0, 6).map((r) => r.key)

        if (!topStates.length) {
          return { metric, series: [], syntheticYears: [2024, 2025] }
        }

        const seriesList = await Promise.all(
          topStates.map(async (state) => {
            const p = new URLSearchParams(params)
            p.set('state', state)
            const resp = await fetchJson<ApiRecord>(baseUrl, '/api/state-trend', p)
            const rows = Array.isArray(resp.data) ? (resp.data as ApiRecord[]) : []
            return normalizeTimeSeries(rows, metric, state).series[0]
          }),
        )

        return {
          metric,
          series: seriesList.filter(Boolean),
          syntheticYears: [2024, 2025],
        }
      }

      if (groupBy === 'season') {
        const seasons = keys?.length
          ? keys
          : ['Kharif', 'Rabi', 'Whole Year', 'Summer', 'Winter', 'Autumn']

        const seriesList = await Promise.all(
          seasons.map(async (season) => {
            const p = new URLSearchParams(params)
            p.set('seasons', season)
            const resp = await fetchJson<ApiRecord>(baseUrl, '/api/yearwise', p)
            const rows = Array.isArray(resp.data) ? (resp.data as ApiRecord[]) : []
            return normalizeTimeSeries(rows, metric, season).series[0]
          }),
        )

        return {
          metric,
          series: seriesList.filter(Boolean),
          syntheticYears: [2024, 2025],
        }
      }

      // Default: single time series
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
      return PROCESSING_COMPONENTS.map((component) => {
        if (component.id === 'pandas') {
          return {
            ...component,
            state: 'success' as const,
            input: 'backend/data/crop_production_1997_2025.csv',
            records: 463847,
            error: null,
          }
        }
        return {
          ...component,
          state: 'not_connected' as const,
          error: 'Big data cluster component (Spark/HDFS/MapReduce) not connected in lightweight REST mode.',
        }
      })
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
