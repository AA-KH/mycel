'use client'

import { useEffect, useRef, useState } from 'react'
import type { Team } from './agents'
import { getToken } from './auth'
import type { ApprovalRequest } from '@/components/control/approval-modal'

/* ------------------------------------------------------------------ */
/* Types — shaped so a real backend event stream (SSE / WebSocket)     */
/* can replace the local simulation without touching the UI.           */
/* ------------------------------------------------------------------ */

export type LogLevel = 'info' | 'action' | 'success' | 'warn' | 'armor'

export type AtlasLog = {
  id: number
  at: number // ms since mission start
  level: LogLevel
  text: string
}

export type HireEvent = {
  id: number
  at: number
  agent: string
  team: Team
  role: string
  badge: string
  clearance: 'GREEN' | 'AMBER'
  mandate: string
}

export type AgentPhase = 'standby' | 'hired' | 'working' | 'done'

export type AgentState = {
  name: string
  phase: AgentPhase
  task: string
  startedAt: number | null // ms since mission start
  finishedAt: number | null
}

export type MissionState = {
  /** ms elapsed since mission start */
  clock: number
  logs: AtlasLog[]
  hires: HireEvent[]
  agents: Record<string, AgentState>
  complete: boolean
  architecture_report?: any
  pendingApprovals: ApprovalRequest[]
}

/* ------------------------------------------------------------------ */
/* Scripted timeline                                                    */
/* ------------------------------------------------------------------ */

type TimelineEvent =
  | { at: number; kind: 'log'; level: LogLevel; text: string }
  | { at: number; kind: 'hire'; agent: string; team: Team; role: string; clearance: 'GREEN' | 'AMBER'; mandate: string }
  | { at: number; kind: 'start'; agent: string; task: string }
  | { at: number; kind: 'finish'; agent: string }
  | { at: number; kind: 'complete' }

const s = (n: number) => n * 1000

