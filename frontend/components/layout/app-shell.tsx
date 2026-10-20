'use client'

import { Menu, Sprout, X } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { TooltipProvider } from '@/components/ui/tooltip'
import { FiltersProvider } from '@/lib/filters-context'
import { cn } from '@/lib/utils'
import { DataSourceBadge } from './data-source-badge'
import { NAV_ITEMS } from './nav-items'

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  return (
    <FiltersProvider>
      <TooltipProvider>
        <div className="flex min-h-dvh">
          <a
            href="#main"
            className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2"
          >
            Skip to content
          </a>

          {open && (
            <button
              type="button"
              aria-label="Close navigation"
              className="fixed inset-0 z-30 bg-foreground/30 lg:hidden"
              onClick={() => setOpen(false)}
            />
          )}

          <aside
            id="app-sidebar"
            className={cn(
              'fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar text-sidebar-foreground transition-transform lg:sticky lg:top-0 lg:h-dvh lg:translate-x-0',
              open ? 'translate-x-0' : '-translate-x-full',
            )}
          >
            <div className="flex items-center justify-between gap-2 px-5 pb-6 pt-5">
              <Link href="/" className="flex items-center gap-2.5" onClick={() => setOpen(false)}>
                <span className="flex size-9 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <Sprout className="size-5" aria-hidden="true" />
                </span>
                <span className="flex flex-col leading-tight">
                  <span className="text-sm font-semibold">AgriStat India</span>
                  <span className="text-xs text-sidebar-foreground/70">Crop production analytics</span>
                </span>
              </Link>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground lg:hidden"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
              >
                <X aria-hidden="true" />
              </Button>
            </div>

            <nav aria-label="Main" className="flex-1 overflow-y-auto px-3">
              <ul className="flex flex-col gap-1">
                {NAV_ITEMS.map((item) => {
                  const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
                  const Icon = item.icon
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setOpen(false)}
                        aria-current={active ? 'page' : undefined}
                        className={cn(
                          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                          active
                            ? 'bg-sidebar-accent font-medium text-sidebar-accent-foreground'
                            : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground',
                        )}
                      >
                        <Icon className={cn('size-4', active && 'text-sidebar-primary')} aria-hidden="true" />
                        {item.label}
                      </Link>
                    </li>
                  )
                })}
              </ul>
            </nav>

            <div className="border-t border-sidebar-border p-4">
              <DataSourceBadge variant="sidebar" />
            </div>
          </aside>

          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-20 flex items-center gap-3 border-b bg-background/90 px-4 py-3 backdrop-blur lg:hidden">
              <Button
                variant="outline"
                size="icon-sm"
                onClick={() => setOpen(true)}
                aria-label="Open navigation"
                aria-expanded={open}
                aria-controls="app-sidebar"
              >
                <Menu aria-hidden="true" />
              </Button>
              <span className="text-sm font-semibold">AgriStat India</span>
              <div className="ml-auto">
                <DataSourceBadge variant="compact" />
              </div>
            </header>
            <main id="main" className="flex-1 px-4 py-6 md:px-8 md:py-8">
              <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-6">{children}</div>
            </main>
          </div>
        </div>
      </TooltipProvider>
    </FiltersProvider>
  )
}
