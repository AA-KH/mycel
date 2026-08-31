import React, { useMemo } from 'react';
import type { LifecycleAgent } from '../../pixel-office/engine/agentLifecycle';
import type { AgentSession } from '../../types/agent';
import { CanvasOffice } from './CanvasOffice';

interface Props {
  agents: AgentSession[];
  highlightStatus?: string | null;
  onAgentClick?: (agentId: string) => void;
}

/**
 * Company staff that are always present regardless of what the backend is
 * running — they are the ones who greet and route incoming hires.
 */
const STAFF: Record<string, LifecycleAgent> = {
  'staff-orchestrator': {
    status: 'working',
    name: 'Orchestrator',
    role: 'Orchestrator',
  },
  'staff-hr': {
    status: 'working',
    name: 'HR Agent',
    role: 'HR Agent',
  },
};

/**
 * Demo crew — only used when the backend has no live sessions, so the office
 * never looks like an abandoned building.
 */
const DEMO_CREW: Record<string, LifecycleAgent> = {
  'demo-1': { status: 'working', name: 'Aarav', role: 'Developer', team: 'developer', breakActivity: null },
  'demo-2': { status: 'working', name: 'Meera', role: 'Designer', team: 'creative', breakActivity: null },
  'demo-3': { status: 'working', name: 'Ishan', role: 'Analyst', team: 'finance', breakActivity: null },
  'demo-4': { status: 'on_break', name: 'Riya', role: 'Counsel', team: 'legal', breakActivity: 'tea' },
  'demo-5': { status: 'working', name: 'Kabir', role: 'Growth', team: 'marketing', breakActivity: null },
  'demo-6': { status: 'on_break', name: 'Nisha', role: 'Ops', team: 'operations', breakActivity: 'reels' },
  'demo-7': { status: 'working', name: 'Dev', role: 'Researcher', team: 'research', breakActivity: null },
  'demo-8': { status: 'on_break', name: 'Arjun', role: 'Developer', team: 'developer', breakActivity: 'sutta' },
};

export default function VirtualOffice({ agents, onAgentClick }: Props) {
  // The lifecycle engine reconciles against this map: new keys get hired and
  // walk in through the entrance, removed keys walk back out.
  const agentStatuses = useMemo(() => {
    const statuses: Record<string, LifecycleAgent> = { ...STAFF };

    if (agents.length === 0) Object.assign(statuses, DEMO_CREW);

    for (const agent of agents) {
      statuses[agent.id] = {
        status: agent.status,
        name: agent.employee_name ?? agent.role,
        role: agent.role,
        team: agent.team,
        breakActivity: agent.break_activity ?? null,
      };
    }

    return statuses;
  }, [agents]);

  return (
    <div className="absolute inset-0 flex flex-col">
      <div className="relative flex-1">
        <CanvasOffice
          agentStatuses={agentStatuses}
          onAgentClick={(id) => onAgentClick?.(id)}
        />
      </div>
    </div>
  );
}
