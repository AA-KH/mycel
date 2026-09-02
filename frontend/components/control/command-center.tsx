'use client'

import { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'
import { ARMORIQ_URL } from '@/lib/agents'
import type { MissionState } from '@/lib/mission-sim'
import { AtlasLogTab } from './atlas-log'
import { HireCardsTab } from './hire-cards'
import { AgentRosterTab } from './agent-roster'
import { BlueprintTab } from './blueprint-tab'
import { ApprovalModal } from './approval-modal'

type TabId = 'atlas' | 'hires' | 'agents' | 'blueprint'

const TABS: { id: TabId; label: string }[] = [
  { id: 'atlas', label: 'Atlas' },
  { id: 'hires', label: 'Hiring' },
  { id: 'agents', label: 'Agents' },
  { id: 'blueprint', label: 'Blueprint' },
]

export function CommandCenter({ mission }: { mission: MissionState }) {
  const [tab, setTab] = useState<TabId>('atlas')

  /* when the mission completes, reveal the blueprint output once */
  const revealedRef = useRef(false)
  useEffect(() => {
    if (mission.complete && !revealedRef.current) {
      revealedRef.current = true
      setTab('blueprint')
    }
  }, [mission.complete])

  const hiredCount = mission.hires.length
  const workingCount = Object.values(mission.agents).filter((a) => a.phase === 'working').length
  const pendingApprovals = mission.pendingApprovals ?? []
  const topApproval = pendingApprovals[0] ?? null

  function dismissApproval(_approval_id: string) {
    // The WS approval_response event automatically removes it from state.
    // Nothing needed here — the modal already called the backend.
  }

  return (
    <>
    <section
      aria-label="Command center"
      className="flex h-full min-h-0 flex-col border-4 border-foreground bg-card pixel-shadow"
    >
      {/* header */}
      <header className="flex shrink-0 items-center justify-between gap-2 border-b-2 border-foreground bg-secondary px-3 py-2">
        <div className="min-w-0">
          <h2 className="truncate font-mono text-[10px] uppercase tracking-widest text-secondary-foreground">
            Command Center
          </h2>
          <p className="truncate font-mono text-[7px] uppercase tracking-widest text-secondary-foreground/70">
            Maya hires {'\u00b7'} Atlas runs the floor
          </p>
        </div>
        <a
          href={ARMORIQ_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="group flex shrink-0 items-center gap-1.5 border-2 border-foreground bg-[#e07a4c] px-2.5 py-1.5 font-mono text-[8px] uppercase tracking-widest text-accent-foreground pixel-shadow-sm transition-colors hover:bg-primary hover:text-primary-foreground active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
        >
          {/* tiny shield glyph */}
          <span
            aria-hidden="true"
            className="inline-block h-2.5 w-2.5 border-2 border-current"
            style={{ clipPath: 'polygon(0 0, 100% 0, 100% 65%, 50% 100%, 0 65%)' }}
          />
          Armor IQ
          <span className="sr-only">(opens the ArmorIQ security log in a new tab)</span>
        </a>
      </header>

      {/* tab bar */}
      <div role="tablist" aria-label="Command center tabs" className="flex shrink-0 border-b-2 border-foreground bg-muted">
        {TABS.map((t) => {
          const active = tab === t.id
          const badge = t.id === 'hires' ? hiredCount : t.id === 'agents' ? workingCount : null
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={active}
              aria-controls={`panel-${t.id}`}
              id={`tab-${t.id}`}
              onClick={() => setTab(t.id)}
              className={cn(
                'flex flex-1 items-center justify-center gap-1.5 border-r-2 border-foreground px-1.5 py-2.5 font-mono text-[8px] uppercase tracking-widest transition-colors last:border-r-0',
                active ? 'bg-card text-foreground' : 'bg-muted text-muted-foreground hover:bg-card/60',
              )}
            >
              {t.label}
              {t.id === 'blueprint' ? (
                <span
                  aria-hidden="true"
                  className={cn(
                    'inline-block h-2 w-2 border border-foreground',
                    mission.complete ? 'bg-[#b9d8ac]' : 'bg-muted-foreground/40 blink',
                  )}
                />
              ) : null}
              {badge !== null && badge > 0 ? (
                <span
                  className={cn(
                    'inline-flex h-4 min-w-4 items-center justify-center border-2 border-foreground px-0.5 font-mono text-[7px]',
                    active ? 'bg-accent text-accent-foreground' : 'bg-secondary text-secondary-foreground',
                  )}
                >
                  {badge}
                </span>
              ) : null}
            </button>
          )
        })}
      </div>

      {/* tab panels */}
      <div className="min-h-0 flex-1">
        <div id="panel-atlas" role="tabpanel" aria-labelledby="tab-atlas" hidden={tab !== 'atlas'} className="h-full">
          <AtlasLogTab logs={mission.logs} complete={mission.complete} />
        </div>
        <div id="panel-hires" role="tabpanel" aria-labelledby="tab-hires" hidden={tab !== 'hires'} className="h-full">
          <HireCardsTab hires={mission.hires} />
        </div>
        <div id="panel-agents" role="tabpanel" aria-labelledby="tab-agents" hidden={tab !== 'agents'} className="h-full">
          <AgentRosterTab agents={mission.agents} clock={mission.clock} />
        </div>
        <div
          id="panel-blueprint"
          role="tabpanel"
          aria-labelledby="tab-blueprint"
          hidden={tab !== 'blueprint'}
          className="h-full"
        >
          <BlueprintTab complete={mission.complete} architectureReport={mission.architecture_report} />
        </div>
      </div>
    </section>

    {/* ArmorIQ approval modal — renders above everything when gating is active */}
    {topApproval ? (
      <ApprovalModal
        request={topApproval}
        onResolved={dismissApproval}
      />
    ) : null}
    </>
  )
}
