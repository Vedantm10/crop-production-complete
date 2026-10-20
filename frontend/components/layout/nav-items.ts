import { Activity, BarChart3, Database, Gauge, LineChart, Map, MapPinned, ShieldCheck, Table2 } from 'lucide-react'

export const NAV_ITEMS = [
  { href: '/', label: 'Overview', icon: Gauge },
  { href: '/map', label: 'India Map', icon: Map },
  { href: '/crops', label: 'Crop Analytics', icon: BarChart3 },
  { href: '/regions', label: 'State & District', icon: MapPinned },
  { href: '/trends', label: 'Trends', icon: LineChart },
  { href: '/explorer', label: 'Data Explorer', icon: Table2 },
  { href: '/quality', label: 'Data Quality', icon: ShieldCheck },
  { href: '/processing', label: 'Processing Status', icon: Activity },
] as const

export const BRAND_ICON = Database
