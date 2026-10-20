import type { BreakdownRow, CropRecord } from './types'

function escapeCell(value: unknown) {
  if (value === null || value === undefined) return ''
  const s = String(value)
  return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

export function toCsv(headers: string[], rows: unknown[][]) {
  return [headers.map(escapeCell).join(','), ...rows.map((row) => row.map(escapeCell).join(','))].join('\n')
}

export function recordsToCsv(records: CropRecord[]) {
  return toCsv(
    ['State_Name', 'District_Name', 'Crop_Year', 'Season', 'Crop', 'Area', 'Production', 'Data_Type'],
    records.map((r) => [r.state, r.district, r.year, r.season, r.crop, r.area, r.production, r.dataType]),
  )
}

export function breakdownToCsv(dimension: string, rows: BreakdownRow[]) {
  return toCsv(
    [dimension, 'Production_tonnes', 'Area_hectares', 'Yield_t_per_ha', 'Records', 'Crops', 'Districts'],
    rows.map((r) => [r.key, r.production, r.area, r.yield === null ? '' : r.yield.toFixed(4), r.records, r.cropCount, r.districtCount]),
  )
}

export function downloadText(filename: string, text: string) {
  const blob = new Blob([text], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}
