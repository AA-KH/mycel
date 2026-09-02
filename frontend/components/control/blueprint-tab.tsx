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

export function BlueprintTab({
  complete,
  architectureReport,
  loadingReport = false,
  demo = false,
  projectId,
}: {
  complete: boolean
  architectureReport?: any
  loadingReport?: boolean
  /** scripted marketing timeline — no backend, sample blueprint is expected */
  demo?: boolean
  projectId: string | null
}) {
  const [mapOpen, setMapOpen] = useState(false)

  const atlas = architectureReport?.atlas_executive
  const isLive = Array.isArray(atlas?.stages) && atlas.stages.length > 0
  const atlasError: string | null = atlas?.error ?? null
  const showFallbackNotice = !isLive && !demo

  const stages: BlueprintStage[] = isLive ? atlas.stages : BLUEPRINT_STAGES
  const decision = isLive && atlas.decision ? atlas.decision : COUNCIL_DECISION
  const rollout = isLive && Array.isArray(atlas.rollout) && atlas.rollout.length > 0 ? atlas.rollout : ROLLOUT_PHASES
  const rolloutOwner = isLive ? 'Atlas' : 'Priya'

  if (!complete) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 bg-muted/60 p-6 text-center">
        <span
          aria-hidden="true"
          className="inline-block h-6 w-6 border-4 border-foreground bg-secondary blink"
        />
        <p className="font-mono text-[11px] uppercase tracking-widest text-foreground">
          Blueprint locked
        </p>
        <p className="max-w-[32ch] text-pretty font-mono text-[10px] uppercase leading-relaxed tracking-widest text-muted-foreground">
          The architecture output unlocks once every cabin reports done and Ethan signs off.
        </p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-widest text-primary-foreground">
          Output · Supply network architecture
        </span>
        <div className="flex items-center gap-1.5">
          <span
            className={cn(
              'border-2 border-foreground px-1.5 py-0.5 font-mono text-[8px] uppercase tracking-widest',
              isLive || demo
                ? 'bg-[#b9d8ac] text-foreground'
                : loadingReport
                  ? 'bg-muted text-muted-foreground blink'
                  : 'bg-[#e07a4c] text-accent-foreground',
            )}
          >
            {isLive ? 'Atlas · Live' : demo ? 'Validated' : loadingReport ? 'Loading' : 'Sample data'}
          </span>
          <button
            type="button"
            onClick={() => setMapOpen(true)}
            className="flex items-center gap-1 border-2 border-foreground bg-accent px-1.5 py-0.5 font-mono text-[8px] uppercase tracking-widest text-accent-foreground transition-transform hover:-translate-y-px active:translate-y-0"
          >
            <span aria-hidden="true" className="inline-block h-1.5 w-1.5 border border-accent-foreground" />
            Expand map
          </button>
        </div>
      </div>

      <div className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-muted/60 p-3">
        {/* ---- live-data status ---- */}
        {showFallbackNotice ? (
          <div
            role="status"
            className={cn(
              'mb-3 border-2 border-foreground p-2.5 pixel-shadow-sm',
              loadingReport ? 'bg-card' : 'bg-[#e07a4c] text-accent-foreground',
            )}
          >
            <p className="font-mono text-[10px] uppercase tracking-widest">
              {loadingReport ? '> Fetching Atlas blueprint…' : '!! Atlas output unavailable — showing sample blueprint'}
            </p>
            {atlasError ? (
              <p className="mt-1 text-pretty text-[11px] leading-snug">
                {atlasError}
                {typeof atlas?.raw === 'string' && atlas.raw.trim() ? (
                  <>
                    {' '}
                    Raw head: <span className="font-mono">{atlas.raw.trim().slice(0, 160)}…</span>
                  </>
                ) : null}
              </p>
            ) : !loadingReport ? (
              <p className="mt-1 text-pretty text-[11px] leading-snug">
                The backend did not return an <span className="font-mono">atlas_executive</span> block for this project.
                Check the Atlas feed for the failure reason and re-run the network.
              </p>
            ) : null}
          </div>
        ) : null}

        {/* ---- interactive map callout ---- */}
        <button
          type="button"
          onClick={() => setMapOpen(true)}
          aria-label="Open the interactive supply network map"
          className="group mb-3 flex w-full items-center justify-between gap-3 border-2 border-foreground bg-foreground px-3 py-2.5 text-left pixel-shadow-sm transition-all hover:bg-primary active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
        >
          <span className="min-w-0">
            <span className="block truncate font-mono text-[11px] uppercase tracking-wider text-secondary">
              {'>'} Interactive network map
            </span>
            <span className="mt-0.5 block text-pretty text-[13px] leading-snug text-card/90">
              Explore the full pipeline — trace flows between nodes, inspect specs, and see failure plays.
            </span>
          </span>
          <span
            aria-hidden="true"
            className="flex shrink-0 items-center gap-1 border-2 border-secondary px-1.5 py-1 font-mono text-[10px] uppercase tracking-widest text-secondary transition-transform group-hover:translate-x-0.5"
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
                  <header className="flex items-start justify-between gap-2 border-b-2 border-foreground bg-primary px-2.5 py-1.5">
                    <h3 className="min-w-0 break-words font-mono text-[10px] uppercase leading-snug tracking-widest text-primary-foreground">
                      {String(i + 1).padStart(2, '0')} · {stage.label}
                    </h3>
                    <span className="shrink-0 font-mono text-[8px] uppercase tracking-widest text-secondary">
                      {stage.owner}
                    </span>
                  </header>
                  {/*
                    Column count is driven by the panel's own width (container query),
                    not the viewport — the command center is a narrow side column, so
                    viewport breakpoints produced 3 cramped columns that overflowed.
                  */}
                  <div
                    className={cn(
                      '@container grid gap-2 p-2.5',
                      stage.nodes?.length > 1 ? 'grid-cols-1 @[380px]:grid-cols-2 @[640px]:grid-cols-3' : 'grid-cols-1',
                    )}
                  >
                    {stage.nodes?.map((node: any) => (
                      <div key={node.id} className="min-w-0 border-2 border-foreground bg-background p-2">
                        <div className="flex items-start justify-between gap-1.5">
                          <span className="min-w-0 flex-1 break-words font-mono text-[11px] uppercase leading-snug tracking-wider">
                            {node.name}
                          </span>
                          {node.share ? (
                            <span className="shrink-0 border-2 border-foreground bg-accent px-1 py-0.5 font-mono text-[9px] tracking-wider text-accent-foreground">
                              {node.share}
                            </span>
                          ) : null}
                        </div>
                        <ul className="mt-1.5 flex flex-col gap-0.5">
                          {node.meta?.map((m: string) => (
                            <li key={m} className="break-words text-sm leading-snug text-foreground/80">
                              {m}
                            </li>
                          ))}
                        </ul>
                        {node.risk ? (
                          <span
                            className={cn(
                              'mt-1.5 inline-block border-2 border-foreground px-1 py-0.5 font-mono text-[8px] uppercase tracking-widest',
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
            <h3 className="font-mono text-[11px] uppercase tracking-widest text-secondary-foreground">
              Council decision record
            </h3>
          </header>
          <dl className="flex flex-col gap-3 p-3">
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
                <dt className="font-mono text-[10px] uppercase tracking-widest text-accent">{label}</dt>
                <dd className="mt-1 text-pretty text-sm leading-relaxed">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        {/* ---- rollout ---- */}
        <section aria-label="Implementation rollout" className="mt-4 border-2 border-foreground bg-card pixel-shadow-sm">
          <header className="border-b-2 border-foreground bg-secondary px-2.5 py-1.5">
            <h3 className="font-mono text-[10px] uppercase tracking-widest text-secondary-foreground">
              Implementation rollout · {rolloutOwner}
            </h3>
          </header>
          <ol className="flex flex-col">
            {rollout.map((p: any, i: number) => (
              <li
                key={p.phase}
                className={cn(
                  'flex items-start gap-2.5 px-2.5 py-2',
                  i < rollout.length - 1 && 'border-b-2 border-dashed border-foreground/30',
                )}
              >
                <span className="shrink-0 border-2 border-foreground bg-primary px-1.5 py-0.5 font-mono text-[8px] uppercase tracking-widest text-primary-foreground">
                  {p.phase}
                </span>
                <span className="min-w-0 flex-1 text-xs leading-snug">{p.action}</span>
                <span
                  className={cn(
                    'shrink-0 border-2 border-foreground px-1 py-0.5 font-mono text-[8px] uppercase tracking-widest',
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

      {mapOpen ? <BlueprintMap onClose={() => setMapOpen(false)} architectureReport={architectureReport} projectId={projectId} /> : null}
    </div>
  )
}
