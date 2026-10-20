/**
 * DEVELOPMENT-ONLY DEMO DATASET
 * ------------------------------------------------------------------
 * Every number produced here is SYNTHETIC. It is generated with a seeded
 * pseudo-random generator so the UI can be demonstrated without the real
 * CSV. State, district, crop and season NAMES are real; the AREA and
 * PRODUCTION values are not agricultural statistics and must never be
 * presented as such. The UI shows a "Demo Data" badge whenever this module
 * backs the analytics service.
 *
 * Deliberate imperfections are injected (missing values, duplicates,
 * negative areas, legacy state spellings) so the Data Quality page has
 * something real to detect.
 */
import { normalizeStateName } from '../state-names'
import type { CropRecord, DataType } from '../types'

export const DEMO_YEAR_MIN = 1997
export const DEMO_YEAR_MAX = 2025
export const DEMO_SYNTHETIC_FROM = 2023

interface CropProfile {
  seasons: string[]
  /** Baseline yield in tonnes per hectare used only for demo generation. */
  baseYield: number
  areaRange: [number, number]
}

const CROPS: Record<string, CropProfile> = {
  Rice: { seasons: ['Kharif', 'Rabi'], baseYield: 2.2, areaRange: [20000, 160000] },
  Wheat: { seasons: ['Rabi'], baseYield: 2.8, areaRange: [25000, 180000] },
  Maize: { seasons: ['Kharif', 'Rabi'], baseYield: 2.4, areaRange: [5000, 60000] },
  Bajra: { seasons: ['Kharif'], baseYield: 1.1, areaRange: [10000, 90000] },
  Jowar: { seasons: ['Kharif', 'Rabi'], baseYield: 0.9, areaRange: [5000, 70000] },
  Gram: { seasons: ['Rabi'], baseYield: 0.9, areaRange: [5000, 60000] },
  'Arhar/Tur': { seasons: ['Kharif'], baseYield: 0.75, areaRange: [3000, 40000] },
  Groundnut: { seasons: ['Kharif', 'Summer'], baseYield: 1.3, areaRange: [4000, 50000] },
  'Rapeseed & Mustard': { seasons: ['Rabi'], baseYield: 1.1, areaRange: [4000, 60000] },
  Soyabean: { seasons: ['Kharif'], baseYield: 1.0, areaRange: [8000, 90000] },
  Sugarcane: { seasons: ['Whole Year'], baseYield: 70, areaRange: [3000, 45000] },
  Potato: { seasons: ['Rabi'], baseYield: 21, areaRange: [1500, 25000] },
}

interface StateProfile {
  /** Spelling used in the synthetic "raw" CSV to exercise name normalization. */
  raw: string
  districts: string[]
  crops: string[]
  scale: number
  startYear?: number
}

