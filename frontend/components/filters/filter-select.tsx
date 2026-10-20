'use client'

import { useId, useMemo } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

export interface FilterOption {
  value: string
  label: string
  disabled?: boolean
}

interface FilterSelectProps {
  label: string
  value: string
  options: FilterOption[]
  onChange: (value: string) => void
  disabled?: boolean
  className?: string
  hint?: string
}

export function FilterSelect({ label, value, options, onChange, disabled, className, hint }: FilterSelectProps) {
  const id = useId()
  const items = useMemo(() => options.map((o) => ({ value: o.value, label: o.label })), [options])
  return (
    <div className={cn('flex min-w-0 flex-col gap-1.5', className)}>
      <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
        {label}
      </label>
      <Select
        items={items}
        value={value}
        onValueChange={(v) => {
          if (typeof v === 'string') onChange(v)
        }}
        disabled={disabled}
      >
        <SelectTrigger id={id} className="w-full min-w-0 bg-card" title={hint}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.value} value={o.value} disabled={o.disabled}>
              {o.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
