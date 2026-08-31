/**
 * Mycel office prop generator — "set dressing" pass.
 *
 * Draws a library of pixel-art props procedurally (tiny raster API + 3x5 pixel
 * font, no deps), writes each one to public/assets/furniture/<ID>/<ID>.png with
 * a manifest, and patches furniture-catalog.json so the runtime catalog picks
 * them up.
 *
 * Art direction (matches the reference floor plan):
 *   • near-black outlines, 3-step shading (shadow / body / highlight)
 *   • warm woods + cold steel, muted saturation, small saturated accents
 *   • every sprite is 16px-grid aligned; wall props hang from the wall row and
 *     spill one row into the room, floor props sit inside their footprint
 *
 * Run: node scripts/generate-office-props.mjs
 */

import { deflateSync } from 'zlib';
import { mkdirSync, readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS = resolve(__dirname, '../public/assets');

// ── PNG encoder ─────────────────────────────────────────────────
const CRC_TABLE = (() => {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
})();

function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}

function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const typeBuf = Buffer.from(type, 'ascii');
  const crcBuf = Buffer.alloc(4);
  crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])));
  return Buffer.concat([len, typeBuf, data, crcBuf]);
}

function encodePng(w, h, rgba) {
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  const raw = Buffer.alloc(h * (1 + w * 4));
  for (let y = 0; y < h; y++) {
    raw[y * (1 + w * 4)] = 0;
    rgba.copy(raw, y * (1 + w * 4) + 1, y * w * 4, (y + 1) * w * 4);
  }
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

// ── Tiny 3x5 pixel font (uppercase + digits) ────────────────────
const FONT = {
  A: ['111', '101', '111', '101', '101'],
  B: ['111', '101', '110', '101', '111'],
  C: ['111', '100', '100', '100', '111'],
  D: ['110', '101', '101', '101', '110'],
  E: ['111', '100', '111', '100', '111'],
  F: ['111', '100', '111', '100', '100'],
  G: ['111', '100', '101', '101', '111'],
  H: ['101', '101', '111', '101', '101'],
  I: ['111', '010', '010', '010', '111'],
  J: ['001', '001', '001', '101', '111'],
  K: ['101', '101', '110', '101', '101'],
  L: ['100', '100', '100', '100', '111'],
  M: ['101', '111', '111', '101', '101'],
  N: ['110', '101', '101', '101', '101'],
  O: ['111', '101', '101', '101', '111'],
  P: ['111', '101', '111', '100', '100'],
  Q: ['111', '101', '101', '111', '001'],
  R: ['111', '101', '111', '110', '101'],
  S: ['111', '100', '111', '001', '111'],
  T: ['111', '010', '010', '010', '010'],
  U: ['101', '101', '101', '101', '111'],
  V: ['101', '101', '101', '101', '010'],
  W: ['101', '101', '111', '111', '101'],
  X: ['101', '101', '010', '101', '101'],
  Y: ['101', '101', '010', '010', '010'],
  Z: ['111', '001', '010', '100', '111'],
  0: ['111', '101', '101', '101', '111'],
  1: ['010', '110', '010', '010', '111'],
  2: ['111', '001', '111', '100', '111'],
  3: ['111', '001', '111', '001', '111'],
  4: ['101', '101', '111', '001', '001'],
  5: ['111', '100', '111', '001', '111'],
  6: ['111', '100', '111', '101', '111'],
  7: ['111', '001', '001', '001', '001'],
  8: ['111', '101', '111', '101', '111'],
  9: ['111', '101', '111', '001', '111'],
  ' ': ['000', '000', '000', '000', '000'],
  '.': ['000', '000', '000', '000', '010'],
  '/': ['001', '001', '010', '100', '100'],
};

// ── Raster canvas ───────────────────────────────────────────────
class S {
  constructor(w, h) {
    this.w = w;
    this.h = h;
    this.buf = Buffer.alloc(w * h * 4);
  }

  px(x, y, hex) {
    x = Math.round(x);
    y = Math.round(y);
    if (x < 0 || y < 0 || x >= this.w || y >= this.h || !hex) return;
    const i = (y * this.w + x) * 4;
    this.buf[i] = parseInt(hex.slice(1, 3), 16);
    this.buf[i + 1] = parseInt(hex.slice(3, 5), 16);
    this.buf[i + 2] = parseInt(hex.slice(5, 7), 16);
    this.buf[i + 3] = hex.length > 7 ? parseInt(hex.slice(7, 9), 16) : 255;
  }

  /** Filled rect. */
  fill(x, y, w, h, hex) {
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) this.px(xx, yy, hex);
    return this;
  }

  hline(x, y, w, hex) {
    return this.fill(x, y, w, 1, hex);
  }

  vline(x, y, h, hex) {
    return this.fill(x, y, 1, h, hex);
  }

  /** Rect outline. */
  stroke(x, y, w, h, hex) {
    this.hline(x, y, w, hex);
    this.hline(x, y + h - 1, w, hex);
    this.vline(x, y, h, hex);
    this.vline(x + w - 1, y, h, hex);
    return this;
  }

  /** Filled rect with outline + optional top highlight / bottom shadow. */
  box(x, y, w, h, body, outline, hl, sh) {
    this.fill(x, y, w, h, body);
    if (outline) this.stroke(x, y, w, h, outline);
    if (hl) this.hline(x + 1, y + 1, w - 2, hl);
    if (sh) this.hline(x + 1, y + h - 2, w - 2, sh);
    return this;
  }

  /** 3x5 text, 1px letter spacing. Returns drawn width. */
  text(x, y, str, hex) {
    let cx = x;
    for (const ch of str.toUpperCase()) {
      const glyph = FONT[ch] ?? FONT[' '];
      for (let gy = 0; gy < 5; gy++) {
        for (let gx = 0; gx < 3; gx++) {
          if (glyph[gy][gx] === '1') this.px(cx + gx, y + gy, hex);
        }
      }
      cx += 4;
    }
    return cx - x - 1;
  }

  textCentered(cx, y, str, hex) {
    const w = str.length * 4 - 1;
    return this.text(Math.round(cx - w / 2), y, str, hex);
  }

  /** Sparse 2px dither of `hex` inside a rect (adds texture). */
  speck(x, y, w, h, hex, mod = 3) {
    for (let yy = y; yy < y + h; yy++) {
      for (let xx = x; xx < x + w; xx++) {
        if ((xx * 3 + yy * 5) % mod === 0) this.px(xx, yy, hex);
      }
    }
    return this;
  }

  png() {
    return encodePng(this.w, this.h, this.buf);
  }
}

