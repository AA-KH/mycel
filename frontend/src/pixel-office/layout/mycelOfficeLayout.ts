/**
 * Mycel AI Company — programmatic office layout.
 *
 * Reproduces the reference floor plan:
 *   Top row:    CREATIVE | DEVELOPER | FINANCE | LEGAL
 *   Mid band:   MARKETING | central hallway (Orchestrator + HR desks) | RESEARCH
 *   Bottom:     OPERATIONS | BREAK LOUNGE | entrance | SERVER ROOM | TOILETS
 *
 * Built programmatically (painter API) instead of a hand-edited 2,000-tile
 * JSON so rooms/desks can be tweaked in one place.
 *
 * Design notes (matching the reference art):
 *   · Department rooms use restrained 2 × 2 workstation grids with identical
 *     orientation, generous aisles, and storage kept against perimeter walls.
 *   · Every room's top wall carries a curated art band — boards, framed photos,
 *     shelves, and bookcases — without competing with the clean desk rhythm.
 *   · Floors are picked per-zone from the grayscale tile set: plank/brick for
 *     the wood hallways, checkerboard for the lounge, small ceramic for the
 *     toilets, tight grid for the server room.
 */

import type { ColorValue } from '../../components/ui/types';
import type {
  AreaDefinition,
  OfficeLayout,
  PlacedFurniture,
  TileType as TileTypeVal,
} from '../types';
import { TileType } from '../types';

// ── Grid ─────────────────────────────────────────────────────────
export const MYCEL_COLS = 46;
export const MYCEL_ROWS = 34;

// ── Named tiles (exported for the agent lifecycle) ───────────────
/** Outside tile where new hires materialize before walking in. */
export const ENTRANCE_TILE = { col: 22, row: 32 };
/** Tile just inside the entrance — the "gate" where hires pause. */
export const GATE_TILE = { col: 22, row: 30 };
/** Tile in front of the HR desk where hires check in. */
export const HR_DESK_TILE = { col: 22, row: 21 };
/** Tile in front of the Orchestrator desk where hires get routed. */
export const ORCHESTRATOR_TILE = { col: 22, row: 16 };
/** Outside spot for smoke breaks (sutta corner, right of the entrance). */
export const SMOKING_SPOT = { col: 27, row: 32 };
/** Free-standing lounge tiles for chai / reels / chatting breaks. */
export const LOUNGE_TILES: Array<{ col: number; row: number }> = [
  { col: 4, row: 30 },
  { col: 7, row: 29 },
  { col: 11, row: 29 },
  { col: 13, row: 28 },
  { col: 9, row: 30 },
];

/** Seat tiles for the two company-level agents (chairs placed there). */
export const ORCHESTRATOR_SEAT_TILE = { col: 22, row: 13 };
export const HR_SEAT_TILE = { col: 22, row: 18 };

// ── Area labels ──────────────────────────────────────────────────
export const AREA_LABELS = {
  creative: 'Creative',
  developer: 'Developer',
  finance: 'Finance',
  legal: 'Legal',
  marketing: 'Marketing',
  research: 'Research',
  operations: 'Operations',
  lounge: 'Break Lounge',
  server: 'Server Room',
  toilets: 'Toilets',
  orchestrator: 'Orchestrator',
  hr: 'HR Agent',
  reception: 'Mycel AI Company',
} as const;

/** team id → Area labels, feed into OfficeState.setAreaMappings so
 *  findFreeSeat(team) naturally seats agents inside their department room. */
export const TEAM_AREA_MAP: Record<string, string[]> = {
  creative: [AREA_LABELS.creative],
  developer: [AREA_LABELS.developer],
  finance: [AREA_LABELS.finance],
  legal: [AREA_LABELS.legal],
  marketing: [AREA_LABELS.marketing],
  research: [AREA_LABELS.research],
  operations: [AREA_LABELS.operations],
};

