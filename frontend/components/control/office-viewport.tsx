'use client'

import { formatElapsed, type MissionState } from '@/lib/mission-sim'
import PixelOffice from '@/components/pixel/pixel-office'
import { ArchitectChat } from './architect-chat'

/**
 * Viewport for the pixelated office scene.
 * Receives the full MissionState so the simulation engine inside
 * PixelOffice can drive agent movement based on log events.
 */
export function OfficeViewport({ mission, projectId }: { mission: MissionState; projectId: string | null }) {
  const { clock, complete } = mission;
  return (
    <section
      aria-label="MYCEL office floor"
      className="relative flex h-full min-h-0 flex-col border-4 border-foreground bg-primary pixel-shadow"
    >
      {/* title bar */}
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          MYCEL HQ · Office floor
        </span>
        <span className="flex items-center gap-3">
          <span className="font-mono text-[8px] uppercase tracking-widest text-secondary">
            Mission clock T+{formatElapsed(clock)}
          </span>
          <span className="flex items-center gap-1.5 font-mono text-[8px] uppercase tracking-widest text-primary-foreground">
            <span className={`inline-block h-2 w-2 ${complete ? 'bg-[#b9d8ac]' : 'bg-accent blink'}`} />
            {complete ? 'Complete' : 'Running'}
          </span>
        </span>
      </div>

      {/* fixed pixel office — camera fits the whole floor, no zoom / scroll */}
      <div className="relative min-h-0 flex-1 overflow-hidden bg-[#0e0e14]">
        <PixelOffice mission={mission} />
        
        {/* Floating architect chatbot */}
        <div className="absolute bottom-4 right-4 z-50">
          <ArchitectChat projectId={projectId} />
        </div>
      </div>
    </section>
  )
}
