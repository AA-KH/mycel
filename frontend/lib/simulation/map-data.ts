/* ------------------------------------------------------------------ */
/* Shared Map Data                                                      */
/* Room definitions, furniture layout, door openings, grid builder,     */
/* agent seat assignments, and blocked-tile computation.                 */
/*                                                                      */
/* Both the canvas renderer (pixel-office.tsx) and the simulation       */
/* engine import from this module — single source of truth.             */
/* ------------------------------------------------------------------ */

import { Direction } from './types';

// ── Layout constants ────────────────────────────────────────────────
export const T = 16;       // tile size in world pixels
export const COLS = 42;
export const ROWS = 34;
export const WORLD_W = COLS * T;
export const WORLD_H = ROWS * T;

// ── Character sprite frame dimensions ───────────────────────────────
// Single source of truth lives in ./types (112×96 = 7 cols × 3 rows
// of 16×32 frames). Re-exported here for existing import sites.
export { CHAR_FRAME_W, CHAR_FRAME_H } from './types';

// ═══════════════════════════════════════════════════════════════════
// ROOM DEFINITIONS (interior tile ranges, inclusive)
// ═══════════════════════════════════════════════════════════════════
export interface RoomDef {
  id: string;
  name: string;
  c1: number; r1: number; // top-left interior tile
  c2: number; r2: number; // bottom-right interior tile
  floor: number;          // floor tile index (0-8)
  tint: string;           // floor color tint
  wallTint: string;
  labelColor: string;
  labelX: number; labelY: number;
  labelRotation?: number;
}

export const ROOMS: RoomDef[] = [
  // ── Top Row ──
  { id: 'research',     name: 'Research',     c1: 1,  r1: 1,  c2: 12, r2: 10, floor: 1, tint: 'rgba(100,190,190,0.45)', wallTint: '#3d5a5a', labelColor: '#7ecfcf', labelX: 5.2,  labelY: 0.4 },
  { id: 'planning',     name: 'Planning',     c1: 15, r1: 1,  c2: 26, r2: 10, floor: 3, tint: 'rgba(120,160,210,0.40)', wallTint: '#3a4a6a', labelColor: '#a5b4fc', labelX: 19.4, labelY: 0.4 },
  { id: 'resilience',   name: 'Resilience',   c1: 29, r1: 1,  c2: 40, r2: 10, floor: 5, tint: 'rgba(100,200,140,0.38)', wallTint: '#3a5a4a', labelColor: '#86efac', labelX: 32.4, labelY: 0.4 },
  // ── Middle Row ──
  { id: 'strategy',     name: 'Strategy',           c1: 1,  r1: 13, c2: 12, r2: 22, floor: 4, tint: 'rgba(200,130,130,0.35)', wallTint: '#5a3a3a', labelColor: '#fca5a5', labelX: 0.61, labelY: 20, labelRotation: -90 },
  { id: 'atlas',        name: 'Executive',       c1: 15, r1: 13, c2: 26, r2: 22, floor: 8, tint: 'rgba(180,160,100,0.35)', wallTint: '#4a4530', labelColor: '#ffd700', labelX: 18.5, labelY: 21.6 },
  { id: 'architecture', name: 'Architecture',       c1: 29, r1: 13, c2: 40, r2: 22, floor: 2, tint: 'rgba(160,140,210,0.38)', wallTint: '#44385a', labelColor: '#c4b5fd', labelX: 41.5, labelY: 15, labelRotation: 90 },
  // ── Bottom Lounge ──
  { id: 'lounge',       name: 'Break Lounge',       c1: 1,  r1: 25, c2: 40, r2: 32, floor: 6, tint: 'rgba(180,170,120,0.32)', wallTint: '#4a4535', labelColor: '#fde68a', labelX: 19, labelY: 32 },
];

// ═══════════════════════════════════════════════════════════════════
// DOOR OPENINGS
// ═══════════════════════════════════════════════════════════════════
export interface DoorDef { col: number; row: number; floor: number }