const TIMELINE: TimelineEvent[] = [
  { at: s(0.3), kind: 'log', level: 'info', text: 'MAYA online. Chief Resource Allocator receiving mission payload…' },
  { at: s(1.0), kind: 'log', level: 'info', text: 'Maya parsing intake: business type, supply reach, priorities, constraints, uploaded files.' },
  { at: s(1.8), kind: 'log', level: 'action', text: 'Maya → query_available_agents(): 21 specialists in registry, matching against mission requirements.' },
  { at: s(2.6), kind: 'log', level: 'action', text: 'Maya assembling task force. Only load-bearing specialists will be hired — the rest stay on standby.' },
  { at: s(3.2), kind: 'log', level: 'armor', text: 'ArmorIQ handshake OK — delegated authority verified. GREEN actions autonomous, AMBER gated, RED blocked.' },
  { at: s(3.7), kind: 'log', level: 'info', text: 'ATLAS online. Orchestrator standing by for Maya\u2019s task force.' },

  /* --- Intelligence wave --- */
  { at: s(4.2), kind: 'log', level: 'action', text: 'Maya → hire_team(): Intelligence cabin — 4 specialists. Reasoning: demand, supplier, benchmark & risk intel are all load-bearing.' },
  { at: s(4.8), kind: 'hire', agent: 'Mira', team: 'Intelligence', role: 'Market & demand intelligence', clearance: 'GREEN', mandate: 'Map demand signals across target customer regions.' },
  { at: s(5.6), kind: 'hire', agent: 'Ravi', team: 'Intelligence', role: 'Supplier intelligence', clearance: 'AMBER', mandate: 'Profile candidate suppliers; quotation requests require approval.' },
  { at: s(6.4), kind: 'hire', agent: 'Anika', team: 'Intelligence', role: 'Industry benchmarking', clearance: 'GREEN', mandate: 'Benchmark cost & lead-time against industry peers.' },
  { at: s(7.2), kind: 'hire', agent: 'Noor', team: 'Intelligence', role: 'Geopolitical risk intelligence', clearance: 'GREEN', mandate: 'Score route & region exposure to external shocks.' },
  { at: s(7.8), kind: 'start', agent: 'Mira', task: 'Scanning demand signals in customer regions' },
  { at: s(8.2), kind: 'start', agent: 'Ravi', task: 'Building supplier long-list from public data' },
  { at: s(8.6), kind: 'start', agent: 'Anika', task: 'Pulling industry cost & lead-time benchmarks' },
  { at: s(9.0), kind: 'start', agent: 'Noor', task: 'Scoring geopolitical exposure per lane' },
  { at: s(9.6), kind: 'log', level: 'info', text: 'Intelligence cabin active. 4 agents running GREEN-class research.' },
  { at: s(10.2), kind: 'log', level: 'action', text: 'Atlas decomposed the mission into 5 workstreams: Intelligence, Network, Resilience, Council, Architecture.' },

  /* --- Network wave --- */
  { at: s(11.5), kind: 'log', level: 'action', text: 'Maya → hire_team(): Network cabin — topology & landed-cost modeling required for multi-region sourcing.' },
  { at: s(12.1), kind: 'hire', agent: 'Aanya', team: 'Network', role: 'Supply-chain network design', clearance: 'GREEN', mandate: 'Draft candidate network topologies.' },
  { at: s(12.9), kind: 'hire', agent: 'Dev', team: 'Network', role: 'Procurement & landed cost', clearance: 'AMBER', mandate: 'Model total landed cost; supplier contact gated by ArmorIQ.' },
  { at: s(13.7), kind: 'hire', agent: 'Kabir', team: 'Network', role: 'Logistics & fulfillment', clearance: 'GREEN', mandate: 'Price and time every candidate route.' },
  { at: s(14.5), kind: 'hire', agent: 'Tara', team: 'Network', role: 'Inventory & capacity planning', clearance: 'GREEN', mandate: 'Size buffers and capacity per node.' },
  { at: s(15.1), kind: 'start', agent: 'Aanya', task: 'Drafting 3 candidate network topologies' },
  { at: s(15.5), kind: 'start', agent: 'Dev', task: 'Computing landed cost per supplier lane' },
  { at: s(15.9), kind: 'start', agent: 'Kabir', task: 'Routing freight: sea / air / rail options' },
  { at: s(16.3), kind: 'start', agent: 'Tara', task: 'Simulating inventory buffers per node' },
  { at: s(17.0), kind: 'log', level: 'armor', text: 'AMBER request from Dev: contact 2 shortlisted suppliers for quotations → awaiting user approval.' },

  /* --- Intelligence completes --- */
  { at: s(19.0), kind: 'finish', agent: 'Mira' },
  { at: s(19.4), kind: 'log', level: 'success', text: 'Mira delivered demand map — 12 demand clusters identified.' },
  { at: s(20.4), kind: 'finish', agent: 'Anika' },
  { at: s(21.2), kind: 'finish', agent: 'Noor' },
  { at: s(21.6), kind: 'log', level: 'success', text: 'Noor flagged 2 high-risk lanes: strait congestion + tariff exposure.' },
  { at: s(22.6), kind: 'finish', agent: 'Ravi' },
  { at: s(23.0), kind: 'log', level: 'success', text: 'Ravi shortlisted 8 suppliers across 3 regions.' },

  /* --- Resilience wave --- */
  { at: s(24.5), kind: 'log', level: 'action', text: 'Maya → hire_team(): Resilience cabin — Noor flagged 2 high-risk lanes, so stress-testing is now load-bearing.' },
  { at: s(25.1), kind: 'hire', agent: 'Zoya', team: 'Resilience', role: 'Failure / risk mapping', clearance: 'GREEN', mandate: 'Map single points of failure in draft network.' },
  { at: s(25.9), kind: 'hire', agent: 'Ishaan', team: 'Resilience', role: 'Disruption scenario generation', clearance: 'GREEN', mandate: 'Generate disruption scenarios: port closure, tariff spike, supplier default.' },
  { at: s(26.7), kind: 'hire', agent: 'Leena', team: 'Resilience', role: 'Stress testing', clearance: 'GREEN', mandate: 'Run every scenario against every topology.' },
  { at: s(27.5), kind: 'hire', agent: 'Arjun', team: 'Resilience', role: 'Continuity & recovery planning', clearance: 'GREEN', mandate: 'Write reroute playbooks for surviving topologies.' },
  { at: s(28.1), kind: 'start', agent: 'Zoya', task: 'Mapping single points of failure' },
  { at: s(28.5), kind: 'start', agent: 'Ishaan', task: 'Generating 14 disruption scenarios' },
  { at: s(29.0), kind: 'start', agent: 'Leena', task: 'Stress-testing topologies vs scenarios' },
  { at: s(29.4), kind: 'start', agent: 'Arjun', task: 'Drafting reroute & recovery playbooks' },

  /* --- Network completes --- */
  { at: s(31.0), kind: 'finish', agent: 'Aanya' },
  { at: s(31.8), kind: 'finish', agent: 'Kabir' },
  { at: s(32.2), kind: 'log', level: 'success', text: 'Kabir priced 22 routes. Cheapest lane 18% under benchmark.' },
  { at: s(33.2), kind: 'finish', agent: 'Tara' },
  { at: s(34.2), kind: 'finish', agent: 'Dev' },
  { at: s(34.6), kind: 'log', level: 'success', text: 'Dev completed landed-cost model across all supplier lanes.' },

  /* --- Council wave --- */
  { at: s(35.7), kind: 'log', level: 'action', text: 'Atlas convening the Strategy Council — cost and resilience evidence now conflict.' },
  { at: s(36.0), kind: 'log', level: 'action', text: 'Maya → hire_team(): 5 strategists staffed to the council bench.' },
  { at: s(36.6), kind: 'hire', agent: 'Helena', team: 'Council', role: 'Cost strategist', clearance: 'GREEN', mandate: 'Argue the lowest-cost network.' },
  { at: s(37.2), kind: 'hire', agent: 'Vikram', team: 'Council', role: 'Resilience strategist', clearance: 'GREEN', mandate: 'Argue the most shock-proof network.' },
  { at: s(37.8), kind: 'hire', agent: 'Nisha', team: 'Council', role: 'Operations strategist', clearance: 'GREEN', mandate: 'Argue operational simplicity.' },
  { at: s(38.4), kind: 'hire', agent: 'Omar', team: 'Council', role: 'Risk / compliance strategist', clearance: 'GREEN', mandate: 'Veto anything non-compliant.' },
  { at: s(39.0), kind: 'hire', agent: 'Sofia', team: 'Council', role: 'Council chair', clearance: 'GREEN', mandate: 'Force a decision. Break ties.' },
  { at: s(39.6), kind: 'start', agent: 'Helena', task: 'Building the cost case' },
  { at: s(39.9), kind: 'start', agent: 'Vikram', task: 'Building the resilience case' },
  { at: s(40.2), kind: 'start', agent: 'Nisha', task: 'Scoring operational complexity' },
  { at: s(40.5), kind: 'start', agent: 'Omar', task: 'Compliance screening all options' },
  { at: s(40.8), kind: 'start', agent: 'Sofia', task: 'Chairing council deliberation' },

  /* --- Resilience completes --- */
  { at: s(42.5), kind: 'finish', agent: 'Zoya' },
  { at: s(43.3), kind: 'finish', agent: 'Ishaan' },
  { at: s(44.3), kind: 'finish', agent: 'Leena' },
  { at: s(44.7), kind: 'log', level: 'success', text: 'Leena: topology B survives 13 of 14 disruption scenarios.' },
  { at: s(45.5), kind: 'finish', agent: 'Arjun' },

  /* --- Council completes, Architecture wave --- */
  { at: s(47.5), kind: 'finish', agent: 'Helena' },
  { at: s(48.0), kind: 'finish', agent: 'Vikram' },
  { at: s(48.5), kind: 'finish', agent: 'Nisha' },
  { at: s(49.0), kind: 'finish', agent: 'Omar' },
  { at: s(50.0), kind: 'finish', agent: 'Sofia' },
  { at: s(50.4), kind: 'log', level: 'success', text: 'Council verdict: topology B with dual-sourcing on critical components.' },

  { at: s(51.5), kind: 'log', level: 'action', text: 'Maya → hire_team(): Architecture cabin — final blueprint, rollout sequencing & independent validation.' },
  { at: s(52.1), kind: 'hire', agent: 'Rohan', team: 'Architecture', role: 'Master supply-chain architect', clearance: 'GREEN', mandate: 'Assemble the master network blueprint.' },
  { at: s(52.9), kind: 'hire', agent: 'Priya', team: 'Architecture', role: 'Implementation planner', clearance: 'AMBER', mandate: 'Sequence rollout; external coordination gated.' },
  { at: s(53.7), kind: 'hire', agent: 'Ethan', team: 'Architecture', role: 'Independent validator', clearance: 'GREEN', mandate: 'Attack the blueprint. Sign off only if it holds.' },
  { at: s(54.0), kind: 'finish', agent: 'Maya' },
  { at: s(54.1), kind: 'log', level: 'success', text: 'Maya: task force complete — 21 hired across 5 cabins. Allocation closed.' },
  { at: s(54.3), kind: 'start', agent: 'Rohan', task: 'Assembling master blueprint' },
  { at: s(54.7), kind: 'start', agent: 'Priya', task: 'Sequencing 90-day rollout plan' },
  { at: s(55.1), kind: 'start', agent: 'Ethan', task: 'Independent validation pass' },
  { at: s(58.5), kind: 'finish', agent: 'Rohan' },
  { at: s(59.5), kind: 'finish', agent: 'Priya' },
  { at: s(61.0), kind: 'finish', agent: 'Ethan' },
  { at: s(61.4), kind: 'log', level: 'success', text: 'Ethan signed off. Blueprint validated against all stress scenarios.' },
  { at: s(62.4), kind: 'log', level: 'success', text: 'MISSION COMPLETE — resilient network blueprint ready for review.' },
  { at: s(62.6), kind: 'complete' },
]

