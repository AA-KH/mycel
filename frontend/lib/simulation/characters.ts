/* ------------------------------------------------------------------ */
/* Agent State Machine & Movement                                       */
/* Creates agents and ticks their IDLE/WALK/WORK FSM each frame.       */
/* Adapted from pixel-agents/characters.ts for log-driven behavior.    */
/* ------------------------------------------------------------------ */

import type { AgentSeatDef, TileInfo } from './map-data';
import { SEAT_TILES, T, tileKey } from './map-data';
import { findPath, type PathOptions } from './tile-map';
import {
  AgentAnimState,
  Direction,
  SIT_COLS,
  WALK_COLS,
  WALK_FRAME_DURATION,
  WALK_SPEED,
  WANDER_MOVES_MAX,
  WANDER_MOVES_MIN,
  WANDER_PAUSE_MAX,
  WANDER_PAUSE_MIN,
  WORK_COLS,
  WORK_FRAME_DURATION,
  type SimAgent,
} from './types';

// ── Helpers ─────────────────────────────────────────────────────────

/** Pixel center of a tile */
function tileCenter(col: number, row: number): { x: number; y: number } {
  return { x: col * T + T / 2, y: row * T + T / 2 };
}

/** Direction from one tile to an adjacent tile */
function directionBetween(
  fromCol: number, fromRow: number,
  toCol: number, toRow: number,
): (typeof Direction)[keyof typeof Direction] {
  const dc = toCol - fromCol;
  const dr = toRow - fromRow;
  if (dc > 0) return Direction.RIGHT;
  if (dc < 0) return Direction.LEFT;
  if (dr > 0) return Direction.DOWN;
  return Direction.UP;
}

function randomRange(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function randomInt(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1));
}

/**
 * Pathfinding constraints for a single agent: all assigned seats are
 * reserved, except this agent's own seat, which it is allowed to enter.
 * This stops an agent from walking through — or parking on — a chair
 * that belongs to somebody else.
 */
function pathOptionsFor(agent: SimAgent): PathOptions {
  return {
    reserved: SEAT_TILES,
    allow: tileKey(agent.seatCol, agent.seatRow),
  };
}

/** True when the agent is standing on its own assigned seat tile. */
export function isAtSeat(agent: SimAgent): boolean {
  return agent.tileCol === agent.seatCol && agent.tileRow === agent.seatRow;
}

// ── Create ──────────────────────────────────────────────────────────

/** Create a SimAgent from a seat definition. Spawns at spawnCol/spawnRow. */
export function createSimAgent(
  seat: AgentSeatDef,
  spawnCol: number,
  spawnRow: number,
): SimAgent {
  const center = tileCenter(spawnCol, spawnRow);
  return {
    name: seat.name,
    role: seat.role,
    room: seat.room,
    state: AgentAnimState.IDLE,
    dir: Direction.DOWN,
    x: center.x,
    y: center.y,
    tileCol: spawnCol,
    tileRow: spawnRow,
    path: [],
    moveProgress: 0,
    charIdx: seat.charIdx,
    frame: 0,
    frameTimer: 0,
    wanderTimer: randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX),
    wanderCount: 0,
    wanderLimit: randomInt(WANDER_MOVES_MIN, WANDER_MOVES_MAX),
    isActive: false,
    visible: false,
    isExecutive: seat.isExecutive ?? false,
    seatCol: seat.seatCol,
    seatRow: seat.seatRow,
    seatDir: seat.seatDir,
  };
}

// ── Update (per-frame tick) ─────────────────────────────────────────

/**
 * Advance the agent's finite state machine by `dt` seconds.
 *
 * State transitions are log-driven via `agent.isActive`:
 * - isActive=true  → pathfind to desk → WORK
 * - isActive=false → pathfind to lounge → IDLE + wander
 */
