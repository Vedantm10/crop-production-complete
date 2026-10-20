import type { Metadata } from 'next'
import { QualityView } from '@/components/views/quality-view'

export const metadata: Metadata = { title: 'Data Quality' }

export default function Page() {
  return <QualityView />
}
