/**
 * Shared, framework-agnostic types for the analytics layer.
 * These mirror the expected columns of data/crop_production_1997_2025.csv:
 * State_Name, District_Name, Crop_Year, Season, Crop, Area, Production, Data_Type
 */

export type DataType = 'Observed' | 'Synthetic'

export interface CropRecord {
  id: number
  /** State name exactly as it appears in the source CSV (before normalization). */
  rawState: string
  /** Canonical state name, matched against GeoJSON `ST_NM`. */
  state: string
  district: string
  year: number
  season: string
  crop: string
  /** Cultivated area in hectares. `null` when missing in source. */
  area: number | null
  /** Production in tonnes. `null` when missing in source. */
  production: number | null
  dataType: DataType
}

export type Metric = 'production' | 'area' | 'yield'
export type DataTypeFilter = 'all' | DataType
export type Dimension = 'state' | 'district' | 'crop' | 'season'

export interface Filters {
  yearFrom: number
  yearTo: number
  state: string
  district: string
  crop: string
  season: string
  dataType: DataTypeFilter
  metric: Metric
}

export interface DatasetMeta {
  source: 'demo' | 'api'
  sourceLabel: string
  /** ISO timestamp supplied by the backend. Never invented in demo mode. */
  lastUpdated: string | null
  recordCount: number
  columns: string[]
  yearMin: number
  yearMax: number
  states: string[]
  crops: string[]
  seasons: string[]
  districtsByState: Record<string, string[]>
  cropsByState: Record<string, string[]>
  seasonsByCrop: Record<string, string[]>
  syntheticYears: number[]
}

export interface KpiSummary {
  totalProduction: number
  totalArea: number
  cropCount: number
  stateCount: number
  districtCount: number
  recordCount: number
  excludedRecords: number
  yearLabel: string
  /** Change in production of the last year vs the previous year in range, in percent. */
  productionChangePct: number | null
  areaChangePct: number | null
  lastYear: number | null
}

export interface BreakdownRow {
  key: string
  production: number
  area: number
  /** Tonnes per hectare. `null` when yield is not a valid measure for the filter set. */
  yield: number | null
  records: number
  cropCount: number
  districtCount: number
}

export interface SeriesPoint {
  year: number
  value: number | null
  synthetic: boolean
}

export interface Series {
  name: string
  points: SeriesPoint[]
}

export interface TimeSeriesResult {
  metric: Metric
  series: Series[]
  syntheticYears: number[]
}

export interface RecordQuery {
  filters: Filters
  search: string
  sortBy: keyof CropRecord
  sortDir: 'asc' | 'desc'
  page: number
  pageSize: number
}

export interface RecordPage {
  rows: CropRecord[]
  total: number
  page: number
  pageSize: number
}

export interface ColumnQuality {
  column: string
  dtype: string
  missing: number
  missingPct: number
  invalid: number
}

export interface QualityReport {
  computed: boolean
  computedBy: string
  totalRows: number
  cleanRows: number
  duplicateRows: number
  negativeValues: number
  missingProduction: number
  missingArea: number
  columns: ColumnQuality[]
  yearCoverage: { year: number; records: number; dataType: DataType | 'Mixed' }[]
  provenance: { dataType: DataType; records: number }[]
  stateNameMappings: { raw: string; normalized: string; records: number }[]
  unmatchedStates: string[]
  geoRegionsWithoutData: string[]
  exclusions: { analysis: string; excluded: number; reason: string }[]
  warnings: string[]
  cleaningSteps: string[]
}

export type ProcessingState = 'not_configured' | 'not_run' | 'running' | 'success' | 'failed' | 'not_connected'

export interface ProcessingComponent {
  id: string
  name: string
  purpose: string
  state: ProcessingState
  lastRun: string | null
  input: string | null
  output: string | null
  records: number | null
  error: string | null
}
