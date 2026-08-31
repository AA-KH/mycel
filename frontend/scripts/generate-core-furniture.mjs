/**
 * Mycel core-furniture generator — "dark theme" pass.
 *
 * The upstream asset pack ships light, pastel sprites (pine desks, white
 * monitors, mint chairs, cream sofas). Dropped onto the reference floor plan's
 * near-black shell they read as a different game. This script redraws every
 * core sprite the Mycel layout actually uses in the reference art direction:
 *
 *   · walnut/espresso woods instead of pine
 *   · charcoal-navy metal (#1b2029 → #586477) instead of light gray
 *   · monitors are DARK bezels with a LIT UI screen (the reference's signature)
 *   · saturated accents only on small surfaces (books, LEDs, upholstery)
 *
 * It also adds props the layout needs but the pack never had: toilet stalls
 * (so the restrooms stop being furnished with benches/tables) and a NOC console
 * + patch-panel rack so the server room is not six clones of one sprite.
 *
 * Overrides are merged INTO furniture-catalog.json by id, so rotation-group
 * metadata written by the asset pack / props pass (groupId, orientation, state,
 * rotationScheme, mirrorSide) survives untouched.
 *
 * Run: node scripts/generate-core-furniture.mjs
 *      SHEET=/tmp/core.png node scripts/generate-core-furniture.mjs   (QA sheet)
 */

import { deflateSync } from 'zlib';
import { mkdirSync, existsSync, readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS = resolve(__dirname, '../public/assets');

// ── PNG encoder (no deps) ───────────────────────────────────────
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
    if (x < 0 || y < 0 || x >= this.w || y >= this.h || !hex) return this;
    const i = (y * this.w + x) * 4;
    this.buf[i] = parseInt(hex.slice(1, 3), 16);
    this.buf[i + 1] = parseInt(hex.slice(3, 5), 16);
    this.buf[i + 2] = parseInt(hex.slice(5, 7), 16);
    this.buf[i + 3] = hex.length > 7 ? parseInt(hex.slice(7, 9), 16) : 255;
    return this;
  }

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

  stroke(x, y, w, h, hex) {
    this.hline(x, y, w, hex);
    this.hline(x, y + h - 1, w, hex);
    this.vline(x, y, h, hex);
    this.vline(x + w - 1, y, h, hex);
    return this;
  }

  /** Filled rect + outline + optional top highlight / bottom shadow rows. */
  box(x, y, w, h, body, outline, hl, sh) {
    this.fill(x, y, w, h, body);
    if (outline) this.stroke(x, y, w, h, outline);
    if (hl) this.hline(x + 1, y + 1, w - 2, hl);
    if (sh) this.hline(x + 1, y + h - 2, w - 2, sh);
    return this;
  }

  /** Rounded-corner box (1px corner nibble) — reads as soft upholstery. */
  round(x, y, w, h, body, outline) {
    this.box(x, y, w, h, body, outline);
    for (const [cx, cy] of [
      [x, y],
      [x + w - 1, y],
      [x, y + h - 1],
      [x + w - 1, y + h - 1],
    ])
      this.px(cx, cy, '#00000000');
    return this;
  }

  /** Sparse dither for texture (wood grain, carpet, foliage). */
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

// ── Palette (reference art direction) ───────────────────────────
const C = {
  out: '#0a0c11',
  // espresso / walnut woods
  woodD: '#2c1c12',
  wood: '#4a2e1b',
  woodL: '#6a4526',
  woodH: '#8b5d34',
  woodT: '#a0713f', // top-surface highlight
  // charcoal navy metal
  metalD: '#161b24',
  metal: '#242c38',
  metalL: '#37414f',
  steel: '#55606f',
  // screens
  scrOff: '#101a24',
  scrBg: '#dfe9f3',
  scrBg2: '#cbdced',
  ink: '#1b2531',
  // foliage
  leafD: '#1e5533',
  leaf: '#2c7742',
  leafL: '#3f9a56',
  leafH: '#59b96c',
  soil: '#241a13',
  terra: '#8a4b2a',
  terraD: '#5c3018',
  // upholstery
  pink: '#c2456e',
  pinkD: '#8d2c4d',
  pinkL: '#dd6c8f',
  // accents
  amber: '#f0b23a',
  cyan: '#4fbce8',
  blue: '#4a86d8',
  green: '#4f9d54',
  red: '#c0453f',
  purple: '#8b6bc4',
  led: '#7ce08a',
  white: '#e9eef4',
  paper: '#e6dcc6',
  brass: '#c19a34',
  gray: '#7c8797',
};

