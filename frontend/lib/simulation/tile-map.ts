/* ------------------------------------------------------------------ */
/* BFS Pathfinding on 4-connected Grid                                  */
/* Adapted from pixel-agents/tileMap.ts — operates on TileInfo[][].    */
/* ------------------------------------------------------------------ */

import type { TileInfo } from './map-data';

/**
 * Extra, per-agent walkability constraints.
 *
 * `reserved` holds tiles owned by *some* agent (every assigned seat).
 * `allow` is the single reserved tile the current agent owns, so it can
 * still reach its own chair while being kept out of everyone else's.
 */
export interface PathOptions {
  reserved?: Set<string>;
  allow?: string;
}

/** True when a tile is reserved by an agent other than the one pathing. */
function isReservedByOther(key: string, opts?: PathOptions): boolean {
  if (!opts?.reserved) return false;
  if (opts.allow === key) return false;
  return opts.reserved.has(key);
}

/** Check if a tile is walkable (floor and not blocked by furniture) */
export function isWalkable(
  col: number,
  row: number,
  grid: TileInfo[][],
  blockedTiles: Set<string>,
  opts?: PathOptions,
): boolean {
  const rows = grid.length;
  const cols = rows > 0 ? grid[0].length : 0;
  if (row < 0 || row >= rows || col < 0 || col >= cols) return false;
  const t = grid[row][col];
  if (t.type !== 'floor') return false;
  const key = `${col},${row}`;
  if (blockedTiles.has(key)) return false;
  if (isReservedByOther(key, opts)) return false;
  return true;
}

/** Get all walkable tile positions on the entire map */
export function getWalkableTiles(
  grid: TileInfo[][],
  blockedTiles: Set<string>,
  opts?: PathOptions,
): Array<{ col: number; row: number }> {
  const rows = grid.length;
  const cols = rows > 0 ? grid[0].length : 0;
  const tiles: Array<{ col: number; row: number }> = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (isWalkable(c, r, grid, blockedTiles, opts)) {
        tiles.push({ col: c, row: r });
      }
    }
  }
  return tiles;
}

/** Get walkable tiles within a rectangular zone (for lounge wandering) */
export function getWalkableTilesInZone(
  grid: TileInfo[][],
  blockedTiles: Set<string>,
  zone: { c1: number; r1: number; c2: number; r2: number },
  opts?: PathOptions,
): Array<{ col: number; row: number }> {
  const tiles: Array<{ col: number; row: number }> = [];
  for (let r = zone.r1; r <= zone.r2; r++) {
    for (let c = zone.c1; c <= zone.c2; c++) {
      if (isWalkable(c, r, grid, blockedTiles, opts)) {
        tiles.push({ col: c, row: r });
      }
    }
  }
  return tiles;
}

/**
 * BFS pathfinding on a 4-connected grid (no diagonals).
 * Returns the path **excluding the start** and **including the end**.
 * Returns [] if start === end, or no path exists.
 */
export function findPath(
  startCol: number,
  startRow: number,
  endCol: number,
  endRow: number,
  grid: TileInfo[][],
  blockedTiles: Set<string>,
  opts?: PathOptions,
): Array<{ col: number; row: number }> {
  if (startCol === endCol && startRow === endRow) return [];

  const key = (c: number, r: number) => `${c},${r}`;
  const startKey = key(startCol, startRow);
  const endKey = key(endCol, endRow);

  // Never allow a destination that belongs to another agent.
  if (isReservedByOther(endKey, opts)) return [];

  // End tile must be walkable (or we treat it as walkable if it's a seat)
  if (!isWalkable(endCol, endRow, grid, blockedTiles, opts)) {
    // Allow pathfinding TO a seat tile even if it's technically in blockedTiles
    // (some seats may overlap with chair furniture that was excluded, but just in case)
    const t = grid[endRow]?.[endCol];
    if (!t || t.type !== 'floor') return [];
  }

  const visited = new Set<string>();
  visited.add(startKey);

  const parent = new Map<string, string>();
  const queue: Array<{ col: number; row: number }> = [{ col: startCol, row: startRow }];

  const dirs = [
    { dc: 0, dr: -1 }, // up
    { dc: 0, dr: 1 },  // down
    { dc: -1, dr: 0 }, // left
    { dc: 1, dr: 0 },  // right
  ];

  while (queue.length > 0) {
    const curr = queue.shift()!;
    const currKey = key(curr.col, curr.row);

    if (currKey === endKey) {
      // Reconstruct path from end to start
      const path: Array<{ col: number; row: number }> = [];
      let k = endKey;
      while (k !== startKey) {
        const [c, r] = k.split(',').map(Number);
        path.unshift({ col: c, row: r });
        k = parent.get(k)!;
      }
      return path;
    }

    for (const d of dirs) {
      const nc = curr.col + d.dc;
      const nr = curr.row + d.dr;
      const nk = key(nc, nr);

      if (visited.has(nk)) continue;

      // Allow walking to the end tile even if blocked (for seat pathfinding),
      // but a tile reserved by another agent is never traversable.
      const isEnd = nc === endCol && nr === endRow;
      if (isReservedByOther(nk, opts)) continue;
      if (!isEnd && !isWalkable(nc, nr, grid, blockedTiles, opts)) continue;
      if (isEnd) {
        const t = grid[nr]?.[nc];
        if (!t || t.type !== 'floor') continue;
      }

      visited.add(nk);
      parent.set(nk, currKey);
      queue.push({ col: nc, row: nr });
    }
  }

  // No path found
  return [];
}
