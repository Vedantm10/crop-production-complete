import type { Metadata } from 'next'
import { ExplorerView } from '@/components/views/explorer-view'

export const metadata: Metadata = { title: 'Data Explorer' }

export default function Page() {
  return <ExplorerView />
}