const BOOK_SPINES = [C.red, C.blue, C.amber, C.green, C.purple, C.cyan, C.paper, C.pink];

const defs = [];
/** Register an override / new prop. `draw(s)` gets a fresh tw*16 × th*16 canvas. */
function prop(id, name, category, tw, th, draw, opts = {}) {
  defs.push({ id, name, category, tw, th, draw, opts });
}

// ═══ Desks ══════════════════════════════════════════════════════
/** Walnut desk, 3/4 view: lit top plane, dark apron, cast shadow. */
prop('DESK_FRONT', 'Desk', 'desks', 3, 2, (s) => {
  s.fill(2, 30, 44, 2, '#00000044'); // contact shadow
  s.box(0, 4, 48, 24, C.wood, C.out);
  // top plane
  s.fill(1, 5, 46, 12, C.woodL);
  s.hline(1, 5, 46, C.woodT);
  s.speck(2, 7, 44, 9, C.woodH, 7);
  s.hline(1, 16, 46, C.woodD); // front lip of the top
  // apron + drawer bank
  s.fill(1, 17, 46, 10, C.wood);
  s.speck(1, 18, 46, 8, C.woodL, 11);
  s.box(30, 18, 15, 8, C.woodD, C.out);
  s.hline(33, 21, 9, C.brass);
  // legs
  s.fill(2, 27, 5, 4, C.woodD);
  s.fill(41, 27, 5, 4, C.woodD);
  s.hline(7, 27, 34, C.woodD);
  s.stroke(0, 4, 48, 24, C.out);
});

prop('DESK_SIDE', 'Desk', 'desks', 1, 4, (s) => {
  s.fill(2, 62, 12, 2, '#00000044');
  s.box(1, 2, 14, 58, C.wood, C.out);
  s.fill(2, 3, 12, 52, C.woodL);
  s.vline(2, 3, 52, C.woodT);
  s.speck(3, 5, 10, 48, C.woodH, 9);
  s.hline(2, 55, 12, C.woodD);
  s.fill(2, 56, 12, 3, C.wood);
  s.fill(2, 59, 4, 3, C.woodD);
  s.fill(10, 59, 4, 3, C.woodD);
});

prop('SMALL_TABLE_FRONT', 'Small Table', 'desks', 2, 2, (s) => {
  s.fill(4, 28, 24, 2, '#00000044');
  s.box(2, 8, 28, 14, C.wood, C.out);
  s.fill(3, 9, 26, 8, C.woodL);
  s.hline(3, 9, 26, C.woodT);
  s.speck(4, 11, 24, 5, C.woodH, 7);
  s.hline(3, 17, 26, C.woodD);
  s.fill(5, 22, 4, 7, C.woodD);
  s.fill(23, 22, 4, 7, C.woodD);
});

prop('COFFEE_TABLE', 'Coffee Table', 'desks', 2, 2, (s) => {
  s.fill(4, 26, 24, 2, '#00000044');
  s.box(3, 10, 26, 12, C.woodD, C.out);
  s.fill(4, 11, 24, 7, C.wood);
  s.hline(4, 11, 24, C.woodH);
  s.speck(5, 13, 22, 4, C.woodL, 7);
  // magazine + coaster on the glass top
  s.box(7, 12, 8, 5, C.paper, C.out);
  s.hline(9, 14, 4, C.red);
  s.box(19, 13, 4, 4, C.metalD, C.out);
  s.px(21, 15, C.cyan);
  s.fill(5, 22, 3, 5, C.woodD);
  s.fill(24, 22, 3, 5, C.woodD);
});