export const DOORS: DoorDef[] = [
  // Vertical doors (between top & middle rows)
  { col: 6, row: 11, floor: 1 }, { col: 7, row: 11, floor: 1 },
  { col: 6, row: 12, floor: 1 }, { col: 7, row: 12, floor: 1 },
  { col: 20, row: 11, floor: 3 }, { col: 21, row: 11, floor: 3 },
  { col: 20, row: 12, floor: 3 }, { col: 21, row: 12, floor: 3 },
  { col: 34, row: 11, floor: 5 }, { col: 35, row: 11, floor: 5 },
  { col: 34, row: 12, floor: 5 }, { col: 35, row: 12, floor: 5 },
  // Vertical doors (between middle row & lounge)
  { col: 6, row: 23, floor: 4 }, { col: 7, row: 23, floor: 4 },
  { col: 6, row: 24, floor: 4 }, { col: 7, row: 24, floor: 4 },
  { col: 20, row: 23, floor: 8 }, { col: 21, row: 23, floor: 8 },
  { col: 20, row: 24, floor: 8 }, { col: 21, row: 24, floor: 8 },
  { col: 34, row: 23, floor: 2 }, { col: 35, row: 23, floor: 2 },
  { col: 34, row: 24, floor: 2 }, { col: 35, row: 24, floor: 2 },
  // Horizontal doors (between adjacent rooms)
  { col: 13, row: 5, floor: 1 }, { col: 14, row: 5, floor: 3 },
  { col: 13, row: 6, floor: 1 }, { col: 14, row: 6, floor: 3 },
  { col: 27, row: 5, floor: 3 }, { col: 28, row: 5, floor: 5 },
  { col: 27, row: 6, floor: 3 }, { col: 28, row: 6, floor: 5 },
  { col: 13, row: 17, floor: 4 }, { col: 14, row: 17, floor: 8 },
  { col: 13, row: 18, floor: 4 }, { col: 14, row: 18, floor: 8 },
  { col: 27, row: 17, floor: 8 }, { col: 28, row: 17, floor: 2 },
  { col: 27, row: 18, floor: 8 }, { col: 28, row: 18, floor: 2 },
];

// ═══════════════════════════════════════════════════════════════════
// FURNITURE PLACEMENT
// ═══════════════════════════════════════════════════════════════════
export interface FurnitureDef {
  img: string;
  col: number;
  row: number;
  mirror?: boolean;
  depth?: number;
  animated?: boolean;
}

