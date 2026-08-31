/**
 * Rendering-only art direction for the Mycel office.
 *
 * These placements intentionally do not participate in the layout's blocked
 * tiles, seats, areas, or pathfinding. They let the canvas renderer enrich a
 * room with reusable assets while the office engine remains the single source
 * of truth for every interactive object.
 */

export type RoomVisual = {
  id: string;
  col: number;
  row: number;
  width: number;
  height: number;
  accent: string;
  material: 'department' | 'wood' | 'checker' | 'tile' | 'server';
};

export type DecorPlacement = {
  roomId: string;
  spriteId: string;
  col: number;
  row: number;
  /** `server-light` is a procedural placeholder until a two-frame rack sprite is supplied. */
  kind?: 'sprite' | 'server-light';
  /** Renders in the shared z-sort with the layout furniture. */
  zOffset?: number;
};

export type AmbientActor = {
  id: string;
  from: { col: number; row: number };
  to: { col: number; row: number };
  periodMs: number;
  palette: number;
  hueShift: number;
};

// Interior room bounds match mycelOfficeLayout.ts exactly. This is a visual
// layer only: changing one of these values never changes a wall, seat, or path.
export const ROOM_VISUALS: RoomVisual[] = [
  { id: 'creative', col: 1, row: 1, width: 10, height: 8, accent: '#8f70a7', material: 'department' },
  { id: 'developer', col: 12, row: 1, width: 10, height: 8, accent: '#668f6d', material: 'department' },
  { id: 'finance', col: 23, row: 1, width: 10, height: 8, accent: '#b29155', material: 'department' },
  { id: 'legal', col: 34, row: 1, width: 11, height: 8, accent: '#6684a6', material: 'department' },
  { id: 'marketing', col: 1, row: 13, width: 10, height: 7, accent: '#b06e8d', material: 'department' },
  { id: 'research', col: 35, row: 13, width: 10, height: 7, accent: '#669d96', material: 'department' },
  { id: 'operations', col: 1, row: 21, width: 12, height: 5, accent: '#b47d51', material: 'department' },
  { id: 'central', col: 12, row: 12, width: 22, height: 9, accent: '#7c563b', material: 'wood' },
  { id: 'central-lower', col: 14, row: 21, width: 12, height: 5, accent: '#7c563b', material: 'wood' },
  { id: 'lounge', col: 1, row: 27, width: 14, height: 4, accent: '#5d6470', material: 'checker' },
  { id: 'server', col: 27, row: 21, width: 6, height: 4, accent: '#59789b', material: 'server' },
  { id: 'toilets', col: 36, row: 27, width: 9, height: 4, accent: '#7895ad', material: 'tile' },
  { id: 'right-lobby', col: 34, row: 21, width: 11, height: 5, accent: '#7c563b', material: 'wood' },
  { id: 'entry', col: 16, row: 26, width: 19, height: 5, accent: '#7c563b', material: 'wood' },
];

// Existing furniture sprites are reused so this can ship without a new art
// bundle. `SERVER_LIGHTS` is deliberately procedural and can later be swapped
// for server_rack_blink1/2 assets without touching the renderer.
export const ROOM_DECOR_CONFIG: DecorPlacement[] = [
  { roomId: 'creative', spriteId: 'PHOTO_WALL', col: 3, row: 1 },
  { roomId: 'creative', spriteId: 'PC_FRONT_ON_1', col: 1, row: 3, zOffset: 12 },
  { roomId: 'creative', spriteId: 'COFFEE', col: 5, row: 6, zOffset: 8 },
  { roomId: 'developer', spriteId: 'CORK_BOARD', col: 18, row: 1 },
  { roomId: 'developer', spriteId: 'PC_FRONT_ON_2', col: 16, row: 3, zOffset: 12 },
  { roomId: 'developer', spriteId: 'MUG', col: 16, row: 5, zOffset: 8 },
  // Keep the finance chart on the open left wall, separated from the compact
  // room sign and the door sightline below.
  { roomId: 'finance', spriteId: 'CHART_BOARD', col: 24, row: 1 },
  { roomId: 'finance', spriteId: 'PC_FRONT_ON_3', col: 24, row: 3, zOffset: 12 },
  { roomId: 'finance', spriteId: 'PAPER_STACK', col: 26, row: 4, zOffset: 8 },
  { roomId: 'legal', spriteId: 'SMALL_PAINTING', col: 39, row: 1 },
  { roomId: 'legal', spriteId: 'MUG', col: 40, row: 5, zOffset: 8 },
  { roomId: 'marketing', spriteId: 'WHITEBOARD_KANBAN', col: 3, row: 13 },
  { roomId: 'marketing', spriteId: 'PC_FRONT_ON_1', col: 1, row: 15, zOffset: 12 },
  { roomId: 'marketing', spriteId: 'COFFEE', col: 8, row: 17, zOffset: 8 },
  { roomId: 'research', spriteId: 'CHART_BOARD', col: 39, row: 13 },
  { roomId: 'research', spriteId: 'PC_FRONT_ON_2', col: 39, row: 18, zOffset: 12 },
  { roomId: 'research', spriteId: 'PAPER_STACK', col: 41, row: 17, zOffset: 8 },
  { roomId: 'operations', spriteId: 'CORK_BOARD', col: 4, row: 21 },
  { roomId: 'operations', spriteId: 'MUG', col: 8, row: 23, zOffset: 8 },
  { roomId: 'lounge', spriteId: 'COFFEE', col: 11, row: 29, zOffset: 8 },
  { roomId: 'server', spriteId: 'SERVER_LIGHTS', col: 28, row: 21, kind: 'server-light' },
  { roomId: 'server', spriteId: 'SERVER_LIGHTS', col: 30, row: 21, kind: 'server-light' },
  { roomId: 'server', spriteId: 'SERVER_LIGHTS', col: 32, row: 21, kind: 'server-light' },
];

// Decorative colleagues make an idle office feel staffed. They are rendered
// only, do not receive a session id, and never participate in hit-testing.
export const AMBIENT_POPULATION: AmbientActor[] = [
  { id: 'atrium-west', from: { col: 14, row: 15 }, to: { col: 17, row: 15 }, periodMs: 5200, palette: 1, hueShift: 18 },
  { id: 'atrium-east', from: { col: 30, row: 16 }, to: { col: 27, row: 16 }, periodMs: 6100, palette: 3, hueShift: -16 },
  { id: 'hr-visitor', from: { col: 18, row: 20 }, to: { col: 20, row: 20 }, periodMs: 4700, palette: 4, hueShift: 24 },
  { id: 'lobby-walk', from: { col: 25, row: 24 }, to: { col: 23, row: 26 }, periodMs: 6800, palette: 2, hueShift: -28 },
];
