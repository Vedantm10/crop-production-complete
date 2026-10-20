import type { Metadata } from 'next'
import { MapView } from '@/components/views/map-view'

export const metadata: Metadata = { title: 'India Map' }

export default function Page() {
  return <MapView />
}