// ── Palette ─────────────────────────────────────────────────────
const C = {
  out: '#0b0d12',
  shadow: '#00000055',
  woodD: '#3d2617',
  wood: '#5c3a22',
  woodL: '#7c5231',
  woodH: '#a2703f',
  metalD: '#232935',
  metal: '#333b4a',
  metalL: '#4b5568',
  steel: '#6b7688',
  white: '#e9eef4',
  offWhite: '#cfd7e0',
  gray: '#8e99a8',
  glass: '#79b3d6',
  glassD: '#3d6c8e',
  glassL: '#b9e0f2',
  brass: '#c9a227',
  paper: '#efe6d2',
  cork: '#9d7449',
  corkD: '#7d5a36',
  red: '#c0453f',
  redD: '#8e2f2b',
  pink: '#d1547d',
  pinkD: '#a63a5f',
  green: '#4f9d54',
  greenD: '#2f6b39',
  leaf: '#57a05a',
  leafD: '#39743f',
  amber: '#f2b134',
  cyan: '#48b7e8',
  blue: '#3f7fd0',
  led: '#7ce08a',
  purple: '#8b6bc4',
  ink: '#161a22',
};

// ── Prop drawings ───────────────────────────────────────────────
const defs = [];

/**
 * Register a prop.
 * `draw(s)` receives a fresh canvas of width*height.
 */