// ── Wall + floor colors (dark reference theme) ───────────────────
/**
 * Near-flat dark navy shell. `colorize` + strong negative contrast collapses
 * the source wall sprite's light gray ramp into a narrow dark band, which is
 * what gives the reference art its heavy "cut-away building" look.
 */
const WALL_NAVY: ColorValue = { h: 226, s: 20, b: -68, c: -62, colorize: true };

/** Department floor: rich, saturated, distinctly darkened wash of the team hue
 *  so rooms pop against the near-black shell (reference art contrast). */
const teamFloor = (h: number, s = 38, b = -42): ColorValue => ({ h, s, b, c: 12, colorize: true });

const HALLWAY_WOOD: ColorValue = { h: 25, s: 34, b: -50, c: 16, colorize: true };
const LOBBY_WOOD: ColorValue = { h: 24, s: 32, b: -46, c: 14, colorize: true };
const LOUNGE_CHECKER: ColorValue = { h: 226, s: 8, b: 6, c: 46, colorize: true };
const SERVER_FLOOR: ColorValue = { h: 232, s: 16, b: -56, c: 12, colorize: true };
const TOILET_FLOOR: ColorValue = { h: 200, s: 16, b: 24, c: 10, colorize: true };
const PAVEMENT: ColorValue = { h: 222, s: 8, b: -48, c: 6, colorize: true };

const FLOOR_COLORS: Record<string, ColorValue> = {
  creative: teamFloor(272, 38, -40),
  developer: teamFloor(122, 34, -42),
  finance: teamFloor(38, 42, -38),
  legal: teamFloor(214, 38, -40),
  marketing: teamFloor(334, 38, -40),
  research: teamFloor(176, 34, -42),
  operations: teamFloor(26, 42, -40),
};

// ── Painter ──────────────────────────────────────────────────────
class Painter {
  tiles: TileTypeVal[];
  tileColors: Array<ColorValue | null>;
  areaTiles: Array<string | null>;
  furniture: PlacedFurniture[] = [];
  private uidCounter = 0;

  constructor() {
    const n = MYCEL_COLS * MYCEL_ROWS;
    this.tiles = new Array(n).fill(TileType.VOID) as TileTypeVal[];
    this.tileColors = new Array(n).fill(null) as Array<ColorValue | null>;
    this.areaTiles = new Array(n).fill(null) as Array<string | null>;
  }

  private idx(col: number, row: number): number {
    return row * MYCEL_COLS + col;
  }

  /** Fill an inclusive rect with a floor tile + color. */
  floor(x0: number, y0: number, x1: number, y1: number, tile: TileTypeVal, color: ColorValue) {
    for (let r = y0; r <= y1; r++) {
      for (let c = x0; c <= x1; c++) {
        const i = this.idx(c, r);
        this.tiles[i] = tile;
        this.tileColors[i] = color;
      }
    }
  }

  /** Set an inclusive rect to WALL. */
  wall(x0: number, y0: number, x1: number, y1: number) {
    for (let r = y0; r <= y1; r++) {
      for (let c = x0; c <= x1; c++) {
        const i = this.idx(c, r);
        this.tiles[i] = TileType.WALL;
        this.tileColors[i] = WALL_NAVY;
      }
    }
  }

  /** Carve a door: replace wall tiles with a floor tile + color. */
  door(x0: number, y0: number, x1: number, y1: number, tile: TileTypeVal, color: ColorValue) {
    this.floor(x0, y0, x1, y1, tile, color);
  }

  /** Assign an Area label to every FLOOR tile in an inclusive rect. */
  area(x0: number, y0: number, x1: number, y1: number, label: string) {
    for (let r = y0; r <= y1; r++) {
      for (let c = x0; c <= x1; c++) {
        const i = this.idx(c, r);
        if (this.tiles[i] !== TileType.WALL && this.tiles[i] !== TileType.VOID) {
          this.areaTiles[i] = label;
        }
      }
    }
  }