// ═══ Monitors ═══════════════════════════════════════════════════
/** Shared chassis: dark bezel, thin stand, keyboard below (desk-top view). */
function monitorChassis(s) {
  s.box(0, 1, 16, 18, C.metal, C.out);
  s.hline(1, 2, 14, C.metalL);
  s.fill(2, 3, 12, 13, C.metalD);
  // stand + base
  s.fill(7, 19, 2, 3, C.steel);
  s.box(4, 21, 8, 3, C.metal, C.out);
  // keyboard
  s.box(1, 25, 14, 5, C.metal, C.out);
  s.hline(2, 26, 12, C.metalL);
  for (let x = 2; x < 14; x += 2) s.vline(x, 27, 2, C.metalD);
  s.px(15, 27, C.steel); // mouse
}

/** Lit UI screen — variant 0 dashboard, 1 code, 2 chat/kanban. */
function litScreen(s, variant) {
  s.fill(3, 4, 10, 11, C.scrBg);
  s.hline(3, 4, 10, C.white);
  if (variant === 0) {
    s.hline(4, 6, 8, C.ink);
    s.fill(4, 8, 2, 6, C.blue);
    s.fill(7, 10, 2, 4, C.green);
    s.fill(10, 7, 2, 7, C.amber);
  } else if (variant === 1) {
    s.fill(3, 4, 10, 11, C.ink);
    s.hline(4, 6, 5, C.cyan);
    s.hline(4, 8, 7, C.green);
    s.hline(5, 10, 4, C.amber);
    s.hline(4, 12, 6, C.purple);
  } else {
    s.fill(4, 6, 5, 2, C.blue);
    s.fill(7, 9, 5, 2, C.pink);
    s.fill(4, 12, 6, 2, C.green);
  }
  s.fill(3, 15, 10, 1, '#00000033');
}

prop('PC_FRONT_ON_1', 'PC', 'electronics', 1, 2, (s) => {
  monitorChassis(s);
  litScreen(s, 0);
  s.px(14, 17, C.led);
});
prop('PC_FRONT_ON_2', 'PC', 'electronics', 1, 2, (s) => {
  monitorChassis(s);
  litScreen(s, 1);
  s.px(14, 17, C.led);
});
prop('PC_FRONT_ON_3', 'PC', 'electronics', 1, 2, (s) => {
  monitorChassis(s);
  litScreen(s, 2);
  s.px(14, 17, C.led);
});
prop('PC_FRONT_OFF', 'PC', 'electronics', 1, 2, (s) => {
  monitorChassis(s);
  s.fill(3, 4, 10, 11, C.scrOff);
  s.hline(4, 5, 6, '#1b2a38');
  s.px(4, 6, '#243543');
  s.px(14, 17, '#3a4452');
});
prop('PC_BACK', 'PC', 'electronics', 1, 2, (s) => {
  monitorChassis(s);
  s.fill(3, 4, 10, 11, C.metal);
  for (let y = 5; y < 14; y += 2) s.hline(4, y, 8, C.metalD);
  s.box(6, 8, 4, 4, C.metalL, C.out);
});
prop('PC_SIDE', 'PC', 'electronics', 1, 2, (s) => {
  s.box(5, 1, 6, 18, C.metal, C.out);
  s.vline(6, 2, 16, C.metalL);
  s.fill(7, 3, 3, 13, C.metalD);
  s.vline(9, 4, 10, C.scrBg2);
  s.fill(7, 19, 2, 3, C.steel);
  s.box(4, 21, 8, 3, C.metal, C.out);
  s.box(3, 25, 10, 5, C.metal, C.out);
  s.hline(4, 26, 8, C.metalL);
});

// ═══ Seating ════════════════════════════════════════════════════
/** Task chair, viewed from behind (agents sit facing the desk below). */
prop('CUSHIONED_CHAIR_FRONT', 'Cushioned Chair', 'chairs', 1, 1, (s) => {
  s.round(3, 0, 10, 8, C.metal, C.out); // backrest
  s.hline(4, 1, 8, C.metalL);
  s.hline(4, 3, 8, '#404d60');
  s.round(2, 7, 12, 6, '#2b3341', C.out); // seat
  s.hline(3, 8, 10, C.metalL);
  s.fill(7, 12, 2, 2, C.steel); // gas post
  s.hline(3, 14, 10, C.metalD); // star base
  s.px(3, 15, C.metalD);
  s.px(12, 15, C.metalD);
  s.px(8, 15, C.metalD);
});

