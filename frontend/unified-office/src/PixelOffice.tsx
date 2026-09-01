import { useCallback, useEffect, useRef, useState } from 'react';

// ═══════════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════════
const T = 16; // tile size in world pixels
const COLS = 42;
const ROWS = 34;
const WORLD_W = COLS * T;
const WORLD_H = ROWS * T;

// Character sprite frame dimensions (from spritesheet 112×96 = 7×4 grid)
const CHAR_FRAME_W = 16;
const CHAR_FRAME_H = 24;

// Colors
const VOID_COLOR = '#0e0e14';
const WALL_TOP_COLOR = '#3a3a5c';
const WALL_FACE_COLOR = '#2c2c48';
const ATLAS_GLOW = '#ffd700';

// ═══════════════════════════════════════════════════════════════════
// ROOM DEFINITIONS (interior tile ranges, inclusive)
// ═══════════════════════════════════════════════════════════════════
interface RoomDef {
  id: string;
  name: string;
  c1: number; r1: number; // top-left interior tile
  c2: number; r2: number; // bottom-right interior tile
  floor: number;          // floor tile index (0-8)
  tint: string;           // floor color tint (applied as overlay)
  wallTint: string;       // wall color for this room
  labelColor: string;
  labelX: number; labelY: number; // label position in tile coords
  labelRotation?: number; // optional rotation in degrees (e.g. -90 for vertical)
}

// ═══════════════════════════════════════════════════════════════════
// HOW TO ADJUST ROOM LABELS:
//   labelX  = horizontal tile column (multiply by 16 to get pixel position)
//   labelY  = vertical tile row (multiply by 16 to get pixel position)
//   labelColor = CSS color string for the label text
//
// To move a label RIGHT → increase labelX
// To move a label LEFT  → decrease labelX
// To move a label DOWN  → increase labelY
// To move a label UP    → decrease labelY
// ═══════════════════════════════════════════════════════════════════
const ROOMS: RoomDef[] = [
  // ── Top Row ──  (rooms span rows 1-10, labels placed at row 2 to avoid wall furniture)
  { id: 'research',     name: 'Research',       c1: 1,  r1: 1,  c2: 12, r2: 10, floor: 1, tint: 'rgba(100,190,190,0.45)', wallTint: '#3d5a5a', labelColor: '#7ecfcf', labelX: 3.8,  labelY: 0.4 },
  { id: 'planning',     name: 'Planning',       c1: 15, r1: 1,  c2: 26, r2: 10, floor: 3, tint: 'rgba(120,160,210,0.40)', wallTint: '#3a4a6a', labelColor: '#a5b4fc', labelX: 17.6, labelY: 0.4 },
  { id: 'resilience',   name: 'Resilience',     c1: 29, r1: 1,  c2: 40, r2: 10, floor: 5, tint: 'rgba(100,200,140,0.38)', wallTint: '#3a5a4a', labelColor: '#86efac', labelX: 31.4, labelY: 0.4 },
  // ── Middle Row ── (rooms span rows 13-22, labels at row 14)
  //   Strategy & Architecture: rotated labels on inner walls facing Atlas
  //   labelRotation: -90 = text reads upward (for left room's right wall)
  //   labelRotation:  90 = text reads downward (for right room's left wall)
  { id: 'strategy',     name: 'Strategy',    c1: 1,  r1: 13, c2: 12, r2: 22, floor: 4, tint: 'rgba(200,130,130,0.35)', wallTint: '#5a3a3a', labelColor: '#fca5a5', labelX: 0.61, labelY: 20, labelRotation: -90 },
  { id: 'atlas',        name: "Executive",       c1: 15, r1: 13, c2: 26, r2: 22, floor: 8, tint: 'rgba(180,160,100,0.35)', wallTint: '#4a4530', labelColor: '#ffd700', labelX: 18.5, labelY: 21.6 },
  { id: 'architecture', name: 'Architecture',   c1: 29, r1: 13, c2: 40, r2: 22, floor: 2, tint: 'rgba(160,140,210,0.38)', wallTint: '#44385a', labelColor: '#c4b5fd', labelX: 41.5, labelY: 15, labelRotation: 90 },
  // ── Bottom Lounge ── (rooms span rows 25-32, label at row 26)
  { id: 'lounge',       name: 'Break Lounge',         c1: 1,  r1: 25, c2: 40, r2: 32, floor: 6, tint: 'rgba(180,170,120,0.32)', wallTint: '#4a4535', labelColor: '#fde68a', labelX: 19, labelY: 32 },
];

// ═══════════════════════════════════════════════════════════════════
// DOOR OPENINGS (tile coords where wall is replaced by floor)
// ═══════════════════════════════════════════════════════════════════
interface DoorDef { col: number; row: number; floor: number }

