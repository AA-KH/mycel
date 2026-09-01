/* ------------------------------------------------------------------ */
/* Simulation Engine                                                    */
/* Bridges MissionState → SimAgent array.                              */
/*                                                                      */
/* • syncWithMission() — reacts to AgentPhase changes (hired/working/  */
/*   done) and flips the corresponding SimAgent's isActive + visible.  */
/* • tick(dt) — advances every visible agent's FSM.                    */
/* ------------------------------------------------------------------ */

import type { AgentPhase, AgentState as MissionAgentState } from '../mission-sim';
import { AGENT_SEATS, BLOCKED_TILES, GRID, LOUNGE_ZONE, SEAT_TILES } from './map-data';
import { createSimAgent, sitAtSeat, updateAgent } from './characters';
import { getWalkableTilesInZone } from './tile-map';
import type { SimAgent } from './types';
import { AgentAnimState, Direction } from './types';

// ── Pre-compute walkable zones ──────────────────────────────────────
// Seats are excluded so a wandering/spawning agent never targets a chair
// that belongs to someone else.
const loungeWalkableTiles = getWalkableTilesInZone(
  GRID, BLOCKED_TILES, LOUNGE_ZONE, { reserved: SEAT_TILES },
);

/** Pick a random walkable tile in the lounge for spawning */
function randomLoungeTile(): { col: number; row: number } {
  if (loungeWalkableTiles.length === 0) return { col: 20, row: 28 }; // fallback
  return loungeWalkableTiles[Math.floor(Math.random() * loungeWalkableTiles.length)];
}

// ── Engine ──────────────────────────────────────────────────────────

export interface SimulationEngine {
  /** All agent instances (visible + invisible) */
  agents: SimAgent[];
  /** Map agent name → SimAgent for O(1) lookup */
  agentMap: Map<string, SimAgent>;
  /** Last-seen phase per agent name, used to detect transitions */
  lastPhase: Map<string, AgentPhase>;
  /** Sync simulation state with the latest mission agent phases */
  syncWithMission(missionAgents: Record<string, MissionAgentState>): void;
  /** Advance every visible agent's FSM by dt seconds */
  tick(dt: number): void;
}

export function createSimulationEngine(): SimulationEngine {
  // Create all agents from seat definitions
  const agents: SimAgent[] = [];
  const agentMap = new Map<string, SimAgent>();
  const lastPhase = new Map<string, AgentPhase>();

  for (const seat of AGENT_SEATS) {
    // Atlas starts at his desk, everyone else spawns offscreen (invisible until hired)
    let agent: SimAgent;
    if (seat.isExecutive) {
      // Atlas starts at his desk, visible and working
      agent = createSimAgent(seat, seat.seatCol, seat.seatRow);
      agent.visible = true;
      agent.isActive = true;
      sitAtSeat(agent);
      lastPhase.set(seat.name, 'working');
    } else {
      // Other agents: created but invisible until hired
      const spawn = randomLoungeTile();
      agent = createSimAgent(seat, spawn.col, spawn.row);
      agent.visible = false;
      agent.isActive = false;
      lastPhase.set(seat.name, 'standby');
    }
    agents.push(agent);
    agentMap.set(seat.name, agent);
  }

  const engine: SimulationEngine = {
    agents,
    agentMap,
    lastPhase,

    syncWithMission(missionAgents: Record<string, MissionAgentState>) {
      for (const [name, mState] of Object.entries(missionAgents)) {
        const agent = this.agentMap.get(name);
        if (!agent) continue;
        
        // Always sync current task if working or hired
        agent.currentTask = mState.phase === 'working' || mState.phase === 'hired' ? mState.task : undefined;

        const prevPhase = this.lastPhase.get(name);
        if (prevPhase === mState.phase) continue; // no change
        this.lastPhase.set(name, mState.phase);

        switch (mState.phase) {
          case 'hired': {
            // Agent just hired — spawn in lounge, visible, idle
            if (!agent.visible) {
              const spawn = randomLoungeTile();
              const center = tileCenter(spawn.col, spawn.row);
              agent.tileCol = spawn.col;
              agent.tileRow = spawn.row;
              agent.x = center.x;
              agent.y = center.y;
            }
            agent.visible = true;
            agent.isActive = false;
            agent.state = AgentAnimState.IDLE;
            agent.dir = Direction.DOWN;
            agent.frame = 0;
            agent.frameTimer = 0;
            break;
          }

          case 'working': {
            // Agent starts working — set active, FSM will pathfind to desk
            agent.visible = true;
            agent.isActive = true;
            // If already at desk, the IDLE handler will transition to WORK
            // If walking, the WALK handler will repath to desk
            break;
          }

          case 'done': {
            // Agent finished — deactivate, FSM will pathfind to lounge
            agent.isActive = false;
            // If sitting at desk (WORK state), the WORK handler will transition to IDLE
            break;
          }

          case 'standby':
          default:
            agent.visible = false;
            agent.isActive = false;
            break;
        }
      }
    },

    tick(dt: number) {
      for (const agent of this.agents) {
        updateAgent(agent, dt, loungeWalkableTiles, GRID, BLOCKED_TILES);
      }
    },
  };

  return engine;
}

// ── Helper (duplicated from characters to avoid circular import) ────
function tileCenter(col: number, row: number): { x: number; y: number } {
  const T = 16;
  return { x: col * T + T / 2, y: row * T + T / 2 };
}