prop('CUSHIONED_CHAIR_BACK', 'Cushioned Chair', 'chairs', 1, 1, (s) => {
  s.round(3, 0, 10, 7, '#2b3341', C.out);
  s.hline(4, 1, 8, C.metalL);
  s.round(2, 6, 12, 7, C.metal, C.out); // seat pan seen from front
  s.hline(3, 7, 10, '#404d60');
  s.hline(3, 11, 10, C.metalD);
  s.fill(7, 12, 2, 2, C.steel);
  s.hline(3, 14, 10, C.metalD);
  s.px(2, 15, C.metalD);
  s.px(13, 15, C.metalD);
});

prop('CUSHIONED_CHAIR_SIDE', 'Cushioned Chair', 'chairs', 1, 1, (s) => {
  s.round(3, 0, 5, 9, C.metal, C.out);
  s.vline(4, 1, 7, C.metalL);
  s.round(3, 8, 10, 5, '#2b3341', C.out);
  s.hline(4, 9, 8, C.metalL);
  s.fill(7, 12, 2, 2, C.steel);
  s.hline(4, 14, 9, C.metalD);
});

prop('CUSHIONED_BENCH', 'Cushioned Bench', 'chairs', 1, 1, (s) => {
  s.round(1, 3, 14, 9, C.pinkD, C.out);
  s.hline(2, 4, 12, C.pink);
  s.hline(2, 7, 12, C.pinkL);
  s.fill(2, 12, 2, 3, C.woodD);
  s.fill(12, 12, 2, 3, C.woodD);
});

prop('WOODEN_BENCH', 'Wooden Bench', 'chairs', 1, 1, (s) => {
  s.box(1, 4, 14, 7, C.wood, C.out);
  s.hline(2, 5, 12, C.woodH);
  s.hline(2, 8, 12, C.woodD);
  s.fill(2, 11, 2, 4, C.woodD);
  s.fill(12, 11, 2, 4, C.woodD);
});

// ═══ Sofas (break lounge — reference magenta upholstery) ════════
prop('SOFA_FRONT', 'Sofa', 'chairs', 2, 1, (s) => {
  s.round(0, 0, 32, 8, C.pinkD, C.out); // backrest
  s.hline(2, 1, 28, C.pink);
  s.vline(15, 2, 5, C.pinkD);
  s.round(0, 6, 32, 8, C.pink, C.out); // seat cushions
  s.hline(2, 7, 28, C.pinkL);
  s.vline(15, 8, 5, C.pinkD);
  s.fill(1, 4, 4, 9, C.pinkD); // arms
  s.fill(27, 4, 4, 9, C.pinkD);
  s.stroke(1, 4, 4, 9, C.out);
  s.stroke(27, 4, 4, 9, C.out);
  s.fill(3, 14, 3, 2, C.woodD);
  s.fill(26, 14, 3, 2, C.woodD);
});

prop('SOFA_BACK', 'Sofa', 'chairs', 2, 1, (s) => {
  s.round(0, 1, 32, 12, C.pinkD, C.out);
  s.hline(2, 2, 28, C.pink);
  s.hline(2, 6, 28, '#7a2542');
  s.vline(15, 3, 9, '#7a2542');
  s.fill(1, 2, 4, 11, C.pink);
  s.fill(27, 2, 4, 11, C.pink);
  s.stroke(1, 2, 4, 11, C.out);
  s.stroke(27, 2, 4, 11, C.out);
  s.fill(3, 13, 3, 2, C.woodD);
  s.fill(26, 13, 3, 2, C.woodD);
});

prop('SOFA_SIDE', 'Sofa', 'chairs', 1, 2, (s) => {
  s.round(0, 0, 9, 32, C.pinkD, C.out); // back panel (facing left)
  s.vline(1, 2, 28, C.pink);
  s.round(6, 1, 10, 30, C.pink, C.out); // seat
  s.vline(7, 3, 26, C.pinkL);
  s.hline(7, 15, 8, C.pinkD);
  s.fill(6, 1, 9, 4, C.pinkD);
  s.fill(6, 27, 9, 4, C.pinkD);
  s.fill(7, 30, 3, 2, C.woodD);
});

