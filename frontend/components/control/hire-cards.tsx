'use client'

import { cn } from '@/lib/utils'
import { getAgent, TEAM_COLORS } from '@/lib/agents'
import { formatElapsed, type HireEvent } from '@/lib/mission-sim'
import { AgentSprite } from '@/components/pixel/agent-sprite'

export function HireCardsTab({ hires }: { hires: HireEvent[] }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Personnel · Hired identity cards
        </span>
        <span className="font-mono text-[8px] uppercase tracking-widest text-secondary">
          {hires.length} hired
        </span>
      </div>

      <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-muted/60 p-3">
        {hires.length === 0 ? (
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {'> No hires yet. Atlas is assessing the mission…'}
            <span className="blink">_</span>
          </p>
        ) : (
          <ul className="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2">
            {[...hires].reverse().map((hire) => (
              <li key={hire.id}>
                <IdentityCard hire={hire} />
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function IdentityCard({ hire }: { hire: HireEvent }) {
  const def = getAgent(hire.agent)
  const colors = TEAM_COLORS[hire.team]

  return (
    <article className="step-enter border-2 border-foreground bg-card pixel-shadow-sm">
      {/* card header strip */}
      <div className={cn('flex items-center justify-between border-b-2 border-foreground px-2.5 py-1.5', colors.bg)}>
        <span className={cn('font-mono text-[7px] uppercase tracking-widest', colors.text)}>
          MYCEL Personnel
        </span>
        <span
          className={cn(
            'border-2 border-foreground px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest',
            hire.clearance === 'GREEN' ? 'bg-[#b9d8ac] text-foreground' : 'bg-secondary text-secondary-foreground',
          )}
        >
          {hire.clearance}
        </span>
      </div>

      <div className="flex gap-2.5 p-2.5">
        {/* pixel portrait */}
        <div
          aria-hidden="true"
          className={cn(
            'flex h-14 w-12 shrink-0 items-end justify-center overflow-hidden border-2 border-foreground',
            colors.bg,
          )}
        >
          {def ? (
            <AgentSprite charIdx={def.charIdx} scale={2} />
          ) : (
            <span className={cn('flex h-full w-full items-center justify-center font-mono text-sm', colors.text)}>
              {hire.agent.slice(0, 2).toUpperCase()}
            </span>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="font-mono text-[11px] uppercase tracking-wider">{hire.agent}</h3>
          <p className="mt-0.5 text-pretty text-[11px] leading-snug text-muted-foreground">{hire.role}</p>
        </div>
      </div>

      <dl className="border-t-2 border-dashed border-foreground/30 px-2.5 py-2">
        <div className="flex items-baseline justify-between gap-2">
          <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Badge</dt>
          <dd className="font-mono text-[8px] tracking-wider">{hire.badge}</dd>
        </div>
        <div className="mt-1 flex items-baseline justify-between gap-2">
          <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Team</dt>
          <dd className="font-mono text-[8px] uppercase tracking-wider">{hire.team}</dd>
        </div>
        <div className="mt-1 flex items-baseline justify-between gap-2">
          <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Hired at</dt>
          <dd className="font-mono text-[8px] tracking-wider">T+{formatElapsed(hire.at)}</dd>
        </div>
        <div className="mt-1.5">
          <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Mandate</dt>
          <dd className="mt-0.5 text-pretty text-[10px] leading-snug">{hire.mandate}</dd>
        </div>
      </dl>
    </article>
  )
}
