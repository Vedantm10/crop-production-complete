/**
 * Bidirectional mapping between dataset State_Name and GeoJSON NAME_1 property.
 * The GeoJSON file at public/geo/india_states.geojson uses historical NAME_1 names
 * (e.g. 'Orissa', 'Uttaranchal', 'Andaman and Nicobar', 'Dadra and Nagar Haveli').
 */
export const CSV_TO_GEOJSON_MAP: Record<string, string> = {
  'Andaman And Nicobar Islands': 'Andaman and Nicobar',
  'Andhra Pradesh': 'Andhra Pradesh',
  'Arunachal Pradesh': 'Arunachal Pradesh',
  'Assam': 'Assam',
  'Bihar': 'Bihar',
  'Chandigarh': 'Chandigarh',
  'Chhattisgarh': 'Chhattisgarh',
  'Goa': 'Goa',
  'Gujarat': 'Gujarat',
  'Haryana': 'Haryana',
  'Himachal Pradesh': 'Himachal Pradesh',
  'Jammu And Kashmir': 'Jammu and Kashmir',
  'Jharkhand': 'Jharkhand',
  'Karnataka': 'Karnataka',
  'Kerala': 'Kerala',
  'Ladakh': 'Jammu and Kashmir',
  'Madhya Pradesh': 'Madhya Pradesh',
  'Maharashtra': 'Maharashtra',
  'Manipur': 'Manipur',
  'Meghalaya': 'Meghalaya',
  'Mizoram': 'Mizoram',
  'Nagaland': 'Nagaland',
  'Odisha': 'Orissa',
  'Puducherry': 'Puducherry',
  'Punjab': 'Punjab',
  'Rajasthan': 'Rajasthan',
  'Sikkim': 'Sikkim',
  'Tamil Nadu': 'Tamil Nadu',
  'Telangana': 'Telangana',
  'The Dadra And Nagar Haveli And Daman And Diu': 'Dadra and Nagar Haveli',
  'Tripura': 'Tripura',
  'Uttar Pradesh': 'Uttar Pradesh',
  'Uttarakhand': 'Uttaranchal',
  'West Bengal': 'West Bengal',
}

export const GEOJSON_TO_CSV_MAP: Record<string, string> = {
  'Andaman and Nicobar': 'Andaman And Nicobar Islands',
  'Andhra Pradesh': 'Andhra Pradesh',
  'Arunachal Pradesh': 'Arunachal Pradesh',
  'Assam': 'Assam',
  'Bihar': 'Bihar',
  'Chandigarh': 'Chandigarh',
  'Chhattisgarh': 'Chhattisgarh',
  'Dadra and Nagar Haveli': 'The Dadra And Nagar Haveli And Daman And Diu',
  'Daman and Diu': 'The Dadra And Nagar Haveli And Daman And Diu',
  'Delhi': 'Delhi',
  'Goa': 'Goa',
  'Gujarat': 'Gujarat',
  'Haryana': 'Haryana',
  'Himachal Pradesh': 'Himachal Pradesh',
  'Jammu and Kashmir': 'Jammu And Kashmir',
  'Jharkhand': 'Jharkhand',
  'Karnataka': 'Karnataka',
  'Kerala': 'Kerala',
  'Madhya Pradesh': 'Madhya Pradesh',
  'Maharashtra': 'Maharashtra',
  'Manipur': 'Manipur',
  'Meghalaya': 'Meghalaya',
  'Mizoram': 'Mizoram',
  'Nagaland': 'Nagaland',
  'Orissa': 'Odisha',
  'Puducherry': 'Puducherry',
  'Punjab': 'Punjab',
  'Rajasthan': 'Rajasthan',
  'Sikkim': 'Sikkim',
  'Tamil Nadu': 'Tamil Nadu',
  'Telangana': 'Telangana',
  'Tripura': 'Tripura',
  'Uttar Pradesh': 'Uttar Pradesh',
  'Uttaranchal': 'Uttarakhand',
  'West Bengal': 'West Bengal',
}

export function csvStateToGeoName(csvState: string): string {
  if (!csvState) return ''
  const trimmed = csvState.trim()
  return CSV_TO_GEOJSON_MAP[trimmed] ?? trimmed
}

export function geoStateToCsvName(geoState: string): string {
  if (!geoState) return ''
  const trimmed = geoState.trim()
  return GEOJSON_TO_CSV_MAP[trimmed] ?? trimmed
}

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
    const geoName = csvStateToGeoName(name)
    if (geoNames.has(geoName) || geoNames.has(name)) matched.push(name)
    else unmatched.push(name)
  }
  return { matched, unmatched }
}