function prop(id, name, category, tw, th, draw, opts = {}) {
  defs.push({
    id,
    name,
    category,
    tw,
    th,
    draw,
    canPlaceOnWalls: !!opts.wall,
    canPlaceOnSurfaces: !!opts.surface,
    backgroundTiles: opts.bg ?? 0,
    isDesk: !!opts.desk,
  });
}

// ── Windows ─────────────────────────────────────────────────────
prop('WINDOW', 'Window', 'wall', 2, 1, (s) => {
  // 32x16 — horizontal window for top/bottom walls.
  s.box(0, 1, 32, 13, C.metal, C.out, C.metalL, C.metalD);
  s.fill(2, 3, 28, 9, C.glassD);
  for (let i = 0; i < 3; i++) {
    s.fill(2 + i * 10, 3, 8, 9, C.glass);
    s.fill(3 + i * 10, 4, 3, 2, C.glassL);
    s.vline(2 + i * 10 + 6, 4, 7, '#8ec5e4');
  }
  s.hline(0, 14, 32, C.out);
  s.hline(1, 15, 30, C.woodD); // sill
});

prop('WINDOW_SIDE', 'Window (Side)', 'wall', 1, 2, (s) => {
  // 16x32 — vertical window for left/right walls.
  s.box(1, 0, 14, 32, C.metal, C.out, null, null);
  s.fill(3, 2, 10, 28, C.glassD);
  for (let i = 0; i < 3; i++) {
    s.fill(3, 3 + i * 9, 10, 7, C.glass);
    s.fill(4, 4 + i * 9, 3, 2, C.glassL);
  }
  s.vline(8, 2, 28, C.metalL);
});

// ── Doors ───────────────────────────────────────────────────────
prop('WOOD_DOOR', 'Door', 'wall', 1, 2, (s) => {
  s.box(1, 0, 14, 30, C.woodD, C.out, null, null);
  s.box(2, 1, 12, 28, C.wood, C.out, null, null);
  // two recessed panels
  s.box(4, 4, 8, 9, C.woodL, C.woodD, C.woodH, null);
  s.box(4, 16, 8, 9, C.woodL, C.woodD, C.woodH, null);
  s.px(12, 15, C.brass);
  s.px(12, 16, C.brass);
  s.hline(1, 30, 14, C.out);
});

prop('GLASS_DOORS', 'Glass Doors', 'wall', 2, 2, (s) => {
  // 32x32 — main entrance double door, warm glow inside.
  s.box(0, 0, 32, 31, C.metalD, C.out, null, null);
  s.box(2, 2, 13, 27, C.metal, C.out, null, null);
  s.box(17, 2, 13, 27, C.metal, C.out, null, null);
  s.fill(4, 4, 9, 23, '#9fc9dd');
  s.fill(19, 4, 9, 23, '#9fc9dd');
  s.fill(5, 5, 3, 8, C.glassL);
  s.fill(20, 5, 3, 8, C.glassL);
  s.vline(13, 12, 6, C.brass);
  s.vline(18, 12, 6, C.brass);
  s.hline(0, 31, 32, C.out);
});

// ── Wall decor ──────────────────────────────────────────────────
prop('CORK_BOARD', 'Cork Board', 'wall', 2, 1, (s) => {
  s.box(0, 0, 32, 15, C.corkD, C.out, null, null);
  s.fill(2, 2, 28, 11, C.cork);
  s.speck(2, 2, 28, 11, C.corkD, 7);
  const notes = [
    [3, 3, 5, 4, C.amber],
    [9, 3, 6, 4, C.paper],
    [16, 3, 5, 4, C.cyan],
    [22, 3, 7, 4, C.pink],
    [3, 8, 7, 4, C.paper],
    [11, 8, 5, 4, C.green],
    [17, 8, 6, 4, C.amber],
    [24, 8, 5, 4, C.glass],
  ];
  for (const [x, y, w, h, col] of notes) {
    s.fill(x, y, w, h, col);
    s.px(x, y, C.out);
    s.hline(x + 1, y + h - 1, w - 1, '#00000033');
  }
});

