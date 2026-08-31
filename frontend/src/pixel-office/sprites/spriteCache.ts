import type { SpriteData } from '../types';

const zoomCaches = new Map<number, WeakMap<SpriteData, HTMLCanvasElement>>();

// ── Outline sprite generation ─────────────────────────────────

const outlineCache = new WeakMap<SpriteData, SpriteData>();
const darkOutlineCache = new WeakMap<SpriteData, SpriteData>();

function buildOutlineSprite(sprite: SpriteData, color: string): SpriteData {
  const rows = sprite.length;
  const cols = sprite[0].length;
  const outline: string[][] = [];
  for (let r = 0; r < rows + 2; r++) {
    outline.push(new Array<string>(cols + 2).fill(''));
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (sprite[r][c] === '') continue;
      const er = r + 1;
      const ec = c + 1;
      if (outline[er - 1][ec] === '') outline[er - 1][ec] = color;
      if (outline[er + 1][ec] === '') outline[er + 1][ec] = color;
      if (outline[er][ec - 1] === '') outline[er][ec - 1] = color;
      if (outline[er][ec + 1] === '') outline[er][ec + 1] = color;
    }
  }

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (sprite[r][c] !== '') outline[r + 1][c + 1] = '';
    }
  }

  return outline;
}

/** Generate a 1px white outline SpriteData (2px larger in each dimension) */
export function getOutlineSprite(sprite: SpriteData): SpriteData {
  const cached = outlineCache.get(sprite);
  if (cached) return cached;
  const outline = buildOutlineSprite(sprite, '#FFFFFF');
  outlineCache.set(sprite, outline);
  return outline;
}

/** A subdued hard outline used by the normal scene pass for pixel separation. */
export function getDarkOutlineSprite(sprite: SpriteData): SpriteData {
  const cached = darkOutlineCache.get(sprite);
  if (cached) return cached;
  const outline = buildOutlineSprite(sprite, '#0a1018');
  darkOutlineCache.set(sprite, outline);
  return outline;
}

export function getCachedSprite(sprite: SpriteData, zoom: number): HTMLCanvasElement {
  let cache = zoomCaches.get(zoom);
  if (!cache) {
    cache = new WeakMap();
    zoomCaches.set(zoom, cache);
  }

  const cached = cache.get(sprite);
  if (cached) return cached;

  const rows = sprite.length;
  const cols = sprite[0].length;
  const canvas = document.createElement('canvas');
  canvas.width = cols * zoom;
  canvas.height = rows * zoom;
  const ctx = canvas.getContext('2d')!;
  ctx.imageSmoothingEnabled = false;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const color = sprite[r][c];
      if (color === '') continue;
      ctx.fillStyle = color;
      ctx.fillRect(c * zoom, r * zoom, zoom, zoom);
    }
  }

  cache.set(sprite, canvas);
  return canvas;
}