  furn(type: string, col: number, row: number, color?: ColorValue) {
    this.furniture.push({
      uid: `kb-${this.uidCounter++}`,
      type,
      col,
      row,
      ...(color ? { color } : {}),
    });
  }

  /** Place a run of wall-mounted props along one wall row: [[col, type], …]. */
  wallStrip(row: number, items: Array<[number, string]>) {
    for (const [col, type] of items) this.furn(type, col, row);
  }
}

/**
 * Oriented workstations — the monitor ALWAYS faces the seated agent, and rooms
 * mix all four facings so each department reads like a real office pod instead
 * of a copy-pasted grid (matching the reference art's varied desk rhythm).
 *
 * Four station builders — deskN / deskS / deskE / deskW — are combined into a
 * different arrangement per department (pods, benches, rows, U-shapes) so no
 * two rooms read the same.
 */
/** Agent sits ABOVE a 3×2 desk facing DOWN — monitor's back to the viewer. */
function deskS(p: Painter, col: number, row: number) {
  p.furn('CUSHIONED_CHAIR_FRONT', col + 1, row - 1);
  p.furn('DESK_FRONT', col, row);
  p.furn('PC_BACK', col + 1, row);
}

/** Agent sits BELOW a 3×2 desk facing UP — glowing screen toward the chair. */
function deskN(p: Painter, col: number, row: number) {
  p.furn('DESK_FRONT', col, row);
  p.furn('PC_FRONT_OFF', col + 1, row);
  p.furn('CUSHIONED_CHAIR_BACK', col + 1, row + 2);
}

/**
 * Vertical 1×4 side desk with the agent(s) on the LEFT facing RIGHT.
 * `seats` picks how many of the desk's two monitor slots are used.
 */
function deskE(p: Painter, col: number, row: number, seats: 1 | 2 = 2) {
  p.furn('DESK_SIDE', col, row);
  for (let i = 0; i < seats; i++) {
    const r = row + i * 2;
    p.furn('PC_SIDE', col, r);
    p.furn('CUSHIONED_CHAIR_SIDE', col - 1, r);
  }
}

/** Vertical 1×4 side desk with the agent(s) on the RIGHT facing LEFT. */
function deskW(p: Painter, col: number, row: number, seats: 1 | 2 = 2) {
  p.furn('DESK_SIDE', col, row);
  for (let i = 0; i < seats; i++) {
    const r = row + i * 2;
    p.furn('PC_SIDE:left', col, r);
    p.furn('CUSHIONED_CHAIR_SIDE:left', col + 1, r);
  }
}

/** Pink upholstery tint for the break-lounge sofas (reference art). */
const SOFA_PINK: ColorValue = { h: 341, s: 52, b: -2, c: 8, colorize: true };
/** Cool steel tint for the server-room maintenance row. */
const RACK_STEEL: ColorValue = { h: 232, s: -30, b: -30, c: 16 };
/** Warm wood tint for the lounge coffee bar counter. */
const BAR_WOOD: ColorValue = { h: 26, s: 20, b: -10, c: 10 };