prop('PHOTO_WALL', 'Framed Photos', 'wall', 2, 1, (s) => {
  const frame = (x, y, w, h, inner) => {
    s.box(x, y, w, h, C.woodL, C.out, null, C.woodD);
    s.fill(x + 2, y + 2, w - 4, h - 4, inner);
  };
  frame(1, 2, 9, 11, '#4a6b8a');
  s.fill(3, 8, 5, 3, '#6b8fa8');
  s.px(5, 6, C.paper);
  frame(11, 1, 10, 12, '#6b5a8a');
  s.fill(13, 7, 6, 4, '#8a76a8');
  frame(22, 3, 9, 10, '#7d6a4a');
  s.fill(24, 8, 5, 3, '#a08c62');
});

prop('WALL_SHELF', 'Wall Shelf', 'wall', 2, 1, (s) => {
  // books + boxes sitting on a plank
  const books = [C.red, C.blue, C.amber, C.green, C.purple, C.cyan, C.paper, C.pinkD];
  for (let i = 0; i < 8; i++) {
    const x = 2 + i * 3;
    const h = 6 + ((i * 5) % 3);
    s.box(x, 11 - h, 3, h, books[i], C.out, null, null);
  }
  s.hline(0, 11, 32, C.out);
  s.fill(0, 12, 32, 2, C.woodL);
  s.hline(0, 14, 32, C.woodD);
});

prop('TV_SCREEN', 'Wall Screen', 'wall', 2, 1, (s) => {
  s.box(1, 0, 30, 14, C.metalD, C.out, null, null);
  s.fill(3, 2, 26, 10, C.ink);
  // fake code lines
  const rows = [
    [C.led, 4, 3, 9],
    [C.cyan, 4, 5, 13],
    [C.amber, 6, 7, 8],
    [C.led, 4, 9, 16],
    [C.offWhite, 18, 3, 6],
    [C.pink, 20, 5, 5],
  ];
  for (const [col, x, y, w] of rows) s.hline(x, y, w, col);
  s.hline(3, 12, 26, C.metalL);
  s.fill(14, 14, 4, 2, C.metalD);
});

prop('CHART_BOARD', 'Chart Board', 'wall', 2, 1, (s) => {
  s.box(0, 0, 32, 15, C.offWhite, C.out, null, C.gray);
  s.fill(2, 2, 28, 11, C.paper);
  // bar chart + trend line
  const bars = [3, 6, 4, 8, 5, 9];
  bars.forEach((h, i) => {
    s.fill(4 + i * 3, 12 - h, 2, h, i % 2 ? C.green : C.blue);
  });
  s.hline(3, 12, 26, C.gray);
  for (let i = 0; i < 8; i++) s.px(22 + i, 9 - Math.floor(i * 0.8), C.red);
});

prop('WHITEBOARD_KANBAN', 'Kanban Board', 'wall', 2, 1, (s) => {
  s.box(0, 0, 32, 15, C.white, C.out, null, C.gray);
  s.fill(2, 2, 28, 11, '#f5f8fb');
  s.vline(11, 2, 11, C.gray);
  s.vline(21, 2, 11, C.gray);
  const notes = [
    [3, 3, C.amber],
    [3, 7, C.amber],
    [7, 5, C.cyan],
    [13, 3, C.pink],
    [13, 8, C.green],
    [17, 4, C.amber],
    [23, 3, C.green],
    [23, 8, C.cyan],
    [27, 5, C.pink],
  ];
  for (const [x, y, col] of notes) {
    s.fill(x, y, 3, 3, col);
    s.px(x, y, C.out);
  }
});

prop('AC_UNIT', 'AC Unit', 'wall', 2, 1, (s) => {
  s.box(1, 0, 30, 10, C.offWhite, C.out, C.white, C.gray);
  for (let i = 0; i < 4; i++) s.hline(4, 4 + i, 24, i % 2 ? C.gray : C.offWhite);
  s.hline(3, 9, 26, C.out);
  s.px(27, 2, C.led);
});

