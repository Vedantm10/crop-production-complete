'use client'

import { AlertTriangle, Inbox } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface ChartCardProps {
  title: string
  description?: string
  action?: ReactNode
  footer?: ReactNode
  isLoading?: boolean
  error?: Error
  isEmpty?: boolean
  emptyMessage?: string
  onRetry?: () => void
  className?: string
  bodyClassName?: string
  children: ReactNode
}

export function ChartCard({
  title,
  description,
  action,
  footer,
  isLoading,
  error,
  isEmpty,
  emptyMessage = 'No records match the current filters.',
  onRetry,
  className,
  bodyClassName = 'h-80',
  children,
}: ChartCardProps) {
  return (
    <Card className={cn('gap-4', className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div className="flex flex-col gap-1">
          <CardTitle className="text-base">{title}</CardTitle>
          {description && <CardDescription className="text-xs">{description}</CardDescription>}
        </div>
        {action}
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className={cn('relative', bodyClassName)} aria-busy={isLoading}>
          {error ? (
            <StateMessage
              icon={<AlertTriangle className="size-5 text-destructive" aria-hidden="true" />}
              title="Could not load data"
              message={error.message}
              action={onRetry && <Button size="sm" variant="outline" onClick={onRetry}>Retry</Button>}
            />
          ) : isLoading ? (
            <Skeleton className="size-full" />
          ) : isEmpty ? (
            <StateMessage icon={<Inbox className="size-5 text-muted-foreground" aria-hidden="true" />} title="No data" message={emptyMessage} />
          ) : (
            children
          )}
        </div>
        {footer}
      </CardContent>
    </Card>
  )
}

export function StateMessage({ icon, title, message, action }: { icon: ReactNode; title: string; message: string; action?: ReactNode }) {
  return (
    <div className="flex size-full flex-col items-center justify-center gap-2 rounded-lg border border-dashed p-6 text-center" role="status">
      {icon}
      <p className="text-sm font-medium">{title}</p>
      <p className="max-w-sm text-pretty text-xs text-muted-foreground">{message}</p>
      {action}
    </div>
  )
}
