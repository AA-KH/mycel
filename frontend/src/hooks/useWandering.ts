/**
 * Hook that manages tile-by-tile walking, cabin roaming, and Chai Break routines for agents.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { WALKABLE_TILES, CABIN_SEATS, LOUNGE_SEATS } from "../config/office-map";
import type { AgentSession, SeatPosition } from "../types/agent";

const STEP_MS = 220; // ms per tile step
const CHAI_BAR_POS = { x: 16, y: 11 }; // Standing position in front of espresso/chai machine

type Dir = "up" | "down" | "left" | "right";
type RoutineState = "AT_DESK" | "WALKING_TO_CHAI" | "DRINKING_CHAI" | "WALKING_TO_DESK" | "ROAMING";

interface WalkerState {
  x: number;
  y: number;
  direction: Dir;
  isWalking: boolean;
  hasChai: boolean;
  routineState: RoutineState;
  homeDesk: { x: number; y: number; direction: Dir };
  path: Array<{ x: number; y: number }>;
  pathIndex: number;
}

const walkableSet = new Set(WALKABLE_TILES.map((t) => `${t.x},${t.y}`));
function isWalkable(x: number, y: number): boolean {
  return walkableSet.has(`${x},${y}`);
}

/** BFS / Manhattan pathfinding along walkable tiles */
function computePath(
  from: { x: number; y: number },
  to: { x: number; y: number },
): Array<{ x: number; y: number }> {
  // Simple BFS for guaranteed collision-free path across hallway and cabins
  const queue: Array<{ x: number; y: number; path: Array<{ x: number; y: number }> }> = [
    { x: from.x, y: from.y, path: [] },
  ];
  const visited = new Set<string>([`${from.x},${from.y}`]);

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (current.x === to.x && current.y === to.y) {
      return current.path;
    }

    const neighbors = [
      { x: current.x + 1, y: current.y },
      { x: current.x - 1, y: current.y },
      { x: current.x, y: current.y + 1 },
      { x: current.x, y: current.y - 1 },
    ];

    for (const n of neighbors) {
      const key = `${n.x},${n.y}`;
      if (!visited.has(key) && isWalkable(n.x, n.y)) {
        visited.add(key);
        queue.push({
          x: n.x,
          y: n.y,
          path: [...current.path, { x: n.x, y: n.y }],
        });
      }
    }
  }

  // Fallback direct manhattan walk
  const fallback: Array<{ x: number; y: number }> = [];
  let { x, y } = from;
  const dx = to.x > x ? 1 : -1;
  while (x !== to.x) {
    x += dx;
    if (isWalkable(x, y)) fallback.push({ x, y });
    else break;
  }
  const dy = to.y > y ? 1 : -1;
  while (y !== to.y) {
    y += dy;
    if (isWalkable(x, y)) fallback.push({ x, y });
    else break;
  }
  return fallback;
}

function stepDirection(
  from: { x: number; y: number },
  to: { x: number; y: number },
): Dir {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  if (Math.abs(dx) > Math.abs(dy)) return dx > 0 ? "right" : "left";
  return dy > 0 ? "down" : "up";
}