const DOORS: DoorDef[] = [
  // Vertical doors (between top & middle rows) - row 11-12 are divider
  { col: 6, row: 11, floor: 1 }, { col: 7, row: 11, floor: 1 },
  { col: 6, row: 12, floor: 1 }, { col: 7, row: 12, floor: 1 },
  { col: 20, row: 11, floor: 3 }, { col: 21, row: 11, floor: 3 },
  { col: 20, row: 12, floor: 3 }, { col: 21, row: 12, floor: 3 },
  { col: 34, row: 11, floor: 5 }, { col: 35, row: 11, floor: 5 },
  { col: 34, row: 12, floor: 5 }, { col: 35, row: 12, floor: 5 },
  // Vertical doors (between middle row & lounge) - row 23-24 are divider
  { col: 6, row: 23, floor: 4 }, { col: 7, row: 23, floor: 4 },
  { col: 6, row: 24, floor: 4 }, { col: 7, row: 24, floor: 4 },
  { col: 20, row: 23, floor: 8 }, { col: 21, row: 23, floor: 8 },
  { col: 20, row: 24, floor: 8 }, { col: 21, row: 24, floor: 8 },
  { col: 34, row: 23, floor: 2 }, { col: 35, row: 23, floor: 2 },
  { col: 34, row: 24, floor: 2 }, { col: 35, row: 24, floor: 2 },
  // Horizontal doors (between adjacent rooms) - col 13-14, col 27-28 are dividers
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
interface FurnitureDef {
  img: string;     // key to look up in FURN_PATHS
  col: number;     // world tile col
  row: number;     // world tile row
  mirror?: boolean; // flip horizontally
  depth?: number;   // override sort row for wall items (lower = further back)
  animated?: boolean; // for PCs that cycle on-frames
}

const FURNITURE: FurnitureDef[] = [
  // ════════════════════════════════════════════
  // RESEARCH CABIN (cols 1-12, rows 1-10)
  // ════════════════════════════════════════════
  // Wall decorations (row 1 = top wall area)
  { img: 'DOUBLE_BOOKSHELF', col: 2, row: 1, depth: 0 },
  { img: 'CLOCK', col: 5, row: 1, depth: 0 },
  { img: 'BOOKSHELF', col: 7, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 10, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING', col: 11, row: 1, depth: 0 },
  // Workstation row 1 (Mira + Ravi)
  { img: 'DESK_FRONT', col: 1, row: 3 },
  { img: 'PC_FRONT_ON', col: 2, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 2, row: 5 },
  { img: 'DESK_FRONT', col: 6, row: 3 },
  { img: 'PC_FRONT_ON', col: 7, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 7, row: 5 },
  // Workstation row 2 (Anika + Noor)
  { img: 'DESK_FRONT', col: 1, row: 7 },
  { img: 'PC_FRONT_ON', col: 2, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 2, row: 9 },
  { img: 'DESK_FRONT', col: 6, row: 7 },
  { img: 'PC_FRONT_ON', col: 7, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 7, row: 9 },
  // Decorations
  { img: 'PLANT', col: 11, row: 4 },
  { img: 'CACTUS', col: 11, row: 8 },
  { img: 'BIN', col: 10, row: 9 },

  // ════════════════════════════════════════════
  // PLANNING CABIN (cols 15-26, rows 1-10)
  // ════════════════════════════════════════════
  { img: 'WHITEBOARD', col: 16, row: 1, depth: 0 },
  { img: 'CLOCK', col: 19, row: 1, depth: 0 },
  { img: 'BOOKSHELF', col: 21, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 24, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING_2', col: 25, row: 1, depth: 0 },
  // Central meeting table area
  { img: 'TABLE_FRONT', col: 18, row: 4 },
  // Chairs around table
  { img: 'WOODEN_CHAIR_SIDE', col: 17, row: 5 },
  { img: 'WOODEN_CHAIR_SIDE', col: 17, row: 7 },
  { img: 'WOODEN_CHAIR_SIDE', col: 22, row: 5, mirror: true },
  { img: 'WOODEN_CHAIR_SIDE', col: 22, row: 7, mirror: true },
  // Side desks with PCs
  { img: 'DESK_FRONT', col: 15, row: 3 },
  { img: 'PC_FRONT_ON', col: 16, row: 3, animated: true },
  { img: 'DESK_FRONT', col: 23, row: 3 },
  { img: 'PC_FRONT_ON', col: 24, row: 3, animated: true },
  // Decorations
  { img: 'PLANT', col: 15, row: 9 },
  { img: 'PLANT_2', col: 25, row: 9 },

  // ════════════════════════════════════════════
  // RESILIENCE CABIN (cols 29-40, rows 1-10)
  // ════════════════════════════════════════════
  { img: 'BOOKSHELF', col: 30, row: 1, depth: 0 },
  { img: 'DOUBLE_BOOKSHELF', col: 33, row: 1, depth: 0 },
  { img: 'CLOCK', col: 36, row: 1, depth: 0 },
  { img: 'HANGING_PLANT', col: 38, row: 1, depth: 0 },
  { img: 'SMALL_PAINTING_2', col: 39, row: 1, depth: 0 },
  // Workstation row 1 (Zoya + Ishaan)
  { img: 'DESK_FRONT', col: 29, row: 3 },
  { img: 'PC_FRONT_ON', col: 30, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 30, row: 5 },
  { img: 'DESK_FRONT', col: 34, row: 3 },
  { img: 'PC_FRONT_ON', col: 35, row: 3, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 35, row: 5 },
  // Workstation row 2 (Leena + Arjun)
  { img: 'DESK_FRONT', col: 29, row: 7 },
  { img: 'PC_FRONT_ON', col: 30, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 30, row: 9 },
  { img: 'DESK_FRONT', col: 34, row: 7 },
  { img: 'PC_FRONT_ON', col: 35, row: 7, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 35, row: 9 },
  // Decorations
  { img: 'PLANT_2', col: 39, row: 4 },
  { img: 'CACTUS', col: 39, row: 8 },

  // ════════════════════════════════════════════
  // STRATEGY PLANNING (cols 1-12, rows 13-22)
  // ════════════════════════════════════════════
  { img: 'WHITEBOARD', col: 2, row: 13, depth: 12 },
  { img: 'LARGE_PAINTING', col: 5, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 8, row: 13, depth: 12 },
  { img: 'CLOCK', col: 11, row: 13, depth: 12 },
  { img: 'HANGING_PLANT', col: 12, row: 13, depth: 12 },
  // Top workstations (Helena, Vikram, Nisha) - 3 desks
  { img: 'DESK_FRONT', col: 1, row: 15 },
  { img: 'PC_FRONT_ON', col: 2, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 2, row: 17 },
  { img: 'DESK_FRONT', col: 5, row: 15 },
  { img: 'PC_FRONT_ON', col: 6, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 6, row: 17 },
  { img: 'DESK_FRONT', col: 9, row: 15 },
  { img: 'PC_FRONT_ON', col: 10, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 10, row: 17 },
  // Bottom workstations (Omar, Sofia)
  { img: 'DESK_FRONT', col: 2, row: 19 },
  { img: 'PC_FRONT_ON', col: 3, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 3, row: 21 },
  { img: 'DESK_FRONT', col: 7, row: 19 },
  { img: 'PC_FRONT_ON', col: 8, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 8, row: 21 },
  // Decorations
  { img: 'PLANT', col: 12, row: 15 },
  { img: 'PLANT_2', col: 1, row: 21 },

  // ════════════════════════════════════════════
  // ATLAS'S OFFICE (cols 15-26, rows 13-22)
  // ════════════════════════════════════════════
  { img: 'DOUBLE_BOOKSHELF', col: 16, row: 13, depth: 12 },
  { img: 'LARGE_PAINTING', col: 19, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 22, row: 13, depth: 12 },
  { img: 'CLOCK', col: 25, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING', col: 15, row: 13, depth: 12 },
  // Executive desk (centered)
  { img: 'DESK_FRONT', col: 19, row: 16 },
  { img: 'PC_FRONT_ON', col: 20, row: 16, animated: true }, // Always ON
  { img: 'CUSHIONED_CHAIR_FRONT', col: 20, row: 18 },
  // Guest area (left side)
  { img: 'SOFA_FRONT', col: 15, row: 17 },
  { img: 'COFFEE_TABLE', col: 15, row: 19 },
  { img: 'COFFEE', col: 16, row: 20 },
  // Large plants flanking the office
  { img: 'LARGE_PLANT', col: 15, row: 14 },
  { img: 'LARGE_PLANT', col: 25, row: 14 },
  { img: 'PLANT', col: 25, row: 21 },
  { img: 'SMALL_TABLE_FRONT', col: 24, row: 19 },
  { img: 'COFFEE', col: 25, row: 19 },

  // ════════════════════════════════════════════
  // ARCHITECTURE CABIN (cols 29-40, rows 13-22)
  // ════════════════════════════════════════════
  { img: 'WHITEBOARD', col: 30, row: 13, depth: 12 },
  { img: 'BOOKSHELF', col: 33, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING', col: 36, row: 13, depth: 12 },
  { img: 'HANGING_PLANT', col: 38, row: 13, depth: 12 },
  { img: 'SMALL_PAINTING_2', col: 39, row: 13, depth: 12 },
  // Workstations (Rohan, Priya)
  { img: 'DESK_FRONT', col: 29, row: 15 },
  { img: 'PC_FRONT_ON', col: 30, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 30, row: 17 },
  { img: 'DESK_FRONT', col: 34, row: 15 },
  { img: 'PC_FRONT_ON', col: 35, row: 15, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 35, row: 17 },
  // Workstation (Ethan)
  { img: 'DESK_FRONT', col: 31, row: 19 },
  { img: 'PC_FRONT_ON', col: 32, row: 19, animated: true },
  { img: 'CUSHIONED_CHAIR_FRONT', col: 32, row: 21 },
  // Decorations
  { img: 'PLANT', col: 39, row: 16 },
  { img: 'CACTUS', col: 29, row: 21 },
  { img: 'PLANT_2', col: 39, row: 20 },

  // ════════════════════════════════════════════
  // BREAK LOUNGE (cols 1-40, rows 25-32)
  // ════════════════════════════════════════════
  // Wall decorations
  { img: 'LARGE_PAINTING', col: 3, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 8, row: 25, depth: 24 },
  { img: 'SMALL_PAINTING', col: 14, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 20, row: 25, depth: 24 },
  { img: 'LARGE_PAINTING', col: 25, row: 25, depth: 24 },
  { img: 'HANGING_PLANT', col: 32, row: 25, depth: 24 },
  { img: 'SMALL_PAINTING_2', col: 37, row: 25, depth: 24 },
  // Left seating area
  { img: 'SOFA_FRONT', col: 3, row: 27 },
  { img: 'COFFEE_TABLE', col: 3, row: 29 },
  { img: 'COFFEE', col: 4, row: 29 },
  { img: 'SOFA_BACK', col: 3, row: 31 },
  // Center seating area
  { img: 'SOFA_SIDE', col: 14, row: 28 },
  { img: 'COFFEE_TABLE', col: 16, row: 28 },
  { img: 'SOFA_SIDE', col: 18, row: 28, mirror: true },
  { img: 'COFFEE', col: 17, row: 29 },
  // Right area - bench & table
  { img: 'SMALL_TABLE_FRONT', col: 30, row: 28 },
  { img: 'WOODEN_BENCH', col: 30, row: 30 },
  { img: 'WOODEN_BENCH', col: 31, row: 30 },
  { img: 'WOODEN_CHAIR_FRONT', col: 30, row: 27 },
  { img: 'WOODEN_CHAIR_FRONT', col: 32, row: 27 },
  // Right reading nook
  { img: 'SOFA_FRONT', col: 36, row: 28 },
  { img: 'SMALL_TABLE_FRONT', col: 36, row: 30 },
  // Plants & decor
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
// AGENT DEFINITIONS
// ═══════════════════════════════════════════════════════════════════
interface AgentDef {
  name: string;
  role: string;
  room: string;
  charIdx: number; // 0-5, selects character sprite
  col: number;
  row: number;
  isExecutive?: boolean;
}

const AGENTS: AgentDef[] = [
  // Research Cabin
  { name: 'Mira', role: 'Lead Researcher', room: 'research', charIdx: 0, col: 2, row: 5 },
  { name: 'Ravi', role: 'Data Analyst', room: 'research', charIdx: 1, col: 7, row: 5 },
  { name: 'Anika', role: 'Market Analyst', room: 'research', charIdx: 2, col: 2, row: 9 },
  { name: 'Noor', role: 'Trend Spotter', room: 'research', charIdx: 3, col: 7, row: 9 },
  // Planning Cabin
  { name: 'Aanya', role: 'Planning Lead', room: 'planning', charIdx: 4, col: 17, row: 5 },
  { name: 'Dev', role: 'Demand Planner', room: 'planning', charIdx: 5, col: 22, row: 5 },
  { name: 'Kabir', role: 'Supply Planner', room: 'planning', charIdx: 0, col: 17, row: 7 },
  { name: 'Tara', role: 'Capacity Analyst', room: 'planning', charIdx: 1, col: 22, row: 7 },
  // Resilience Cabin
  { name: 'Zoya', role: 'Risk Assessor', room: 'resilience', charIdx: 2, col: 30, row: 5 },
  { name: 'Ishaan', role: 'Continuity Planner', room: 'resilience', charIdx: 3, col: 35, row: 5 },
  { name: 'Leena', role: 'Crisis Coordinator', room: 'resilience', charIdx: 4, col: 30, row: 9 },
  { name: 'Arjun', role: 'Recovery Specialist', room: 'resilience', charIdx: 5, col: 35, row: 9 },
  // Strategy Planning
  { name: 'Helena', role: 'Strategy Lead', room: 'strategy', charIdx: 0, col: 2, row: 17 },
  { name: 'Vikram', role: 'Business Strategist', room: 'strategy', charIdx: 1, col: 6, row: 17 },
  { name: 'Nisha', role: 'Portfolio Analyst', room: 'strategy', charIdx: 2, col: 10, row: 17 },
  { name: 'Omar', role: 'Growth Planner', room: 'strategy', charIdx: 3, col: 3, row: 21 },
  { name: 'Sofia', role: 'Innovation Scout', room: 'strategy', charIdx: 4, col: 8, row: 21 },
  // Atlas (Executive)
  { name: 'Atlas', role: 'Executive Orchestrator', room: 'atlas', charIdx: 5, col: 20, row: 18, isExecutive: true },
  // Architecture Cabin
  { name: 'Rohan', role: 'System Architect', room: 'architecture', charIdx: 0, col: 30, row: 17 },
  { name: 'Priya', role: 'Platform Engineer', room: 'architecture', charIdx: 1, col: 35, row: 17 },
  { name: 'Ethan', role: 'Infrastructure Lead', room: 'architecture', charIdx: 2, col: 32, row: 21 },
];

// ═══════════════════════════════════════════════════════════════════
// ASSET PATH MAP
// ═══════════════════════════════════════════════════════════════════
const PA = '/assets/pixel-agents'; // base path

const FURN_PATHS: Record<string, string> = {
  'DESK_FRONT': `${PA}/furniture/DESK/DESK_FRONT.png`,
  'DESK_SIDE': `${PA}/furniture/DESK/DESK_SIDE.png`,
  'PC_FRONT_ON': `${PA}/furniture/PC/PC_FRONT_ON_1.png`, // default frame
  'PC_FRONT_ON_1': `${PA}/furniture/PC/PC_FRONT_ON_1.png`,
  'PC_FRONT_ON_2': `${PA}/furniture/PC/PC_FRONT_ON_2.png`,
  'PC_FRONT_ON_3': `${PA}/furniture/PC/PC_FRONT_ON_3.png`,
  'PC_FRONT_OFF': `${PA}/furniture/PC/PC_FRONT_OFF.png`,
  'PC_SIDE': `${PA}/furniture/PC/PC_SIDE.png`,
  'CUSHIONED_CHAIR_FRONT': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_FRONT.png`,
  'CUSHIONED_CHAIR_BACK': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_BACK.png`,
  'CUSHIONED_CHAIR_SIDE': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_SIDE.png`,
  'BOOKSHELF': `${PA}/furniture/BOOKSHELF/BOOKSHELF.png`,
  'DOUBLE_BOOKSHELF': `${PA}/furniture/DOUBLE_BOOKSHELF/DOUBLE_BOOKSHELF.png`,
  'WHITEBOARD': `${PA}/furniture/WHITEBOARD/WHITEBOARD.png`,
  'CLOCK': `${PA}/furniture/CLOCK/CLOCK.png`,
  'COFFEE': `${PA}/furniture/COFFEE/COFFEE.png`,
  'COFFEE_TABLE': `${PA}/furniture/COFFEE_TABLE/COFFEE_TABLE.png`,
  'SOFA_FRONT': `${PA}/furniture/SOFA/SOFA_FRONT.png`,
  'SOFA_BACK': `${PA}/furniture/SOFA/SOFA_BACK.png`,
  'SOFA_SIDE': `${PA}/furniture/SOFA/SOFA_SIDE.png`,
  'LARGE_PAINTING': `${PA}/furniture/LARGE_PAINTING/LARGE_PAINTING.png`,
  'SMALL_PAINTING': `${PA}/furniture/SMALL_PAINTING/SMALL_PAINTING.png`,
  'SMALL_PAINTING_2': `${PA}/furniture/SMALL_PAINTING_2/SMALL_PAINTING_2.png`,
  'PLANT': `${PA}/furniture/PLANT/PLANT.png`,
  'PLANT_2': `${PA}/furniture/PLANT_2/PLANT_2.png`,
  'LARGE_PLANT': `${PA}/furniture/LARGE_PLANT/LARGE_PLANT.png`,
  'HANGING_PLANT': `${PA}/furniture/HANGING_PLANT/HANGING_PLANT.png`,
  'CACTUS': `${PA}/furniture/CACTUS/CACTUS.png`,
  'BIN': `${PA}/furniture/BIN/BIN.png`,
  'POT': `${PA}/furniture/POT/POT.png`,
  'TABLE_FRONT': `${PA}/furniture/TABLE_FRONT/TABLE_FRONT.png`,
  'SMALL_TABLE_FRONT': `${PA}/furniture/SMALL_TABLE/SMALL_TABLE_FRONT.png`,
  'WOODEN_CHAIR_SIDE': `${PA}/furniture/WOODEN_CHAIR/WOODEN_CHAIR_SIDE.png`,
  'WOODEN_CHAIR_FRONT': `${PA}/furniture/WOODEN_CHAIR/WOODEN_CHAIR_FRONT.png`,
  'WOODEN_BENCH': `${PA}/furniture/WOODEN_BENCH/WOODEN_BENCH.png`,
  'CUSHIONED_BENCH': `${PA}/furniture/CUSHIONED_BENCH/CUSHIONED_BENCH.png`,
};

// ═══════════════════════════════════════════════════════════════════
// TILE GRID BUILDER
// ═══════════════════════════════════════════════════════════════════
type TileInfo = { type: 'void' } | { type: 'wall' } | { type: 'floor'; floorIdx: number };

function buildGrid(): TileInfo[][] {
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

const GRID = buildGrid();

// ═══════════════════════════════════════════════════════════════════
// ASSET LOADER
// ═══════════════════════════════════════════════════════════════════
function loadImg(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(img); // graceful fallback
    img.src = src;
  });
}

interface AssetBundle {
  floors: HTMLImageElement[];
  wall: HTMLImageElement;
  carpets: HTMLImageElement[];
  characters: HTMLImageElement[];
  furniture: Record<string, HTMLImageElement>;
}

async function loadAllAssets(): Promise<AssetBundle> {
  // Floor tiles
  const floorPromises = Array.from({ length: 9 }, (_, i) =>
    loadImg(`${PA}/floors/floor_${i}.png`)
  );
  // Wall tile
  const wallPromise = loadImg(`${PA}/walls/wall_0.png`);
  // Carpets
  const carpetPromises = Array.from({ length: 3 }, (_, i) =>
    loadImg(`${PA}/carpets/carpet_${i}.png`)
  );
  // Characters
  const charPromises = Array.from({ length: 6 }, (_, i) =>
    loadImg(`${PA}/characters/char_${i}.png`)
  );
  // Furniture
  const furnEntries = Object.entries(FURN_PATHS);
  const furnPromises = furnEntries.map(([, path]) => loadImg(path));

  const [floors, wall, carpets, characters, ...furnImgs] = await Promise.all([
    Promise.all(floorPromises),
    wallPromise,
    Promise.all(carpetPromises),
    Promise.all(charPromises),
    ...furnPromises,
  ]);

  const furniture: Record<string, HTMLImageElement> = {};
  furnEntries.forEach(([key], i) => {
    furniture[key] = furnImgs[i];
  });

  return { floors, wall, carpets, characters, furniture };
}

// ═══════════════════════════════════════════════════════════════════
// RENDERING ENGINE
// ═══════════════════════════════════════════════════════════════════

function renderFrame(
  ctx: CanvasRenderingContext2D,
  assets: AssetBundle,
  zoom: number,
  panX: number,
  panY: number,
  time: number,
  hoveredAgent: AgentDef | null,
  canvasW: number,
  canvasH: number,
) {
  const dpr = window.devicePixelRatio || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Clear canvas
  ctx.fillStyle = VOID_COLOR;
  ctx.fillRect(0, 0, canvasW, canvasH);

  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, zoom);
  ctx.imageSmoothingEnabled = false;

  // ── Helper: find room for a tile ──────────────────────
  function findRoomForTile(c: number, r: number): RoomDef | undefined {
    return ROOMS.find(rm => c >= rm.c1 && c <= rm.c2 && r >= rm.r1 && r <= rm.r2);
  }
  function findNearestRoom(c: number, r: number): RoomDef | undefined {
    // For wall tiles, find adjacent room
    return findRoomForTile(c, r + 1) || findRoomForTile(c, r - 1) ||
      findRoomForTile(c + 1, r) || findRoomForTile(c - 1, r) ||
      findRoomForTile(c, r);
  }

  // ── 1. Draw floor tiles ───────────────────────────────
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = GRID[r][c];
      if (tile.type === 'floor') {
        const floorImg = assets.floors[tile.floorIdx];
        const px = c * T, py = r * T;
        if (floorImg?.complete && floorImg.naturalWidth > 0) {
          ctx.drawImage(floorImg, 0, 0, T, T, px, py, T, T);
        } else {
          ctx.fillStyle = '#4a6b5e';
          ctx.fillRect(px, py, T, T);
        }
        // Apply room color tint overlay
        const room = findRoomForTile(c, r);
        if (room) {
          ctx.fillStyle = room.tint;
          ctx.fillRect(px, py, T, T);
        }
      }
    }
  }

  // ── 2. Draw wall tiles ────────────────────────────────
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = GRID[r][c];
      if (tile.type === 'wall') {
        const px = c * T, py = r * T;
        const hasFloorBelow = r + 1 < ROWS && GRID[r + 1][c].type === 'floor';
        const hasFloorAbove = r - 1 >= 0 && GRID[r - 1][c].type === 'floor';
        const nearRoom = findNearestRoom(c, r);
        const wallBase = nearRoom?.wallTint || WALL_FACE_COLOR;

        if (hasFloorBelow && !hasFloorAbove) {
          // Top wall — lighter, like a shelf ledge
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          // Highlight edge
          ctx.fillStyle = 'rgba(255,255,255,0.08)';
          ctx.fillRect(px, py + T - 2, T, 2);
          // Top edge shadow
          ctx.fillStyle = 'rgba(0,0,0,0.15)';
          ctx.fillRect(px, py, T, 1);
        } else if (!hasFloorBelow && hasFloorAbove) {
          // Bottom wall — darker
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(0,0,0,0.2)';
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(255,255,255,0.06)';
          ctx.fillRect(px, py, T, 1);
        } else {
          // Side wall or corner
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(0,0,0,0.1)';
          ctx.fillRect(px, py, T, T);
          // Subtle vertical edges
          ctx.fillStyle = 'rgba(255,255,255,0.04)';
          ctx.fillRect(px, py, 1, T);
          ctx.fillStyle = 'rgba(0,0,0,0.08)';
          ctx.fillRect(px + T - 1, py, 1, T);
        }
      }
    }
  }

  // ── 3. Draw Atlas's Office glow border ────────────────
  const atlasRoom = ROOMS.find(r => r.id === 'atlas')!;
  const glowAlpha = 0.3 + 0.15 * Math.sin(time * 2);
  const glowX = (atlasRoom.c1 - 1) * T;
  const glowY = (atlasRoom.r1 - 1) * T;
  const glowW = (atlasRoom.c2 - atlasRoom.c1 + 3) * T;
  const glowH = (atlasRoom.r2 - atlasRoom.r1 + 3) * T;
  ctx.strokeStyle = ATLAS_GLOW;
  ctx.globalAlpha = glowAlpha;
  ctx.lineWidth = 3;
  ctx.strokeRect(glowX + 1.5, glowY + 1.5, glowW - 3, glowH - 3);
  // Inner glow
  ctx.strokeStyle = ATLAS_GLOW;
  ctx.globalAlpha = glowAlpha * 0.4;
  ctx.lineWidth = 6;
  ctx.strokeRect(glowX + 3, glowY + 3, glowW - 6, glowH - 6);
  ctx.globalAlpha = 1;
  ctx.lineWidth = 1;

  // ── 4. Collect all drawables for depth sorting ────────
  interface Drawable {
    sortRow: number;
    draw: () => void;
  }
  const drawables: Drawable[] = [];

  // Add furniture
  for (const furn of FURNITURE) {
    const sortRow = furn.depth ?? furn.row;
    drawables.push({
      sortRow,
      draw: () => {
        let imgKey = furn.img;
        // Handle animated PCs - cycle through frames
        if (furn.animated && imgKey === 'PC_FRONT_ON') {
          const frame = Math.floor(time * 2) % 3;
          imgKey = `PC_FRONT_ON_${frame + 1}`;
        }
        const img = assets.furniture[imgKey];
        if (!img?.complete || img.naturalWidth === 0) return;

        const px = furn.col * T;
        const py = furn.row * T;
        const iw = img.naturalWidth;
        const ih = img.naturalHeight;

        ctx.save();
        if (furn.mirror) {
          ctx.translate(px + iw, py);
          ctx.scale(-1, 1);
          ctx.drawImage(img, 0, 0, iw, ih);
        } else {
          ctx.drawImage(img, px, py, iw, ih);
        }
        ctx.restore();
      },
    });
  }

  // Add agents
  for (const agent of AGENTS) {
    drawables.push({
      sortRow: agent.row,
      draw: () => {
        const charImg = assets.characters[agent.charIdx];
        if (!charImg?.complete || charImg.naturalWidth === 0) return;

        const px = agent.col * T;
        const py = agent.row * T;

        // Draw character frame (first frame of south-facing row)
        // Spritesheet: 112×96 = 7 cols × 4 rows, each frame 16×24
        const srcX = 0;
        const srcY = 0; // row 0 = south/front
        ctx.drawImage(
          charImg,
          srcX, srcY, CHAR_FRAME_W, CHAR_FRAME_H,
          px, py - CHAR_FRAME_H + T, CHAR_FRAME_W, CHAR_FRAME_H
        );

        // Draw name label
        ctx.save();
        ctx.font = '4px "Press Start 2P", monospace';
        ctx.textAlign = 'center';
        const labelX = px + CHAR_FRAME_W / 2;
        const labelY = py + T + 5;

        // Label background
        const metrics = ctx.measureText(agent.name);
        const labelW = metrics.width + 4;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(labelX - labelW / 2, labelY - 4, labelW, 7);

        // Name text
        if (agent.isExecutive) {
          ctx.fillStyle = ATLAS_GLOW;
        } else {
          ctx.fillStyle = '#ffffff';
        }
        ctx.fillText(agent.name, labelX, labelY);

        // Executive badge / active indicator
        if (agent.isExecutive) {
          // Pulsing glow circle
          const pulseR = 3 + Math.sin(time * 3) * 1;
          ctx.beginPath();
          ctx.arc(px + CHAR_FRAME_W / 2, py - CHAR_FRAME_H + T - 4, pulseR, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 215, 0, ${0.5 + 0.3 * Math.sin(time * 3)})`;
          ctx.fill();
          ctx.strokeStyle = ATLAS_GLOW;
          ctx.lineWidth = 0.5;
          ctx.stroke();

          // "ACTIVE" label
          ctx.font = '3px "Press Start 2P", monospace';
          ctx.fillStyle = '#00ff88';
          ctx.textAlign = 'center';
          ctx.fillText('⚡ ACTIVE', labelX, labelY + 8);
        }

        // Hovered agent tooltip
        if (hoveredAgent && hoveredAgent.name === agent.name) {
          const tooltipY = py - CHAR_FRAME_H + T - 12;
          // Speech bubble background
          ctx.fillStyle = 'rgba(20, 24, 36, 0.92)';
          const roleText = agent.role;
          ctx.font = '3px "Press Start 2P", monospace';
          const rMetrics = ctx.measureText(roleText);
          const tw = Math.max(rMetrics.width + 8, 40);
          ctx.fillRect(labelX - tw / 2, tooltipY - 10, tw, 12);
          ctx.strokeStyle = agent.isExecutive ? ATLAS_GLOW : '#5070a0';
          ctx.lineWidth = 0.5;
          ctx.strokeRect(labelX - tw / 2, tooltipY - 10, tw, 12);
          ctx.fillStyle = '#95d8ff';
          ctx.textAlign = 'center';
          ctx.fillText(roleText, labelX, tooltipY - 3);
          // Tail
          ctx.fillStyle = 'rgba(20, 24, 36, 0.92)';
          ctx.beginPath();
          ctx.moveTo(labelX - 3, tooltipY + 2);
          ctx.lineTo(labelX, tooltipY + 5);
          ctx.lineTo(labelX + 3, tooltipY + 2);
          ctx.fill();
        }

        ctx.restore();
      },
    });
  }

  // Sort by row for proper depth ordering
  drawables.sort((a, b) => a.sortRow - b.sortRow);

  // Draw all drawables
  for (const d of drawables) {
    d.draw();
  }

  // ── 5. Draw room labels ───────────────────────────────
  ctx.save();
  ctx.font = '7px "Press Start 2P", monospace';
  ctx.textAlign = 'left';
  for (const room of ROOMS) {
    if (!room.name) continue; // skip empty labels
    const lx = room.labelX * T;
    const ly = room.labelY * T;
    const rot = room.labelRotation || 0;

    // Measure text for background panel
    const metrics = ctx.measureText(room.name);
    const textW = metrics.width;
    const padX = 4;
    const padY = 3;
    const bgW = textW + padX * 2;
    const bgH = 7 + padY * 2;

    ctx.save();
    ctx.translate(lx, ly);
    if (rot !== 0) {
      ctx.rotate((rot * Math.PI) / 180);
    }

    const bgX = -padX;
    const bgY = -padY - 1;

    // Dark background panel
    ctx.fillStyle = 'rgba(10, 12, 24, 0.82)';
    ctx.fillRect(bgX, bgY, bgW, bgH);

    // Colored border (matches the room label color)
    ctx.strokeStyle = room.labelColor;
    ctx.globalAlpha = 0.6;
    ctx.lineWidth = 1;
    ctx.strokeRect(bgX + 0.5, bgY + 0.5, bgW - 1, bgH - 1);
    ctx.globalAlpha = 1;

    // Label text
    ctx.fillStyle = room.labelColor;
    ctx.fillText(room.name, 0, 6);

    ctx.restore();
  }
  ctx.restore();

  // ── 6. Draw grid lines (subtle) ───────────────────────
  ctx.save();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
  ctx.lineWidth = 0.5;
  for (let r = 0; r <= ROWS; r++) {
    for (let c = 0; c <= COLS; c++) {
      if (r < ROWS && c < COLS && GRID[r][c].type === 'floor') {
        ctx.strokeRect(c * T, r * T, T, T);
      }
    }
  }
  ctx.restore();

  ctx.restore(); // Undo zoom + pan transform

  // ── 7. Draw minimap ───────────────────────────────────
  const mmScale = 3; // pixels per tile in minimap
  const mmW = COLS * mmScale;
  const mmH = ROWS * mmScale;
  const mmX = canvasW - mmW - 12;
  const mmY = canvasH - mmH - 12;

  // Minimap background
  ctx.fillStyle = 'rgba(10, 10, 18, 0.85)';
  ctx.fillRect(mmX - 2, mmY - 2, mmW + 4, mmH + 4);
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
  ctx.lineWidth = 1;
  ctx.strokeRect(mmX - 2, mmY - 2, mmW + 4, mmH + 4);

  // Minimap tiles
  const roomColors: Record<string, string> = {
    research: '#7ecfcf',
    planning: '#a5b4fc',
    resilience: '#86efac',
    strategy: '#fca5a5',
    atlas: '#ffd700',
    architecture: '#c4b5fd',
    lounge: '#fde68a',
  };

  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = GRID[r][c];
      if (tile.type === 'floor') {
        // Find room for color
        const room = ROOMS.find(rm => c >= rm.c1 && c <= rm.c2 && r >= rm.r1 && r <= rm.r2);
        ctx.fillStyle = room ? roomColors[room.id] || '#666' : '#555';
        ctx.globalAlpha = 0.5;
        ctx.fillRect(mmX + c * mmScale, mmY + r * mmScale, mmScale, mmScale);
        ctx.globalAlpha = 1;
      } else if (tile.type === 'wall') {
        ctx.fillStyle = '#444';
        ctx.globalAlpha = 0.5;
        ctx.fillRect(mmX + c * mmScale, mmY + r * mmScale, mmScale, mmScale);
        ctx.globalAlpha = 1;
      }
    }
  }

  // Minimap agent dots
  for (const agent of AGENTS) {
    ctx.fillStyle = agent.isExecutive ? '#ffd700' : '#ffffff';
    ctx.globalAlpha = 0.9;
    ctx.fillRect(
      mmX + agent.col * mmScale,
      mmY + agent.row * mmScale,
      mmScale, mmScale
    );
    ctx.globalAlpha = 1;
  }

  // Minimap viewport indicator
  const vpLeft = (-panX / zoom) / T * mmScale;
  const vpTop = (-panY / zoom) / T * mmScale;
  const vpW = (canvasW / zoom) / T * mmScale;
  const vpH = (canvasH / zoom) / T * mmScale;
  ctx.strokeStyle = '#ffffff';
  ctx.globalAlpha = 0.6;
  ctx.lineWidth = 1;
  ctx.strokeRect(mmX + vpLeft, mmY + vpTop, vpW, vpH);
  ctx.globalAlpha = 1;

  // ── 8. Draw status bar ────────────────────────────────
  ctx.save();
  ctx.fillStyle = 'rgba(10, 12, 20, 0.88)';
  ctx.fillRect(0, 0, canvasW, 32);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.fillRect(0, 31, canvasW, 1);

  // Title
  ctx.font = '10px "Press Start 2P", monospace';
  ctx.fillStyle = '#e7ecf7';
  ctx.textAlign = 'left';
  ctx.fillText('Supply Chain HQ', 12, 20);

  // Status indicators
  ctx.font = '8px "Press Start 2P", monospace';
  ctx.fillStyle = '#78f7b5';
  ctx.textAlign = 'right';
  ctx.fillText(`⚡ ${AGENTS.length} Agents`, canvasW - 180, 20);

  ctx.fillStyle = '#ffd700';
  ctx.fillText('Atlas: ACTIVE', canvasW - 12, 20);

  ctx.restore();

  // ── 9. Draw zoom indicator ────────────────────────────
  ctx.save();
  ctx.font = '8px "Press Start 2P", monospace';
  ctx.fillStyle = '#95d8ff';
  ctx.textAlign = 'left';
  ctx.fillText(`${Math.round(zoom * 100)}%`, 12, canvasH - 12);
  ctx.restore();
}

