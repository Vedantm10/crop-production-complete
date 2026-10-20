'use client'

import { CheckCircle2, CircleDashed, CircleOff, Loader2, Plug, XCircle } from 'lucide-react'
import { StateMessage } from '@/components/dashboard/chart-card'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { dataMode, useProcessingStatus } from '@/hooks/use-analytics'
import type { ProcessingState } from '@/lib/data/types'
import { formatNumber } from '@/lib/format'
import { cn } from '@/lib/utils'

const STATE_META: Record<ProcessingState, { label: string; icon: typeof CheckCircle2; className: string }> = {
  success: { label: 'Succeeded', icon: CheckCircle2, className: 'bg-success/15 text-success' },
  running: { label: 'Running', icon: Loader2, className: 'bg-accent/15 text-accent' },
  failed: { label: 'Failed', icon: XCircle, className: 'bg-destructive/10 text-destructive' },
  not_run: { label: 'Not run yet', icon: CircleDashed, className: 'bg-muted text-muted-foreground' },
  not_configured: { label: 'Not configured', icon: CircleOff, className: 'bg-muted text-muted-foreground' },
  not_connected: { label: 'Not connected', icon: Plug, className: 'bg-warning/15 text-warning-foreground' },
}

export function ProcessingView() {
  const { data, error, isLoading, mutate } = useProcessingStatus()

  return (
    <>
      <PageHeader
        title="Processing status"
        description="Status of each backend component in the pipeline. Values are reported by the backend — nothing here is simulated."
      />

      {dataMode === 'demo' && (
        <p className="rounded-lg bg-secondary/60 px-4 py-3 text-xs text-secondary-foreground">
          No backend is connected, so every component reports <span className="font-semibold">Not connected</span>. Once the
          API exposes <code className="font-mono">/api/v1/processing/status</code>, real run times, record counts and errors
          appear here.
        </p>
      )}

      {error ? (
        <Card className="h-56">
          <StateMessage
            icon={<XCircle className="size-5 text-destructive" aria-hidden="true" />}
            title="Could not load processing status"
            message={error.message}
            action={
              <button type="button" className="text-xs underline" onClick={() => mutate()}>
                Retry
              </button>
            }
          />
        </Card>
      ) : isLoading || !data ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }, (_, i) => (
            <Skeleton key={i} className="h-56" />
          ))}
        </div>
      ) : (
        <ol className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.map((c, i) => {
            const meta = STATE_META[c.state]
            const Icon = meta.icon
            return (
              <li key={c.id}>
                <Card className="h-full">
                  <CardHeader className="flex flex-row items-start justify-between gap-3">
                    <div className="flex flex-col gap-1">
                      <CardDescription className="font-mono text-xs">Step {i + 1}</CardDescription>
                      <CardTitle className="text-base">{c.name}</CardTitle>
                    </div>
                    <span className={cn('inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium', meta.className)}>
                      <Icon className={cn('size-3.5', c.state === 'running' && 'animate-spin')} aria-hidden="true" />
                      {meta.label}
                    </span>
                  </CardHeader>
                  <CardContent className="flex flex-col gap-4">
                    <p className="text-pretty text-sm text-muted-foreground">{c.purpose}</p>
                    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs">
                      <dt className="text-muted-foreground">Last run</dt>
                      <dd>{c.lastRun ? new Date(c.lastRun).toLocaleString('en-IN') : '—'}</dd>
                      <dt className="text-muted-foreground">Input</dt>
                      <dd className="break-all font-mono">{c.input ?? '—'}</dd>
                      <dt className="text-muted-foreground">Output</dt>
                      <dd className="break-all font-mono">{c.output ?? '—'}</dd>
                      <dt className="text-muted-foreground">Records</dt>
                      <dd className="font-mono tabular-nums">{c.records === null ? '—' : formatNumber(c.records)}</dd>
                    </dl>
                    {c.error && (
                      <p className="rounded-md bg-destructive/10 px-3 py-2 font-mono text-xs text-destructive" role="alert">
                        {c.error}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </li>
            )
          })}
        </ol>
      )}
    </>
  )
}