export function useWandering(
  agents: AgentSession[],
  assignedSeats: Map<string, SeatPosition>,
): Map<string, SeatPosition & { isWalking: boolean; hasChai?: boolean }> {
  const walkersRef = useRef<Map<string, WalkerState>>(new Map());
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const [tick, setTick] = useState(0);

  const rerender = useCallback(() => setTick((t) => t + 1), []);

  const initWalker = useCallback((agent: AgentSession): WalkerState => {
    const defaultSeat = CABIN_SEATS[agent.role] || LOUNGE_SEATS[0];
    return {
      x: defaultSeat.x,
      y: defaultSeat.y,
      direction: defaultSeat.direction as Dir,
      isWalking: false,
      hasChai: false,
      routineState: "AT_DESK",
      homeDesk: { x: defaultSeat.x, y: defaultSeat.y, direction: defaultSeat.direction as Dir },
      path: [],
      pathIndex: 0,
    };
  }, []);

  const executeRoutine = useCallback(
    (id: string) => {
      const walker = walkersRef.current.get(id);
      if (!walker) return;

      // ── ROUTINE STATE MACHINE ──
      if (walker.routineState === "AT_DESK") {
        // Agent was at desk: 60% chance to go to Chai Bar, 40% chance to roam nearby
        if (Math.random() < 0.6) {
          walker.routineState = "WALKING_TO_CHAI";
          const path = computePath({ x: walker.x, y: walker.y }, CHAI_BAR_POS);
          if (path.length > 0) {
            walker.path = path;
            walker.pathIndex = 0;
            walker.isWalking = true;
          }
        } else {
          walker.routineState = "ROAMING";
          const target = LOUNGE_SEATS[Math.floor(Math.random() * LOUNGE_SEATS.length)];
          const path = computePath({ x: walker.x, y: walker.y }, { x: target.x, y: target.y });
          if (path.length > 0) {
            walker.path = path;
            walker.pathIndex = 0;
            walker.isWalking = true;
          }
        }
      } else if (walker.routineState === "DRINKING_CHAI") {
        // Finished drinking chai: walk back to their cabin desk!
        walker.routineState = "WALKING_TO_DESK";
        walker.hasChai = true; // Holds steaming cup on the way back
        const path = computePath({ x: walker.x, y: walker.y }, walker.homeDesk);
        if (path.length > 0) {
          walker.path = path;
          walker.pathIndex = 0;
          walker.isWalking = true;
        }
      } else {
        // Returned to desk
        walker.routineState = "AT_DESK";
        walker.hasChai = false;
        walker.direction = walker.homeDesk.direction;
      }

      // Step along path
      const stepThrough = () => {
        const w = walkersRef.current.get(id);
        if (!w || w.pathIndex >= w.path.length) {
          if (w) {
            w.isWalking = false;
            w.path = [];
            w.pathIndex = 0;

            if (w.routineState === "WALKING_TO_CHAI") {
              w.routineState = "DRINKING_CHAI";
              w.hasChai = true;
              w.direction = "up"; // Face espresso machine
              rerender();
              // Spend 6-9 seconds drinking hot chai
              const drinkTimer = setTimeout(() => executeRoutine(id), 6000 + Math.random() * 3000);
              timersRef.current.set(id, drinkTimer);
              return;
            } else if (w.routineState === "WALKING_TO_DESK" || w.routineState === "ROAMING") {
              w.routineState = "AT_DESK";
              w.hasChai = false;
              w.direction = w.homeDesk.direction;
            }
          }
          rerender();
          // Relax at desk for 10-18 seconds before next routine
          const pause = 10000 + Math.random() * 8000;
          const timer = setTimeout(() => executeRoutine(id), pause);
          timersRef.current.set(id, timer);
          return;
        }

        const nextTile = w.path[w.pathIndex];
        w.direction = stepDirection({ x: w.x, y: w.y }, nextTile);
        w.x = nextTile.x;
        w.y = nextTile.y;
        w.pathIndex++;
        rerender();

        const timer = setTimeout(stepThrough, STEP_MS);
        timersRef.current.set(id, timer);
      };

      if (walker.isWalking) {
        const timer = setTimeout(stepThrough, STEP_MS);
        timersRef.current.set(id, timer);
      } else {
        const timer = setTimeout(() => executeRoutine(id), 5000);
        timersRef.current.set(id, timer);
      }
    },
    [rerender],
  );

  useEffect(() => {
    const currentIds = new Set<string>();

    for (const agent of agents) {
      if (agent.status === "working") {
        if (walkersRef.current.has(agent.id)) {
          walkersRef.current.delete(agent.id);
          const timer = timersRef.current.get(agent.id);
          if (timer) clearTimeout(timer);
          timersRef.current.delete(agent.id);
        }
        continue;
      }

      currentIds.add(agent.id);

      if (!walkersRef.current.has(agent.id)) {
        walkersRef.current.set(agent.id, initWalker(agent));
        // Stagger initial chai routines so characters don't all move at the same second
        const delay = 4000 + Math.random() * 10000;
        const timer = setTimeout(() => executeRoutine(agent.id), delay);
        timersRef.current.set(agent.id, timer);
      }
    }

    for (const id of walkersRef.current.keys()) {
      if (!currentIds.has(id)) {
        walkersRef.current.delete(id);
        const timer = timersRef.current.get(id);
        if (timer) clearTimeout(timer);
        timersRef.current.delete(id);
      }
    }
  }, [agents, initWalker, executeRoutine]);

  useEffect(() => {
    return () => {
      for (const timer of timersRef.current.values()) {
        clearTimeout(timer);
      }
    };
  }, []);

  const positions = new Map<string, SeatPosition & { isWalking: boolean; hasChai?: boolean }>();
  for (const agent of agents) {
    if (agent.status === "working") {
      const seat = assignedSeats.get(agent.id);
      if (seat) positions.set(agent.id, { ...seat, isWalking: false, hasChai: false });
    } else {
      const walker = walkersRef.current.get(agent.id);
      if (walker) {
        positions.set(agent.id, {
          x: walker.x,
          y: walker.y,
          direction: walker.direction,
          deskX: walker.x,
          deskY: walker.y,
          zone: walker.hasChai ? "break" : "idle",
          isWalking: walker.isWalking,
          hasChai: walker.hasChai,
        });
      }
    }
  }

  return positions;
}
