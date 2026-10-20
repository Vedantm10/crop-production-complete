import type { Metadata } from 'next'
import { ProcessingView } from '@/components/views/processing-view'

export const metadata: Metadata = { title: 'Processing Status' }

export default function Page() {
  return <ProcessingView />
}
