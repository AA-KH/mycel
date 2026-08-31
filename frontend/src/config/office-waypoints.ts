/**
 * Office Waypoints — fixed landmark coordinates in the 48×32 Mycel office grid.
 *
 * These define the entry/exit paths agents walk. Since the layout is fixed,
 * no dynamic pathfinding is needed — just waypoint-to-waypoint segments
 * handled by the existing BFS in tileMap.findPath().
 */

// ── Key Landmarks ───────────────────────────────────────────────

/** Front entrance double doors — bottom-center of the hall */
export const ENTRANCE_TILE = { col: 24, row: 30 };

/** HR Agent desk — middle of central hall */
export const HR_DESK_TILE = { col: 24, row: 18 };

/** Orchestrator desk — top of central hall */
export const ORCHESTRATOR_TILE = { col: 24, row: 12 };

/** Break Lounge center — where idle agents hang out */
export const BREAK_LOUNGE_CENTER = { col: 8, row: 28 };

/** Server Room entrance */
export const SERVER_ROOM_TILE = { col: 34, row: 18 };

// ── Zone Doorways ───────────────────────────────────────────────
// Each room's entry point from the central hall

export const ZONE_DOORWAYS: Record<string, { col: number; row: number }> = {
  creative:   { col: 6, row: 10 },
  developer:  { col: 16, row: 10 },
  finance:    { col: 30, row: 10 },
  legal:      { col: 42, row: 10 },
  marketing:  { col: 6, row: 16 },
  research:   { col: 42, row: 16 },
  operations: { col: 6, row: 24 },
  lounge:     { col: 8, row: 26 },
};

// ── Zone Tile Regions ───────────────────────────────────────────
// Bounding boxes for each room (used for dimming overlay + area tiles)

export interface ZoneRegion {
  label: string;
  color: string;
  startCol: number;
  startRow: number;
  endCol: number;   // exclusive
  endRow: number;    // exclusive
}

export const ZONE_REGIONS: ZoneRegion[] = [
  // Top row
  { label: "CREATIVE",   color: "#7c3aed", startCol: 1,  startRow: 1,  endCol: 11, endRow: 9 },
  { label: "DEVELOPER",  color: "#059669", startCol: 12, startRow: 1,  endCol: 22, endRow: 9 },
  { label: "FINANCE",    color: "#d97706", startCol: 26, startRow: 1,  endCol: 36, endRow: 9 },
  { label: "LEGAL",      color: "#2563eb", startCol: 37, startRow: 1,  endCol: 47, endRow: 9 },
  // Middle row
  { label: "MARKETING",  color: "#db2777", startCol: 1,  startRow: 11, endCol: 11, endRow: 21 },
  { label: "RESEARCH",   color: "#0d9488", startCol: 37, startRow: 11, endCol: 47, endRow: 21 },
  // Bottom row
  { label: "OPERATIONS", color: "#c2410c", startCol: 1,  startRow: 23, endCol: 11, endRow: 28 },
  { label: "BREAK LOUNGE", color: "#78716c", startCol: 1,  startRow: 28, endCol: 11, endRow: 32 },
];

// ── Hall Waypoint (route between landmarks) ─────────────────────

/** Main hall center column — agents walk along this column */
export const HALL_CENTER_COL = 24;

// ── Path Generators ─────────────────────────────────────────────

/**
 * Generate waypoints for agent entry: Entrance → HR Desk → Room Doorway
 * The agent walks these segments, pausing at the HR desk for WalletCard sync.
 */
export function getEntryPath(zone: string): Array<{ col: number; row: number }> {
  const doorway = ZONE_DOORWAYS[zone];
  if (!doorway) {
    // Fallback: walk to hall center
    return [ENTRANCE_TILE, HR_DESK_TILE];
  }
  return [
    ENTRANCE_TILE,
    HR_DESK_TILE,       // pause here for WalletCard sync
    doorway,            // room doorway
  ];
}

/**
 * Generate waypoints for agent exit: Desk → Room Doorway → Break Lounge
 * Called when agent's task ends and no new work is queued.
 */
export function getExitPath(zone: string): Array<{ col: number; row: number }> {
  const doorway = ZONE_DOORWAYS[zone];
  if (!doorway) {
    return [BREAK_LOUNGE_CENTER];
  }
  return [
    doorway,
    { col: HALL_CENTER_COL, row: doorway.row },  // step into hall
    BREAK_LOUNGE_CENTER,
  ];
}

/**
 * Generate waypoints for returning from break lounge to a desk.
 * Used when an idle agent gets reassigned to a new task.
 */
export function getReturnFromBreakPath(zone: string): Array<{ col: number; row: number }> {
  const doorway = ZONE_DOORWAYS[zone];
  if (!doorway) {
    return [HR_DESK_TILE];
  }
  return [
    { col: HALL_CENTER_COL, row: BREAK_LOUNGE_CENTER.row }, // exit lounge into hall
    HR_DESK_TILE,       // check in with HR
    doorway,            // back to room
  ];
}
