'use client'

import { useCallback, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { getAgent, TEAM_COLORS } from '@/lib/agents'
import { AGENT_DOSSIERS } from '@/lib/agent-dossiers'
import { formatElapsed, type AgentState, type HireEvent } from '@/lib/mission-sim'
import { AgentSprite } from '@/components/pixel/agent-sprite'

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mb-2 flex items-center gap-2 font-mono text-[9px] uppercase tracking-widest text-accent">
      <span aria-hidden="true" className="inline-block h-2 w-2 border-2 border-foreground bg-accent" />
      {children}
    </h4>
  )
}

const PHASE_STYLES: Record<string, string> = {
  standby: 'bg-muted text-muted-foreground',
  hired: 'bg-secondary text-secondary-foreground',
  working: 'bg-accent text-accent-foreground',
  done: 'bg-[#b9d8ac] text-foreground',
}

const PHASE_LABEL: Record<string, string> = {
  standby: 'Standby',
  hired: 'Hired · awaiting assignment',
  working: 'Working',
  done: 'Completed',
}

export function HireDossierCard({
  hire,
  state,
  clock,
  onClose,
}: {
  hire: HireEvent
  state: AgentState | undefined
  clock: number
  onClose: () => void
}) {
  const def = getAgent(hire.agent)
  const dossier = AGENT_DOSSIERS[hire.agent]
  const colors = TEAM_COLORS[hire.team] || { bg: 'bg-muted', text: 'text-muted-foreground', chip: 'bg-muted' }
  const closeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const onBackdrop = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === e.currentTarget) onClose()
    },
    [onClose],
  )

  const phase = state?.phase ?? 'hired'
  let elapsed = ''
  if (state?.startedAt != null) {
    const end = state.finishedAt ?? clock
    elapsed = formatElapsed(end - state.startedAt)
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="hire-dossier-title"
      onClick={onBackdrop}
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/60 p-4 sm:p-8"
    >
      <div className="flex max-h-full w-full max-w-2xl flex-col border-4 border-foreground bg-card pixel-shadow">
        {/* ---------- header ---------- */}
        <header className={cn('relative flex shrink-0 items-stretch border-b-4 border-foreground', colors.bg)}>
          <div className="flex w-24 shrink-0 items-end justify-center overflow-hidden border-r-4 border-foreground bg-card/40 pt-3 sm:w-28">
            {def ? (
              <AgentSprite charIdx={def.charIdx} scale={4} />
            ) : (
              <span className={cn('flex h-full w-full items-center justify-center pb-3 font-mono text-2xl', colors.text)}>
                {hire.agent.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>
          <div className="min-w-0 flex-1 px-4 py-3 pr-12">
            <div className="mb-1.5 flex flex-wrap items-center gap-1.5">
              <span className="inline-block border-2 border-foreground bg-card px-2 py-0.5 font-mono text-[8px] uppercase tracking-widest text-foreground">
                {hire.team} team
              </span>
              <span
                className={cn(
                  'inline-block border-2 border-foreground px-2 py-0.5 font-mono text-[8px] uppercase tracking-widest',
                  hire.clearance === 'GREEN' ? 'bg-[#b9d8ac] text-foreground' : 'bg-secondary text-secondary-foreground',
                )}
              >
                Clearance {hire.clearance}
              </span>
            </div>
            <h3 id="hire-dossier-title" className="font-mono text-xl uppercase tracking-wider text-foreground sm:text-2xl">
              {hire.agent}
            </h3>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-foreground/70">{hire.role}</p>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close personnel card"
            className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center border-2 border-foreground bg-card font-mono text-sm text-foreground pixel-shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            {'\u00d7'}
          </button>
        </header>

        {/* ---------- scrollable body ---------- */}
        <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
          {/* mandate */}
          <section>
            <SectionLabel>Mandate from Maya</SectionLabel>
            <p className="text-pretty border-2 border-foreground bg-muted/70 p-3 text-[13px] leading-relaxed text-foreground">
              {hire.mandate}
            </p>
          </section>

          {/* personnel record */}
          <section className="mt-5">
            <SectionLabel>Personnel record</SectionLabel>
            <dl className="grid grid-cols-2 gap-px border-2 border-foreground bg-foreground sm:grid-cols-4">
              {[
                { label: 'Badge', value: hire.badge },
                { label: 'Team', value: hire.team },
                { label: 'Clearance', value: hire.clearance },
                { label: 'Hired at', value: `T+${formatElapsed(hire.at)}` },
              ].map((item) => (
                <div key={item.label} className="flex flex-col gap-1 bg-card px-3 py-2">
                  <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">{item.label}</dt>
                  <dd className="font-mono text-[10px] uppercase tracking-wider text-foreground">{item.value}</dd>
                </div>
              ))}
            </dl>
          </section>

          {/* work assignment */}
          <section className="mt-5">
            <SectionLabel>Work assignment</SectionLabel>
            <div className="border-2 border-foreground bg-background">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b-2 border-dashed border-foreground/30 px-3 py-2">
                <span className="flex items-center gap-2">
                  <span
                    aria-hidden="true"
                    className={cn(
                      'inline-block h-2.5 w-2.5 border-2 border-foreground',
                      phase === 'working'
                        ? 'bg-accent blink'
                        : phase === 'done'
                          ? 'bg-[#b9d8ac]'
                          : 'bg-secondary',
                    )}
                  />
                  <span
                    className={cn(
                      'border-2 border-foreground px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest',
                      PHASE_STYLES[phase],
                    )}
                  >
                    {PHASE_LABEL[phase]}
                  </span>
                </span>
                {elapsed ? (
                  <span className="font-mono text-[9px] tabular-nums uppercase tracking-widest text-muted-foreground">
                    {phase === 'done' ? 'Took' : 'Running'} {elapsed}
                  </span>
                ) : null}
              </div>
              <div className="px-3 py-2.5">
                {state?.task ? (
                  <p className="text-pretty text-[12px] leading-relaxed text-foreground">{state.task}</p>
                ) : (
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    {'> Atlas has not dispatched a task yet'}
                    <span className="blink">_</span>
                  </p>
                )}
                {state?.startedAt != null ? (
                  <dl className="mt-2.5 flex flex-wrap gap-x-5 gap-y-1">
                    <div className="flex items-baseline gap-1.5">
                      <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Started</dt>
                      <dd className="font-mono text-[9px] tabular-nums tracking-wider">T+{formatElapsed(state.startedAt)}</dd>
                    </div>
                    {state.finishedAt != null ? (
                      <div className="flex items-baseline gap-1.5">
                        <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">Finished</dt>
                        <dd className="font-mono text-[9px] tabular-nums tracking-wider">
                          T+{formatElapsed(state.finishedAt)}
                        </dd>
                      </div>
                    ) : null}
                  </dl>
                ) : null}
              </div>
            </div>
          </section>

          {/* responsibilities from dossier */}
          {dossier?.responsibilities ? (
            <section className="mt-5">
              <SectionLabel>Responsible for</SectionLabel>
              <ul className="grid gap-x-4 gap-y-1.5 sm:grid-cols-2">
                {dossier.responsibilities.map((r) => (
                  <li key={r} className="flex gap-2 text-[12px] leading-snug text-foreground/90">
                    <span aria-hidden="true" className={cn('mt-1 h-2 w-2 shrink-0 border border-foreground', colors.bg)} />
                    <span className="text-pretty">{r}</span>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {/* MCP tools */}
          {dossier?.tools ? (
            <section className="mt-5">
              <SectionLabel>MCP tools</SectionLabel>
              <ul className="flex flex-wrap gap-1.5">
                {dossier.tools.map((t) => (
                  <li
                    key={t}
                    className="border-2 border-foreground bg-primary px-2 py-1 font-mono text-[10px] text-primary-foreground"
                  >
                    {t}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>

        {/* ---------- footer ---------- */}
        <footer className="flex shrink-0 items-center justify-between border-t-2 border-foreground bg-muted px-4 py-2">
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">
            MYCEL Personnel {'\u00b7'} {hire.badge}
          </span>
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">Esc to close</span>
        </footer>
      </div>
    </div>
  )
}
