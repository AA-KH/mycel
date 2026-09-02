'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { formatElapsed, type AtlasLog } from '@/lib/mission-sim'

const LEVEL_STYLES: Record<string, { prefix: string; className: string }> = {
  info: { prefix: '>', className: 'text-foreground' },
  action: { prefix: '>>', className: 'text-accent' },
  success: { prefix: 'OK', className: 'text-[#3d7a4a]' },
  warn: { prefix: '!!', className: 'text-destructive' },
  error: { prefix: 'ERR', className: 'text-destructive font-bold' },
  armor: { prefix: 'AIQ', className: 'text-[#8a5a2b]' },
}

/* shared log body — rendered both inline in the tab and inside the fullscreen overlay */
function AtlasLogBody({
  logs,
  complete,
  expanded,
}: {
  logs: AtlasLog[]
  complete: boolean
  expanded: boolean
}) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [logs.length])

  const textSize = expanded ? 'text-xs md:text-sm' : 'text-[10px]'

  return (
    <div
      className={cn('pixel-scroll min-h-0 flex-1 overflow-y-auto bg-card', expanded ? 'p-4 md:p-6' : 'p-3')}
      role="log"
      aria-label="Atlas orchestrator log"
      aria-live="polite"
    >
      {logs.length === 0 ? (
        <p className={cn('font-mono uppercase tracking-widest text-muted-foreground', textSize)}>
          {'> Waiting for Atlas…'}
          <span className="blink">_</span>
        </p>
      ) : (
        <ol className={cn('flex flex-col', expanded ? 'gap-3' : 'gap-2')}>
          {logs.map((log) => {
            const style = LEVEL_STYLES[log.level] || LEVEL_STYLES.info
            return (
              <li
                key={log.id}
                className={cn('step-enter flex items-baseline gap-2 font-mono leading-relaxed', textSize, expanded && 'gap-3')}
              >
                <span className="shrink-0 text-muted-foreground">[{formatElapsed(log.at)}]</span>
                <span className={cn('shrink-0 font-bold', style.className)}>{style.prefix}</span>
                <span className={cn('text-pretty', style.className)}>{log.text}</span>
              </li>
            )
          })}
        </ol>
      )}
      {!complete && logs.length > 0 ? (
        <p className={cn('mt-2 font-mono text-accent', textSize)}>
          {'>'} <span className="blink">_</span>
        </p>
      ) : null}
      <div ref={bottomRef} />
    </div>
  )
}

function LiveIndicator({ complete }: { complete: boolean }) {
  return (
    <span className="flex items-center gap-1.5 font-mono text-[8px] uppercase tracking-widest text-secondary">
      <span className={cn('inline-block h-2 w-2 bg-secondary', !complete && 'blink')} />
      {complete ? 'Idle' : 'Live'}
    </span>
  )
}

export function AtlasLogTab({ logs, complete }: { logs: AtlasLog[]; complete: boolean }) {
  const [expanded, setExpanded] = useState(false)
  const expandBtnRef = useRef<HTMLButtonElement>(null)

  /* close the fullscreen feed with Escape and return focus to the trigger */
  useEffect(() => {
    if (!expanded) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setExpanded(false)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      expandBtnRef.current?.focus()
    }
  }, [expanded])

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between gap-2 border-b-2 border-foreground bg-primary px-3 py-2">
        <span className="truncate font-mono text-[9px] uppercase tracking-widest text-primary-foreground">
          Atlas · Orchestrator feed
        </span>
        <div className="flex shrink-0 items-center gap-3">
          <LiveIndicator complete={complete} />
          <button
            ref={expandBtnRef}
            type="button"
            onClick={() => setExpanded(true)}
            aria-haspopup="dialog"
            aria-expanded={expanded}
            aria-label="Expand orchestrator feed to full screen"
            title="Full screen"
            className="flex items-center gap-1.5 border-2 border-foreground bg-card px-2 py-1 font-mono text-[8px] uppercase tracking-widest text-foreground pixel-shadow-sm hover:bg-muted active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            <ExpandGlyph />
            <span className="hidden sm:inline">Expand</span>
          </button>
        </div>
      </div>

      <AtlasLogBody logs={logs} complete={complete} expanded={false} />

      {/* fullscreen overlay */}
      {expanded ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Atlas orchestrator feed, full screen"
          className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6"
        >
          <button
            type="button"
            aria-label="Close full screen feed"
            onClick={() => setExpanded(false)}
            className="absolute inset-0 bg-foreground/60"
          />
          <div className="relative flex h-full w-full flex-col border-4 border-foreground bg-card pixel-shadow">
            <header className="flex shrink-0 items-center justify-between gap-2 border-b-2 border-foreground bg-primary px-4 py-2.5">
              <div className="flex min-w-0 items-center gap-4">
                <h2 className="truncate font-mono text-[10px] uppercase tracking-widest text-primary-foreground md:text-xs">
                  Atlas · Orchestrator feed
                </h2>
                <LiveIndicator complete={complete} />
                <span className="hidden font-mono text-[8px] uppercase tracking-widest text-primary-foreground/60 md:inline">
                  {logs.length} {logs.length === 1 ? 'entry' : 'entries'}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setExpanded(false)}
                autoFocus
                className="flex items-center gap-1.5 border-2 border-foreground bg-card px-2.5 py-1 font-mono text-[9px] uppercase tracking-widest text-foreground pixel-shadow-sm hover:bg-muted active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
              >
                <CollapseGlyph />
                Close
                <span className="sr-only">(or press Escape)</span>
              </button>
            </header>
            <AtlasLogBody logs={logs} complete={complete} expanded />
          </div>
        </div>
      ) : null}
    </div>
  )
}

/* pixel-style corner glyphs, drawn with borders to match the retro UI */
function ExpandGlyph() {
  return (
    <span aria-hidden="true" className="relative inline-block h-2.5 w-2.5">
      <span className="absolute left-0 top-0 h-1.5 w-1.5 border-l-2 border-t-2 border-current" />
      <span className="absolute bottom-0 right-0 h-1.5 w-1.5 border-b-2 border-r-2 border-current" />
    </span>
  )
}

function CollapseGlyph() {
  return (
    <span aria-hidden="true" className="relative inline-block h-2.5 w-2.5">
      <span className="absolute left-0 top-0 h-1.5 w-1.5 border-b-2 border-r-2 border-current" />
      <span className="absolute bottom-0 right-0 h-1.5 w-1.5 border-l-2 border-t-2 border-current" />
    </span>
  )
}