// ═══ Storage / wall units ═══════════════════════════════════════
function bookRow(s, x, y, w, h, seed) {
  s.fill(x, y, w, h, '#0f131b');
  let cx = x;
  let i = seed;
  while (cx < x + w - 1) {
    const bw = 1 + (i % 3 === 0 ? 1 : 0);
    const bh = h - 1 - (i % 3 === 1 ? 1 : 0);
    s.fill(cx, y + (h - bh), bw, bh, BOOK_SPINES[i % BOOK_SPINES.length]);
    cx += bw + 1;
    i++;
  }
}

prop('BOOKSHELF', 'Bookshelf', 'wall', 2, 1, (s) => {
  s.box(0, 0, 32, 16, C.woodD, C.out);
  bookRow(s, 2, 2, 28, 5, 1);
  s.hline(1, 7, 30, C.woodL);
  bookRow(s, 2, 9, 28, 5, 4);
  s.hline(1, 14, 30, C.woodL);
  s.hline(0, 15, 32, C.out);
});

prop('DOUBLE_BOOKSHELF', 'Double Bookshelf', 'wall', 2, 2, (s) => {
  s.box(0, 0, 32, 32, C.woodD, C.out);
  let seed = 0;
  for (let r = 0; r < 4; r++) {
    bookRow(s, 2, 2 + r * 8, 28, 6, seed);
    s.hline(1, 8 + r * 8, 30, C.woodL);
    seed += 3;
  }
  s.vline(15, 1, 30, '#1c130d');
});

prop('BIN', 'Bin', 'misc', 1, 1, (s) => {
  s.box(4, 4, 9, 11, C.metal, C.out);
  s.hline(5, 5, 7, C.metalL);
  s.vline(7, 6, 8, C.metalD);
  s.vline(10, 6, 8, C.metalD);
  s.box(3, 2, 11, 3, C.metalL, C.out);
  s.hline(6, 15, 5, '#00000044');
});

prop('CLOCK', 'Clock', 'wall', 1, 2, (s) => {
  s.round(2, 2, 12, 12, C.metalD, C.out);
  s.fill(4, 4, 8, 8, C.white);
  s.px(3, 7, C.white);
  s.px(12, 7, C.white);
  s.px(7, 3, C.white);
  s.px(7, 12, C.white);
  s.vline(7, 5, 3, C.ink); // hands
  s.hline(8, 7, 3, C.red);
  s.px(7, 7, C.ink);
});

// ═══ Greenery ═══════════════════════════════════════════════════
function pot(s, x, y, w, h) {
  s.box(x, y, w, h, C.terra, C.out);
  s.hline(x + 1, y + 1, w - 2, '#a35c34');
  s.hline(x + 1, y + h - 2, w - 2, C.terraD);
  s.fill(x + 1, y, w - 2, 1, C.soil);
}

/** Layered frond blob — the reference's plants are dense and dark. */
function frond(s, cx, cy, r) {
  for (let y = -r; y <= r; y++) {
    for (let x = -r; x <= r; x++) {
      const d = Math.abs(x) + Math.abs(y) * 1.2;
      if (d > r) continue;
      const c = d > r - 1 ? C.leafD : d > r - 2.5 ? C.leaf : C.leafL;
      s.px(cx + x, cy + y, c);
    }
  }
}

prop('PLANT', 'Plant', 'decor', 1, 2, (s) => {
  frond(s, 8, 10, 6);
  frond(s, 4, 13, 4);
  frond(s, 12, 12, 4);
  s.speck(2, 5, 12, 12, C.leafH, 9);
  s.vline(8, 16, 6, C.leafD);
  pot(s, 4, 22, 9, 9);
  s.fill(6, 31, 5, 1, '#00000044');
});

prop('PLANT_2', 'Plant (Tall)', 'decor', 1, 2, (s) => {
  s.vline(8, 8, 14, C.leafD);
  for (const [x, y, r] of [
    [8, 5, 4],
    [4, 9, 3],
    [12, 8, 3],
    [5, 15, 3],
    [11, 14, 3],
  ])
    frond(s, x, y, r);
  s.speck(2, 3, 12, 16, C.leafH, 11);
  pot(s, 5, 22, 7, 9);
});