export function updateAgent(
  agent: SimAgent,
  dt: number,
  loungeWalkableTiles: Array<{ col: number; row: number }>,
  grid: TileInfo[][],
  blockedTiles: Set<string>,
): void {
  if (!agent.visible) return;

  agent.frameTimer += dt;

  switch (agent.state) {
    // ── WORK: sitting at desk, typing animation ─────────────────
    case AgentAnimState.WORK: {
      if (agent.frameTimer >= WORK_FRAME_DURATION) {
        agent.frameTimer -= WORK_FRAME_DURATION;
        agent.frame = (agent.frame + 1) % WORK_COLS.length;
      }
      // Keep the agent glued to the seat while working.
      agent.dir = agent.seatDir;
      // Transition: if no longer active → stand up, head to lounge
      if (!agent.isActive) {
        agent.frame = 0;
        agent.frameTimer = 0;
        agent.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
        agent.wanderCount = 0;
        agent.wanderLimit = randomInt(WANDER_MOVES_MIN, WANDER_MOVES_MAX);
        // Immediately pathfind to a random lounge tile
        pathfindToLounge(agent, loungeWalkableTiles, grid, blockedTiles);
        // If no route out exists this frame, stay seated (rather than
        // popping into a standing pose on top of the chair) and retry.
        if (agent.state === AgentAnimState.WORK) {
          agent.state = AgentAnimState.SIT;
        }
      }
      break;
    }

    // ── SIT: seated, not working — waiting for a route out ──────
    case AgentAnimState.SIT: {
      if (agent.frameTimer >= WORK_FRAME_DURATION) {
        agent.frameTimer -= WORK_FRAME_DURATION;
        agent.frame = (agent.frame + 1) % SIT_COLS.length;
      }
      agent.dir = agent.seatDir;

      if (agent.isActive) {
        agent.state = AgentAnimState.WORK;
        agent.frame = 0;
        agent.frameTimer = 0;
        break;
      }

      agent.wanderTimer -= dt;
      if (agent.wanderTimer <= 0) {
        agent.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
        pathfindToLounge(agent, loungeWalkableTiles, grid, blockedTiles);
      }
      break;
    }

    // ── IDLE: in lounge, wandering ──────────────────────────────
    case AgentAnimState.IDLE: {
      agent.frame = 0; // static standing pose
      // Transition: if became active → pathfind to desk
      if (agent.isActive) {
        const path = findPath(
          agent.tileCol, agent.tileRow,
          agent.seatCol, agent.seatRow,
          grid, blockedTiles, pathOptionsFor(agent),
        );
        if (path.length > 0) {
          agent.path = path;
          agent.moveProgress = 0;
          agent.state = AgentAnimState.WALK;
          agent.frame = 0;
          agent.frameTimer = 0;
        } else if (isAtSeat(agent)) {
          // Already on the seat tile — sit down and start working
          sitAtSeat(agent);
        }
        // Otherwise unreachable this frame; stay idle and retry next tick.
        break;
      }
      // Wander countdown
      agent.wanderTimer -= dt;
      if (agent.wanderTimer <= 0) {
        // Pick a random walkable tile in the lounge to wander to
        if (loungeWalkableTiles.length > 0) {
          const target = loungeWalkableTiles[
            Math.floor(Math.random() * loungeWalkableTiles.length)
          ];
          const path = findPath(
            agent.tileCol, agent.tileRow,
            target.col, target.row,
            grid, blockedTiles, pathOptionsFor(agent),
          );
          if (path.length > 0) {
            agent.path = path;
            agent.moveProgress = 0;
            agent.state = AgentAnimState.WALK;
            agent.frame = 0;
            agent.frameTimer = 0;
            agent.wanderCount++;
          }
        }
        agent.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
      }
      break;
    }

    // ── WALK: moving along BFS path ─────────────────────────────
    case AgentAnimState.WALK: {
      // Walk animation frame cycling
      if (agent.frameTimer >= WALK_FRAME_DURATION) {
        agent.frameTimer -= WALK_FRAME_DURATION;
        agent.frame = (agent.frame + 1) % WALK_COLS.length;
      }

      // Path complete → transition
      if (agent.path.length === 0) {
        const center = tileCenter(agent.tileCol, agent.tileRow);
        agent.x = center.x;
        agent.y = center.y;

        if (agent.isActive && isAtSeat(agent)) {
          // Arrived at the desk — sit down and start working
          sitAtSeat(agent);
        } else if (isAtSeat(agent)) {
          // Standing on our own seat but not active — sit rather than
          // hover on the chair; SIT retries the walk to the lounge.
          agent.state = AgentAnimState.SIT;
          agent.dir = agent.seatDir;
          agent.frame = 0;
          agent.frameTimer = 0;
          agent.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
        } else {
          agent.state = AgentAnimState.IDLE;
          agent.wanderTimer = randomRange(WANDER_PAUSE_MIN, WANDER_PAUSE_MAX);
          agent.frame = 0;
          agent.frameTimer = 0;
        }
        break;
      }

      // Move toward next tile in path
      const nextTile = agent.path[0];
      agent.dir = directionBetween(agent.tileCol, agent.tileRow, nextTile.col, nextTile.row);

      agent.moveProgress += (WALK_SPEED / T) * dt;

      const fromCenter = tileCenter(agent.tileCol, agent.tileRow);
      const toCenter = tileCenter(nextTile.col, nextTile.row);
      const t = Math.min(agent.moveProgress, 1);
      agent.x = fromCenter.x + (toCenter.x - fromCenter.x) * t;
      agent.y = fromCenter.y + (toCenter.y - fromCenter.y) * t;

      if (agent.moveProgress >= 1) {
        // Arrived at next tile
        agent.tileCol = nextTile.col;
        agent.tileRow = nextTile.row;
        agent.x = toCenter.x;
        agent.y = toCenter.y;
        agent.path.shift();
        agent.moveProgress = 0;
      }

      // If became active while wandering → repath to desk
      if (agent.isActive) {
        const lastStep = agent.path[agent.path.length - 1];
        if (!lastStep || lastStep.col !== agent.seatCol || lastStep.row !== agent.seatRow) {
          const newPath = findPath(
            agent.tileCol, agent.tileRow,
            agent.seatCol, agent.seatRow,
            grid, blockedTiles, pathOptionsFor(agent),
          );
          if (newPath.length > 0) {
            agent.path = newPath;
            agent.moveProgress = 0;
          }
        }
      }
      break;
    }
  }
}

