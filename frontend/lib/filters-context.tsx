'use client'

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import type { DatasetMeta, Filters } from './data/types'
import { useMeta } from '@/hooks/use-analytics'

type DraftFilters = Omit<Filters, 'yearFrom' | 'yearTo'> & { yearFrom: number | null; yearTo: number | null }

const DEFAULT_DRAFT: DraftFilters = {
  yearFrom: null,
  yearTo: null,
  state: 'all',
  district: 'all',
  crop: 'all',
  season: 'all',
  dataType: 'all',
  metric: 'production',
}

interface FiltersContextValue {
  meta: DatasetMeta | undefined
  metaError: Error | undefined
  /** Fully resolved filters, or null until dataset metadata is available. */
  filters: Filters | null
  setFilter: <K extends keyof Filters>(key: K, value: Filters[K]) => void
  setYearRange: (from: number, to: number) => void
  resetFilters: () => void
  isDefault: boolean
}

const FiltersContext = createContext<FiltersContextValue | null>(null)

/** Enforces dependent-filter rules so the UI can never hold an inconsistent combination. */
function reconcile(next: DraftFilters, meta: DatasetMeta | undefined): DraftFilters {
  const result = { ...next }
  if (!meta) return result
  if (result.state !== 'all' && meta.states?.length && !meta.states.includes(result.state)) {
    result.state = 'all'
  }
  if (result.district !== 'all' && result.state !== 'all') {
    const districts = meta.districtsByState?.[result.state]
    if (districts && districts.length > 0 && !districts.includes(result.district)) {
      result.district = 'all'
    }
  }
  if (result.crop !== 'all' && result.state !== 'all') {
    const crops = meta.cropsByState?.[result.state]
    if (crops && crops.length > 0 && !crops.includes(result.crop)) {
      result.crop = 'all'
    }
  }
  if (result.season !== 'all' && result.crop !== 'all') {
    const seasons = meta.seasonsByCrop?.[result.crop]
    if (seasons && seasons.length > 0 && !seasons.includes(result.season)) {
      result.season = 'all'
    }
  }
  if (result.metric === 'yield' && result.crop === 'all') result.metric = 'production'
  if (result.yearFrom !== null && result.yearTo !== null && result.yearFrom > result.yearTo) {
    ;[result.yearFrom, result.yearTo] = [result.yearTo, result.yearFrom]
  }
  return result
}

export function FiltersProvider({ children }: { children: ReactNode }) {
  const { data: meta, error: metaError } = useMeta()
  const [draft, setDraft] = useState<DraftFilters>(DEFAULT_DRAFT)

  const setFilter = useCallback<FiltersContextValue['setFilter']>(
    (key, value) => {
      setDraft((prev) => {
        const next = { ...prev, [key]: value }
        if (key === 'state') next.district = 'all'
        return reconcile(next, meta)
      })
    },
    [meta],
  )

  const setYearRange = useCallback(
    (from: number, to: number) => setDraft((prev) => reconcile({ ...prev, yearFrom: from, yearTo: to }, meta)),
    [meta],
  )

  const resetFilters = useCallback(() => setDraft(DEFAULT_DRAFT), [])

  const filters = useMemo<Filters>(() => {
    const yearMin = meta?.yearMin ?? 1997
    const yearMax = meta?.yearMax ?? 2025
    return {
      ...draft,
      yearFrom: draft.yearFrom ?? yearMin,
      yearTo: draft.yearTo ?? yearMax,
    }
  }, [draft, meta])

  const isDefault = useMemo(() => {
    const yearMin = meta?.yearMin ?? 1997
    const yearMax = meta?.yearMax ?? 2025
    return (
      filters.yearFrom === yearMin &&
      filters.yearTo === yearMax &&
      draft.state === 'all' &&
      draft.district === 'all' &&
      draft.crop === 'all' &&
      draft.season === 'all' &&
      draft.dataType === 'all' &&
      draft.metric === 'production'
    )
  }, [draft, filters, meta])

  const value = useMemo(
    () => ({ meta, metaError, filters, setFilter, setYearRange, resetFilters, isDefault }),
    [meta, metaError, filters, setFilter, setYearRange, resetFilters, isDefault],
  )

  return <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>
}

export function useFilters() {
  const ctx = useContext(FiltersContext)
  if (!ctx) throw new Error('useFilters must be used inside <FiltersProvider>')
  return ctx
}