prop('COMPANY_SIGN', 'Company Sign', 'wall', 3, 2, (s) => {
  // 48x32 lobby plaque
  s.box(1, 1, 46, 26, C.redD, C.out, null, null);
  s.box(3, 3, 42, 22, '#a33832', C.out, '#bf4a42', '#7a2622');
  s.textCentered(24, 8, 'MYCEL', C.brass);
  s.textCentered(24, 16, 'AI COMPANY', '#e8c76a');
  s.hline(4, 13, 40, '#7a2622');
  s.hline(1, 28, 46, C.out);
});

prop('EXIT_SIGN', 'Exit Sign', 'wall', 1, 1, (s) => {
  s.box(2, 3, 12, 8, C.greenD, C.out, null, null);
  s.textCentered(8, 5, 'EX', '#c9f7cf');
  s.px(7, 11, C.metalD);
  s.px(8, 11, C.metalD);
});

// ── Floor furniture ─────────────────────────────────────────────
prop('FILE_CABINET', 'File Cabinet', 'storage', 1, 2, (s) => {
  s.box(1, 4, 14, 27, C.metal, C.out, C.metalL, C.metalD);
  for (let i = 0; i < 3; i++) {
    const y = 7 + i * 8;
    s.box(3, y, 10, 7, C.metalL, C.metalD, null, null);
    s.hline(6, y + 3, 4, C.steel);
  }
  s.hline(1, 31, 14, C.out);
  // paper tray on top
  s.fill(4, 2, 8, 2, C.paper);
  s.px(3, 3, C.out);
  s.px(12, 3, C.out);
});

prop('PRINTER', 'Printer', 'electronics', 1, 2, (s) => {
  s.box(1, 12, 14, 18, C.metalD, C.out, C.metalL, null);
  s.fill(3, 15, 10, 5, C.metal);
  s.hline(3, 21, 10, C.out);
  s.fill(3, 22, 10, 3, C.paper); // output tray
  s.px(12, 14, C.led);
  s.px(4, 14, C.cyan);
  s.fill(5, 9, 6, 3, C.paper); // paper feed
  s.hline(5, 8, 6, C.out);
  s.hline(1, 30, 14, C.out);
});

prop('COFFEE_MACHINE', 'Coffee Machine', 'electronics', 1, 2, (s) => {
  s.box(2, 8, 12, 22, C.metalD, C.out, C.metalL, null);
  s.fill(4, 11, 8, 5, C.ink);
  s.hline(5, 12, 3, C.led);
  s.hline(5, 14, 5, C.steel);
  s.fill(4, 18, 8, 6, C.metal);
  s.fill(6, 20, 4, 4, C.woodD); // cup slot
  s.px(7, 22, C.paper);
  s.px(8, 22, C.paper);
  s.hline(3, 27, 10, C.metalL);
  s.hline(2, 30, 12, C.out);
});

prop('WATER_COOLER', 'Water Cooler', 'electronics', 1, 2, (s) => {
  s.box(4, 3, 8, 10, '#8fd0ea', C.out, null, null); // jug
  s.fill(5, 4, 3, 6, '#c9ecf7');
  s.box(3, 13, 10, 17, C.offWhite, C.out, C.white, C.gray);
  s.fill(5, 17, 6, 4, C.metalD);
  s.px(6, 19, C.cyan);
  s.px(9, 19, C.red);
  s.hline(5, 24, 6, C.gray);
  s.hline(3, 30, 10, C.out);
});

prop('FRIDGE', 'Fridge', 'storage', 1, 2, (s) => {
  s.box(1, 2, 14, 29, C.offWhite, C.out, C.white, C.gray);
  s.hline(2, 13, 12, C.out);
  s.vline(12, 4, 8, C.steel);
  s.vline(12, 15, 12, C.steel);
  s.px(4, 5, C.pink); // magnet
  s.px(6, 8, C.amber);
  s.fill(3, 17, 4, 3, C.paper);
  s.hline(1, 31, 14, C.out);
});

