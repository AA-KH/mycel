'use client'

import { useCallback, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { TEAM_COLORS, type AgentDef } from '@/lib/agents'
import { AGENT_DOSSIERS } from '@/lib/agent-dossiers'
import { AgentSprite } from '@/components/pixel/agent-sprite'

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mb-2 flex items-center gap-2 font-mono text-[9px] uppercase tracking-widest text-accent">
      <span aria-hidden="true" className="inline-block h-2 w-2 border-2 border-foreground bg-accent" />
      {children}
    </h4>
  )
}

export function AgentDossierCard({
  agent,
  onClose,
}: {
  agent: AgentDef
  onClose: () => void
}) {
  const dossier = AGENT_DOSSIERS[agent.name]
  const colors = TEAM_COLORS[agent.team]
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

  if (!dossier) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dossier-title"
      onClick={onBackdrop}
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/60 p-4 sm:p-8"
    >
      <div className="flex max-h-full w-full max-w-2xl flex-col border-4 border-foreground bg-card pixel-shadow">
        {/* ---------- header ---------- */}
        <header className={cn('relative flex shrink-0 items-stretch gap-0 border-b-4 border-foreground', colors.bg)}>
          <div className="flex w-24 shrink-0 items-end justify-center overflow-hidden border-r-4 border-foreground bg-card/40 pt-3 sm:w-28">
            <AgentSprite charIdx={agent.charIdx} scale={4} />
          </div>
          <div className="min-w-0 flex-1 px-4 py-3 pr-12">
            <span
              className={cn(
                'mb-1.5 inline-block border-2 border-foreground bg-card px-2 py-0.5 font-mono text-[8px] uppercase tracking-widest text-foreground',
              )}
            >
              {agent.team} team
            </span>
            <h3 id="dossier-title" className="font-mono text-xl uppercase tracking-wider text-foreground sm:text-2xl">
              {agent.name}
            </h3>
            <p className="mt-0.5 font-mono text-[10px] uppercase tracking-widest text-foreground/70">{agent.role}</p>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close dossier"
            className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center border-2 border-foreground bg-card font-mono text-sm text-foreground pixel-shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            {'\u00d7'}
          </button>
        </header>

        {/* ---------- scrollable body ---------- */}
        <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-5">
          {/* mission */}
          <p className="text-pretty border-2 border-foreground bg-muted/70 p-3 text-[13px] leading-relaxed text-foreground">
            {dossier.mission}
          </p>

          {/* responsibilities */}
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

          {/* how it works */}
          {dossier.workflow ? (
            <section className="mt-5">
              <SectionLabel>How {agent.name} works</SectionLabel>
              <ol className="flex flex-col gap-1.5">
                {dossier.workflow.map((step, i) => (
                  <li key={step} className="flex gap-2.5 text-[12px] leading-snug text-foreground/90">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center border-2 border-foreground bg-secondary font-mono text-[9px] text-secondary-foreground">
                      {i + 1}
                    </span>
                    <span className="text-pretty pt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </section>
          ) : null}

          {/* MCP tools */}
          {dossier.tools ? (
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

          {/* sample output */}
          {dossier.output ? (
            <section className="mt-5">
              <SectionLabel>Sample output</SectionLabel>
              <div className="border-2 border-foreground bg-foreground p-3 pixel-shadow-sm">
                <p className="mb-2 font-mono text-[9px] uppercase tracking-widest text-secondary">
                  {'>'} {dossier.output.title}
                </p>
                <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-card">
                  {dossier.output.lines.join('\n')}
                </pre>
              </div>
            </section>
          ) : null}
        </div>

        {/* ---------- footer ---------- */}
        <footer className="flex shrink-0 items-center justify-between border-t-2 border-foreground bg-muted px-4 py-2">
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">
            Agent dossier {'\u00b7'} {agent.name}
          </span>
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">Esc to close</span>
        </footer>
      </div>
    </div>
  )
}
