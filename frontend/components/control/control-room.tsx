'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { PixelChip } from '@/components/pixel/pixel-ui'
import { useMissionSim } from '@/lib/mission-sim'
import { OfficeViewport } from './office-viewport'
import { CommandCenter } from './command-center'
import { TeamTab } from './team-tab'

import { useSearchParams } from 'next/navigation'

export function ControlRoom() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get('project')
  const mission = useMissionSim(projectId)
  const [teamOpen, setTeamOpen] = useState(false)

  /* close the team directory with Escape */
  useEffect(() => {
    if (!teamOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setTeamOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [teamOpen])

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
        <div className="flex shrink-0 items-center gap-2">
          <button
            type="button"
            onClick={() => setTeamOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={teamOpen}
            className="border-2 border-foreground bg-secondary px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest text-secondary-foreground pixel-shadow-sm hover:bg-muted hover:text-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            Team
          </button>
          <Link
            href="/"
            className="border-2 border-foreground bg-card px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted hover:bg-destructive/10 hover:text-destructive hover:border-destructive transition-colors"
          >
            Exit
          </Link>
          <Link
            href={`/setup?project=${projectId || ''}`}
            className="border-2 border-foreground bg-card px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted"
          >
            Edit inputs
          </Link>
        </div>
      </header>

      {/* team directory overlay */}
      {teamOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Team directory"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
        >
          <button
            type="button"
            aria-label="Close team directory"
            onClick={() => setTeamOpen(false)}
            className="absolute inset-0 bg-foreground/60"
          />
          <div className="relative flex h-full w-full max-w-3xl flex-col border-4 border-foreground bg-card pixel-shadow">
            <header className="flex shrink-0 items-center justify-between gap-2 border-b-2 border-foreground bg-secondary px-3 py-2">
              <h2 className="font-mono text-[10px] uppercase tracking-widest text-secondary-foreground">
                Team Directory
              </h2>
              <button
                type="button"
                onClick={() => setTeamOpen(false)}
                className="border-2 border-foreground bg-card px-2.5 py-1 font-mono text-[9px] uppercase tracking-widest pixel-shadow-sm hover:bg-muted active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
              >
                Close
              </button>
            </header>
            <div className="min-h-0 flex-1">
              <TeamTab />
            </div>
          </div>
        </div>
      ) : null}

      {/* main split: office viewport + command center */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_minmax(360px,480px)] md:p-5">
        <div className="min-h-0 max-lg:h-[42svh]">
          <OfficeViewport mission={mission} projectId={projectId} />
        </div>
        <div className="min-h-0 max-lg:flex-1">
          <CommandCenter mission={mission} projectId={projectId} />
        </div>
      </div>
    </main>
  )
}
