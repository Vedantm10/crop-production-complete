import type { Metadata } from 'next'
import { CropsView } from '@/components/views/crops-view'

export const metadata: Metadata = { title: 'Crop Analytics' }

export default function Page() {
  return <CropsView />
}