/* Maya and Atlas are always on duty from t=0 — Maya hires, Atlas orchestrates */
const INITIAL_AGENTS: Record<string, AgentState> = {
  Maya: { name: 'Maya', phase: 'working', task: 'Allocating the task force', startedAt: 0, finishedAt: null },
  Atlas: { name: 'Atlas', phase: 'working', task: 'Orchestrating the mission', startedAt: 0, finishedAt: null },
}

function badgeFor(agent: string, index: number): string {
  return `MYC-${String(index + 1).padStart(3, '0')}-${agent.slice(0, 3).toUpperCase()}`
}

// Determine API URLs
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = API_URL.replace(/^http/, 'ws')

/* ------------------------------------------------------------------ */
/* Hook                                                                */
/* ------------------------------------------------------------------ */

export function useMissionSim(projectId?: string | null): MissionState {
  const [state, setState] = useState<MissionState>({
    clock: 0,
    logs: [],
    hires: [],
    agents: INITIAL_AGENTS,
    complete: false,
    pendingApprovals: [],
  })

  // ---- BACKEND DRIVEN MODE ----
  useEffect(() => {
    if (!projectId) return

    let active = true
    let ws: WebSocket | null = null

    async function loadSnapshot() {
      try {
        const token = getToken()
        const res = await fetch(`${API_URL}/api/v1/realtime/snapshot/${projectId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        })
        if (!res.ok) {
          console.error('Snapshot load failed:', res.status, res.statusText)
          try {
            const errorText = await res.text()
            console.error('Snapshot error details:', errorText)
          } catch (e) {}
          throw new Error('Failed to load snapshot')
        }
        const data = await res.json()
        if (!active) return
        if (data && !data.error) {
          setState(data)
        }
      } catch (err) {
        console.error("Failed to load project snapshot:", err)
      }
    }

    loadSnapshot().then(() => {
      if (!active) return
      ws = new WebSocket(`${WS_URL}/api/v1/realtime/sessions/${projectId}`)
      
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          const kind = msg.kind
          const data = msg.data
          
          setState(prev => {
            const next = { ...prev }
            const relTime = next.clock // Use current clock for new events
            
            if (kind === 'log') {
              next.logs = [...prev.logs, { id: prev.logs.length, at: relTime, level: data.level, text: data.text }]
            } else if (kind === 'hire') {
              next.hires = [...prev.hires, {
                id: prev.hires.length,
                at: relTime,
                agent: data.agent,
                team: data.team,
                role: data.role,
                badge: data.badge,
                clearance: data.clearance,
                mandate: data.mandate
              }]
              next.agents = {
                ...prev.agents,
                [data.agent]: { name: data.agent, phase: 'hired', task: 'Awaiting assignment', startedAt: null, finishedAt: null }
              }
            } else if (kind === 'start') {
              const a = prev.agents[data.agent] || { name: data.agent }
              next.agents = {
                ...prev.agents,
                [data.agent]: { ...a, phase: 'working', task: data.task, startedAt: relTime }
              }
            } else if (kind === 'finish') {
              const a = prev.agents[data.agent]
              if (a) {
                next.agents = {
                  ...prev.agents,
                  [data.agent]: { ...a, phase: 'done', finishedAt: relTime }
                }
              }
            } else if (kind === 'complete') {
              next.complete = true
              // Re-fetch snapshot to get the live architecture_report from backend
              setTimeout(() => {
                loadSnapshot()
              }, 1000) // small delay to ensure backend has saved the report
            } else if (kind === 'approval_request') {
              // ArmorIQ is asking the user to approve/deny an agent tool call
              next.pendingApprovals = [
                ...(prev.pendingApprovals ?? []),
                {
                  approval_id: data.approval_id,
                  agent: data.agent,
                  tool: data.tool,
                  intent: data.intent,
                  risk: data.risk,
                  reason: data.reason,
                } as any,
              ]
              // Also log it so the Atlas log shows the gate
              next.logs = [
                ...prev.logs,
                {
                  id: prev.logs.length,
                  at: relTime,
                  level: 'armor' as const,
                  text: `ArmorIQ — ${data.agent} requests approval to run ${data.tool} (${data.risk} risk)`,
                },
              ]
            } else if (kind === 'approval_response') {
              // Remove the resolved approval from the queue
              next.pendingApprovals = (prev.pendingApprovals ?? []).filter(
                (a: any) => a.approval_id !== data.approval_id,
              )
              // Log the outcome
              const action = data.approved ? 'APPROVED' : 'DENIED'
              next.logs = [
                ...prev.logs,
                {
                  id: prev.logs.length,
                  at: relTime,
                  level: data.approved ? ('success' as const) : ('warn' as const),
                  text: `ArmorIQ — Human ${action} ${data.tool} for ${data.agent}`,
                },
              ]
            }
            return next
          })
        } catch (err) {
          console.error("WS parse error", err)
        }
      }
    })

    // Tick the clock locally just to keep the UI timer moving
    const startTick = performance.now()
    const timer = setInterval(() => {
      setState(s => ({ ...s, clock: s.clock + (performance.now() - startTick) }))
    }, 100)

    return () => {
      active = false
      if (ws) ws.close()
      clearInterval(timer)
    }
  }, [projectId])

  // ---- SCRIPTED TIMELINE MODE (MARKETING DEMO) ----
  const startRef = useRef<number | null>(null)
  const cursorRef = useRef(0)
  const idRef = useRef(0)

  useEffect(() => {
    if (projectId) return // Disable mock if real project

    startRef.current = performance.now()

    const tick = () => {
      const start = startRef.current
      if (start === null) return
      const elapsed = performance.now() - start

      let cursor = cursorRef.current
      const due: TimelineEvent[] = []
      while (cursor < TIMELINE.length && TIMELINE[cursor].at <= elapsed) {
        due.push(TIMELINE[cursor])
        cursor++
      }
      cursorRef.current = cursor

      setState((prev) => {
        let next = prev
        if (due.length > 0) {
          const logs = [...prev.logs]
          const hires = [...prev.hires]
          const agents = { ...prev.agents }
          let complete = prev.complete

          for (const ev of due) {
            if (ev.kind === 'log') {
              logs.push({ id: idRef.current++, at: ev.at, level: ev.level, text: ev.text })
            } else if (ev.kind === 'hire') {
              hires.push({
                id: idRef.current++,
                at: ev.at,
                agent: ev.agent,
                team: ev.team,
                role: ev.role,
                badge: badgeFor(ev.agent, hires.length),
                clearance: ev.clearance,
                mandate: ev.mandate,
              })
              agents[ev.agent] = { name: ev.agent, phase: 'hired', task: 'Onboarding…', startedAt: null, finishedAt: null }
              logs.push({
                id: idRef.current++,
                at: ev.at,
                level: 'action',
                text: `HIRED ${ev.agent.toUpperCase()} — ${ev.role}. Clearance ${ev.clearance}.`,
              })
            } else if (ev.kind === 'start') {
              agents[ev.agent] = { name: ev.agent, phase: 'working', task: ev.task, startedAt: ev.at, finishedAt: null }
            } else if (ev.kind === 'finish') {
              const a = agents[ev.agent]
              if (a) agents[ev.agent] = { ...a, phase: 'done', finishedAt: ev.at }
            } else if (ev.kind === 'complete') {
              complete = true
              const atlas = agents.Atlas
              if (atlas) agents.Atlas = { ...atlas, phase: 'done', finishedAt: ev.at }
            }
          }
          next = { clock: elapsed, logs, hires, agents, complete, architecture_report: prev.architecture_report, pendingApprovals: prev.pendingApprovals ?? [] }
        } else {
          next = { ...prev, clock: elapsed }
        }
        return next
      })
    }

    const interval = window.setInterval(tick, 250)
    return () => window.clearInterval(interval)
  }, [projectId])

  return state
}

export function formatElapsed(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(total / 60)
  const sec = total % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}
