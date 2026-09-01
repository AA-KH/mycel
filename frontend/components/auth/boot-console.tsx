'use client'

import { useEffect, useRef, useState } from 'react'

const AGENTS = [
  { tag: 'RAVI', line: 'scanning 1,284 tier-1 supplier records' },
  { tag: 'DEV', line: 'pricing landed cost across 3 sourcing lanes' },
  { tag: 'AANYA', line: 'plant capacity model → 140k units / yr' },
  { tag: 'NISHA', line: 'bottleneck watch armed at 71% utilization' },
  { tag: 'TARA', line: 'safety stock solver → 30d central cover' },
  { tag: 'KABIR', line: 'priced 22 outbound lanes, 2 flagged' },
  { tag: 'MIRA', line: 'demand clustered into 12 regions' },
  { tag: 'COUNCIL', line: 'stress-testing 14 disruption scenarios' },
  { tag: 'MYCEL', line: 'network graph stable — awaiting operator' },
]

type Log = { id: number; tag: string; line: string; ok: boolean }

/**
 * Left rail of the auth screen: a live MYCEL boot log that keeps
 * streaming agent chatter while the operator signs in.
 */
export function BootConsole() {
  const [logs, setLogs] = useState<Log[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const idRef = useRef(0)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (reduce) {
      setLogs(
        AGENTS.map((a, i) => ({ id: i, tag: a.tag, line: a.line, ok: true })),
      )
      idRef.current = AGENTS.length
      return
    }

    const timer = setInterval(() => {
      const next = AGENTS[idRef.current % AGENTS.length]
      const id = idRef.current++
      setLogs((prev) => {
        const appended = [
          ...prev,
          { id, tag: next.tag, line: next.line, ok: id % 7 !== 6 },
        ]
        return appended.slice(-14)
      })
    }, 900)

    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs])

  return (
    <div className="flex min-h-0 flex-1 flex-col border-4 border-foreground bg-primary pixel-shadow">
      {/* title bar */}
      <div className="flex shrink-0 items-center justify-between border-b-4 border-foreground bg-foreground px-4 py-2.5">
        <p className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          MYCEL.NET // BOOT LOG
        </p>
        <span className="flex items-center gap-1.5 font-mono text-[8px] uppercase tracking-widest text-secondary">
          <span className="h-2 w-2 bg-secondary node-blink" aria-hidden="true" />
          Live
        </span>
      </div>

      {/* streaming log */}
      <div
        ref={scrollRef}
        role="log"
        aria-live="polite"
        aria-label="MYCEL network boot log"
        className="pixel-scroll min-h-0 flex-1 overflow-y-auto p-4 font-mono text-[10px] leading-relaxed lg:p-5 lg:text-[11px]"
      >
        {logs.map((log) => (
          <p key={log.id} className="step-enter flex gap-2 py-1">
            <span className="shrink-0 text-secondary">{'>'}</span>
            <span className="shrink-0 text-secondary">[{log.tag}]</span>
            <span className="text-primary-foreground/80">{log.line}</span>
            <span
              className={log.ok ? 'ml-auto shrink-0 text-teal-mist' : 'ml-auto shrink-0 text-accent'}
            >
              {log.ok ? 'OK' : '...'}
            </span>
          </p>
        ))}
        <p className="py-1 text-secondary">
          {'> _'}
          <span className="blink">|</span>
        </p>
      </div>

      {/* footer readout */}
      <dl className="grid shrink-0 grid-cols-3 border-t-4 border-foreground bg-card">
        <Stat label="Agents" value="09" />
        <Stat label="Nodes" value="12" className="border-x-2 border-foreground" />
        <Stat label="Scenarios" value="14" />
      </dl>
    </div>
  )
}

function Stat({
  label,
  value,
  className,
}: {
  label: string
  value: string
  className?: string
}) {
  return (
    <div className={`px-3 py-3 text-center ${className ?? ''}`}>
      <dt className="font-mono text-[8px] uppercase tracking-widest text-accent">{label}</dt>
      <dd className="mt-1 font-mono text-lg tracking-wider text-foreground">{value}</dd>
    </div>
  )
}
