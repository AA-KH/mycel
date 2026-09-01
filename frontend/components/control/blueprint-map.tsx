'use client'

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import {
  BLUEPRINT_STAGES,
  COUNCIL_DECISION,
  downstreamIds,
  findNode,
  upstreamIds,
  type BlueprintNode,
} from '@/lib/blueprint'

const RISK_STYLES: Record<NonNullable<BlueprintNode['risk']>, string> = {
  low: 'bg-[#b9d8ac] text-foreground',
  medium: 'bg-secondary text-secondary-foreground',
  high: 'bg-[#e07a4c] text-accent-foreground',
}

type Edge = { key: string; from: string; to: string; label?: string; d: string; mx: number; my: number }

export function BlueprintMap({ onClose }: { onClose: () => void }) {
  const [selectedId, setSelectedId] = useState<string>('sup-a')
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [edges, setEdges] = useState<Edge[]>([])
  const [canvas, setCanvas] = useState({ w: 0, h: 0 })

  const canvasRef = useRef<HTMLDivElement>(null)
  const nodeRefs = useRef(new Map<string, HTMLElement | null>())
  const closeRef = useRef<HTMLButtonElement>(null)

  const selected = findNode(selectedId)
  const activeId = hoverId ?? selectedId

  /** Node ids highlighted alongside the active node. */
  const related = useMemo(() => {
    const node = findNode(activeId)
    if (!node) return new Set<string>()
    return new Set([...upstreamIds(node), ...downstreamIds(node)])
  }, [activeId])

  /* ---------- measure node positions and build SVG edge paths ---------- */
  const measure = useCallback(() => {
    const canvasEl = canvasRef.current
    if (!canvasEl) return
    const box = canvasEl.getBoundingClientRect()
    const next: Edge[] = []

    for (const stage of BLUEPRINT_STAGES) {
      for (const node of stage.nodes) {
        const fromEl = nodeRefs.current.get(node.id)
        if (!fromEl) continue
        const a = fromEl.getBoundingClientRect()
        for (const toId of downstreamIds(node)) {
          const toEl = nodeRefs.current.get(toId)
          if (!toEl) continue
          const b = toEl.getBoundingClientRect()
          const x1 = a.right - box.left
          const y1 = a.top + a.height / 2 - box.top
          const x2 = b.left - box.left
          const y2 = b.top + b.height / 2 - box.top
          const mx = x1 + (x2 - x1) / 2
          // orthogonal stepped path — matches the pixel aesthetic
          const d = `M ${x1} ${y1} H ${mx} V ${y2} H ${x2}`
          next.push({ key: `${node.id}->${toId}`, from: node.id, to: toId, label: node.flowLabel, d, mx, my: y1 })
        }
      }
    }

    setEdges(next)
    setCanvas({ w: canvasEl.scrollWidth, h: canvasEl.scrollHeight })
  }, [])

  useLayoutEffect(() => {
    measure()
    const ro = new ResizeObserver(() => measure())
    if (canvasRef.current) ro.observe(canvasRef.current)
    for (const el of nodeRefs.current.values()) if (el) ro.observe(el)
    window.addEventListener('resize', measure)
    return () => {
      ro.disconnect()
      window.removeEventListener('resize', measure)
    }
  }, [measure])

  /* ---------- keyboard + focus ---------- */
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

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="map-title"
      onClick={onBackdrop}
      className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/70 p-2 sm:p-5"
    >
      <div className="flex h-full w-full max-w-[1400px] flex-col border-4 border-foreground bg-card pixel-shadow">
        {/* ---------- header ---------- */}
        <header className="flex shrink-0 items-center justify-between gap-2 border-b-4 border-foreground bg-primary px-3 py-2 sm:px-4">
          <div className="min-w-0 flex-1">
            <h2
              id="map-title"
              className="truncate font-mono text-sm uppercase tracking-widest text-primary-foreground sm:text-base"
            >
              Supply network map
            </h2>
            <p className="mt-0.5 truncate font-mono text-[8px] uppercase tracking-widest text-secondary">
              Rohan {'\u00b7'} Master architecture {'\u00b7'} click any node to inspect
            </p>
          </div>
          <div className="hidden shrink-0 items-center gap-1.5 md:flex">
            {(['low', 'medium', 'high'] as const).map((r) => (
              <span
                key={r}
                className={cn(
                  'border-2 border-foreground px-1.5 py-0.5 font-mono text-[7px] uppercase tracking-widest',
                  RISK_STYLES[r],
                )}
              >
                {r} risk
              </span>
            ))}
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close network map"
            className="flex h-8 w-8 shrink-0 items-center justify-center border-2 border-foreground bg-card font-mono text-sm text-foreground pixel-shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            {'\u00d7'}
          </button>
        </header>

        {/* ---------- body: canvas + inspector ---------- */}
        <div className="grid min-h-0 flex-1 grid-cols-1 max-lg:grid-rows-[minmax(0,3fr)_minmax(0,2fr)] lg:grid-cols-[minmax(0,1fr)_340px]">
          {/* ===== pipeline canvas ===== */}
          <div className="pixel-scroll min-h-0 overflow-auto bg-muted/60 diag-texture">
            <div ref={canvasRef} className="relative w-max min-w-full p-4">
              {/* edge layer */}
              <svg
                aria-hidden="true"
                width={canvas.w}
                height={canvas.h}
                viewBox={`0 0 ${canvas.w} ${canvas.h}`}
                className="pointer-events-none absolute left-0 top-0"
              >
                {edges.map((e) => {
                  const isActive = e.from === activeId || e.to === activeId
                  return (
                    <g key={e.key}>
                      <path
                        d={e.d}
                        fill="none"
                        stroke="var(--color-foreground)"
                        strokeWidth={isActive ? 4 : 2}
                        strokeOpacity={isActive ? 1 : 0.28}
                      />
                      {isActive ? (
                        <path
                          d={e.d}
                          fill="none"
                          stroke="var(--color-accent)"
                          strokeWidth={2}
                          strokeDasharray="6 8"
                          className="flow-dash"
                        />
                      ) : null}
                    </g>
                  )
                })}
              </svg>

              {/* node columns */}
              <div className="relative flex items-stretch gap-0">
                {BLUEPRINT_STAGES.map((stage, si) => (
                  <div key={stage.id} className="flex items-stretch">
                    <div className="flex w-[212px] shrink-0 flex-col gap-3 sm:w-[236px]">
                      <div className="border-2 border-foreground bg-card px-2 py-1.5 pixel-shadow-sm">
                        <p className="font-mono text-[9px] uppercase tracking-widest text-foreground">
                          {String(si + 1).padStart(2, '0')} {'\u00b7'} {stage.label}
                        </p>
                        <p className="mt-0.5 font-mono text-[7px] uppercase tracking-widest text-accent">
                          {stage.owner}
                        </p>
                        {stage.question ? (
                          <p className="mt-1 text-pretty text-[10px] leading-snug text-muted-foreground">
                            {stage.question}
                          </p>
                        ) : null}
                      </div>

                      <div className="flex flex-1 flex-col justify-center gap-4">
                        {stage.nodes.map((node) => {
                          const isSelected = node.id === selectedId
                          const isRelated = related.has(node.id)
                          return (
                            <button
                              key={node.id}
                              ref={(el) => {
                                nodeRefs.current.set(node.id, el)
                              }}
                              type="button"
                              aria-pressed={isSelected}
                              aria-label={`Inspect ${node.name}`}
                              onClick={() => setSelectedId(node.id)}
                              onMouseEnter={() => setHoverId(node.id)}
                              onMouseLeave={() => setHoverId(null)}
                              onFocus={() => setHoverId(node.id)}
                              onBlur={() => setHoverId(null)}
                              className={cn(
                                'relative block border-2 border-foreground bg-card p-2 text-left transition-all',
                                isSelected
                                  ? 'bg-card pixel-shadow ring-4 ring-accent'
                                  : isRelated
                                    ? 'pixel-shadow-sm'
                                    : 'pixel-shadow-sm opacity-80 hover:opacity-100',
                              )}
                            >
                              <div className="flex items-start justify-between gap-1.5">
                                <span className="font-mono text-[10px] uppercase leading-tight tracking-wider">
                                  {node.name}
                                </span>
                                {node.share ? (
                                  <span className="shrink-0 border-2 border-foreground bg-accent px-1 font-mono text-[8px] tracking-wider text-accent-foreground">
                                    {node.share}
                                  </span>
                                ) : null}
                              </div>
                              {node.location ? (
                                <p className="mt-1 font-mono text-[8px] uppercase tracking-widest text-muted-foreground">
                                  {node.location}
                                </p>
                              ) : null}
                              <p className="mt-1.5 text-pretty text-[10px] leading-snug text-foreground/80">
                                {node.meta[0]}
                              </p>
                              {node.risk ? (
                                <span
                                  className={cn(
                                    'mt-1.5 inline-block border-2 border-foreground px-1 font-mono text-[7px] uppercase tracking-widest',
                                    RISK_STYLES[node.risk],
                                  )}
                                >
                                  {node.risk}
                                </span>
                              ) : null}
                            </button>
                          )
                        })}
                      </div>
                    </div>

                    {/* gutter the edges are drawn through */}
                    {si < BLUEPRINT_STAGES.length - 1 ? <div className="w-16 shrink-0 sm:w-20" /> : null}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* ===== inspector ===== */}
          <aside
            aria-label="Node inspector"
            className="pixel-scroll min-h-0 overflow-y-auto border-foreground bg-card max-lg:border-t-4 lg:border-l-4"
          >
            {selected ? (
              <div className="flex flex-col">
                <div className="sticky top-0 z-10 border-b-2 border-foreground bg-secondary px-3 py-2">
                  <p className="font-mono text-[7px] uppercase tracking-widest text-secondary-foreground/70">
                    Node inspector
                  </p>
                  <h3 className="font-mono text-sm uppercase tracking-wider text-secondary-foreground">
                    {selected.name}
                  </h3>
                  <p className="mt-0.5 font-mono text-[8px] uppercase tracking-widest text-secondary-foreground/80">
                    {findStageLabel(selected.stage)}
                    {selected.location ? ` \u00b7 ${selected.location}` : ''}
                  </p>
                </div>

                <div className="flex flex-col gap-4 p-3">
                  {selected.function ? (
                    <p className="text-pretty border-2 border-foreground bg-muted/70 p-2.5 text-[12px] leading-relaxed">
                      {selected.function}
                    </p>
                  ) : null}

                  {selected.detail ? (
                    <section>
                      <InspectorLabel>Specification</InspectorLabel>
                      <dl className="flex flex-col divide-y-2 divide-dashed divide-foreground/25 border-2 border-foreground">
                        {selected.detail.map((d) => (
                          <div key={d.label} className="px-2 py-1.5">
                            <dt className="font-mono text-[7px] uppercase tracking-widest text-accent">{d.label}</dt>
                            <dd className="mt-0.5 text-pretty text-[11px] leading-snug">{d.value}</dd>
                          </div>
                        ))}
                      </dl>
                    </section>
                  ) : null}

                  <section>
                    <InspectorLabel>Connections</InspectorLabel>
                    <div className="flex flex-col gap-2">
                      <ConnectionRow
                        heading="Upstream"
                        ids={upstreamIds(selected)}
                        onSelect={setSelectedId}
                        onHover={setHoverId}
                      />
                      <ConnectionRow
                        heading="Downstream"
                        ids={downstreamIds(selected)}
                        onSelect={setSelectedId}
                        onHover={setHoverId}
                      />
                    </div>
                  </section>

                  {selected.fallback ? (
                    <section>
                      <InspectorLabel>If this node fails</InspectorLabel>
                      <div className="border-2 border-foreground bg-foreground p-2.5 pixel-shadow-sm">
                        <p className="mb-1 font-mono text-[8px] uppercase tracking-widest text-secondary">
                          {'>'} Arjun {'\u00b7'} continuity play
                        </p>
                        <p className="text-pretty font-mono text-[11px] leading-relaxed text-card">
                          {selected.fallback}
                        </p>
                      </div>
                    </section>
                  ) : null}

                  <section>
                    <InspectorLabel>Council mandate</InspectorLabel>
                    <p className="text-pretty border-2 border-foreground bg-muted/70 p-2.5 text-[11px] leading-relaxed">
                      {COUNCIL_DECISION.allocation}
                    </p>
                  </section>
                </div>
              </div>
            ) : null}
          </aside>
        </div>

        {/* ---------- footer ---------- */}
        <footer className="flex shrink-0 items-center justify-between gap-2 border-t-2 border-foreground bg-muted px-3 py-2">
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">
            {BLUEPRINT_STAGES.length} layers {'\u00b7'} {edges.length} flows {'\u00b7'} scroll to pan
          </span>
          <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">Esc to close</span>
        </footer>
      </div>
    </div>
  )
}

function InspectorLabel({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="mb-1.5 flex items-center gap-1.5 font-mono text-[9px] uppercase tracking-widest text-foreground">
      <span aria-hidden="true" className="inline-block h-2 w-2 border-2 border-foreground bg-accent" />
      {children}
    </h4>
  )
}

function ConnectionRow({
  heading,
  ids,
  onSelect,
  onHover,
}: {
  heading: string
  ids: string[]
  onSelect: (id: string) => void
  onHover: (id: string | null) => void
}) {
  return (
    <div>
      <p className="mb-1 font-mono text-[7px] uppercase tracking-widest text-muted-foreground">{heading}</p>
      {ids.length === 0 ? (
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">{'\u2014'} network edge</p>
      ) : (
        <ul className="flex flex-wrap gap-1.5">
          {ids.map((id) => {
            const n = findNode(id)
            if (!n) return null
            return (
              <li key={id}>
                <button
                  type="button"
                  onClick={() => onSelect(id)}
                  onMouseEnter={() => onHover(id)}
                  onMouseLeave={() => onHover(null)}
                  className="border-2 border-foreground bg-card px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider pixel-shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground"
                >
                  {n.name}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

function findStageLabel(stageId: string): string {
  return BLUEPRINT_STAGES.find((s) => s.id === stageId)?.label ?? stageId
}
