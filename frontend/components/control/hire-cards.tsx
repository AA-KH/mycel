'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { getAgent, TEAM_COLORS } from '@/lib/agents'
import { formatElapsed, type AgentState, type HireEvent } from '@/lib/mission-sim'
import { AgentSprite } from '@/components/pixel/agent-sprite'
import { HireDossierCard } from './hire-dossier-card'

export function HireCardsTab({
  hires,
  agents,
  clock,
}: {
  hires: HireEvent[]
  agents: Record<string, AgentState>
  clock: number
}) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const selected = selectedId != null ? hires.find((h) => h.id === selectedId) : undefined

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
            {'> No hires yet. Maya is assessing the mission…'}
            <span className="blink">_</span>
          </p>
        ) : (
          <ul className="grid grid-cols-1 gap-3 min-[480px]:grid-cols-2">
            {[...hires].reverse().map((hire) => (
              <li key={hire.id}>
                <IdentityCard hire={hire} state={agents[hire.agent]} onOpen={() => setSelectedId(hire.id)} />
              </li>
            ))}
          </ul>
        )}
      </div>

      {selected ? (
        <HireDossierCard
          hire={selected}
          state={agents[selected.agent]}
          clock={clock}
          onClose={() => setSelectedId(null)}
        />
      ) : null}
    </div>
  )
}

function IdentityCard({
  hire,
  state,
  onOpen,
}: {
  hire: HireEvent
  state: AgentState | undefined
  onOpen: () => void
}) {
  const def = getAgent(hire.agent)
  const colors = TEAM_COLORS[hire.team] || { bg: 'bg-muted', text: 'text-muted-foreground', chip: 'bg-muted' }
  const phase = state?.phase ?? 'hired'

  return (
    <article className="step-enter">
      <button
        type="button"
        onClick={onOpen}
        aria-label={`Open personnel card for ${hire.agent}`}
        className="group block w-full border-2 border-foreground bg-card text-left pixel-shadow-sm transition-all hover:scale-[1.04] hover:pixel-shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent active:scale-100 active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
      >
        {/* card header strip */}
        <div className={cn('flex items-center justify-between border-b-2 border-foreground px-2.5 py-1.5', colors.bg)}>
          <span className={cn('font-mono text-[7px] uppercase tracking-widest', colors.text)}>MYCEL Personnel</span>
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
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-mono text-[11px] uppercase tracking-wider">{hire.agent}</h3>
              <span
                aria-hidden="true"
                className={cn(
                  'inline-block h-2 w-2 shrink-0 border border-foreground',
                  phase === 'working' ? 'bg-accent blink' : phase === 'done' ? 'bg-[#b9d8ac]' : 'bg-secondary',
                )}
              />
            </div>
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
            <dd className="mt-0.5 line-clamp-2 text-pretty text-[10px] leading-snug">{hire.mandate}</dd>
          </div>
        </dl>

        <div className="flex items-center justify-between border-t-2 border-foreground bg-muted px-2.5 py-1.5">
          <span className="font-mono text-[7px] uppercase tracking-widest text-muted-foreground">
            {phase === 'working' ? 'On assignment' : phase === 'done' ? 'Assignment complete' : 'Awaiting assignment'}
          </span>
          <span className="font-mono text-[7px] uppercase tracking-widest text-foreground group-hover:text-accent">
            View details {'\u2192'}
          </span>
        </div>
      </button>
    </article>
  )
}
