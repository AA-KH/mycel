/**
 * Agent lifecycle — the "living office" script.
 *
 * A hire does not teleport into a chair. It materializes outside the entrance,
 * walks through the gate, checks in at the HR desk, gets routed by the
 * Orchestrator, and only then claims a desk inside its department room. While
 * it works it can step out for chai / reels / a smoke break, and when its task
 * completes (or fails) it walks back out of the building and dematerializes.
 *
 * The engine (`OfficeState`) owns movement; this owns the *order* of moves.
 * Every phase either issues one command or waits — so a stalled pathfind
 * degrades into "already there" instead of freezing an agent forever.
 */

import { Direction } from '../types';
import {
  ENTRANCE_TILE,
  GATE_TILE,
  HR_DESK_TILE,
  HR_SEAT_TILE,
  LOUNGE_TILES,
  ORCHESTRATOR_SEAT_TILE,
  ORCHESTRATOR_TILE,
  SMOKING_SPOT,
} from '../layout/mycelOfficeLayout';
import type { OfficeState } from './officeState';

export type LifecyclePhase =
  | 'materializing'
  | 'to_gate'
  | 'at_gate'
  | 'to_hr'
  | 'at_hr'
  | 'to_orchestrator'
  | 'at_orchestrator'
  | 'to_desk'
  | 'working'
  | 'to_break'
  | 'on_break'
  | 'leaving'
  | 'gone';

/** The slice of an agent session the office actually reacts to. */
export interface LifecycleAgent {
  status: string;
  name: string;
  role?: string;
  team?: string;
  breakActivity?: string | null;
}

interface Entry {
  charId: number;
  phase: LifecyclePhase;
  /** Seconds left in a "pause and look busy" beat. */
  timer: number;
  team?: string;
  role?: string;
  status: string;
  breakActivity: string | null;
  /** Company-level agents (Orchestrator, HR) skip the whole intake walk. */
  isStaff: boolean;
  /** Fan-out slot so a crowd queues side by side instead of stacking. */
  slot: number;
}

const GATE_PAUSE_SEC = 1.0;
const HR_PAUSE_SEC = 2.0;
const ORCHESTRATOR_PAUSE_SEC = 1.8;
/** Gap between two hires walking in, so intake reads as a queue. */
const HIRE_STAGGER_SEC = 0.9;
/** Column offsets applied by queue slot, in tiles. */
const SLOT_DX = [0, 1, -1, 2, -2, 3, -3, 4, -4];

/** Where each break takes an agent. */
function breakSpot(activity: string | null): { col: number; row: number } {
  switch (activity) {
    case 'smoke_break':
      return SMOKING_SPOT;
    case 'chai':
      return LOUNGE_TILES[0];
    case 'scrolling_reels':
      return LOUNGE_TILES[1];
    case 'chatting':
      return LOUNGE_TILES[3];
    default:
      return LOUNGE_TILES[2];
  }
}

const STAFF_SEAT_TILES: Record<string, { col: number; row: number }> = {
  Orchestrator: ORCHESTRATOR_SEAT_TILE,
  'HR Agent': HR_SEAT_TILE,
};

export class AgentLifecycle {
  private entries = new Map<string, Entry>();
  private nextCharId = 1;
  /** Hires waiting outside for their turn to walk through the door. */
  private hireQueue: Array<{ sessionId: string; agent: LifecycleAgent }> = [];
  private hireCooldown = 0;
  private nextSlot = 0;

  constructor(private state: OfficeState) {}

  /** Character id for a session, for click-through from canvas to session. */
  charIdFor(sessionId: string): number | undefined {
    return this.entries.get(sessionId)?.charId;
  }

  sessionIdFor(charId: number): string | undefined {
    for (const [sessionId, entry] of this.entries) {
      if (entry.charId === charId) return sessionId;
    }
    return undefined;
  }

  phaseFor(sessionId: string): LifecyclePhase | undefined {
    return this.entries.get(sessionId)?.phase;
  }

  /**
   * Reconcile against the live session map: hire what is new, update statuses,
   * and send anything that vanished walking for the exit.
   */
  sync(agents: Record<string, LifecycleAgent>): void {
    for (const [sessionId, agent] of Object.entries(agents)) {
      const existing = this.entries.get(sessionId);
      if (existing) {
        existing.status = agent.status;
        existing.breakActivity = agent.breakActivity ?? null;
        existing.team = agent.team ?? existing.team;
        continue;
      }
      if (agent.role && STAFF_SEAT_TILES[agent.role]) {
        // Orchestrator / HR run intake, so they are seated immediately.
        this.hire(sessionId, agent);
        continue;
      }
      if (this.hireQueue.some((q) => q.sessionId === sessionId)) continue;
      this.hireQueue.push({ sessionId, agent });
    }

    for (const [sessionId, entry] of this.entries) {
      if (agents[sessionId]) continue;
      if (entry.phase === 'leaving' || entry.phase === 'gone') continue;
      entry.phase = 'leaving';
      entry.timer = 0;
      this.state.setAgentActive(entry.charId, false);
      this.state.setAgentTool(entry.charId, null);
      this.state.walkToTile(entry.charId, ENTRANCE_TILE.col, ENTRANCE_TILE.row);
    }
  }