prop('CACTUS', 'Cactus', 'decor', 1, 2, (s) => {
  s.box(6, 6, 5, 17, C.leaf, C.out);
  s.vline(7, 7, 15, C.leafL);
  s.box(2, 11, 4, 7, C.leaf, C.out);
  s.box(11, 14, 4, 6, C.leaf, C.out);
  s.px(8, 9, C.leafH);
  s.px(8, 15, C.leafH);
  s.px(8, 8, C.pink); // bloom
  pot(s, 4, 23, 9, 8);
});

prop('LARGE_PLANT', 'Large Plant', 'decor', 2, 3, (s) => {
  s.vline(16, 18, 16, C.leafD);
  s.vline(15, 22, 12, '#173f26');
  for (const [x, y, r] of [
    [16, 10, 8],
    [7, 16, 6],
    [25, 15, 6],
    [11, 24, 5],
    [22, 25, 5],
  ])
    frond(s, x, y, r);
  s.speck(3, 4, 26, 26, C.leafH, 9);
  pot(s, 9, 34, 14, 13);
  s.fill(12, 47, 8, 1, '#00000044');
});

prop('POT', 'Pot', 'decor', 1, 1, (s) => {
  frond(s, 8, 5, 4);
  s.speck(4, 2, 9, 6, C.leafH, 7);
  pot(s, 4, 9, 9, 6);
});

prop('HANGING_PLANT', 'Hanging Plant', 'wall', 1, 2, (s) => {
  s.hline(4, 1, 8, C.metalD); // bracket
  s.vline(8, 1, 3, C.metalD);
  s.box(3, 4, 11, 6, C.terraD, C.out);
  s.hline(4, 5, 9, C.terra);
  frond(s, 8, 4, 4);
  // trailing vines
  for (const [x, len] of [
    [4, 11],
    [8, 16],
    [12, 9],
  ]) {
    for (let i = 0; i < len; i++) s.px(x + (i % 2), 10 + i, i % 3 === 0 ? C.leafL : C.leafD);
  }
});

prop('COFFEE', 'Coffee', 'misc', 1, 1, (s) => {
  s.box(4, 5, 8, 8, C.white, C.out);
  s.fill(5, 6, 6, 2, '#4a2c18');
  s.hline(5, 12, 6, C.gray);
  s.px(12, 8, C.white);
  s.px(12, 9, C.white);
  s.px(7, 3, '#ffffff55');
  s.px(9, 2, '#ffffff33');
});

// ═══ New props the layout needs ═════════════════════════════════
/** Restroom stall pair — replaces the benches the pack forced into toilets. */
prop('TOILET_STALL', 'Toilet Stall', 'misc', 2, 2, (s) => {
  s.box(0, 0, 32, 26, '#2f3a45', C.out); // partition block
  s.hline(1, 1, 30, '#3f4c59');
  s.vline(15, 1, 24, C.out); // divider
  for (const x of [1, 16]) {
    s.box(x, 4, 15, 21, '#3a4652', C.out); // stall door
    s.fill(x + 2, 6, 11, 12, '#33404b');
    s.hline(x + 2, 6, 11, '#46545f');
    s.px(x + 12, 14, C.brass); // latch
    s.hline(x + 3, 21, 9, '#2a343d');
  }
  s.fill(2, 26, 28, 1, '#00000044');
});

/** Patch-panel cabinet so the rack wall is not one sprite six times. */
prop('SERVER_RACK_3', 'Patch Panel', 'electronics', 1, 2, (s) => {
  s.box(1, 0, 14, 31, C.metalD, C.out);
  s.hline(2, 1, 12, C.metalL);
  for (let y = 3; y < 27; y += 6) {
    s.fill(3, y, 10, 4, '#1d2530');
    for (let x = 3; x < 13; x += 2) s.px(x, y + 1, y % 12 === 3 ? C.cyan : C.led);
    // patch cables sagging out of the panel
    for (let x = 3; x < 13; x += 3) s.px(x, y + 3, x % 2 ? C.amber : C.blue);
  }
  s.fill(3, 27, 10, 3, '#1d2530');
  s.px(4, 28, C.red);
  s.px(6, 28, C.led);
});

