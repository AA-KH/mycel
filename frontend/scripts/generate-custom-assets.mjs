/**
 * Custom pixel-art furniture generator for the Mycel office.
 *
 * Encodes hand-drawn pixel maps into PNGs (no deps — raw zlib + CRC32),
 * writes them into public/assets/furniture/<ID>/, and patches
 * furniture-catalog.json so the runtime catalog picks them up.
 *
 * Run: node scripts/generate-custom-assets.mjs
 */

import { deflateSync } from 'zlib';
import { mkdirSync, readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ASSETS = resolve(__dirname, '../public/assets');

// ── Minimal PNG encoder ─────────────────────────────────────────
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

/** rgba: Uint8Array of w*h*4 */
function encodePng(w, h, rgba) {
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; // bit depth
  ihdr[9] = 6; // RGBA
  const raw = Buffer.alloc(h * (1 + w * 4));
  for (let y = 0; y < h; y++) {
    raw[y * (1 + w * 4)] = 0; // filter none
    rgba.copy(raw, y * (1 + w * 4) + 1, y * w * 4, (y + 1) * w * 4);
  }
  return Buffer.concat([
    sig,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

/** Convert palette + string rows into an RGBA buffer. '.' = transparent. */
function rasterize(palette, rows) {
  const h = rows.length;
  const w = rows[0].length;
  const buf = Buffer.alloc(w * h * 4);
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const ch = rows[y][x];
      if (ch === '.') continue;
      const hex = palette[ch];
      if (!hex) throw new Error(`No palette entry for '${ch}' at ${x},${y}`);
      const i = (y * w + x) * 4;
      buf[i] = parseInt(hex.slice(1, 3), 16);
      buf[i + 1] = parseInt(hex.slice(3, 5), 16);
      buf[i + 2] = parseInt(hex.slice(5, 7), 16);
      buf[i + 3] = hex.length > 7 ? parseInt(hex.slice(7, 9), 16) : 255;
    }
  }
  return { w, h, buf };
}

// ── Pixel art ───────────────────────────────────────────────────

/** SERVER_RACK — tall dark cabinet, unit slots, green/amber LEDs. 16×32. */
const SERVER_RACK = {
  palette: {
    o: '#0b0d12', // outline
    b: '#1c2028', // body dark
    B: '#272c38', // body light
    v: '#141820', // vent slot
    g: '#4ade80', // green led
    a: '#f6b93b', // amber led
    c: '#38bdf8', // cyan led
    s: '#3a4152', // steel highlight
    f: '#101318', // feet
  },
  rows: [
    '................',
    '................',
    '.oooooooooooooo.',
    '.obbbbbbbbbbbbo.',
    '.obssssssssssbo.',
    '.oboooooooooobo.',
    '.obBBBBBBBBBBbo.',
    '.obvvvvvvvvgabo.',
    '.obBBBBBBBBBBbo.',
    '.oboooooooooobo.',
    '.obBBBBBBBBBBbo.',
    '.obvvvvvvvvcgbo.',
    '.obBBBBBBBBBBbo.',
    '.oboooooooooobo.',
    '.obBBBBBBBBBBbo.',
    '.obvvvvvvvvagbo.',
    '.obBBBBBBBBBBbo.',
    '.oboooooooooobo.',
    '.obBBBBBBBBBBbo.',
    '.obvvvvvvvvggbo.',
    '.obBBBBBBBBBBbo.',
    '.oboooooooooobo.',
    '.obBBBBBBBBBBbo.',
    '.obvvvvvvvvcabo.',
    '.obBBBBBBBBBBbo.',
    '.oboooooooooobo.',
    '.obbbbbbbbbbbbo.',
    '.obbbbbbbbbbbbo.',
    '.oooooooooooooo.',
    '..ff........ff..',
    '..ff........ff..',
    '................',
  ],
  entry: {
    id: 'SERVER_RACK',
    name: 'Server Rack',
    label: 'Server Rack',
    category: 'electronics',
    file: 'SERVER_RACK.png',
    furniturePath: 'furniture/SERVER_RACK/SERVER_RACK.png',
    width: 16,
    height: 32,
    footprintW: 1,
    footprintH: 2,
    isDesk: false,
    canPlaceOnWalls: false,
    canPlaceOnSurfaces: false,
    backgroundTiles: 1,
    groupId: 'SERVER_RACK',
  },
};

/** VENDING_MACHINE — red machine, lit window with snacks. 16×32. */
const VENDING_MACHINE = {
  palette: {
    o: '#0b0d12',
    r: '#b03a3a', // body red
    R: '#d05050', // body highlight
    d: '#7c2626', // body shadow
    w: '#131b2b', // window bg
    W: '#20304a', // window shelf
    y: '#f6c945', // snack yellow
    g: '#6fd06f', // snack green
    c: '#5ab6e8', // snack blue
    p: '#e88ab0', // snack pink
    s: '#2a2f3c', // slot
    L: '#e8edf2', // light strip
    k: '#1c2028', // base
  },
  rows: [
    '................',
    '.oooooooooooooo.',
    '.oRRRRRRRRRRRRo.',
    '.oLLLLLLLLLLRdo.',
    '.oRRRRRRRRRRRdo.',
    '.oRowwwwwwwoRdo.',
    '.oRowyygccwoRdo.',
    '.oRowwwwwwwoRdo.',
    '.oRoWWWWWWWoRdo.',
    '.oRowpwygwwoRdo.',
    '.oRowwwwwwwoRdo.',
    '.oRoWWWWWWWoRdo.',
    '.oRowccwpywoRdo.',
    '.oRowwwwwwwoRdo.',
    '.oRoWWWWWWWoRdo.',
    '.oRowgywcwwoRdo.',
    '.oRowwwwwwwoRdo.',
    '.oRoooooooooRdo.',
    '.oRRRRRRRRRRRdo.',
    '.oRossoRRRRRRdo.',
    '.oRossoRoooRRdo.',
    '.oRRRRRRosoRRdo.',
    '.oRRRRRRosoRRdo.',
    '.oRRRRRRoooRRdo.',
    '.oRosssssoRRRdo.',
    '.oRosssssoRRRdo.',
    '.oRRRRRRRRRRRdo.',
    '.oddddddddddddo.',
    '.oooooooooooooo.',
    '.okk........kko.',
    '................',
    '................',
  ],
  entry: {
    id: 'VENDING_MACHINE',
    name: 'Vending Machine',
    label: 'Vending Machine',
    category: 'electronics',
    file: 'VENDING_MACHINE.png',
    furniturePath: 'furniture/VENDING_MACHINE/VENDING_MACHINE.png',
    width: 16,
    height: 32,
    footprintW: 1,
    footprintH: 2,
    isDesk: false,
    canPlaceOnWalls: false,
    canPlaceOnSurfaces: false,
    backgroundTiles: 1,
    groupId: 'VENDING_MACHINE',
  },
};

/** SINK — wall-mounted mirror + white basin for the toilets. 16×32. */
const SINK = {
  palette: {
    o: '#0b0d12',
    m: '#8fc3d9', // mirror glass
    M: '#c9e7f2', // mirror glint
    f: '#3d4454', // frame
    w: '#e8edf2', // porcelain
    W: '#ffffff', // porcelain highlight
    s: '#aeb9c4', // porcelain shadow
    t: '#7d8794', // tap steel
    d: '#5a636e', // drain
    p: '#454c5a', // pipe
  },
  rows: [
    '................',
    '.offffffffffffo.',
    '.ofmmmMmmmmmmfo.',
    '.ofmmMmmmmmmmfo.',
    '.ofmMmmmmmmmmfo.',
    '.ofmmmmmmmmmmfo.',
    '.ofmmmmmmmmmmfo.',
    '.ofmmmmmmmmmmfo.',
    '.offffffffffffo.',
    '................',
    '......ott.......',
    '......ot........',
    '.oooooottoooooo.',
    '.oWWWWWWWWWWWWo.',
    '.oWwwwwwwwwwwso.',
    '.oWwwwwddwwwwso.',
    '.oWwwwwwwwwwwso.',
    '.osssssssssssso.',
    '.oooooooooooooo.',
    '......opp.......',
    '......opp.......',
    '......opp.......',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
  ],
  entry: {
    id: 'SINK',
    name: 'Sink',
    label: 'Sink',
    category: 'wall',
    file: 'SINK.png',
    furniturePath: 'furniture/SINK/SINK.png',
    width: 16,
    height: 32,
    footprintW: 1,
    footprintH: 2,
    isDesk: false,
    canPlaceOnWalls: true,
    canPlaceOnSurfaces: false,
    backgroundTiles: 0,
    groupId: 'SINK',
  },
};

/** Toilet stall door factory — dark door with a colored sign plate. */
function toiletDoor(id, name, signHex) {
  return {
    palette: {
      o: '#0b0d12',
      d: '#343a48', // door body
      D: '#414859', // door light
      k: '#22262f', // door shadow
      n: '#c9d1d9', // knob
      S: signHex, // sign plate
      W: '#f5f7fa', // sign icon
    },
    rows: [
      '................',
      '.oooooooooooooo.',
      '.oDDDDDDDDDDDko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddSSSSSSddko.',
      '.oDddSWWWWSddko.',
      '.oDddSWWWWSddko.',
      '.oDddSSSSSSddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDdDDDDDDDddko.',
      '.oDdkkkkkkkddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddnnko.',
      '.oDddddddddnnko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDdDDDDDDDddko.',
      '.oDdkkkkkkkddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.oDddddddddddko.',
      '.okkkkkkkkkkkko.',
      '.oooooooooooooo.',
    ],
    entry: {
      id,
      name,
      label: name,
      category: 'wall',
      file: `${id}.png`,
      furniturePath: `furniture/${id}/${id}.png`,
      width: 16,
      height: 32,
      footprintW: 1,
      footprintH: 2,
      isDesk: false,
      canPlaceOnWalls: true,
      canPlaceOnSurfaces: false,
      backgroundTiles: 0,
      groupId: id,
    },
  };
}

const TOILET_DOOR_MEN = toiletDoor('TOILET_DOOR_MEN', 'Toilet Door (Men)', '#3b82f6');
const TOILET_DOOR_WOMEN = toiletDoor('TOILET_DOOR_WOMEN', 'Toilet Door (Women)', '#ec4899');

// ── Build ───────────────────────────────────────────────────────
const ASSET_DEFS = [SERVER_RACK, VENDING_MACHINE, SINK, TOILET_DOOR_MEN, TOILET_DOOR_WOMEN];

const catalogPath = resolve(ASSETS, 'furniture-catalog.json');
const catalog = JSON.parse(readFileSync(catalogPath, 'utf8'));
const newIds = new Set(ASSET_DEFS.map((a) => a.entry.id));
const filtered = catalog.filter((e) => !newIds.has(e.id));

for (const def of ASSET_DEFS) {
  const { w, h, buf } = rasterize(def.palette, def.rows);
  if (w !== def.entry.width || h !== def.entry.height) {
    throw new Error(`${def.entry.id}: pixel map is ${w}x${h}, expected ${def.entry.width}x${def.entry.height}`);
  }
  const dir = resolve(ASSETS, 'furniture', def.entry.id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(resolve(dir, def.entry.file), encodePng(w, h, buf));
  writeFileSync(
    resolve(dir, 'manifest.json'),
    JSON.stringify(
      {
        id: def.entry.id,
        name: def.entry.name,
        category: def.entry.category,
        type: 'asset',
        file: def.entry.file,
        width: def.entry.width,
        height: def.entry.height,
        footprintW: def.entry.footprintW,
        footprintH: def.entry.footprintH,
        canPlaceOnWalls: def.entry.canPlaceOnWalls,
        canPlaceOnSurfaces: def.entry.canPlaceOnSurfaces,
        backgroundTiles: def.entry.backgroundTiles,
      },
      null,
      2,
    ),
  );
  filtered.push(def.entry);
  console.log(`✓ ${def.entry.id} (${w}x${h})`);
}

writeFileSync(catalogPath, JSON.stringify(filtered, null, 1));
console.log(`✓ furniture-catalog.json updated (${filtered.length} entries)`);
