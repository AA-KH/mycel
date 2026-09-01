/* ------------------------------------------------------------------ */
/* Simulation Engine — Core Types                                      */
/* Enums, interfaces, and constants for the log-driven agent engine.    */
/* ------------------------------------------------------------------ */

// ── Agent animation states ──────────────────────────────────────────
export const AgentAnimState = {
  IDLE: 'idle',
  WALK: 'walk',
  /** Seated at a desk but not actively typing */
  SIT: 'sit',
  /** Seated at a desk, typing animation */
  WORK: 'work',
} as const;
export type AgentAnimState = (typeof AgentAnimState)[keyof typeof AgentAnimState];

// ── Direction (logical facing — NOT a spritesheet row index) ────────
export const Direction = {
  DOWN: 0,
  LEFT: 1,
  RIGHT: 2,
  UP: 3,
} as const;
export type Direction = (typeof Direction)[keyof typeof Direction];

// ── Layout constants ────────────────────────────────────────────────
export const TILE_SIZE = 16;

/* ==================================================================
 * CHARACTER SPRITESHEET GEOMETRY
 * ------------------------------------------------------------------
 * Verified directly against public/assets/pixel-agents/characters/
 * char_0..char_5.png — every sheet is 112x96 px, which is a
 * 7 col x 3 row grid of 16x32 frames (NOT 7x4 of 16x24).
 *
 * Row layout (confirmed by per-frame alpha bounding boxes):
 *   row 0 → facing DOWN  (front view, eyes visible)
 *   row 1 → facing UP    (back view, no face)
 *   row 2 → facing RIGHT (side profile; LEFT is this row mirrored)
 *
 * Column layout:
 *   cols 0-2 → standing / walk cycle (feet reach the frame baseline)
 *   cols 3-4 → seated idle  (body lowered / legs bent)
 *   cols 5-6 → seated working (typing arm poses)
 * ================================================================== */
export const CHAR_FRAME_W = 16;
export const CHAR_FRAME_H = 32;
export const CHAR_SHEET_COLS = 7;
export const CHAR_SHEET_ROWS = 3;
export const CHAR_SHEET_W = CHAR_FRAME_W * CHAR_SHEET_COLS; // 112
export const CHAR_SHEET_H = CHAR_FRAME_H * CHAR_SHEET_ROWS; // 96

/** Maps a logical Direction to its spritesheet row + horizontal mirror. */
export const DIR_SHEET: Record<Direction, { row: number; mirror: boolean }> = {
  [Direction.DOWN]: { row: 0, mirror: false },
  [Direction.UP]: { row: 1, mirror: false },
  [Direction.RIGHT]: { row: 2, mirror: false },
  [Direction.LEFT]: { row: 2, mirror: true },
};

/** Neutral standing frame. */
export const STAND_COL = 0;
/**
 * Walk cycle built from the 3 standing columns as a 4-phase gait:
 * step-left → neutral → step-right → neutral.
 */
export const WALK_COLS = [1, 0, 2, 0] as const;
/** Seated idle frames (hands resting). */
export const SIT_COLS = [3, 4] as const;
/** Seated typing frames (arms raised to the keyboard). */
export const WORK_COLS = [5, 6] as const;

/* ==================================================================
 * SPRITE BOUNDS  (measured, not assumed)
 * ------------------------------------------------------------------
 * For each sheet row and each frame group, the vertical extent of the
 * opaque pixels inside the 32px-tall frame:
 *   `top`      → smallest first-opaque row  (min across all 6 sheets)
 *   `baseline` → largest  last-opaque row   (max across all 6 sheets)
 *
 *   row 0 (DOWN)   standing 0..30   seated 5..31
 *   row 1 (UP)     standing 0..30   seated 0..25  (chair hides the legs)
 *   row 2 (RIGHT)  standing 3..30   seated 4..29
 *
 * `baseline` is the character's contact line — where the art puts the
 * feet when standing, and where it puts the last visible pixel of the
 * seated pose. Both are pinned to the bottom edge of the occupied tile
 * (see resolveAgentSprite), because a chair sprite's own silhouette
 * also ends on that same line. The seated groups are NOT the standing
 * body shifted: each direction crops the lower body by a different
 * amount, so the offsets must come from these measurements and never
 * from one global "sit offset".
 *
 * `top` only feeds labels/badges/hitboxes, never the anchor.
 * ================================================================== */
export interface SpriteBound {
  top: number;
  baseline: number;
}
export const SPRITE_BOUNDS: Record<number, { standing: SpriteBound; seated: SpriteBound }> = {
  0: { standing: { top: 0, baseline: 30 }, seated: { top: 5, baseline: 31 } },
  1: { standing: { top: 0, baseline: 30 }, seated: { top: 0, baseline: 25 } },
  2: { standing: { top: 3, baseline: 30 }, seated: { top: 4, baseline: 29 } },
};

// ── Runtime agent state (mutated by the engine every tick) ──────────
export interface SimAgent {
  name: string;
  role: string;
  room: string;
  state: AgentAnimState;
  dir: Direction;
  /** Pixel X — smoothly interpolated between tiles */
  x: number;
  /** Pixel Y — smoothly interpolated between tiles */
  y: number;
  /** Current grid column (integer) */
  tileCol: number;
  /** Current grid row (integer) */
  tileRow: number;
  /** Remaining BFS path nodes (tile coords), excluding start */
  path: Array<{ col: number; row: number }>;
  /** 0-1 lerp between current tile and next tile in path */
  moveProgress: number;
  /** Character spritesheet index (0-5) */
  charIdx: number;
  /** Current animation frame index */
  frame: number;
  /** Accumulator for animation frame timing (seconds) */
  frameTimer: number;
  /** Countdown timer for wander decisions in IDLE (seconds) */
  wanderTimer: number;
  /** Number of wander moves completed in current idle cycle */
  wanderCount: number;
  /** Max wander moves before picking a new idle spot */
  wanderLimit: number;
  /** true → agent is working (pathfind to desk); false → idle/break */
  isActive: boolean;
  currentTask?: string;
  /** false until the agent's 'hired' event fires */
  visible: boolean;
  /** Display as executive (Atlas pulsing glow) */
  isExecutive: boolean;
  /** Assigned desk chair tile column */
  seatCol: number;
  /** Assigned desk chair tile row */
  seatRow: number;
  /** Direction agent faces when seated */
  seatDir: Direction;
}

// ── Timing / physics constants ──────────────────────────────────────
/** Pixels per second while walking (3 tiles/sec at 16px tiles) */
export const WALK_SPEED = 48;
/** Seconds between walk animation frame advances */
export const WALK_FRAME_DURATION = 0.15;
/** Seconds between work/typing animation frame advances */
export const WORK_FRAME_DURATION = 0.4;
/** Min seconds an idle agent waits before wandering */
export const WANDER_PAUSE_MIN = 2.0;
/** Max seconds an idle agent waits before wandering */
export const WANDER_PAUSE_MAX = 5.0;
/** Min wander moves before resting */
export const WANDER_MOVES_MIN = 2;
/** Max wander moves before resting */
export const WANDER_MOVES_MAX = 5;