/** NOC console: two lit screens on a steel bench (server-room ops station). */
prop('SERVER_CONSOLE', 'Ops Console', 'electronics', 2, 2, (s) => {
  // screens
  for (const x of [2, 17]) {
    s.box(x, 2, 13, 12, C.metal, C.out);
    s.fill(x + 2, 4, 9, 8, C.ink);
    s.hline(x + 3, 5, 5, C.led);
    s.hline(x + 3, 7, 7, C.cyan);
    s.hline(x + 3, 9, 4, C.amber);
    s.fill(x + 5, 14, 3, 2, C.steel);
  }
  // bench
  s.box(0, 16, 32, 9, C.metal, C.out);
  s.hline(1, 17, 30, C.metalL);
  s.fill(2, 20, 12, 3, C.metalD); // keyboard
  s.fill(18, 20, 10, 3, C.metalD);
  s.fill(1, 25, 4, 5, C.metalD);
  s.fill(27, 25, 4, 5, C.metalD);
  s.fill(4, 30, 24, 1, '#00000044');
});

// ── Emit sprites + merge catalog ────────────────────────────────
const catalogPath = resolve(ASSETS, 'furniture-catalog.json');
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));
const byId = new Map(catalog.map((e) => [e.id, e]));

for (const d of defs) {
  const w = d.tw * 16;
  const h = d.th * 16;
  const s = new S(w, h);
  d.draw(s);

  const existing = byId.get(d.id);
  // Keep the pack's directory layout (rotation groups live in one folder).
  const relPath = existing?.furniturePath ?? `furniture/${d.id}/${d.id}.png`;
  const file = existing?.file ?? `${d.id}.png`;
  const abs = resolve(ASSETS, relPath);
  mkdirSync(dirname(abs), { recursive: true });
  writeFileSync(abs, s.png());

  const manifestPath = resolve(dirname(abs), 'manifest.json');
  const manifest = existsSync(manifestPath)
    ? JSON.parse(readFileSync(manifestPath, 'utf8'))
    : { id: d.id, name: d.name, category: d.category };
  manifest.width = w;
  manifest.height = h;
  manifest.footprintW = d.tw;
  manifest.footprintH = d.th;
  writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

  if (existing) {
    // Redraw only: geometry is identical, rotation metadata must survive.
    existing.width = w;
    existing.height = h;
    existing.footprintW = d.tw;
    existing.footprintH = d.th;
  } else {
    catalog.push({
      id: d.id,
      name: d.name,
      label: d.name,
      category: d.category,
      file,
      furniturePath: relPath,
      width: w,
      height: h,
      footprintW: d.tw,
      footprintH: d.th,
      isDesk: !!d.opts.desk,
      canPlaceOnWalls: !!d.opts.wall,
      canPlaceOnSurfaces: !!d.opts.surface,
      backgroundTiles: d.opts.bg ?? 0,
      groupId: d.id,
    });
  }
  console.log(`✓ ${d.id} (${w}x${h}) → ${relPath}`);
}

writeFileSync(catalogPath, JSON.stringify(catalog, null, 1));
console.log(`✓ furniture-catalog.json merged (${catalog.length} entries)`);

// ── QA contact sheet ────────────────────────────────────────────
if (process.env.SHEET) {
  const SCALE = 4;
  const CELL = 52;
  const COLS = 8;
  const rows = Math.ceil(defs.length / COLS);
  const sheet = new S(COLS * CELL * SCALE, rows * CELL * SCALE);
  sheet.fill(0, 0, sheet.w, sheet.h, '#12161f');
  defs.forEach((d, i) => {
    const gx = (i % COLS) * CELL * SCALE;
    const gy = Math.floor(i / COLS) * CELL * SCALE;
    const src = new S(d.tw * 16, d.th * 16);
    d.draw(src);
    sheet.fill(gx + 2, gy + 2, CELL * SCALE - 4, CELL * SCALE - 4, '#1e2532');
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
  });
  writeFileSync(process.env.SHEET, sheet.png());
  console.log(`✓ contact sheet → ${process.env.SHEET}`);
}