export function buildMycelLayout(): OfficeLayout {
  const p = new Painter();
  // Tile pattern indices → grayscale sprites in assets/floors:
  //   1 flat · 2 large grout · 3 tight grid · 4 small ceramic
  //   5 mosaic · 6 thin plank · 7 wide plank · 8 fine check · 9 wide check
  const FLAT = TileType.FLOOR_1;
  const GRID = TileType.FLOOR_3;
  const CERAMIC = TileType.FLOOR_4;
  const MOSAIC = TileType.FLOOR_5;
  const PLANK = TileType.FLOOR_7;
  const CHECK = TileType.FLOOR_9;

  // ══ Floors ══════════════════════════════════════════════════
  // Top department rooms (interior rows 1–8)
  p.floor(1, 1, 10, 8, FLAT, FLOOR_COLORS.creative);
  p.floor(12, 1, 21, 8, FLAT, FLOOR_COLORS.developer);
  p.floor(23, 1, 32, 8, FLAT, FLOOR_COLORS.finance);
  p.floor(34, 1, 44, 8, FLAT, FLOOR_COLORS.legal);

  // Horizontal corridor under the top rooms (rows 10–11, full width)
  p.floor(1, 10, 44, 11, PLANK, HALLWAY_WOOD);

  // Marketing (interior cols 1–10, rows 13–19)
  p.floor(1, 13, 10, 19, FLAT, FLOOR_COLORS.marketing);
  // Research (interior cols 35–44, rows 13–19)
  p.floor(35, 13, 44, 19, FLAT, FLOOR_COLORS.research);
  // Central hallway (cols 12–33, rows 12–20)
  p.floor(12, 12, 33, 20, PLANK, HALLWAY_WOOD);

  // Operations (interior cols 1–12, rows 21–25)
  p.floor(1, 21, 12, 25, FLAT, FLOOR_COLORS.operations);
  // Central hallway continues (cols 14–25, rows 21–25)
  p.floor(14, 21, 25, 25, PLANK, HALLWAY_WOOD);
  // Server room (interior cols 27–32, rows 21–24)
  p.floor(27, 21, 32, 24, GRID, SERVER_FLOOR);
  // Right open area next to server room (cols 34–44, rows 21–25)
  p.floor(34, 21, 44, 25, PLANK, HALLWAY_WOOD);

  // Bottom hallway strip between lounge and toilets (cols 16–34, rows 26–30)
  p.floor(16, 26, 34, 30, PLANK, LOBBY_WOOD);

  // Break lounge — black/white checkerboard (interior cols 1–14, rows 27–30)
  p.floor(1, 27, 14, 30, CHECK, LOUNGE_CHECKER);

  // Toilets (interior cols 36–44, rows 27–30)
  p.floor(36, 27, 44, 30, CERAMIC, TOILET_FLOOR);

  // Outside pavement (rows 32–33, around the entrance)
  p.floor(17, 32, 29, 33, MOSAIC, PAVEMENT);

  // ══ Walls ═══════════════════════════════════════════════════
  // Outer shell
  p.wall(0, 0, 45, 0); // top
  p.wall(0, 0, 0, 31); // left
  p.wall(45, 0, 45, 31); // right
  p.wall(0, 31, 45, 31); // bottom (entrance carved later)

  // Top-room dividers (rows 0–9)
  p.wall(11, 0, 11, 9);
  p.wall(22, 0, 22, 9);
  p.wall(33, 0, 33, 9);
  // Wall under top rooms (row 9)
  p.wall(0, 9, 45, 9);

  // Marketing walls
  p.wall(0, 12, 11, 12); // top
  p.wall(11, 12, 11, 20); // right
  p.wall(0, 20, 13, 20); // bottom (shared with operations top)
  // Research walls
  p.wall(34, 12, 45, 12); // top
  p.wall(34, 12, 34, 20); // left
  p.wall(34, 20, 45, 20); // bottom

  // Operations right wall
  p.wall(13, 20, 13, 26);
  // Server room walls
  p.wall(26, 20, 33, 20); // top
  p.wall(26, 20, 26, 25); // left
  p.wall(33, 20, 33, 25); // right
  p.wall(26, 25, 33, 25); // bottom

  // Break lounge walls
  p.wall(0, 26, 15, 26); // top
  p.wall(15, 26, 15, 31); // right
  // Toilets walls
  p.wall(35, 26, 45, 26); // top
  p.wall(35, 26, 35, 31); // left

  // ══ Doors ═══════════════════════════════════════════════════
  // Top rooms open into the corridor (row 9)
  p.door(5, 9, 6, 9, PLANK, HALLWAY_WOOD);
  p.door(16, 9, 17, 9, PLANK, HALLWAY_WOOD);
  p.door(27, 9, 28, 9, PLANK, HALLWAY_WOOD);
  p.door(38, 9, 39, 9, PLANK, HALLWAY_WOOD);
  // Marketing / Research side doors into central hallway
  p.door(11, 15, 11, 16, FLAT, FLOOR_COLORS.marketing);
  p.door(34, 15, 34, 16, FLAT, FLOOR_COLORS.research);
  // Operations door
  p.door(13, 22, 13, 23, FLAT, FLOOR_COLORS.operations);
  // Server room door (left side)
  p.door(26, 22, 26, 23, GRID, SERVER_FLOOR);
  // Lounge door
  p.door(15, 28, 15, 29, CHECK, LOUNGE_CHECKER);
  // Toilets door
  p.door(35, 28, 35, 29, CERAMIC, TOILET_FLOOR);
  // Main entrance (bottom wall gap)
  p.door(21, 31, 24, 31, PLANK, LOBBY_WOOD);

  // ══ Outer-shell windows ═════════════════════════════════════
  // Vertical slit windows punched through the left / right facade, the way the
  // reference art breaks up its long dark exterior walls.
  for (const row of [2, 5, 14, 17, 22, 28]) {
    p.furn('WINDOW_SIDE', 0, row);
    p.furn('WINDOW_SIDE', 45, row);
  }

  // ══ Furniture ═══════════════════════════════════════════════
  // ── Creative (cols 1–10): gallery wall, art-studio bullpen ───
  p.wallStrip(0, [
    [1, 'BOOKSHELF'],
    [8, 'WALL_SHELF'],
  ]);
  // Three readable workstations leave a generous studio aisle for roaming.
  deskN(p, 1, 3);
  deskS(p, 1, 7);
  deskW(p, 9, 3, 1);
  p.furn('FILE_CABINET', 10, 4);
  p.furn('PLANT', 10, 7);
  p.furn('CACTUS', 8, 1);
  p.furn('BIN', 8, 8);

  // ── Developer (cols 12–21): kanban wall + code racks ─────────
  p.wallStrip(0, [
    [12, 'WHITEBOARD_KANBAN'],
    [19, 'TV_SCREEN'],
  ]);
  // Two benches plus a lower review station; the middle stays walkable.
  deskE(p, 15, 3, 1);
  deskN(p, 13, 6);
  deskS(p, 18, 7);
  p.furn('SERVER_RACK', 21, 2);
  p.furn('SERVER_RACK_3', 21, 5);
  p.furn('BIN', 21, 8);
  p.furn('PRINTER', 12, 1);
  p.furn('PLANT_2', 12, 4);
  p.furn('CACTUS', 12, 7);

  // ── Finance (cols 23–32): charts, ledgers, filing ────────────
  p.wallStrip(0, [
    [23, 'PHOTO_WALL'],
    [30, 'WALL_SHELF'],
  ]);
  // Keep the lower doorway lane completely clear: this is a shared office,
  // not a row of desks facing the corridor.
  deskS(p, 24, 3);
  deskN(p, 27, 4);
  deskE(p, 31, 4, 1);
  p.furn('FILE_CABINET', 32, 1);
  p.furn('FILE_CABINET', 32, 3);
  p.furn('WATER_COOLER', 32, 6);
  p.furn('BIN', 32, 8);
  p.furn('PRINTER', 24, 7);
  p.furn('PLANT', 26, 6);
  p.furn('POT', 23, 4);

  // ── Legal (cols 34–44): law library wall ─────────────────────
  p.wallStrip(0, [
    [34, 'BOOKSHELF'],
    [42, 'WALL_SHELF'],
  ]);
  p.furn('CLOCK', 44, 0);
  // The reading desk stays above the entrance so agents can enter, exit, and
  // gather in the legal room without a chair spilling into the doorway.
  deskW(p, 36, 3, 1);
  deskE(p, 41, 3, 1);
  deskN(p, 38, 4);
  p.furn('DOUBLE_BOOKSHELF', 43, 2);
  p.furn('FILE_CABINET', 44, 5);
  p.furn('BIN', 44, 8);
  p.furn('PALM', 42, 7);
  p.furn('PLANT_2', 34, 4);
  p.furn('POT', 38, 1);

  // ── Marketing (cols 1–10, rows 13–19): campaign wall ─���───────
  p.wallStrip(12, [
    [1, 'PHOTO_WALL'],
    [8, 'WALL_SHELF'],
  ]);
  // Three campaign stations with open floor between them.
  deskS(p, 1, 15);
  deskS(p, 6, 15);
  deskN(p, 4, 18);
  p.furn('FILE_CABINET', 10, 13);
  p.furn('PLANT_2', 4, 13);
  p.furn('PRINTER', 4, 18);
  p.furn('BIN', 9, 14);

  // ── Research (cols 35–44, rows 13–19): lab boards ────────────
  p.wallStrip(12, [
    [35, 'TV_SCREEN'],
    [42, 'BOOKSHELF'],
  ]);
  // Three lab stations ring a clear central walkway.
  deskN(p, 38, 14);
  deskE(p, 43, 15, 1);
  deskS(p, 39, 18);
  p.furn('FILE_CABINET', 44, 13);
  p.furn('PRINTER', 35, 13);
  p.furn('PLANT', 38, 15);
  p.furn('PLANT_2', 35, 17);
  p.furn('BIN', 38, 19);

  // ── Operations (cols 1–12, rows 21–25): ops wall + vending ───
  p.wallStrip(20, [
    [1, 'CHART_BOARD'],
    [9, 'WHITEBOARD_KANBAN'],
  ]);
  // Two stations and a small equipment corner keep the ops room airy.
  deskS(p, 1, 23);
  deskS(p, 6, 23);
  p.furn('VENDING_MACHINE', 11, 21);
  p.furn('VENDING_MACHINE', 12, 21);
  p.furn('WATER_COOLER', 11, 24);
  p.furn('PLANT', 12, 24);
  p.furn('BIN', 10, 25);
  p.furn('PALM', 2, 25);
  p.furn('PLANT_2', 6, 25);

  // ── Corridor gallery (row 9): framed photo strips + doors ────
  p.wallStrip(9, [
    [1, 'PHOTO_WALL'],
    [3, 'PHOTO_WALL'],
    [8, 'PHOTO_WALL'],
    [12, 'PHOTO_WALL'],
    [14, 'PHOTO_WALL'],
    [20, 'PHOTO_WALL'],
    [23, 'PHOTO_WALL'],
    [25, 'PHOTO_WALL'],
    [30, 'PHOTO_WALL'],
    [35, 'PHOTO_WALL'],
    [42, 'PHOTO_WALL'],
  ]);
  p.furn('EXIT_SIGN', 32, 9);
  // Closed wooden doors reading as each room's entrance.
  p.furn('WOOD_DOOR', 7, 9);
  p.furn('WOOD_DOOR', 18, 9);
  p.furn('WOOD_DOOR', 29, 9);
  p.furn('WOOD_DOOR', 40, 9);
  p.furn('WOOD_DOOR', 11, 17);
  p.furn('WOOD_DOOR', 34, 17);
  p.furn('WOOD_DOOR', 13, 24);
  p.furn('WOOD_DOOR', 26, 24);
  p.furn('WOOD_DOOR', 15, 30);
  p.furn('WOOD_DOOR', 35, 30);

  // ── Orchestrator island (central hallway) ────────────────────
  // A partition of counters behind the desk, exactly like the reference's
  // free-standing command station in the middle of the wood floor.
  p.furn('COUNTER', 20, 12, BAR_WOOD);
  p.furn('COUNTER', 22, 12, BAR_WOOD);
  p.furn('CUSHIONED_CHAIR_FRONT', ORCHESTRATOR_SEAT_TILE.col, ORCHESTRATOR_SEAT_TILE.row);
  p.furn('DESK_FRONT', 21, 14);
  p.furn('PC_FRONT_OFF', 22, 14);
  p.furn('DESK_LAMP', 23, 15);
  p.furn('PAPER_STACK', 21, 15);
  p.furn('PALM', 18, 13);
  p.furn('PALM', 24, 13);

  // ── HR desk (below orchestrator) ─────────────────────────────
  p.furn('COUNTER', 20, 17, BAR_WOOD);
  p.furn('COUNTER', 22, 17, BAR_WOOD);
  p.furn('CUSHIONED_CHAIR_FRONT', HR_SEAT_TILE.col, HR_SEAT_TILE.row);
  p.furn('DESK_FRONT', 21, 19);
  p.furn('PC_FRONT_OFF', 22, 19);
  p.furn('MUG', 23, 20);
  p.furn('PAPER_STACK', 21, 20);
  p.furn('PALM', 18, 18);
  p.furn('PALM', 24, 18);

  // ── Hallway greenery ────────────────────────────────────────
  p.furn('LARGE_PLANT', 12, 12);
  p.furn('LARGE_PLANT', 32, 12);
  p.furn('HANGING_PLANT', 15, 9);
  p.furn('HANGING_PLANT', 27, 9);
  p.furn('PLANT', 14, 20);
  p.furn('PLANT_2', 25, 20);
  p.furn('PALM', 14, 12);
  p.furn('PALM', 30, 12);
  p.furn('POT', 16, 25);
  p.furn('PLANT', 14, 26);
  p.furn('PLANT_2', 25, 26);

  // ── Break lounge: coffee bar + two pink sofa clusters ────────
  p.wallStrip(26, [
    [1, 'PHOTO_WALL'],
    [3, 'PHOTO_WALL'],
    [5, 'TV_SCREEN'],
    [8, 'COUNTER'],
    [10, 'COUNTER'],
    [12, 'CORK_BOARD'],
  ]);
  p.furn('COFFEE_MACHINE', 11, 27);
  p.furn('FRIDGE', 13, 27);
  p.furn('VENDING_MACHINE', 14, 27);
  p.furn('WATER_COOLER', 14, 29);
  // Cluster 1
  p.furn('SOFA_FRONT', 2, 27, SOFA_PINK);
  p.furn('COFFEE_TABLE', 2, 29);
  p.furn('COFFEE', 3, 29);
  p.furn('SOFA_SIDE', 1, 29, SOFA_PINK);
  p.furn('SOFA_BACK', 2, 31, SOFA_PINK);
  // Cluster 2
  p.furn('SOFA_FRONT', 6, 27, SOFA_PINK);
  p.furn('COFFEE_TABLE', 6, 29);
  p.furn('MUG', 7, 29);
  p.furn('SOFA_SIDE', 8, 29, SOFA_PINK);
  p.furn('PLANT', 5, 30);
  p.furn('PALM', 9, 29);
  p.furn('PLANT_2', 1, 27);
  p.furn('CACTUS', 10, 30);

  // ── Server room: rack wall, maintenance row, AC unit ─────────
  p.furn('AC_UNIT', 28, 20);
  p.furn('AC_UNIT', 31, 20);
  for (let c = 27; c <= 32; c++) {
    p.furn(c % 2 === 1 ? 'SERVER_RACK' : 'SERVER_RACK_2', c, 21);
  }
  p.furn('SERVER_RACK', 28, 23, RACK_STEEL);
  p.furn('SERVER_RACK_2', 30, 23, RACK_STEEL);
  p.furn('SERVER_RACK', 32, 23, RACK_STEEL);
  p.furn('BIN', 27, 24);

  // ── Right lobby next to the server room ─────────────────────
  p.wallStrip(20, [
    [35, 'PHOTO_WALL'],
    [37, 'PHOTO_WALL'],
    [39, 'COUNTER'],
    [41, 'COUNTER'],
    [43, 'WALL_SHELF'],
  ]);
  p.furn('RUG_ACCENT', 37, 23);
  p.furn('PALM', 41, 23);
  p.furn('PLANT_2', 34, 21);
  p.furn('PLANT', 44, 21);
  p.furn('PLANT', 44, 24);
  p.furn('POT', 35, 25);
  p.furn('SMALL_TABLE_FRONT', 41, 21);

  // ── Bottom lobby: rug, plants, entrance flair ───────────────
  p.furn('RUG_ACCENT', 28, 28);
  p.furn('PLANT', 31, 28);
  p.furn('PALM', 32, 26);
  p.furn('PLANT_2', 17, 26);
  p.furn('PALM', 19, 29);
  p.furn('PALM', 25, 29);
  p.furn('PLANT', 17, 30);
  p.furn('PLANT_2', 27, 30);
  p.furn('GLASS_DOORS', 22, 30);
  p.furn('EXIT_SIGN', 20, 31);
  p.furn('COMPANY_SIGN', 21, 32);
  p.furn('PALM', 18, 32);
  p.furn('PALM', 27, 32);

  // ── Toilets: separated MEN / WOMEN stalls with a shared sink run ──
  p.wallStrip(26, [
    [37, 'TOILET_DOOR_MEN'],
    [43, 'TOILET_DOOR_WOMEN'],
  ]);
  p.furn('TOILET_MIRROR', 39, 26);
  p.furn('TOILET_MIRROR', 41, 26);
  p.furn('SINK', 39, 27);
  p.furn('SINK', 41, 27);
  p.furn('TOILET_STALL', 36, 29);
  p.furn('TOILET_STALL', 42, 29);
  p.furn('BIN', 40, 29);
  p.furn('PLANT_2', 44, 27);
  p.furn('PLANT', 44, 30);

  // ══ Areas ═══════════════════════════════════════════════════
  p.area(1, 1, 10, 8, AREA_LABELS.creative);
  p.area(12, 1, 21, 8, AREA_LABELS.developer);
  p.area(23, 1, 32, 8, AREA_LABELS.finance);
  p.area(34, 1, 44, 8, AREA_LABELS.legal);
  p.area(1, 13, 10, 19, AREA_LABELS.marketing);
  p.area(35, 13, 44, 19, AREA_LABELS.research);
  p.area(1, 21, 12, 25, AREA_LABELS.operations);
  p.area(1, 27, 14, 30, AREA_LABELS.lounge);
  p.area(27, 21, 32, 24, AREA_LABELS.server);
  p.area(36, 27, 44, 30, AREA_LABELS.toilets);
  p.area(20, 13, 24, 15, AREA_LABELS.orchestrator);
  p.area(20, 18, 24, 20, AREA_LABELS.hr);
  p.area(19, 32, 26, 33, AREA_LABELS.reception);

  // Muted plaque/area accents keep the editor's area system useful without
  // turning the normal office view into a saturated color wash.
  const areas: AreaDefinition[] = [
    { label: AREA_LABELS.creative, color: '#8f70a7' },
    { label: AREA_LABELS.developer, color: '#668f6d' },
    { label: AREA_LABELS.finance, color: '#b29155' },
    { label: AREA_LABELS.legal, color: '#6684a6' },
    { label: AREA_LABELS.marketing, color: '#b06e8d' },
    { label: AREA_LABELS.research, color: '#669d96' },
    { label: AREA_LABELS.operations, color: '#b47d51' },
    { label: AREA_LABELS.lounge, color: '#5d6470' },
    { label: AREA_LABELS.server, color: '#59789b' },
    { label: AREA_LABELS.toilets, color: '#7895ad' },
    { label: AREA_LABELS.orchestrator, color: '#8f7d58' },
    { label: AREA_LABELS.hr, color: '#a46a86' },
    { label: AREA_LABELS.reception, color: '#a36658' },
  ];

  return {
    version: 1,
    cols: MYCEL_COLS,
    rows: MYCEL_ROWS,
    tiles: p.tiles,
    tileColors: p.tileColors,
    areaTiles: p.areaTiles,
    areas,
    furniture: p.furniture,
  };
}