prop('COUNTER', 'Counter', 'desks', 2, 1, (s) => {
  s.fill(0, 2, 32, 3, C.woodH);
  s.hline(0, 1, 32, C.out);
  s.hline(0, 5, 32, C.out);
  s.fill(0, 6, 32, 9, C.wood);
  s.speck(0, 6, 32, 9, C.woodD, 9);
  s.hline(0, 15, 32, C.out);
  s.vline(10, 6, 9, C.woodD);
  s.vline(21, 6, 9, C.woodD);
});

prop('SERVER_RACK_2', 'Server Rack (Mesh)', 'electronics', 1, 2, (s) => {
  s.box(1, 2, 14, 29, C.metalD, C.out, C.metalL, null);
  for (let i = 0; i < 7; i++) {
    const y = 5 + i * 3;
    s.fill(3, y, 10, 2, C.ink);
    s.px(3 + (i % 3), y, i % 2 ? C.led : C.amber);
    s.px(11, y, i % 3 === 0 ? C.cyan : C.led);
  }
  s.fill(3, 27, 10, 2, C.metal);
  s.hline(1, 31, 14, C.out);
  s.px(3, 31, C.ink);
  s.px(12, 31, C.ink);
});

prop('PALM', 'Palm Tree', 'decor', 2, 2, (s) => {
  // pot
  s.box(9, 22, 14, 9, C.woodL, C.out, C.woodH, C.woodD);
  s.fill(11, 21, 10, 2, C.woodD);
  // trunk
  s.fill(15, 12, 2, 10, C.woodD);
  // fronds
  const fronds = [
    [-9, -2],
    [9, -2],
    [-7, -7],
    [7, -7],
    [0, -10],
    [-4, -9],
    [4, -9],
  ];
  for (const [dx, dy] of fronds) {
    for (let t = 0; t <= 9; t++) {
      const x = 16 + (dx * t) / 9;
      const y = 12 + (dy * t) / 9 - Math.sin((t / 9) * Math.PI) * 2;
      s.px(x, y, t > 5 ? C.leaf : C.leafD);
      s.px(x, y + 1, C.leafD);
    }
  }
  s.px(16, 2, C.leaf);
});

prop('DESK_LAMP', 'Desk Lamp', 'misc', 1, 1, (s) => {
  s.fill(5, 12, 6, 2, C.metalD);
  s.vline(8, 6, 6, C.metalL);
  s.box(4, 3, 9, 4, C.amber, C.out, '#ffd980', null);
  s.hline(5, 7, 7, '#ffe9b0');
}, { surface: true });

prop('PAPER_STACK', 'Paper Stack', 'misc', 1, 1, (s) => {
  s.box(3, 8, 11, 6, C.paper, C.out, '#ffffff', C.gray);
  s.hline(5, 10, 7, C.gray);
  s.hline(5, 12, 5, C.gray);
}, { surface: true });

prop('MUG', 'Mug', 'misc', 1, 1, (s) => {
  s.box(5, 8, 7, 6, C.white, C.out, null, C.gray);
  s.px(12, 10, C.out);
  s.px(12, 11, C.out);
  s.fill(6, 9, 5, 2, '#6b4429');
}, { surface: true });

prop('RUG_ACCENT', 'Accent Rug', 'decor', 3, 2, (s) => {
  // low-profile rug (drawn flat, no outline shading so it reads as floor)
  s.fill(0, 4, 48, 25, '#3f5c40');
  s.stroke(0, 4, 48, 25, '#2f4631');
  s.stroke(3, 7, 42, 19, '#587a58');
  s.speck(4, 8, 40, 17, '#476848', 5);
});

