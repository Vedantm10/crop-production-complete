/**
 * Pure aggregation functions. They work on any CropRecord[] — demo or a
 * parsed real CSV — and mirror the groupBy/sum logic the PySpark and
 * MapReduce jobs are expected to perform on the backend.
 */
import type {
  BreakdownRow,
  CropRecord,
  DatasetMeta,
  Dimension,
  Filters,
  KpiSummary,
  Metric,
  QualityReport,
  RecordPage,
  RecordQuery,
  Series,
  TimeSeriesResult,
} from './types'

export const hasValidProduction = (r: CropRecord) => r.production !== null && r.production >= 0
export const hasValidArea = (r: CropRecord) => r.area !== null && r.area >= 0
export const hasValidYieldInputs = (r: CropRecord) =>
  hasValidProduction(r) && hasValidArea(r) && (r.area as number) > 0

/** Yield is only meaningful when a single crop is selected — summing tonnes of sugarcane and wheat is not a yield. */
export const isYieldValid = (f: Pick<Filters, 'crop'>) => f.crop !== 'all'

function duplicateKey(r: CropRecord) {
  return [r.rawState, r.district, r.year, r.season, r.crop, r.area, r.production].join('|')
}

export function cleanRecords(raw: CropRecord[]) {
  const seen = new Set<string>()
  const clean: CropRecord[] = []
  let duplicates = 0
  for (const r of raw) {
    const key = duplicateKey(r)
    if (seen.has(key)) {
      duplicates++
      continue
    }
    seen.add(key)
    clean.push(r)
  }
  return { clean, duplicates }
}

const uniqueSorted = (values: Iterable<string>) => Array.from(new Set(values)).sort((a, b) => a.localeCompare(b))

export function buildMeta(
  records: CropRecord[],
  source: DatasetMeta['source'],
  sourceLabel: string,
  lastUpdated: string | null,
): DatasetMeta {
  const districtsByState: Record<string, Set<string>> = {}
  const cropsByState: Record<string, Set<string>> = {}
  const seasonsByCrop: Record<string, Set<string>> = {}
  const syntheticYears = new Set<number>()
  let yearMin = Number.POSITIVE_INFINITY
  let yearMax = Number.NEGATIVE_INFINITY

  for (const r of records) {
    ;(districtsByState[r.state] ??= new Set()).add(r.district)
    ;(cropsByState[r.state] ??= new Set()).add(r.crop)
    ;(seasonsByCrop[r.crop] ??= new Set()).add(r.season)
    if (r.dataType === 'Synthetic') syntheticYears.add(r.year)
    if (r.year < yearMin) yearMin = r.year
    if (r.year > yearMax) yearMax = r.year
  }

  const toSorted = (m: Record<string, Set<string>>) =>
    Object.fromEntries(Object.entries(m).map(([k, v]) => [k, uniqueSorted(v)]))

  return {
    source,
    sourceLabel,
    lastUpdated,
    recordCount: records.length,
    columns: ['State_Name', 'District_Name', 'Crop_Year', 'Season', 'Crop', 'Area', 'Production', 'Data_Type'],
    yearMin,
    yearMax,
    states: uniqueSorted(records.map((r) => r.state)),
    crops: uniqueSorted(records.map((r) => r.crop)),
    seasons: uniqueSorted(records.map((r) => r.season)),
    districtsByState: toSorted(districtsByState),
    cropsByState: toSorted(cropsByState),
    seasonsByCrop: toSorted(seasonsByCrop),
    syntheticYears: Array.from(syntheticYears).sort((a, b) => a - b),
  }
}

export function applyFilters(records: CropRecord[], f: Filters) {
  return records.filter(
    (r) =>
      r.year >= f.yearFrom &&
      r.year <= f.yearTo &&
      (f.state === 'all' || r.state === f.state) &&
      (f.district === 'all' || r.district === f.district) &&
      (f.crop === 'all' || r.crop === f.crop) &&
      (f.season === 'all' || r.season === f.season) &&
      (f.dataType === 'all' || r.dataType === f.dataType),
  )
}

function sums(records: CropRecord[]) {
  let production = 0
  let area = 0
  let yieldProduction = 0
  let yieldArea = 0
  for (const r of records) {
    if (hasValidProduction(r)) production += r.production as number
    if (hasValidArea(r)) area += r.area as number
    if (hasValidYieldInputs(r)) {
      yieldProduction += r.production as number
      yieldArea += r.area as number
    }
  }
  return { production, area, yield: yieldArea > 0 ? yieldProduction / yieldArea : null }
}

const pctChange = (current: number, previous: number) => (previous > 0 ? ((current - previous) / previous) * 100 : null)

