import type { AgentSession, SeatPosition, TileMapData } from "../types/agent";

export const OFFICE_WIDTH = 26;
export const OFFICE_HEIGHT = 16;
export const TILE_SIZE = 32;

/**
 * Walkable tile coordinates — agents can walk within cabins and across the central hallway
 */
export const WALKABLE_TILES: Array<{ x: number; y: number }> = [];

// Hallways (Vertical cols 12-13, Horizontal row 8)
for (let y = 0; y < OFFICE_HEIGHT; y++) {
  WALKABLE_TILES.push({ x: 12, y });
  WALKABLE_TILES.push({ x: 13, y });
}
for (let x = 0; x < OFFICE_WIDTH; x++) {
  WALKABLE_TILES.push({ x, y: 8 });
}

// Manager Cabin Walkable floor (cols 1-10, rows 1-6)
for (let x = 1; x <= 10; x++) {
  for (let y = 1; y <= 6; y++) {
    // Avoid blocking the desk area directly
    if (!(x >= 4 && x <= 6 && y === 3)) {
      WALKABLE_TILES.push({ x, y });
    }
  }
}

// Dev & QA Lab Walkable floor (cols 1-10, rows 10-14)
for (let x = 1; x <= 10; x++) {
  for (let y = 10; y <= 14; y++) {
    if (!(y === 11 && (x === 2 || x === 3 || x === 5 || x === 6 || x === 8 || x === 9))) {
      WALKABLE_TILES.push({ x, y });
    }
  }
}

// Research & Review Hub Walkable floor (cols 15-24, rows 1-6)
for (let x = 15; x <= 24; x++) {
  for (let y = 1; y <= 6; y++) {
    if (!(y === 3 && (x === 16 || x === 17 || x === 20 || x === 21))) {
      WALKABLE_TILES.push({ x, y });
    }
  }
}

// Chai & Reels Lounge Walkable floor (cols 15-24, rows 10-14)
for (let x = 15; x <= 24; x++) {
  for (let y = 10; y <= 14; y++) {
    WALKABLE_TILES.push({ x, y });
  }
}

/**
 * Specialized Cabin Seats
 */
export const CABIN_SEATS: Record<string, SeatPosition> = {
  // Manager's Executive Cabin Desk
  manager: { x: 5, y: 2, direction: "down", deskX: 5, deskY: 3, zone: "work" },
  Architect: { x: 5, y: 2, direction: "down", deskX: 5, deskY: 3, zone: "work" },

  // Dev & QA Pods
  coder: { x: 3, y: 12, direction: "up", deskX: 3, deskY: 11, zone: "work" },
  Developer: { x: 3, y: 12, direction: "up", deskX: 3, deskY: 11, zone: "work" },
  "Frontend Developer": { x: 6, y: 12, direction: "up", deskX: 6, deskY: 11, zone: "work" },
  "Backend Developer": { x: 3, y: 12, direction: "up", deskX: 3, deskY: 11, zone: "work" },
  tester: { x: 9, y: 12, direction: "up", deskX: 9, deskY: 11, zone: "work" },
  "QA Engineer": { x: 9, y: 12, direction: "up", deskX: 9, deskY: 11, zone: "work" },
  Debugger: { x: 9, y: 12, direction: "up", deskX: 9, deskY: 11, zone: "work" },

  // Research & Review Hub
  researcher: { x: 17, y: 4, direction: "up", deskX: 17, deskY: 3, zone: "work" },
  "Technical Writer": { x: 17, y: 4, direction: "up", deskX: 17, deskY: 3, zone: "work" },
  reviewer: { x: 21, y: 4, direction: "up", deskX: 21, deskY: 3, zone: "work" },
  "Code Reviewer": { x: 21, y: 4, direction: "up", deskX: 21, deskY: 3, zone: "work" },
  "Data Engineer": { x: 17, y: 4, direction: "up", deskX: 17, deskY: 3, zone: "work" },
  "DevOps Engineer": { x: 21, y: 4, direction: "up", deskX: 21, deskY: 3, zone: "work" },
  Designer: { x: 17, y: 4, direction: "up", deskX: 17, deskY: 3, zone: "work" },
};

/**
 * Break Room & Reels Lounge Seats (when idle or relaxing)
 */
export const LOUNGE_SEATS: SeatPosition[] = [
  { x: 18, y: 13, direction: "up", deskX: 18, deskY: 14, zone: "break" }, // Sofa Left (Reels)
  { x: 20, y: 13, direction: "up", deskX: 20, deskY: 14, zone: "break" }, // Sofa Right (Reels)
  { x: 16, y: 11, direction: "down", deskX: 16, deskY: 10, zone: "break" }, // Coffee Maker Bar
  { x: 23, y: 11, direction: "down", deskX: 23, deskY: 10, zone: "break" }, // Water Cooler
  { x: 22, y: 13, direction: "left", deskX: 21, deskY: 13, zone: "break" }, // Beanbag Chair
];

export const OFFICE_MAP: TileMapData = {
  width: OFFICE_WIDTH,
  height: OFFICE_HEIGHT,
  tileSize: TILE_SIZE,
  layers: [],
  seats: Object.values(CABIN_SEATS),
};

/**
 * Assign appropriate cabin seat based on the agent's role or status
 */
export function assignSeats(agents: AgentSession[]): Map<string, SeatPosition> {
  const result = new Map<string, SeatPosition>();

  agents.forEach((agent, i) => {
    // When working: assign to designated Cabin workstation
    if (agent.status === "working") {
      const cabinSeat = CABIN_SEATS[agent.role];
      if (cabinSeat) {
        result.set(agent.id, cabinSeat);
        return;
      }
    }

    // On break: randomly assign either their cabin desk or the Chai & Reels Lounge
    if (agent.status === "on_break" && i % 2 === 1) {
      const loungeSeat = LOUNGE_SEATS[i % LOUNGE_SEATS.length];
      result.set(agent.id, loungeSeat);
      return;
    }

    // Default to role cabin seat or fallback
    const seat = CABIN_SEATS[agent.role] || LOUNGE_SEATS[i % LOUNGE_SEATS.length];
    result.set(agent.id, seat);
  });

  return result;
}
