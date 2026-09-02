'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import {
  BLUEPRINT_STAGES,
  COUNCIL_DECISION,
  ROLLOUT_PHASES,
  type BlueprintNode,
  type BlueprintStage,
} from '@/lib/blueprint'
import { BlueprintMap } from './blueprint-map'

const RISK_STYLES: Record<NonNullable<BlueprintNode['risk']>, string> = {
  low: 'bg-[#b9d8ac] text-foreground',
  medium: 'bg-secondary text-secondary-foreground',
  high: 'bg-[#e07a4c] text-accent-foreground',
}

export function BlueprintTab({ complete, architectureReport }: { complete: boolean; architectureReport?: any }) {
  const [mapOpen, setMapOpen] = useState(false)

  const stages: BlueprintStage[] = architectureReport?.atlas_executive?.stages || BLUEPRINT_STAGES;
  const decision = architectureReport?.atlas_executive?.decision || COUNCIL_DECISION;
  const rollout = architectureReport?.atlas_executive?.rollout || ROLLOUT_PHASES;

  if (!complete) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 bg-muted/60 p-6 text-center">
        <span
          aria-hidden="true"
          className="inline-block h-6 w-6 border-4 border-foreground bg-secondary blink"
        />
        <p className="font-mono text-[10px] uppercase tracking-widest text-foreground">
          Blueprint locked
        </p>
        <p className="max-w-[32ch] text-pretty font-mono text-[9px] uppercase leading-relaxed tracking-widest text-muted-foreground">
          The architecture output unlocks once every cabin reports done and Ethan signs off.
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Output · Supply network architecture
        </span>
        <div className="flex items-center gap-1.5">
          <span className="border-2 border-foreground bg-[#b9d8ac] px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest text-foreground">
            Validated
          </span>
          <button
            type="button"
            onClick={() => setMapOpen(true)}
            className="flex items-center gap-1 border-2 border-foreground bg-accent px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest text-accent-foreground transition-transform hover:-translate-y-px active:translate-y-0"
          >
            <span aria-hidden="true" className="inline-block h-1.5 w-1.5 border border-accent-foreground" />
            Expand map
          </button>
        </div>
      </div>

      <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-muted/60 p-3">
        {/* ---- interactive map callout ---- */}
        <button
          type="button"
          onClick={() => setMapOpen(true)}
          aria-label="Open the interactive supply network map"
          className="group mb-3 flex w-full items-center justify-between gap-3 border-2 border-foreground bg-foreground px-3 py-2.5 text-left pixel-shadow-sm transition-all hover:bg-primary active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
        >
          <span className="min-w-0">
            <span className="block font-mono text-[9px] uppercase tracking-widest text-secondary">
              {'>'} Interactive network map
            </span>
            <span className="mt-0.5 block text-pretty text-[10px] leading-snug text-card/80">
              Explore the full pipeline — trace flows between nodes, inspect specs, and see failure plays.
            </span>
          </span>
          <span
            aria-hidden="true"
            className="flex shrink-0 items-center gap-1 border-2 border-secondary px-1.5 py-1 font-mono text-[8px] uppercase tracking-widest text-secondary transition-transform group-hover:translate-x-0.5"
          >
            Open {'\u2192'}
          </span>
        </button>

        {/* ---- flow diagram ---- */}
        <section aria-label="Architecture flow" className="step-enter">
          <ol className="flex flex-col">
            {stages.map((stage: any, i: number) => (
              <li key={stage.id}>
                <div className="border-2 border-foreground bg-card pixel-shadow-sm">
                  <header className="flex items-center justify-between border-b-2 border-foreground bg-primary px-2.5 py-1.5">
                    <h3 className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
                      {String(i + 1).padStart(2, '0')} · {stage.label}
                    </h3>
                    <span className="font-mono text-[7px] uppercase tracking-widest text-secondary">
                      {stage.owner}
                    </span>
                  </header>
                  <div
                    className={cn(
                      'grid gap-2 p-2.5',
                      stage.nodes?.length > 1 ? 'min-[420px]:grid-cols-2 lg:grid-cols-3' : 'grid-cols-1',
                    )}
                  >
                    {stage.nodes?.map((node: any) => (
                      <div key={node.id} className="border-2 border-foreground bg-background p-2">
                        <div className="flex items-center justify-between gap-1.5">
                          <span className="font-mono text-[9px] uppercase tracking-wider">{node.name}</span>
                          {node.share ? (
                            <span className="border-2 border-foreground bg-accent px-1 py-0.5 font-mono text-[8px] tracking-wider text-accent-foreground">
                              {node.share}
                            </span>
                          ) : null}
                        </div>
                        <ul className="mt-1.5 flex flex-col gap-0.5">
                          {node.meta?.map((m: string) => (
                            <li key={m} className="text-[10px] leading-snug text-foreground/80">
                              {m}
                            </li>
                          ))}
                        </ul>
                        {node.risk ? (
                          <span
                            className={cn(
                              'mt-1.5 inline-block border-2 border-foreground px-1 py-0.5 font-mono text-[7px] uppercase tracking-widest',
                              RISK_STYLES[node.risk as NonNullable<BlueprintNode['risk']>],
                            )}
                          >
                            Risk {node.risk}
                          </span>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </div>

                {/* connector arrow */}
                {i < stages.length - 1 ? (
                  <div aria-hidden="true" className="flex flex-col items-center py-1">
                    <span className="h-3 w-1 bg-foreground" />
                    <span
                      className="h-2.5 w-4 bg-foreground"
                      style={{ clipPath: 'polygon(0 0, 100% 0, 50% 100%)' }}
                    />
                  </div>
                ) : null}
              </li>
            ))}
          </ol>
        </section>

        {/* ---- council decision record ---- */}
        <section aria-label="Council decision" className="mt-4 border-2 border-foreground bg-card pixel-shadow-sm">
          <header className="border-b-2 border-foreground bg-secondary px-2.5 py-1.5">
            <h3 className="font-mono text-[9px] uppercase tracking-widest text-secondary-foreground">
              Council decision record
            </h3>
          </header>
          <dl className="flex flex-col gap-2 p-2.5">
            {(
              [
                ['Verdict', decision.verdict],
                ['Allocation', decision.allocation],
                ['Reason', decision.reason],
                ['Trade-off', decision.tradeoff],
                ['Resilience', decision.resilience],
              ] as const
            ).map(([label, value]) => (
              <div key={label}>
                <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">{label}</dt>
                <dd className="mt-0.5 text-pretty text-[11px] leading-relaxed">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* ---- rollout ---- */}
        <section aria-label="Implementation rollout" className="mt-4 border-2 border-foreground bg-card pixel-shadow-sm">
          <header className="border-b-2 border-foreground bg-secondary px-2.5 py-1.5">
            <h3 className="font-mono text-[9px] uppercase tracking-widest text-secondary-foreground">
              Implementation rollout · Priya
            </h3>
          </header>
          <ol className="flex flex-col">
            {rollout.map((p: any, i: number) => (
              <li
                key={p.phase}
                className={cn(
                  'flex items-center gap-2.5 px-2.5 py-2',
                  i < rollout.length - 1 && 'border-b-2 border-dashed border-foreground/30',
                )}
              >
                <span className="shrink-0 border-2 border-foreground bg-primary px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest text-primary-foreground">
                  {p.phase}
                </span>
                <span className="min-w-0 flex-1 text-[11px] leading-snug">{p.action}</span>
                <span
                  className={cn(
                    'shrink-0 border-2 border-foreground px-1 py-0.5 font-mono text-[7px] uppercase tracking-widest',
                    p.status === 'Ready now' ? 'bg-[#b9d8ac] text-foreground' : 'bg-muted text-muted-foreground',
                  )}
                >
                  {p.status}
                </span>
              </li>
            ))}
          </ol>
        </section>

      </div>

      {mapOpen ? <BlueprintMap onClose={() => setMapOpen(false)} architectureReport={architectureReport} /> : null}
    </div>
  )
}
