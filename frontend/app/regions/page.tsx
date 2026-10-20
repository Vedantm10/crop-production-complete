import type { Metadata } from 'next'
import { RegionsView } from '@/components/views/regions-view'

export const metadata: Metadata = { title: 'State & District' }

export default function Page() {
  return <RegionsView />
}
