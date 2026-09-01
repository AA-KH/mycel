'use client'

import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { formatElapsed, type AtlasLog } from '@/lib/mission-sim'

const LEVEL_STYLES: Record<AtlasLog['level'], { prefix: string; className: string }> = {
  info: { prefix: '>', className: 'text-foreground' },
  action: { prefix: '>>', className: 'text-accent' },
  success: { prefix: 'OK', className: 'text-[#3d7a4a]' },
  warn: { prefix: '!!', className: 'text-destructive' },
  armor: { prefix: 'AIQ', className: 'text-[#8a5a2b]' },
}

export function AtlasLogTab({ logs, complete }: { logs: AtlasLog[]; complete: boolean }) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [logs.length])

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Atlas · Orchestrator feed
        </span>
        <span className="flex items-center gap-1.5 font-mono text-[8px] uppercase tracking-widest text-secondary">
          <span className={cn('inline-block h-2 w-2 bg-secondary', !complete && 'blink')} />
          {complete ? 'Idle' : 'Live'}
        </span>
      </div>

      <div
        className="pixel-scroll min-h-0 flex-1 overflow-y-auto bg-card p-3"
        role="log"
        aria-label="Atlas orchestrator log"
        aria-live="polite"
      >
        {logs.length === 0 ? (
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            {'> Waiting for Atlas…'}
            <span className="blink">_</span>
          </p>
        ) : (
          <ol className="flex flex-col gap-2">
            {logs.map((log) => {
              const style = LEVEL_STYLES[log.level]
              return (
                <li key={log.id} className="step-enter flex items-baseline gap-2 font-mono text-[10px] leading-relaxed">
                  <span className="shrink-0 text-muted-foreground">[{formatElapsed(log.at)}]</span>
                  <span className={cn('shrink-0 font-bold', style.className)}>{style.prefix}</span>
                  <span className={cn('text-pretty', style.className)}>{log.text}</span>
                </li>
              )
            })}
          </ol>
        )}
        {!complete && logs.length > 0 ? (
          <p className="mt-2 font-mono text-[10px] text-accent">
            {'>'} <span className="blink">_</span>
          </p>
        ) : null}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