// ── Internal helpers ────────────────────────────────────────────────

/**
 * Snap an agent onto its seat and start the working animation.
 * Position is hard-set to the seat tile centre so the sprite lines up
 * with the chair exactly, with no sub-pixel drift left over from the walk.
 */
export function sitAtSeat(agent: SimAgent): void {
  const center = tileCenter(agent.seatCol, agent.seatRow);
  agent.tileCol = agent.seatCol;
  agent.tileRow = agent.seatRow;
  agent.x = center.x;
  agent.y = center.y;
  agent.path = [];
  agent.moveProgress = 0;
  agent.dir = agent.seatDir;
  agent.state = AgentAnimState.WORK;
  agent.frame = 0;
  agent.frameTimer = 0;
}

/** Find a path from the agent's current tile to a random lounge tile */
function pathfindToLounge(
  agent: SimAgent,
  loungeWalkableTiles: Array<{ col: number; row: number }>,
  grid: TileInfo[][],
  blockedTiles: Set<string>,
): void {
  if (loungeWalkableTiles.length === 0) return;
  const target = loungeWalkableTiles[
    Math.floor(Math.random() * loungeWalkableTiles.length)
  ];
  const path = findPath(
    agent.tileCol, agent.tileRow,
    target.col, target.row,
    grid, blockedTiles, pathOptionsFor(agent),
  );
  if (path.length > 0) {
    agent.path = path;
    agent.moveProgress = 0;
    agent.state = AgentAnimState.WALK;
    agent.frame = 0;
    agent.frameTimer = 0;
  }
}
