/**
 * Canonical names follow the `ST_NM` property of public/geo/india_states.geojson.
 * Source datasets (e.g. the data.gov.in crop production CSV) use different spellings,
 * trailing whitespace, and pre-2020 UT names, so every name passes through here.
 */
const ALIASES: Record<string, string> = {
  'andaman and nicobar islands': 'Andaman & Nicobar',
  'andaman and nicobar': 'Andaman & Nicobar',
  'andaman & nicobar islands': 'Andaman & Nicobar',
  'jammu and kashmir': 'Jammu & Kashmir',
  'jammu & kashmir': 'Jammu & Kashmir',
  orissa: 'Odisha',
  uttaranchal: 'Uttarakhand',
  pondicherry: 'Puducherry',
  'nct of delhi': 'Delhi',
  'dadra and nagar haveli': 'Dadra and Nagar Haveli and Daman and Diu',
  'daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
  'the dadra and nagar haveli and daman and diu': 'Dadra and Nagar Haveli and Daman and Diu',
}

export function normalizeStateName(raw: string): string {
  const cleaned = raw.trim().replace(/\s+/g, ' ')
  const alias = ALIASES[cleaned.toLowerCase()]
  if (alias) return alias
  return cleaned
    .toLowerCase()
    .split(' ')
    .map((word) => (word === 'and' ? 'and' : word.charAt(0).toUpperCase() + word.slice(1)))
    .join(' ')
}

export function matchToGeo(names: string[], geoNames: Set<string>) {
  const matched: string[] = []
  const unmatched: string[] = []
  for (const name of names) {
    if (geoNames.has(name)) matched.push(name)
    else unmatched.push(name)
  }
  return { matched, unmatched }
}
