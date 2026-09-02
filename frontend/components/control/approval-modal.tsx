'use client'

import { useCallback, useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'
import { API_URL } from '@/lib/mission-sim'
import { getToken } from '@/lib/auth'

export type ApprovalRequest = {
  approval_id: string
  agent: string
  tool: string
  intent: string
  /** GREEN = autonomous (never shown), AMBER = needs approval, RED = blocked (never shown) */
  risk: 'GREEN' | 'AMBER' | 'RED'
  reason?: string
  args_preview?: string
}

const CLASS_STYLE: Record<string, string> = {
  GREEN: 'bg-[#b9d8ac] text-foreground',
  AMBER: 'bg-secondary text-secondary-foreground',
  RED:   'bg-[#e07a4c] text-accent-foreground',
}

const CLASS_LABEL: Record<string, string> = {
  GREEN: 'Autonomous',
  AMBER: 'Approval Required',
  RED:   'Blocked',
}

async function submitDecision(approval_id: string, approved: boolean) {
  const token = getToken()
  await fetch(`${API_URL}/api/v1/realtime/approvals/${approval_id}/respond`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ approved }),
  })
}

export function ApprovalModal({
  request,
  onResolved,
}: {
  request: ApprovalRequest
  onResolved: (approval_id: string) => void
}) {
  const denyRef = useRef<HTMLButtonElement>(null)

  // Focus deny button by default (safe default)
  useEffect(() => { denyRef.current?.focus() }, [])

  // ESC = deny
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') handleDeny() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const handleApprove = useCallback(async () => {
    await submitDecision(request.approval_id, true)
    onResolved(request.approval_id)
  }, [request.approval_id, onResolved])

  const handleDeny = useCallback(async () => {
    await submitDecision(request.approval_id, false)
    onResolved(request.approval_id)
  }, [request.approval_id, onResolved])

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="armor-title"
      className="fixed inset-0 z-[60] flex items-center justify-center bg-foreground/80 p-4"
    >
      <div className="w-full max-w-lg border-4 border-foreground bg-card pixel-shadow">

        {/* ── Header ── */}
        <header className="border-b-4 border-foreground bg-[#e07a4c] px-4 py-2.5">
          <div className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="inline-block h-4 w-4 shrink-0 border-2 border-foreground bg-card"
              style={{ clipPath: 'polygon(0 0, 100% 0, 100% 65%, 50% 100%, 0 65%)' }}
            />
            <h2
              id="armor-title"
              className="font-mono text-[11px] uppercase tracking-widest text-accent-foreground"
            >
              ArmorIQ &middot; Human Approval Required
            </h2>
          </div>
        </header>

        {/* ── Body ── */}
        <div className="flex flex-col gap-3 p-4">

          {/* Agent + Tool + Class badge */}
          <div className="flex flex-wrap items-center gap-2 border-2 border-foreground bg-muted/60 px-3 py-2">
            <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">Agent</span>
            <span className="border-2 border-foreground bg-card px-1.5 font-mono text-[9px] uppercase tracking-wider">
              {request.agent}
            </span>
            <span className="font-mono text-[8px] uppercase tracking-widest text-muted-foreground">wants to call</span>
            <span className="border-2 border-foreground bg-accent px-1.5 font-mono text-[9px] uppercase tracking-wider text-accent-foreground">
              {request.tool}()
            </span>
            <span
              className={cn(
                'ml-auto border-2 border-foreground px-1.5 font-mono text-[8px] uppercase tracking-widest',
                CLASS_STYLE[request.risk] ?? CLASS_STYLE.AMBER,
              )}
            >
              {CLASS_LABEL[request.risk] ?? request.risk}
            </span>
          </div>

          {/* Why approval is needed */}
          <div className="border-2 border-foreground bg-foreground p-3">
            <p className="mb-1 font-mono text-[7px] uppercase tracking-widest text-secondary">
              &gt; Why approval is needed
            </p>
            <p className="text-pretty font-mono text-[11px] leading-relaxed text-card">
              {request.intent}
            </p>
          </div>

          {/* ArmorIQ policy reason */}
          {request.reason ? (
            <div className="border-l-4 border-[#e07a4c] bg-muted/40 pl-3 py-2 pr-2">
              <p className="font-mono text-[7px] uppercase tracking-widest text-muted-foreground mb-0.5">
                ArmorIQ Policy
              </p>
              <p className="font-mono text-[10px] leading-snug text-foreground">
                {request.reason}
              </p>
            </div>
          ) : null}

          {/* Args preview */}
          {request.args_preview ? (
            <details className="border-2 border-foreground">
              <summary className="cursor-pointer px-2 py-1 font-mono text-[8px] uppercase tracking-widest text-muted-foreground hover:bg-muted/40">
                View parameters
              </summary>
              <pre className="overflow-x-auto bg-muted/20 p-2 font-mono text-[9px] leading-snug text-foreground">
                {request.args_preview}
              </pre>
            </details>
          ) : null}

          <p className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
            No response in 120 s &rarr; auto-denied &middot; Esc = Deny
          </p>
        </div>

        {/* ── Footer ── */}
        <footer className="grid grid-cols-2 border-t-4 border-foreground">
          <button
            ref={denyRef}
            type="button"
            onClick={handleDeny}
            id="armoriq-deny-btn"
            className="border-r-2 border-foreground bg-card px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground transition-colors hover:bg-[#e07a4c] hover:text-accent-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            Deny
          </button>
          <button
            type="button"
            onClick={handleApprove}
            id="armoriq-approve-btn"
            className="border-l-2 border-foreground bg-card px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground transition-colors hover:bg-[#b9d8ac] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
          >
            Approve &rarr; ArmorIQ
          </button>
        </footer>
      </div>
    </div>
  )
}