export function computeKpis(records: CropRecord[], f: Filters): KpiSummary {
  const filtered = applyFilters(records, f)
  const totals = sums(filtered)
  const years = uniqueSorted(filtered.map((r) => String(r.year))).map(Number)
  const lastYear = years.at(-1) ?? null
  const prevYear = years.at(-2) ?? null

  let productionChangePct: number | null = null
  let areaChangePct: number | null = null
  if (lastYear !== null && prevYear !== null) {
    const last = sums(filtered.filter((r) => r.year === lastYear))
    const prev = sums(filtered.filter((r) => r.year === prevYear))
    productionChangePct = pctChange(last.production, prev.production)
    areaChangePct = pctChange(last.area, prev.area)
  }

  return {
    totalProduction: totals.production,
    totalArea: totals.area,
    cropCount: new Set(filtered.map((r) => r.crop)).size,
    stateCount: new Set(filtered.map((r) => r.state)).size,
    districtCount: new Set(filtered.map((r) => `${r.state}|${r.district}`)).size,
    recordCount: filtered.length,
    excludedRecords: filtered.filter((r) => !hasValidProduction(r) || !hasValidArea(r)).length,
    yearLabel: f.yearFrom === f.yearTo ? String(f.yearFrom) : `${f.yearFrom}–${f.yearTo}`,
    productionChangePct,
    areaChangePct,
    lastYear,
  }
}

export function breakdown(records: CropRecord[], dimension: Dimension, f: Filters): BreakdownRow[] {
  const filtered = applyFilters(records, f)
  const groups = new Map<string, CropRecord[]>()
  for (const r of filtered) {
    const key = r[dimension]
    const list = groups.get(key)
    if (list) list.push(r)
    else groups.set(key, [r])
  }
  const yieldValid = isYieldValid(f) || dimension === 'crop'
  return Array.from(groups, ([key, rows]) => {
    const s = sums(rows)
    return {
      key,
      production: s.production,
      area: s.area,
      yield: yieldValid ? s.yield : null,
      records: rows.length,
      cropCount: new Set(rows.map((r) => r.crop)).size,
      districtCount: new Set(rows.map((r) => r.district)).size,
    }
  }).sort((a, b) => b.production - a.production)
}

export function timeSeries(
  records: CropRecord[],
  f: Filters,
  metric: Metric,
  groupBy: Dimension | null,
  options: { top?: number; keys?: string[] } = {},
): TimeSeriesResult {
  const filtered = applyFilters(records, f)
  const syntheticYears = new Set(filtered.filter((r) => r.dataType === 'Synthetic').map((r) => r.year))
  const years: number[] = []
  for (let y = f.yearFrom; y <= f.yearTo; y++) years.push(y)

  let groupKeys: string[] = ['Total']
  if (groupBy) {
    if (options.keys?.length) groupKeys = options.keys
    else {
      groupKeys = breakdown(records, groupBy, f)
        .slice(0, options.top ?? 6)
        .map((row) => row.key)
    }
  }

  const series: Series[] = groupKeys.map((key) => {
    const rows = groupBy ? filtered.filter((r) => r[groupBy] === key) : filtered
    const byYear = new Map<number, CropRecord[]>()
    for (const r of rows) {
      const list = byYear.get(r.year)
      if (list) list.push(r)
      else byYear.set(r.year, [r])
    }
    return {
      name: key,
      points: years.map((year) => {
        const yearRows = byYear.get(year)
        if (!yearRows?.length) return { year, value: null, synthetic: syntheticYears.has(year) }
        const s = sums(yearRows)
        const value = metric === 'production' ? s.production : metric === 'area' ? s.area : s.yield
        return { year, value, synthetic: syntheticYears.has(year) }
      }),
    }
  })

  return { metric, series, syntheticYears: Array.from(syntheticYears).sort((a, b) => a - b) }
}

export function queryRecords(records: CropRecord[], q: RecordQuery): RecordPage {
  const search = q.search.trim().toLowerCase()
  let rows = applyFilters(records, q.filters)
  if (search) {
    rows = rows.filter(
      (r) =>
        r.state.toLowerCase().includes(search) ||
        r.district.toLowerCase().includes(search) ||
        r.crop.toLowerCase().includes(search) ||
        r.season.toLowerCase().includes(search) ||
        String(r.year).includes(search),
    )
  }
  const dir = q.sortDir === 'asc' ? 1 : -1
  rows = [...rows].sort((a, b) => {
    const av = a[q.sortBy]
    const bv = b[q.sortBy]
    if (av === bv) return 0
    if (av === null) return 1
    if (bv === null) return -1
    return av > bv ? dir : -dir
  })
  const start = (q.page - 1) * q.pageSize
  return { rows: rows.slice(start, start + q.pageSize), total: rows.length, page: q.page, pageSize: q.pageSize }
}