  private hire(sessionId: string, agent: LifecycleAgent): void {
    const charId = this.nextCharId++;
    const staffSeatTile = agent.role ? STAFF_SEAT_TILES[agent.role] : undefined;

    if (staffSeatTile) {
      // Orchestrator / HR sit at their own named desks from the first frame —
      // they are the ones running intake, so they cannot queue for it.
      const seatId = this.state.getSeatAtTile(staffSeatTile.col, staffSeatTile.row);
      this.state.addAgent(charId, undefined, undefined, seatId ?? undefined, true, agent.team);
      this.state.setAgentActive(charId, true);
      this.state.setAgentTool(charId, 'browser');
      this.entries.set(sessionId, {
        charId,
        phase: 'working',
        timer: 0,
        team: agent.team,
        role: agent.role,
        status: agent.status,
        breakActivity: agent.breakActivity ?? null,
        isStaff: true,
        slot: 0,
      });
      return;
    }

    const slot = this.nextSlot++;
    this.state.spawnAgentAtTile(charId, ENTRANCE_TILE.col, ENTRANCE_TILE.row, agent.team);
    this.entries.set(sessionId, {
      charId,
      phase: 'materializing',
      timer: 0,
      team: agent.team,
      role: agent.role,
      status: agent.status,
      breakActivity: agent.breakActivity ?? null,
      isStaff: false,
      slot,
    });
  }

  /** Advance every scripted agent. Call once per frame, after state.update(dt). */
  tick(dt: number): void {
    // Let one hire through the door at a time so intake reads as a queue.
    this.hireCooldown -= dt;
    while (this.hireQueue.length > 0 && this.hireCooldown <= 0) {
      const next = this.hireQueue.shift();
      if (!next) break;
      if (!this.entries.has(next.sessionId)) this.hire(next.sessionId, next.agent);
      this.hireCooldown += HIRE_STAGGER_SEC;
    }

    for (const [sessionId, entry] of this.entries) {
      if (entry.phase === 'gone') {
        if (!this.state.hasCharacter(entry.charId)) this.entries.delete(sessionId);
        continue;
      }
      if (!this.state.hasCharacter(entry.charId)) {
        this.entries.delete(sessionId);
        continue;
      }
      // Keep scripted agents from wandering off between beats.
      if (entry.phase !== 'working') this.state.holdStill(entry.charId);
      entry.timer -= dt;
      this.advance(entry);
    }
  }

  /**
   * Walk to a shared waypoint, offset by the agent's queue slot so a group
   * lines up shoulder to shoulder instead of collapsing onto one tile.
   */
  private walk(entry: Entry, tile: { col: number; row: number }): boolean {
    const dx = SLOT_DX[entry.slot % SLOT_DX.length];
    if (dx !== 0 && this.state.walkToTile(entry.charId, tile.col + dx, tile.row)) return true;
    return this.state.walkToTile(entry.charId, tile.col, tile.row);
  }

  private advance(entry: Entry): void {
    const id = entry.charId;
    const arrived = this.state.hasArrived(id);

    switch (entry.phase) {
      case 'materializing': {
        if (this.state.isMaterializing(id)) return;
        this.walk(entry, GATE_TILE);
        entry.phase = 'to_gate';
        return;
      }

      case 'to_gate': {
        if (!arrived) return;
        entry.timer = GATE_PAUSE_SEC;
        entry.phase = 'at_gate';
        return;
      }

      case 'at_gate': {
        if (entry.timer > 0) return;
        this.walk(entry, HR_DESK_TILE);
        entry.phase = 'to_hr';
        return;
      }

      case 'to_hr': {
        if (!arrived) return;
        this.state.faceDirection(id, Direction.UP);
        this.state.showWaitingBubble(id);
        entry.timer = HR_PAUSE_SEC;
        entry.phase = 'at_hr';
        return;
      }

      case 'at_hr': {
        if (entry.timer > 0) return;
        this.walk(entry, ORCHESTRATOR_TILE);
        entry.phase = 'to_orchestrator';
        return;
      }

      case 'to_orchestrator': {
        if (!arrived) return;
        this.state.faceDirection(id, Direction.UP);
        entry.timer = ORCHESTRATOR_PAUSE_SEC;
        entry.phase = 'at_orchestrator';
        return;
      }

      case 'at_orchestrator': {
        if (entry.timer > 0) return;
        this.state.claimSeatForTeam(id, entry.team);
        entry.phase = 'to_desk';
        return;
      }

      case 'to_desk': {
        if (!arrived) return;
        this.state.setAgentActive(id, true);
        this.state.setAgentTool(id, 'browser');
        entry.phase = 'working';
        return;
      }

      case 'working': {
        if (entry.status === 'complete' || entry.status === 'failure') {
          this.state.setAgentActive(id, false);
          this.state.setAgentTool(id, null);
          this.walk(entry, ENTRANCE_TILE);
          entry.phase = 'leaving';
          return;
        }
        if (entry.status === 'on_break') {
          this.state.setAgentActive(id, false);
          this.state.setAgentTool(id, null);
          this.walk(entry, breakSpot(entry.breakActivity));
          entry.phase = 'to_break';
          return;
        }
        return;
      }

      case 'to_break': {
        if (!arrived) return;
        entry.phase = 'on_break';
        return;
      }

      case 'on_break': {
        if (entry.status === 'complete' || entry.status === 'failure') {
          this.walk(entry, ENTRANCE_TILE);
          entry.phase = 'leaving';
          return;
        }
        if (entry.status !== 'on_break') {
          this.state.setAgentActive(id, true);
          this.state.setAgentTool(id, 'browser');
          this.state.sendToSeat(id);
          entry.phase = 'to_desk';
          return;
        }
        return;
      }

      case 'leaving': {
        if (!arrived) return;
        this.state.removeAgent(id);
        entry.phase = 'gone';
        return;
      }

      default:
        return;
    }
  }
}