// ═══════════════════════════════════════════════════════════════════
// LOADING SCREEN
// ═══════════════════════════════════════════════════════════════════
function LoadingScreen() {
  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 100,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      background: VOID_COLOR, color: '#e7ecf7',
      fontFamily: '"Press Start 2P", monospace',
    }}>
      <div style={{ fontSize: 20, marginBottom: 24, color: '#ffd700' }}>
        Supply Chain HQ
      </div>
      <div style={{ fontSize: 10, marginBottom: 32, color: '#7ecfcf' }}>
        Loading Office Assets...
      </div>
      <div style={{
        width: 200, height: 8,
        background: '#1a1e2e', border: '1px solid #2a3448',
        overflow: 'hidden',
      }}>
        <div style={{
          width: '60%', height: '100%',
          background: 'linear-gradient(90deg, #ffd700, #ff8800)',
          animation: 'loadPulse 1.5s ease-in-out infinite',
        }} />
      </div>
      <style>{`
        @keyframes loadPulse {
          0%, 100% { width: 30%; opacity: 0.6; }
          50% { width: 90%; opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════
export default function PixelOffice() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [assets, setAssets] = useState<AssetBundle | null>(null);
  const [loading, setLoading] = useState(true);

  // Camera state (refs for perf — don't trigger re-renders)
  const zoomRef = useRef(3);
  const panRef = useRef({ x: 0, y: 0 });
  const isPanning = useRef(false);
  const lastMouse = useRef({ x: 0, y: 0 });
  const hoveredAgentRef = useRef<AgentDef | null>(null);
  const [, forceRender] = useState(0);

  // ── Asset Loading ───────────────────────────────────
  useEffect(() => {
    loadAllAssets().then((bundle) => {
      setAssets(bundle);
      setLoading(false);
    });
  }, []);

  // ── Initial Centering ───────────────────────────────
  useEffect(() => {
    if (!assets) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cw = canvas.clientWidth;
    const ch = canvas.clientHeight;
    // Calculate zoom to fit the office
    const fitZoom = Math.min(cw / WORLD_W, (ch - 32) / WORLD_H) * 0.92;
    zoomRef.current = Math.max(2, Math.min(5, fitZoom));
    // Center the office
    panRef.current = {
      x: (cw - WORLD_W * zoomRef.current) / 2,
      y: (ch - WORLD_H * zoomRef.current) / 2 + 16,
    };
  }, [assets]);

  // ── Animation Loop ──────────────────────────────────
  useEffect(() => {
    if (!assets) return;
    let animId: number;

    const loop = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const cw = canvas.clientWidth;
      const ch = canvas.clientHeight;

      if (canvas.width !== cw * dpr || canvas.height !== ch * dpr) {
        canvas.width = cw * dpr;
        canvas.height = ch * dpr;
      }

      renderFrame(
        ctx, assets,
        zoomRef.current,
        panRef.current.x,
        panRef.current.y,
        performance.now() / 1000,
        hoveredAgentRef.current,
        cw, ch
      );

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [assets]);

  // ── Zoom (mouse wheel) ─────────────────────────────
  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const oldZoom = zoomRef.current;
    const delta = e.deltaY > 0 ? -0.25 : 0.25;
    const newZoom = Math.max(1.5, Math.min(8, oldZoom + delta));

    // Zoom toward mouse position
    const worldX = (mx - panRef.current.x) / oldZoom;
    const worldY = (my - panRef.current.y) / oldZoom;
    panRef.current.x = mx - worldX * newZoom;
    panRef.current.y = my - worldY * newZoom;
    zoomRef.current = newZoom;
  }, []);

  // ── Pan (mouse drag) ───────────────────────────────
  const onPointerDown = useCallback((e: React.PointerEvent) => {
    isPanning.current = true;
    lastMouse.current = { x: e.clientX, y: e.clientY };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (isPanning.current) {
      panRef.current.x += e.clientX - lastMouse.current.x;
      panRef.current.y += e.clientY - lastMouse.current.y;
      lastMouse.current = { x: e.clientX, y: e.clientY };
    }

    // Check hover on agents
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const worldX = (mx - panRef.current.x) / zoomRef.current;
    const worldY = (my - panRef.current.y) / zoomRef.current;

    let found: AgentDef | null = null;
    for (const agent of AGENTS) {
      const ax = agent.col * T;
      const ay = agent.row * T - CHAR_FRAME_H + T;
      if (worldX >= ax && worldX <= ax + CHAR_FRAME_W &&
        worldY >= ay && worldY <= ay + CHAR_FRAME_H + 8) {
        found = agent;
        break;
      }
    }

    if (found !== hoveredAgentRef.current) {
      hoveredAgentRef.current = found;
      forceRender(n => n + 1);
    }
  }, []);

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    isPanning.current = false;
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  }, []);

  // ── Cursor style ────────────────────────────────────
  const cursorStyle = hoveredAgentRef.current ? 'pointer' : isPanning.current ? 'grabbing' : 'grab';

  return (
    <div id="pixel-office-root" style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: VOID_COLOR, position: 'relative' }}>
      {loading && <LoadingScreen />}
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
          cursor: cursorStyle,
          imageRendering: 'pixelated',
        }}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
      />
      {/* Keyboard hint overlay */}
      <div style={{
        position: 'absolute', bottom: 8, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: 12, alignItems: 'center',
        padding: '4px 12px',
        background: 'rgba(10, 12, 20, 0.75)',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 4,
        fontFamily: '"Press Start 2P", monospace',
        fontSize: 7,
        color: '#666',
        pointerEvents: 'none',
      }}>
        <span>🖱️ Scroll to Zoom</span>
        <span>•</span>
        <span>✋ Drag to Pan</span>
        <span>•</span>
        <span>👆 Hover Agents for Details</span>
      </div>
    </div>
  );
}
