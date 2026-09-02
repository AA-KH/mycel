'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { AGENTS, TEAM_COLORS, type AgentDef, type Team } from '@/lib/agents'
import { AGENT_TAGLINES, TEAM_DESCRIPTIONS } from '@/lib/agent-dossiers'
import { AgentSprite } from '@/components/pixel/agent-sprite'
import { AgentDossierCard } from './agent-dossier-card'

const TEAM_ORDER: Team[] = ['Executive', 'Intelligence', 'Network', 'Resilience', 'Council', 'Architecture']

const TEAM_TAGLINE: Record<Team, string> = {
  Executive: 'Runs the whole floor',
  Intelligence: 'What exists out there?',
  Network: 'How should we connect it?',
  Resilience: 'What happens when it breaks?',
  Council: 'What should we actually do?',
  Architecture: 'What does the final network look like?',
}

export function TeamTab() {
  const [selected, setSelected] = useState<AgentDef | null>(null)

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Org chart {'\u00b7'} Full agent directory
        </span>
        <span className="font-mono text-[8px] uppercase tracking-widest text-secondary">
          {AGENTS.length} agents
        </span>
      </div>

      <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-muted/60 p-3">
        {/* overall directory intro */}
        <div className="mb-4 border-2 border-foreground bg-card p-3 pixel-shadow-sm">
          <p className="text-pretty text-[13px] leading-relaxed text-foreground/90">
            An autonomous organization of {AGENTS.length} agents across six teams that researches, designs,
            stress-tests, and debates its way to a complete supply network architecture.
          </p>
          <p className="mt-1.5 font-mono text-[10px] uppercase tracking-widest text-accent">
            Click any member to open their full dossier
          </p>
        </div>

        <div className="flex flex-col gap-5">
          {TEAM_ORDER.map((team) => {
            const members = AGENTS.filter((a) => a.team === team)
            const colors = TEAM_COLORS[team]
            return (
              <section key={team} aria-label={`${team} team`}>
                <header className="mb-2">
                  <div className="flex items-baseline gap-2">
                    <h3
                      className={cn(
                        'inline-block border-2 border-foreground px-2 py-0.5 font-mono text-[10px] uppercase tracking-widest',
                        colors.bg,
                        colors.text,
                      )}
                    >
                      {team}
                    </h3>
                    <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                      {TEAM_TAGLINE[team]}
                    </span>
                  </div>
                  {/* team description lives outside the member cards */}
                  <p className="mt-1.5 text-pretty text-[13px] leading-relaxed text-foreground/75">
                    {TEAM_DESCRIPTIONS[team]}
                  </p>
                </header>

                <ul className="flex flex-col gap-2">
                  {members.map((member) => (
                    <li key={member.name}>
                      <button
                        type="button"
                        onClick={() => setSelected(member)}
                        className="group flex w-full items-center gap-2.5 border-2 border-foreground bg-card p-2 text-left pixel-shadow-sm transition-colors hover:bg-muted active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                        aria-haspopup="dialog"
                        aria-label={`Open dossier for ${member.name}, ${member.role}`}
                      >
                        {/* pixel portrait */}
                        <span
                          aria-hidden="true"
                          className={cn(
                            'flex h-12 w-11 shrink-0 items-end justify-center overflow-hidden border-2 border-foreground',
                            colors.bg,
                          )}
                        >
                          <AgentSprite charIdx={member.charIdx} scale={2} />
                        </span>

                        <span className="min-w-0 flex-1">
                          <span className="flex flex-wrap items-baseline gap-x-2">
                            <span className="font-mono text-[13px] uppercase tracking-wider">{member.name}</span>
                            <span className="font-mono text-[9px] uppercase tracking-widest text-accent">
                              {member.role}
                            </span>
                          </span>
                          <span className="mt-0.5 block truncate text-[12px] leading-relaxed text-foreground/70">
                            {AGENT_TAGLINES[member.name] ?? member.detail}
                          </span>
                        </span>

                        {/* open-dossier affordance */}
                        <span
                          aria-hidden="true"
                          className="shrink-0 border-2 border-foreground bg-muted px-1.5 py-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground transition-colors group-hover:bg-accent group-hover:text-accent-foreground"
                        >
                          {'\u25b8'}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )
          })}
        </div>
      </div>

      {selected ? <AgentDossierCard agent={selected} onClose={() => setSelected(null)} /> : null}
    </div>
  )
}