export const FURNITURE: FurnitureDef[] = [
  // ── RESEARCH CABIN (cols 1-12, rows 1-10) ─────────────────────
  { img: 'DOUBLE_BOOKSHELF', col: 2, row: 1, depth: 0 },
  { img: 'CLOCK', col: 5, row: 1, depth: 0 },
  { img: 'BOOKSHELF', col: 7, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 10, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING', col: 11, row: 1, depth: 0 },
  { img: 'DESK_FRONT', col: 1, row: 3 },
  { img: 'PC_FRONT_ON', col: 2, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 2, row: 5 },
  { img: 'DESK_FRONT', col: 6, row: 3 },
  { img: 'PC_FRONT_ON', col: 7, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 7, row: 5 },
  { img: 'DESK_FRONT', col: 1, row: 7 },
  { img: 'PC_FRONT_ON', col: 2, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 2, row: 9 },
  { img: 'DESK_FRONT', col: 6, row: 7 },
  { img: 'PC_FRONT_ON', col: 7, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 7, row: 9 },
  { img: 'PLANT', col: 11, row: 4 },
  { img: 'CACTUS', col: 11, row: 8 },
  { img: 'BIN', col: 10, row: 9 },
  // ── PLANNING CABIN (cols 15-26, rows 1-10) ────────────────────
  { img: 'WHITEBOARD', col: 16, row: 1, depth: 0 },
  { img: 'CLOCK', col: 19, row: 1, depth: 0 },
  { img: 'BOOKSHELF', col: 21, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 24, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING_2', col: 25, row: 1, depth: 0 },
  { img: 'TABLE_FRONT', col: 18, row: 4 },
  { img: 'WOODEN_CHAIR_SIDE', col: 17, row: 5 },
  { img: 'WOODEN_CHAIR_SIDE', col: 17, row: 7 },
  { img: 'WOODEN_CHAIR_SIDE', col: 22, row: 5, mirror: true },
  { img: 'WOODEN_CHAIR_SIDE', col: 22, row: 7, mirror: true },
  { img: 'DESK_FRONT', col: 15, row: 3 },
  { img: 'PC_FRONT_ON', col: 16, row: 3, animated: true },
  { img: 'DESK_FRONT', col: 23, row: 3 },
  { img: 'PC_FRONT_ON', col: 24, row: 3, animated: true },
  { img: 'PLANT', col: 15, row: 9 },
  { img: 'PLANT_2', col: 25, row: 9 },
  // ── RESILIENCE CABIN (cols 29-40, rows 1-10) ──────────────────
  { img: 'BOOKSHELF', col: 30, row: 1, depth: 0 },
  { img: 'DOUBLE_BOOKSHELF', col: 33, row: 1, depth: 0 },
  { img: 'CLOCK', col: 36, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 38, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING_2', col: 39, row: 1, depth: 0 },
  { img: 'DESK_FRONT', col: 29, row: 3 },
  { img: 'PC_FRONT_ON', col: 30, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 30, row: 5 },
  { img: 'DESK_FRONT', col: 34, row: 3 },
  { img: 'PC_FRONT_ON', col: 35, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 35, row: 5 },
  { img: 'DESK_FRONT', col: 29, row: 7 },
  { img: 'PC_FRONT_ON', col: 30, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 30, row: 9 },
  { img: 'DESK_FRONT', col: 34, row: 7 },
  { img: 'PC_FRONT_ON', col: 35, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 35, row: 9 },
  { img: 'PLANT_2', col: 39, row: 4 },
  { img: 'CACTUS', col: 39, row: 8 },
  // ── STRATEGY (cols 1-12, rows 13-22) ──────────────────────────
  { img: 'WHITEBOARD', col: 2, row: 13, depth: 12 },
  { img: 'LARGE_PAINTING', col: 5, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 8, row: 13, depth: 12 },
  { img: 'CLOCK', col: 11, row: 13, depth: 12 },
  { img: 'HANGING_PLANT', col: 12, row: 13, depth: 12 },
  { img: 'DESK_FRONT', col: 1, row: 15 },
  { img: 'PC_FRONT_ON', col: 2, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 2, row: 17 },
  { img: 'DESK_FRONT', col: 5, row: 15 },
  { img: 'PC_FRONT_ON', col: 6, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 6, row: 17 },
  { img: 'DESK_FRONT', col: 9, row: 15 },
  { img: 'PC_FRONT_ON', col: 10, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 10, row: 17 },
  { img: 'DESK_FRONT', col: 2, row: 19 },
  { img: 'PC_FRONT_ON', col: 3, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 3, row: 21 },
  { img: 'DESK_FRONT', col: 7, row: 19 },
  { img: 'PC_FRONT_ON', col: 8, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 8, row: 21 },
  { img: 'PLANT', col: 12, row: 15 },
  { img: 'PLANT_2', col: 1, row: 21 },
  // ── ATLAS'S OFFICE (cols 15-26, rows 13-22) ──────────────────
  { img: 'DOUBLE_BOOKSHELF', col: 16, row: 13, depth: 12 },
  { img: 'LARGE_PAINTING', col: 19, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 22, row: 13, depth: 12 },
  { img: 'CLOCK', col: 25, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING', col: 15, row: 13, depth: 12 },
  { img: 'DESK_FRONT', col: 19, row: 16 },
  { img: 'PC_FRONT_ON', col: 20, row: 16, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 20, row: 18 },
  // Maya's hiring desk — shares the Executive Cabin with Atlas
  { img: 'DESK_FRONT', col: 21, row: 19 },
  { img: 'PC_FRONT_ON', col: 22, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 22, row: 21 },
  { img: 'SOFA_FRONT', col: 15, row: 17 },
  { img: 'COFFEE_TABLE', col: 15, row: 19 },
  { img: 'COFFEE', col: 16, row: 20 },
  { img: 'LARGE_PLANT', col: 15, row: 14 },
  { img: 'LARGE_PLANT', col: 25, row: 14 },
  { img: 'PLANT', col: 25, row: 21 },
  { img: 'SMALL_TABLE_FRONT', col: 24, row: 19 },
  { img: 'COFFEE', col: 25, row: 19 },
  // ── ARCHITECTURE CABIN (cols 29-40, rows 13-22) ──────────────
  { img: 'WHITEBOARD', col: 30, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 33, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING', col: 36, row: 13, depth: 12 },
  { img: 'HANGING_PLANT', col: 38, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING_2', col: 39, row: 13, depth: 12 },
  { img: 'DESK_FRONT', col: 29, row: 15 },
  { img: 'PC_FRONT_ON', col: 30, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 30, row: 17 },
  { img: 'DESK_FRONT', col: 34, row: 15 },
  { img: 'PC_FRONT_ON', col: 35, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 35, row: 17 },
  { img: 'DESK_FRONT', col: 31, row: 19 },
  { img: 'PC_FRONT_ON', col: 32, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_BACK', col: 32, row: 21 },
  { img: 'PLANT', col: 39, row: 16 },
  { img: 'CACTUS', col: 29, row: 21 },
  { img: 'PLANT_2', col: 39, row: 20 },
  // ── BREAK LOUNGE (cols 1-40, rows 25-32) ─────────────────────
  { img: 'LARGE_PAINTING', col: 3, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 8, row: 25, depth: 24 },
  { img: 'SMALL_PAINTING', col: 14, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 20, row: 25, depth: 24 },
  { img: 'LARGE_PAINTING', col: 25, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 32, row: 25, depth: 24 },
  { img: 'SMALL_PAINTING_2', col: 37, row: 25, depth: 24 },
  { img: 'SOFA_FRONT', col: 3, row: 27 },
  { img: 'COFFEE_TABLE', col: 3, row: 29 },
  { img: 'COFFEE', col: 4, row: 29 },
  { img: 'SOFA_BACK', col: 3, row: 31 },
  { img: 'SOFA_SIDE', col: 14, row: 28 },
  { img: 'COFFEE_TABLE', col: 16, row: 28 },
  { img: 'SOFA_SIDE', col: 18, row: 28, mirror: true },
  { img: 'COFFEE', col: 17, row: 29 },
  { img: 'SMALL_TABLE_FRONT', col: 30, row: 28 },
  { img: 'WOODEN_BENCH', col: 30, row: 30 },
  { img: 'WOODEN_BENCH', col: 31, row: 30 },
  { img: 'WOODEN_CHAIR_FRONT', col: 30, row: 27 },
  { img: 'WOODEN_CHAIR_FRONT', col: 32, row: 27 },
  { img: 'SOFA_FRONT', col: 36, row: 28 },
  { img: 'SMALL_TABLE_FRONT', col: 36, row: 30 },
  { img: 'LARGE_PLANT', col: 1, row: 26 },
  { img: 'LARGE_PLANT', col: 40, row: 26 },
  { img: 'PLANT', col: 1, row: 31 },
  { img: 'PLANT_2', col: 40, row: 31 },
  { img: 'PLANT', col: 10, row: 28 },
  { img: 'PLANT_2', col: 23, row: 28 },
  { img: 'BIN', col: 27, row: 31 },
  { img: 'POT', col: 12, row: 31 },
  { img: 'CACTUS', col: 34, row: 31 },
];

// ═══════════════════════════════════════════════════════════════════
// AGENT SEAT ASSIGNMENTS
// Maps each agent name → their desk chair tile + room.
// ═══════════════════════════════════════════════════════════════════
export interface AgentSeatDef {
  name: string;
  role: string;
  room: string;
  charIdx: number;
  seatCol: number;
  seatRow: number;
  seatDir: (typeof Direction)[keyof typeof Direction];
  isExecutive?: boolean;
}

export const AGENT_SEATS: AgentSeatDef[] = [
  // Research Cabin
  { name: 'Mira',    role: 'Lead Researcher',        room: 'research',     charIdx: 0, seatCol: 2,  seatRow: 5,  seatDir: Direction.UP },
  { name: 'Ravi',    role: 'Data Analyst',            room: 'research',     charIdx: 1, seatCol: 7,  seatRow: 5,  seatDir: Direction.UP },
  { name: 'Anika',   role: 'Market Analyst',          room: 'research',     charIdx: 2, seatCol: 2,  seatRow: 9,  seatDir: Direction.UP },
  { name: 'Noor',    role: 'Trend Spotter',           room: 'research',     charIdx: 3, seatCol: 7,  seatRow: 9,  seatDir: Direction.UP },
  // Planning Cabin
  { name: 'Aanya',   role: 'Planning Lead',           room: 'planning',     charIdx: 4, seatCol: 17, seatRow: 5,  seatDir: Direction.RIGHT },
  { name: 'Dev',     role: 'Demand Planner',          room: 'planning',     charIdx: 5, seatCol: 22, seatRow: 5,  seatDir: Direction.LEFT },
  { name: 'Kabir',   role: 'Supply Planner',          room: 'planning',     charIdx: 0, seatCol: 17, seatRow: 7,  seatDir: Direction.RIGHT },
  { name: 'Tara',    role: 'Capacity Analyst',        room: 'planning',     charIdx: 1, seatCol: 22, seatRow: 7,  seatDir: Direction.LEFT },
  // Resilience Cabin
  { name: 'Zoya',    role: 'Risk Assessor',           room: 'resilience',   charIdx: 2, seatCol: 30, seatRow: 5,  seatDir: Direction.UP },
  { name: 'Ishaan',  role: 'Continuity Planner',      room: 'resilience',   charIdx: 3, seatCol: 35, seatRow: 5,  seatDir: Direction.UP },
  { name: 'Leena',   role: 'Crisis Coordinator',      room: 'resilience',   charIdx: 4, seatCol: 30, seatRow: 9,  seatDir: Direction.UP },
  { name: 'Arjun',   role: 'Recovery Specialist',     room: 'resilience',   charIdx: 5, seatCol: 35, seatRow: 9,  seatDir: Direction.UP },
  // Strategy
  { name: 'Helena',  role: 'Strategy Lead',           room: 'strategy',     charIdx: 0, seatCol: 2,  seatRow: 17, seatDir: Direction.UP },
  { name: 'Vikram',  role: 'Business Strategist',     room: 'strategy',     charIdx: 1, seatCol: 6,  seatRow: 17, seatDir: Direction.UP },
  { name: 'Nisha',   role: 'Portfolio Analyst',       room: 'strategy',     charIdx: 2, seatCol: 10, seatRow: 17, seatDir: Direction.UP },
  { name: 'Omar',    role: 'Growth Planner',          room: 'strategy',     charIdx: 3, seatCol: 3,  seatRow: 21, seatDir: Direction.UP },
  { name: 'Sofia',   role: 'Innovation Scout',        room: 'strategy',     charIdx: 4, seatCol: 8,  seatRow: 21, seatDir: Direction.UP },
  // Executive Cabin — Atlas orchestrates, Maya hires
  { name: 'Atlas',   role: 'Executive Orchestrator',  room: 'atlas',        charIdx: 5, seatCol: 20, seatRow: 18, seatDir: Direction.UP, isExecutive: true },
  { name: 'Maya',    role: 'Chief Resource Allocator', room: 'atlas',       charIdx: 4, seatCol: 22, seatRow: 21, seatDir: Direction.UP, isExecutive: true },
  // Architecture
  { name: 'Rohan',   role: 'System Architect',        room: 'architecture', charIdx: 0, seatCol: 30, seatRow: 17, seatDir: Direction.UP },
  { name: 'Priya',   role: 'Platform Engineer',       room: 'architecture', charIdx: 1, seatCol: 35, seatRow: 17, seatDir: Direction.UP },
  { name: 'Ethan',   role: 'Infrastructure Lead',     room: 'architecture', charIdx: 2, seatCol: 32, seatRow: 21, seatDir: Direction.UP },
];

// ═══════════════════════════════════════════════════════════════════
// TILE GRID BUILDER
// ═══════════════════════════════════════════════════════════════════
export type TileInfo = { type: 'void' } | { type: 'wall' } | { type: 'floor'; floorIdx: number };

export function buildGrid(): TileInfo[][] {
  const grid: TileInfo[][] = Array.from({ length: ROWS }, () =>
    Array.from({ length: COLS }, (): TileInfo => ({ type: 'void' }))
  );

  for (const room of ROOMS) {
    // Fill interior with floor
    for (let r = room.r1; r <= room.r2; r++) {
      for (let c = room.c1; c <= room.c2; c++) {
        grid[r][c] = { type: 'floor', floorIdx: room.floor };
      }
    }
    // Build walls around the room
    const wc1 = room.c1 - 1, wc2 = room.c2 + 1;
    const wr1 = room.r1 - 1, wr2 = room.r2 + 1;
    for (let c = wc1; c <= wc2; c++) {
      if (wr1 >= 0 && wr1 < ROWS && c >= 0 && c < COLS && grid[wr1][c].type !== 'floor')
        grid[wr1][c] = { type: 'wall' };
      if (wr2 >= 0 && wr2 < ROWS && c >= 0 && c < COLS && grid[wr2][c].type !== 'floor')
        grid[wr2][c] = { type: 'wall' };
    }
    for (let r = wr1; r <= wr2; r++) {
      if (wc1 >= 0 && wc1 < COLS && r >= 0 && r < ROWS && grid[r][wc1].type !== 'floor')
        grid[r][wc1] = { type: 'wall' };
      if (wc2 >= 0 && wc2 < COLS && r >= 0 && r < ROWS && grid[r][wc2].type !== 'floor')
        grid[r][wc2] = { type: 'wall' };
    }
  }

  // Apply door openings
  for (const door of DOORS) {
    if (door.row >= 0 && door.row < ROWS && door.col >= 0 && door.col < COLS) {
      grid[door.row][door.col] = { type: 'floor', floorIdx: door.floor };
    }
  }

  return grid;
}

export const GRID = buildGrid();

// ═══════════════════════════════════════════════════════════════════
// BLOCKED TILES (furniture that agents cannot walk through)
// ═══════════════════════════════════════════════════════════════════

/** Furniture types that agents can occupy (chairs, small items) */
const NON_BLOCKING = new Set([
  'CUSHIONED_CHAIR_FRONT', 'CUSHIONED_CHAIR_BACK', 'CUSHIONED_CHAIR_SIDE',
  'WOODEN_CHAIR_SIDE', 'WOODEN_CHAIR_FRONT', 'WOODEN_CHAIR_BACK',
  'COFFEE', // small item sitting on tables
]);

/** Chair sprites — used to decide seat-vs-occupant draw order. */
const CHAIR_IMAGES = new Set([
  'CUSHIONED_CHAIR_FRONT', 'CUSHIONED_CHAIR_BACK', 'CUSHIONED_CHAIR_SIDE',
  'WOODEN_CHAIR_FRONT', 'WOODEN_CHAIR_BACK', 'WOODEN_CHAIR_SIDE',
]);

export function isChair(img: string): boolean {
  return CHAIR_IMAGES.has(img);
}

/**
 * Tile footprints for furniture: [width, height] in tiles.
 *
 * Every entry is derived from the sprite's real pixel dimensions
 * divided by the 16px tile size, so the collision box always matches
 * what is actually drawn. Anything absent defaults to [1, 1].
 */
export const FOOTPRINTS: Record<string, [number, number]> = {
  // ── Desks & tables ──
  'DESK_FRONT':         [3, 2], // 48x32
  'DESK_SIDE':          [1, 4], // 16x64
  'TABLE_FRONT':        [3, 4], // 48x64
  'COFFEE_TABLE':       [2, 2], // 32x32
  'SMALL_TABLE_FRONT':  [2, 2], // 32x32
  'SMALL_TABLE_SIDE':   [1, 3], // 16x48
  'COUNTER':            [2, 1], // 32x16
  // ── Seating ──
  'SOFA_FRONT':         [2, 1], // 32x16
  'SOFA_BACK':          [2, 1], // 32x16
  'SOFA_SIDE':          [1, 2], // 16x32
  'WOODEN_BENCH':       [1, 1], // 16x16
  'CUSHIONED_BENCH':    [1, 1], // 16x16
  'WOODEN_CHAIR_FRONT': [1, 2], // 16x32
  'WOODEN_CHAIR_BACK':  [1, 2], // 16x32
  'WOODEN_CHAIR_SIDE':  [1, 2], // 16x32
  // ── Plants & decor ──
  'LARGE_PLANT':        [2, 3], // 32x48
  'PALM':               [2, 2], // 32x32
  'PLANT':              [1, 2], // 16x32
  'PLANT_2':            [1, 2], // 16x32
  'CACTUS':             [1, 2], // 16x32
  // ── Appliances & fixtures ──
  'DOUBLE_BOOKSHELF':   [2, 2], // 32x32
  'BOOKSHELF':          [2, 1], // 32x16
  'SERVER_CONSOLE':     [2, 2], // 32x32
  'SERVER_RACK':        [1, 2], // 16x32
  'FILE_CABINET':       [1, 2], // 16x32
  'FRIDGE':             [1, 2], // 16x32
  'PRINTER':            [1, 2], // 16x32
  'SINK':               [1, 2], // 16x32
  'VENDING_MACHINE':    [1, 2], // 16x32
  'WATER_COOLER':       [1, 2], // 16x32
  'COFFEE_MACHINE':     [1, 2], // 16x32
  'PC_FRONT_ON':        [1, 2], // 16x32
  'PC_FRONT_OFF':       [1, 2], // 16x32
  'PC_BACK':            [1, 2], // 16x32
  'PC_SIDE':            [1, 2], // 16x32
};

/** Footprint lookup with a safe [1, 1] default. */
export function footprintOf(img: string): [number, number] {
  return FOOTPRINTS[img] ?? [1, 1];
}

export function computeBlockedTiles(): Set<string> {
  const blocked = new Set<string>();
  for (const f of FURNITURE) {
    // Wall-mounted items (explicit depth = wall row) don't block floor
    if (f.depth !== undefined) continue;
    // Chairs and tiny items are walkable
    if (NON_BLOCKING.has(f.img)) continue;

    const [w, h] = footprintOf(f.img);
    for (let dc = 0; dc < w; dc++) {
      for (let dr = 0; dr < h; dr++) {
        blocked.add(`${f.col + dc},${f.row + dr}`);
      }
    }
  }
  return blocked;
}

export const BLOCKED_TILES = computeBlockedTiles();

// ═════════════════════════════════════════════════════════════���═════
// SEAT TILES
// ═══════════════════════════════════════════════════════════════════

export const tileKey = (col: number, row: number) => `${col},${row}`;

/**
 * Every agent's assigned seat tile. Used by pathfinding to reserve
 * seats: an agent may walk onto its own seat but never onto another
 * agent's, so two characters can't end up stacked in one chair.
 */
export const SEAT_TILES: Set<string> = new Set(
  AGENT_SEATS.map(s => tileKey(s.seatCol, s.seatRow)),
);

/**
 * Seat tiles whose occupant faces UP (away from the camera). For these
 * the chair is drawn AFTER the character so its backrest overlaps the
 * character's lower body, which is what makes them read as sitting
 * *in* the chair rather than standing on it. Side-facing seats keep
 * the default order (chair behind the character).
 */
export const SEAT_OVERLAY_TILES: Set<string> = new Set(
  AGENT_SEATS
    .filter(s => s.seatDir === Direction.UP)
    .map(s => tileKey(s.seatCol, s.seatRow)),
);

// ═══════════════════════════════════════════════════════════════════
// LOUNGE ZONE (for idle wandering)
// ═══════════════════════════════════════════════════════════════════
const loungeRoom = ROOMS.find(r => r.id === 'lounge')!;
export const LOUNGE_ZONE = {
  c1: loungeRoom.c1,
  r1: loungeRoom.r1,
  c2: loungeRoom.c2,
  r2: loungeRoom.r2,
};