export function buildQualityReport(raw: CropRecord[], clean: CropRecord[], duplicates: number, geoNames: string[] | null): QualityReport {
  const missingProduction = clean.filter((r) => r.production === null).length
  const missingArea = clean.filter((r) => r.area === null).length
  const negativeProduction = clean.filter((r) => r.production !== null && r.production < 0).length
  const negativeArea = clean.filter((r) => r.area !== null && r.area < 0).length
  const zeroArea = clean.filter((r) => r.area === 0).length
  const pct = (n: number) => (clean.length ? (n / clean.length) * 100 : 0)

  const yearMap = new Map<number, { records: number; observed: number; synthetic: number }>()
  for (const r of clean) {
    const entry = yearMap.get(r.year) ?? { records: 0, observed: 0, synthetic: 0 }
    entry.records++
    if (r.dataType === 'Synthetic') entry.synthetic++
    else entry.observed++
    yearMap.set(r.year, entry)
  }

  const mappingMap = new Map<string, { raw: string; normalized: string; records: number }>()
  for (const r of clean) {
    if (r.rawState === r.state) continue
    const entry = mappingMap.get(r.rawState) ?? { raw: r.rawState, normalized: r.state, records: 0 }
    entry.records++
    mappingMap.set(r.rawState, entry)
  }

  const states = uniqueSorted(clean.map((r) => r.state))
  const geoSet = geoNames ? new Set(geoNames) : null
  const unmatchedStates = geoSet ? states.filter((s) => !geoSet.has(s)) : []
  const geoRegionsWithoutData = geoNames ? geoNames.filter((g) => !states.includes(g)).sort() : []

  const observed = clean.filter((r) => r.dataType === 'Observed').length
  const synthetic = clean.length - observed

  const warnings: string[] = []
  if (synthetic > 0) {
    const synthYears = Array.from(yearMap).filter(([, v]) => v.synthetic > 0).map(([y]) => y)
    warnings.push(
      `${synthetic.toLocaleString('en-IN')} records (${Math.min(...synthYears)}–${Math.max(...synthYears)}) are labelled Synthetic and must not be reported as official statistics.`,
    )
  }
  if (negativeArea + negativeProduction > 0)
    warnings.push(`${negativeArea + negativeProduction} records contain negative values and are excluded from totals.`)
  if (missingProduction > 0) warnings.push(`${missingProduction} records have no Production value.`)
  if (!geoSet) warnings.push('GeoJSON could not be loaded, so state-name matching was not validated.')
  else if (unmatchedStates.length) warnings.push(`${unmatchedStates.length} dataset state(s) do not match any map region.`)
  const yearsWithGaps = Array.from(yearMap.values()).map((v) => v.records)
  if (yearsWithGaps.length && Math.min(...yearsWithGaps) < Math.max(...yearsWithGaps) * 0.8)
    warnings.push('Record counts vary noticeably across years (e.g. states formed later), so year-on-year totals are not fully comparable.')

  return {
    computed: true,
    computedBy: 'Browser validation on loaded dataset',
    totalRows: raw.length,
    cleanRows: clean.length,
    duplicateRows: duplicates,
    negativeValues: negativeArea + negativeProduction,
    missingProduction,
    missingArea,
    columns: [
      { column: 'State_Name', dtype: 'string', missing: 0, missingPct: 0, invalid: unmatchedStates.length },
      { column: 'District_Name', dtype: 'string', missing: 0, missingPct: 0, invalid: 0 },
      { column: 'Crop_Year', dtype: 'int', missing: 0, missingPct: 0, invalid: 0 },
      { column: 'Season', dtype: 'string', missing: 0, missingPct: 0, invalid: 0 },
      { column: 'Crop', dtype: 'string', missing: 0, missingPct: 0, invalid: 0 },
      { column: 'Area', dtype: 'float (ha)', missing: missingArea, missingPct: pct(missingArea), invalid: negativeArea },
      { column: 'Production', dtype: 'float (t)', missing: missingProduction, missingPct: pct(missingProduction), invalid: negativeProduction },
      { column: 'Data_Type', dtype: 'category', missing: 0, missingPct: 0, invalid: 0 },
    ],
    yearCoverage: Array.from(yearMap, ([year, v]) => ({
      year,
      records: v.records,
      dataType: v.synthetic && v.observed ? ('Mixed' as const) : v.synthetic ? ('Synthetic' as const) : ('Observed' as const),
    })).sort((a, b) => a.year - b.year),
    provenance: [
      { dataType: 'Observed', records: observed },
      { dataType: 'Synthetic', records: synthetic },
    ],
    stateNameMappings: Array.from(mappingMap.values()),
    unmatchedStates,
    geoRegionsWithoutData,
    exclusions: [
      { analysis: 'Production totals', excluded: missingProduction + negativeProduction, reason: 'Missing or negative Production' },
      { analysis: 'Area totals', excluded: missingArea + negativeArea, reason: 'Missing or negative Area' },
      {
        analysis: 'Yield (t/ha)',
        excluded: clean.filter((r) => !hasValidYieldInputs(r)).length,
        reason: 'Needs valid Production and Area > 0' + (zeroArea ? ` (${zeroArea} zero-area rows)` : ''),
      },
      { analysis: 'All analyses', excluded: duplicates, reason: 'Exact duplicate rows removed' },
    ],
    warnings,
    cleaningSteps: [
      'Trimmed whitespace and normalised state names to GeoJSON ST_NM spelling',
      `Removed ${duplicates} exact duplicate rows`,
      'Flagged negative Area/Production values as invalid (kept in explorer, excluded from totals)',
      'Kept missing values as null — no imputation is performed',
      'Preserved Data_Type so Synthetic rows can be filtered and visually distinguished',
    ],
  }
}
