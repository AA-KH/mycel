'use client'

import Link from 'next/link'
import { PixelChip } from '@/components/pixel/pixel-ui'
import { useMissionSim } from '@/lib/mission-sim'
import { OfficeViewport } from './office-viewport'
import { CommandCenter } from './command-center'

export function ControlRoom() {
  const mission = useMissionSim()

  return (
    <main className="flex h-svh flex-col overflow-hidden bg-background diag-texture">
      {/* top bar */}
      <header className="flex shrink-0 items-center justify-between gap-3 border-b-4 border-foreground bg-card px-4 py-2.5 md:px-6">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs uppercase tracking-widest">
            MYCEL <span className="text-accent">// Mission Control</span>
          </span>
          <PixelChip variant={mission.complete ? 'yellow' : 'orange'} className="hidden sm:inline-block">
            {mission.complete ? 'Blueprint ready' : 'Network compiling'}
          </PixelChip>
        </div>
        <Link
          href="/setup"
          className="border-2 border-foreground bg-card px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted"
        >
          Edit inputs
        </Link>
      </header>

      {/* main split: office viewport + command center */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(360px,480px)] md:p-5">
        <div className="min-h-0 max-lg:h-[42svh]">
          <OfficeViewport mission={mission} />
        </div>
        <div className="min-h-0 max-lg:flex-1">
          <CommandCenter mission={mission} />
        </div>
      </div>
    </main>
  )
}