const STATES: StateProfile[] = [
  { raw: 'Uttar Pradesh', districts: ['Agra', 'Bareilly', 'Gorakhpur', 'Meerut', 'Varanasi'], crops: ['Wheat', 'Rice', 'Sugarcane', 'Potato', 'Rapeseed & Mustard', 'Bajra'], scale: 1.5 },
  { raw: 'Punjab', districts: ['Ludhiana', 'Amritsar', 'Bathinda', 'Patiala'], crops: ['Wheat', 'Rice', 'Maize', 'Potato'], scale: 1.4 },
  { raw: 'Haryana', districts: ['Karnal', 'Hisar', 'Sirsa', 'Kurukshetra'], crops: ['Wheat', 'Rice', 'Bajra', 'Rapeseed & Mustard'], scale: 1.1 },
  { raw: 'Madhya Pradesh', districts: ['Indore', 'Sehore', 'Ujjain', 'Jabalpur', 'Vidisha'], crops: ['Soyabean', 'Wheat', 'Gram', 'Maize', 'Arhar/Tur'], scale: 1.3 },
  { raw: 'Maharashtra', districts: ['Pune', 'Nashik', 'Ahmednagar', 'Latur', 'Kolhapur'], crops: ['Sugarcane', 'Jowar', 'Soyabean', 'Arhar/Tur', 'Gram'], scale: 1.3 },
  { raw: 'Rajasthan', districts: ['Jaipur', 'Bikaner', 'Kota', 'Alwar', 'Jodhpur'], crops: ['Bajra', 'Rapeseed & Mustard', 'Wheat', 'Gram', 'Groundnut'], scale: 1.2 },
  { raw: 'Gujarat', districts: ['Rajkot', 'Junagadh', 'Banaskantha', 'Anand'], crops: ['Groundnut', 'Bajra', 'Wheat', 'Rice'], scale: 1.0 },
  { raw: 'West Bengal', districts: ['Bardhaman', 'Hooghly', 'Nadia', 'Murshidabad'], crops: ['Rice', 'Potato', 'Wheat', 'Rapeseed & Mustard'], scale: 1.2 },
  { raw: 'Bihar', districts: ['Patna', 'Gaya', 'Muzaffarpur', 'Purnia'], crops: ['Rice', 'Wheat', 'Maize', 'Arhar/Tur'], scale: 1.0 },
  { raw: 'Andhra Pradesh', districts: ['Guntur', 'Krishna', 'East Godavari', 'Kurnool'], crops: ['Rice', 'Groundnut', 'Maize', 'Arhar/Tur'], scale: 1.1 },
  { raw: 'Telangana ', districts: ['Nalgonda', 'Karimnagar', 'Warangal', 'Nizamabad'], crops: ['Rice', 'Maize', 'Arhar/Tur', 'Jowar'], scale: 0.9, startYear: 2014 },
  { raw: 'Karnataka', districts: ['Belagavi', 'Mysuru', 'Raichur', 'Davanagere'], crops: ['Jowar', 'Rice', 'Sugarcane', 'Maize', 'Groundnut'], scale: 1.0 },
  { raw: 'Tamil Nadu', districts: ['Thanjavur', 'Coimbatore', 'Villupuram', 'Madurai'], crops: ['Rice', 'Sugarcane', 'Groundnut', 'Maize'], scale: 0.9 },
  { raw: 'Orissa', districts: ['Cuttack', 'Ganjam', 'Sambalpur', 'Balasore'], crops: ['Rice', 'Groundnut', 'Arhar/Tur'], scale: 0.9 },
  { raw: 'Chhattisgarh', districts: ['Raipur', 'Durg', 'Bilaspur'], crops: ['Rice', 'Maize', 'Gram'], scale: 0.8 },
  { raw: 'Assam', districts: ['Nagaon', 'Barpeta', 'Sonitpur'], crops: ['Rice', 'Rapeseed & Mustard', 'Potato'], scale: 0.7 },
  { raw: 'Jharkhand', districts: ['Ranchi', 'Hazaribagh', 'Dumka'], crops: ['Rice', 'Maize', 'Arhar/Tur'], scale: 0.6 },
  { raw: 'Kerala', districts: ['Palakkad', 'Thrissur', 'Alappuzha'], crops: ['Rice'], scale: 0.4 },
  { raw: 'Himachal Pradesh', districts: ['Kangra', 'Mandi', 'Shimla'], crops: ['Wheat', 'Maize', 'Potato'], scale: 0.35 },
  { raw: 'Uttaranchal', districts: ['Dehradun', 'Haridwar', 'Udham Singh Nagar'], crops: ['Wheat', 'Rice', 'Sugarcane'], scale: 0.45 },
  { raw: 'Jammu and Kashmir', districts: ['Anantnag', 'Baramulla', 'Jammu'], crops: ['Rice', 'Maize', 'Wheat'], scale: 0.4 },
  { raw: 'Tripura', districts: ['West Tripura', 'Gomati'], crops: ['Rice', 'Potato'], scale: 0.25 },
]

function mulberry32(seed: number) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

let cache: CropRecord[] | null = null

export function generateDemoRecords(seed = 20251020): CropRecord[] {
  if (cache) return cache
  const rand = mulberry32(seed)
  const between = (min: number, max: number) => min + rand() * (max - min)
  const records: CropRecord[] = []
  let id = 1

  for (const st of STATES) {
    const state = normalizeStateName(st.raw)
    for (const district of st.districts) {
      for (const crop of st.crops) {
        const profile = CROPS[crop]
        const seasons = profile.seasons.filter((_, i) => i === 0 || rand() > 0.45)
        for (const season of seasons) {
          const seasonShare = season === profile.seasons[0] ? 1 : between(0.15, 0.4)
          const baseArea = between(...profile.areaRange) * st.scale * seasonShare
          const areaTrend = between(-0.006, 0.014)
          const yieldTrend = between(0.006, 0.02)
          const localYield = profile.baseYield * between(0.75, 1.25)
          const startYear = st.startYear ?? DEMO_YEAR_MIN

          for (let year = startYear; year <= DEMO_YEAR_MAX; year++) {
            const t = year - DEMO_YEAR_MIN
            const droughtShock = year === 2002 || year === 2009 || year === 2014 ? between(0.78, 0.92) : 1
            const area = baseArea * (1 + areaTrend) ** t * between(0.93, 1.07)
            const yieldPerHa = localYield * (1 + yieldTrend) ** t * between(0.88, 1.12) * droughtShock
            const dataType: DataType = year >= DEMO_SYNTHETIC_FROM ? 'Synthetic' : 'Observed'

            let areaValue: number | null = Math.round(area)
            let productionValue: number | null = Math.round(area * yieldPerHa)
            const roll = rand()
            if (roll < 0.012) productionValue = null
            else if (roll < 0.016) areaValue = null
            else if (roll < 0.0175) areaValue = -Math.abs(areaValue)

            const record: CropRecord = {
              id: id++,
              rawState: st.raw,
              state,
              district,
              year,
              season,
              crop,
              area: areaValue,
              production: productionValue,
              dataType,
            }
            records.push(record)
            if (rand() < 0.002) records.push({ ...record, id: id++ })
          }
        }
      }
    }
  }

  cache = records
  return records
}
