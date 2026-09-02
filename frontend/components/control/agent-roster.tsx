'use client'

import { cn } from '@/lib/utils'
import { AGENTS, TEAM_COLORS, type Team } from '@/lib/agents'
import { formatElapsed, type AgentState } from '@/lib/mission-sim'

const TEAM_ORDER: Team[] = ['Executive', 'Intelligence', 'Network', 'Resilience', 'Council', 'Architecture']

export function AgentRosterTab({
  agents,
  clock,
}: {
  agents: Record<string, AgentState>
  clock: number
}) {
  const activeCount = Object.values(agents).filter((a) => a.phase === 'working').length

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Workforce · Live status
        </span>
        <span className="font-mono text-[8px] uppercase tracking-widest text-secondary">
          {activeCount} working
        </span>
      </div>

      <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-card p-3">
        <div className="flex flex-col gap-4">
          {TEAM_ORDER.map((team) => {
            const members = AGENTS.filter((a) => a.team === team)
            return (
              <section key={team}>
                <h3
                  className={cn(
                    'mb-1.5 inline-block border-2 border-foreground px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest',
                    TEAM_COLORS[team].bg,
                    TEAM_COLORS[team].text,
                  )}
                >
                  {team}
                </h3>
                <ul className="flex flex-col gap-1.5">
                  {members.map((member) => (
                    <AgentRow
                      key={member.name}
                      name={member.name}
                      role={member.role}
                      state={agents[member.name]}
                      clock={clock}
                    />
                  ))}
                </ul>
              </section>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function AgentRow({
  name,
  role,
  state,
  clock,
}: {
  name: string
  role: string
  state: AgentState | undefined
  clock: number
}) {
  const phase = state?.phase ?? 'standby'

  let elapsed = ''
  if (state?.startedAt != null) {
    const end = state.finishedAt ?? clock
    elapsed = formatElapsed(end - state.startedAt)
  }

  const phaseStyles: Record<string, string> = {
    standby: 'bg-muted text-muted-foreground',
    hired: 'bg-secondary text-secondary-foreground',
    working: 'bg-accent text-accent-foreground',
    done: 'bg-[#b9d8ac] text-foreground',
  }

  const phaseLabel: Record<string, string> = {
    standby: 'Standby',
    hired: 'Hired',
    working: 'Working',
    done: 'Done',
  }

  return (
    <li
      className={cn(
        'flex items-center gap-2 border-2 border-foreground bg-background px-2.5 py-2',
        phase === 'standby' && 'opacity-50',
      )}
    >
      <span
        className={cn(
          'inline-block h-2.5 w-2.5 shrink-0 border-2 border-foreground',
          phase === 'working' ? 'bg-accent blink' : phase === 'done' ? 'bg-[#b9d8ac]' : phase === 'hired' ? 'bg-secondary' : 'bg-muted',
        )}
        aria-hidden="true"
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="font-mono text-[12px] uppercase tracking-wider text-foreground">{name}</span>
          <span className="truncate text-[11px] text-foreground/90">{role}</span>
        </div>
        {state && phase !== 'standby' && phase !== 'hired' ? (
          <p className="mt-0.5 truncate text-[12px] leading-snug text-foreground">{state.task}</p>
        ) : null}
      </div>
      <div className="flex shrink-0 flex-col items-end gap-0.5">
        <span
          className={cn(
            'border-2 border-foreground px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-widest',
            phaseStyles[phase],
          )}
        >
          {phaseLabel[phase]}
        </span>
        {elapsed ? (
          <span className="font-mono text-[10px] tabular-nums tracking-wider text-foreground/90">{elapsed}</span>
        ) : null}
      </div>
    </li>
  )
}