// ── Toilet fittings ─────────────────────────────────────────────
prop('URINAL', 'Urinal', 'wall', 1, 1, (s) => {
  s.box(4, 1, 9, 12, C.white, C.out, null, C.gray);
  s.fill(6, 3, 5, 6, '#dbe4ec');
  s.hline(6, 10, 5, C.steel);
  s.px(8, 2, C.steel);
});

prop('TOILET_MIRROR', 'Mirror', 'wall', 1, 1, (s) => {
  s.box(2, 1, 12, 13, C.metalL, C.out, null, null);
  s.fill(4, 3, 8, 9, '#a8d3e6');
  s.fill(5, 4, 2, 4, C.glassL);
});

// ── Build ───────────────────────────────────────────────────────
const catalogPath = resolve(ASSETS, 'furniture-catalog.json');
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));
const newIds = new Set(defs.map((d) => d.id));
const out = catalog.filter((e) => !newIds.has(e.id));

for (const d of defs) {
  const w = d.tw * 16;
  const h = d.th * 16;
  const s = new S(w, h);
  d.draw(s);
  const dir = resolve(ASSETS, 'furniture', d.id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, `${d.id}.png`), s.png());
  const manifest = {
    id: d.id,
    name: d.name,
    category: d.category,
    type: 'asset',
    file: `${d.id}.png`,
    width: w,
    height: h,
    footprintW: d.tw,
    footprintH: d.th,
    canPlaceOnWalls: d.canPlaceOnWalls,
    canPlaceOnSurfaces: d.canPlaceOnSurfaces,
    backgroundTiles: d.backgroundTiles,
  };
  writeFileSync(resolve(dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
  out.push({
    id: d.id,
    name: d.name,
    label: d.name,
    category: d.category,
    file: `${d.id}.png`,
    furniturePath: `furniture/${d.id}/${d.id}.png`,
    width: w,
    height: h,
    footprintW: d.tw,
    footprintH: d.th,
    isDesk: d.isDesk,
    canPlaceOnWalls: d.canPlaceOnWalls,
    canPlaceOnSurfaces: d.canPlaceOnSurfaces,
    backgroundTiles: d.backgroundTiles,
    groupId: d.id,
  });
  console.log(`✓ ${d.id} (${w}x${h})`);
}

writeFileSync(catalogPath, JSON.stringify(out, null, 1));
console.log(`✓ furniture-catalog.json updated (${out.length} entries)`);

// ── Optional QA contact sheet: SHEET=/tmp/props.png node ... ────
if (process.env.SHEET) {
  const SCALE = 4;
  const CELL = 64; // sprite cell in source px
  const COLS = 7;
  const rows = Math.ceil(defs.length / COLS);
  const sheet = new S(COLS * CELL * SCALE, rows * CELL * SCALE);
  sheet.fill(0, 0, sheet.w, sheet.h, '#1b2030');
  defs.forEach((d, i) => {
    const gx = (i % COLS) * CELL * SCALE;
    const gy = Math.floor(i / COLS) * CELL * SCALE;
    const src = new S(d.tw * 16, d.th * 16);
    d.draw(src);
    sheet.fill(gx + 2, gy + 2, CELL * SCALE - 4, CELL * SCALE - 4, '#2a3145');
    for (let y = 0; y < src.h; y++) {
      for (let x = 0; x < src.w; x++) {
        const idx = (y * src.w + x) * 4;
        if (src.buf[idx + 3] === 0) continue;
        const hex = `#${src.buf[idx].toString(16).padStart(2, '0')}${src.buf[idx + 1]
          .toString(16)
          .padStart(2, '0')}${src.buf[idx + 2].toString(16).padStart(2, '0')}`;
        sheet.fill(gx + 8 + x * SCALE, gy + 8 + y * SCALE, SCALE, SCALE, hex);
      }
    }
    sheet.text(gx + 8, gy + CELL * SCALE - 14, d.id.slice(0, 14), '#9fb0c8');
  });
  writeFileSync(process.env.SHEET, sheet.png());
  console.log(`✓ contact sheet → ${process.env.SHEET}`);
}
