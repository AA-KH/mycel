export const TILE_SIZE = 32;
export const TILESET_PATH = "/assets/office-tileset.png"; // Placeholder path

export function getTilePosition(tileIndex: number, columns: number = 10) {
  const x = (tileIndex % columns) * TILE_SIZE;
  const y = Math.floor(tileIndex / columns) * TILE_SIZE;
  return { x, y };
}
