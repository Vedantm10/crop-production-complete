import { AlertCircle, ArrowDownRight, ArrowUpRight, Minus, RotateCcw, type LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatPct } from '@/lib/format'
import { cn } from '@/lib/utils'

interface KpiCardProps {
  label: string
  value: string
  unit?: string
  icon: LucideIcon
  changePct?: number | null
  changeLabel?: string
  caption?: string
  isLoading?: boolean
  error?: Error | null
  onRetry?: () => void
}

export function KpiCard({ label, value, unit, icon: Icon, changePct, changeLabel, caption, isLoading, error, onRetry }: KpiCardProps) {
  const TrendIcon = changePct === null || changePct === undefined ? Minus : changePct >= 0 ? ArrowUpRight : ArrowDownRight
  return (
    <Card className="gap-3 p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
        <span className="flex size-8 items-center justify-center rounded-md bg-secondary text-secondary-foreground">
          <Icon className="size-4" aria-hidden="true" />
        </span>
      </div>
      {error ? (
        <div className="flex flex-col gap-1 py-1 text-xs text-destructive">
          <div className="flex items-center gap-1.5 font-medium">
            <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
            <span>Could not load KPI</span>
          </div>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-1 flex w-fit items-center gap-1 text-[11px] font-medium text-foreground underline hover:no-underline"
            >
              <RotateCcw className="size-3" aria-hidden="true" />
              Retry
            </button>
          )}
        </div>
      ) : isLoading ? (
        <Skeleton className="h-8 w-28" />
      ) : (
        <p className="flex items-baseline gap-1.5">
          <span className="font-mono text-2xl font-semibold tracking-tight tabular-nums">{value}</span>
          {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
        </p>
      )}
      {!error && (changePct !== undefined ? (
        <p className="flex items-center gap-1 text-xs text-muted-foreground">
          <span
            className={cn(
              'inline-flex items-center gap-0.5 font-medium',
              changePct === null ? 'text-muted-foreground' : changePct >= 0 ? 'text-success' : 'text-destructive',
            )}
          >
            <TrendIcon className="size-3.5" aria-hidden="true" />
            {formatPct(changePct)}
          </span>
          {changeLabel}
        </p>
      ) : (
        caption && <p className="text-xs text-muted-foreground">{caption}</p>
      ))}
    </Card>
  )
}

