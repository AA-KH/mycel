/**
 * Mycel Office Layout Generator
 *
 * Generates the 48×32 office layout JSON matching the reference floor plan.
 * Run: node --experimental-modules scripts/generate-layout.mjs
 *
 * Output: public/assets/mycel-layout.json
 */

import { writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const COLS = 48;
const ROWS = 32;
const WALL = 0;
const FLOOR_1 = 1; // default brown wood (hall)
const FLOOR_2 = 2;
const FLOOR_3 = 3;
const FLOOR_4 = 4;
const FLOOR_5 = 5;
const FLOOR_6 = 6;
const FLOOR_7 = 7;
const FLOOR_8 = 8;
const VOID = 255;

// ── Tile Grid ────────────────────────────────────────────────────
const tiles = new Array(COLS * ROWS).fill(WALL);

// Helper: fill a rect with a tile type
function fillRect(startCol, startRow, endCol, endRow, tileType) {
  for (let r = startRow; r < endRow; r++) {
    for (let c = startCol; c < endCol; c++) {
      if (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
        tiles[r * COLS + c] = tileType;
      }
    }
  }
}

// Helper: set single tile
function setTile(col, row, tileType) {
  if (row >= 0 && row < ROWS && col >= 0 && col < COLS) {
    tiles[row * COLS + col] = tileType;
  }
}

// --- Room floors ---
// Top row rooms
fillRect(1, 1, 11, 9, FLOOR_3);    // Creative (purple → use floor_3 + purple tileColor)
fillRect(12, 1, 22, 9, FLOOR_4);   // Developer (green → floor_4 + green tileColor)
fillRect(26, 1, 36, 9, FLOOR_5);   // Finance (amber → floor_5 + amber tileColor)
fillRect(37, 1, 47, 9, FLOOR_6);   // Legal (blue → floor_6 + blue tileColor)

// Central hall (brown wood)
fillRect(11, 1, 26, 32, FLOOR_1);  // Main hall column
fillRect(11, 9, 48, 11, FLOOR_1);  // Horizontal corridor top
fillRect(11, 21, 48, 23, FLOOR_1); // Horizontal corridor bottom

// Middle row rooms
fillRect(1, 11, 11, 21, FLOOR_7);  // Marketing (pink → floor_7 + pink tileColor)
fillRect(37, 11, 47, 21, FLOOR_8); // Research (teal → floor_8 + teal tileColor)

// Bottom row
fillRect(1, 23, 11, 28, FLOOR_2);  // Operations (tan → floor_2 + tan tileColor)
fillRect(1, 28, 11, 31, FLOOR_1);  // Break Lounge (checkerboard simulated with floor_1)
fillRect(37, 23, 47, 31, FLOOR_1); // Toilets area

// Doorways (ensure floor tiles connect rooms to hall)
// Creative doorway
setTile(11, 4, FLOOR_1); setTile(11, 5, FLOOR_1);
// Developer doorway
setTile(16, 9, FLOOR_1); setTile(17, 9, FLOOR_1);
// Finance doorway
setTile(26, 4, FLOOR_1); setTile(26, 5, FLOOR_1);
// Legal doorway
setTile(37, 4, FLOOR_1); setTile(36, 4, FLOOR_1);
// Marketing doorway
setTile(11, 15, FLOOR_1); setTile(11, 16, FLOOR_1);
// Research doorway
setTile(37, 15, FLOOR_1); setTile(36, 15, FLOOR_1);
// Operations doorway
setTile(11, 25, FLOOR_1); setTile(11, 26, FLOOR_1);
// Break Lounge doorway
setTile(11, 29, FLOOR_1); setTile(11, 30, FLOOR_1);

// Front entrance (bottom center)
setTile(23, 31, FLOOR_1); setTile(24, 31, FLOOR_1);
setTile(25, 31, FLOOR_1);

// ── Tile Colors ──────────────────────────────────────────────────
const tileColors = new Array(COLS * ROWS).fill(null);

function fillTileColor(startCol, startRow, endCol, endRow, color) {
  for (let r = startRow; r < endRow; r++) {
    for (let c = startCol; c < endCol; c++) {
      if (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
        tileColors[r * COLS + c] = color;
      }
    }
  }
}

// HSB color format used by the engine: { h, s, b, c }
const PURPLE = { h: 270, s: 60, b: -10, c: 0 };
const GREEN = { h: 140, s: 55, b: -15, c: 0 };
const AMBER = { h: 35, s: 70, b: 5, c: 0 };
const BLUE = { h: 220, s: 55, b: -10, c: 0 };
const PINK = { h: 330, s: 60, b: 5, c: 0 };
const TEAL = { h: 170, s: 50, b: -10, c: 0 };
const TAN = { h: 25, s: 40, b: 5, c: 0 };
const CHECKER = { h: 0, s: 0, b: 20, c: 0 };
const HALL_BROWN = { h: 30, s: 30, b: -5, c: 0 };

fillTileColor(1, 1, 11, 9, PURPLE);
fillTileColor(12, 1, 22, 9, GREEN);
fillTileColor(26, 1, 36, 9, AMBER);
fillTileColor(37, 1, 47, 9, BLUE);
fillTileColor(1, 11, 11, 21, PINK);
fillTileColor(37, 11, 47, 21, TEAL);
fillTileColor(1, 23, 11, 28, TAN);
fillTileColor(1, 28, 11, 31, CHECKER);

// Hall gets brown wood
fillTileColor(11, 1, 26, 32, HALL_BROWN);
fillTileColor(11, 9, 48, 11, HALL_BROWN);
fillTileColor(11, 21, 48, 23, HALL_BROWN);

// ── Area Definitions ─────────────────────────────────────────────
const areas = [
  { label: "CREATIVE", color: "#7c3aed" },
  { label: "DEVELOPER", color: "#059669" },
  { label: "FINANCE", color: "#d97706" },
  { label: "LEGAL", color: "#2563eb" },
  { label: "MARKETING", color: "#db2777" },
  { label: "RESEARCH", color: "#0d9488" },
  { label: "OPERATIONS", color: "#c2410c" },
  { label: "BREAK LOUNGE", color: "#78716c" },
];

const areaTiles = new Array(COLS * ROWS).fill(null);

function fillAreaTiles(startCol, startRow, endCol, endRow, label) {
  for (let r = startRow; r < endRow; r++) {
    for (let c = startCol; c < endCol; c++) {
      if (r >= 0 && r < ROWS && c >= 0 && c < COLS) {
        areaTiles[r * COLS + c] = label;
      }
    }
  }
}

fillAreaTiles(1, 1, 11, 9, "CREATIVE");
fillAreaTiles(12, 1, 22, 9, "DEVELOPER");
fillAreaTiles(26, 1, 36, 9, "FINANCE");
fillAreaTiles(37, 1, 47, 9, "LEGAL");
fillAreaTiles(1, 11, 11, 21, "MARKETING");
fillAreaTiles(37, 11, 47, 21, "RESEARCH");
fillAreaTiles(1, 23, 11, 28, "OPERATIONS");
fillAreaTiles(1, 28, 11, 31, "BREAK LOUNGE");

// ── Furniture ────────────────────────────────────────────────────
// Using furniture types from the existing furniture-catalog.json
// Common types: desk_front, desk_back, desk_side, chair_front, chair_back,
// chair_side, monitor, bookshelf, plant_1, plant_2, server_rack, sofa, etc.

const furniture = [];
let uidCounter = 0;
function uid() { return `f_${++uidCounter}`; }

function placeDesk(col, row, type = "desk_front") {
  furniture.push({ uid: uid(), type, col, row });
}

function placeChair(col, row, type = "chair_front") {
  furniture.push({ uid: uid(), type, col, row });
}

function placeItem(col, row, type) {
  furniture.push({ uid: uid(), type, col, row });
}

// ── Creative Room (cols 1-10, rows 1-8) ──────────────────────
placeDesk(2, 3, "desk_front"); placeChair(2, 4, "chair_front");
placeDesk(5, 3, "desk_front"); placeChair(5, 4, "chair_front");
placeDesk(2, 6, "desk_front"); placeChair(2, 7, "chair_front");
placeDesk(5, 6, "desk_front"); placeChair(5, 7, "chair_front");
placeItem(8, 1, "bookshelf");
placeItem(9, 1, "bookshelf");
placeItem(1, 1, "plant_1");
placeItem(10, 8, "plant_2");

// ── Developer Room (cols 12-21, rows 1-8) ────────────────────
placeDesk(13, 3, "desk_front"); placeChair(13, 4, "chair_front");
placeDesk(16, 3, "desk_front"); placeChair(16, 4, "chair_front");
placeDesk(19, 3, "desk_front"); placeChair(19, 4, "chair_front");
placeItem(13, 1, "server_rack");
placeItem(15, 1, "server_rack");
placeItem(17, 1, "server_rack");
placeItem(12, 8, "plant_1");
placeItem(21, 1, "plant_2");

// ── Finance Room (cols 26-35, rows 1-8) ──────────────────────
placeDesk(27, 3, "desk_front"); placeChair(27, 4, "chair_front");
placeDesk(30, 3, "desk_front"); placeChair(30, 4, "chair_front");
placeDesk(33, 3, "desk_front"); placeChair(33, 4, "chair_front");
placeItem(34, 1, "bookshelf");
placeItem(26, 1, "plant_1");
placeItem(35, 8, "plant_2");

// ── Legal Room (cols 37-46, rows 1-8) ────────────────────────
placeDesk(38, 3, "desk_front"); placeChair(38, 4, "chair_front");
placeDesk(41, 3, "desk_front"); placeChair(41, 4, "chair_front");
placeDesk(38, 6, "desk_front"); placeChair(38, 7, "chair_front");
placeDesk(41, 6, "desk_front"); placeChair(41, 7, "chair_front");
placeItem(44, 1, "bookshelf");
placeItem(45, 1, "bookshelf");
placeItem(37, 1, "plant_1");
placeItem(46, 8, "plant_2");

// ── Marketing Room (cols 1-10, rows 11-20) ───────────────────
placeDesk(2, 13, "desk_front"); placeChair(2, 14, "chair_front");
placeDesk(5, 13, "desk_front"); placeChair(5, 14, "chair_front");
placeDesk(2, 17, "desk_front"); placeChair(2, 18, "chair_front");
placeDesk(5, 17, "desk_front"); placeChair(5, 18, "chair_front");
placeItem(8, 11, "bookshelf");
placeItem(1, 11, "plant_1");
placeItem(10, 20, "plant_2");

// ── Research Room (cols 37-46, rows 11-20) ───────────────────
placeDesk(38, 13, "desk_front"); placeChair(38, 14, "chair_front");
placeDesk(41, 13, "desk_front"); placeChair(41, 14, "chair_front");
placeDesk(38, 17, "desk_front"); placeChair(38, 18, "chair_front");
placeDesk(41, 17, "desk_front"); placeChair(41, 18, "chair_front");
placeItem(44, 11, "bookshelf");
placeItem(45, 11, "bookshelf");
placeItem(37, 11, "plant_1");
placeItem(46, 20, "plant_2");

// ── Operations Room (cols 1-10, rows 23-27) ──────────────────
placeDesk(2, 24, "desk_front"); placeChair(2, 25, "chair_front");
placeDesk(5, 24, "desk_front"); placeChair(5, 25, "chair_front");
placeItem(8, 23, "bookshelf");
placeItem(1, 23, "plant_1");

// ── Break Lounge (cols 1-10, rows 28-30) ─────────────────────
placeItem(2, 29, "sofa_front");
placeItem(5, 29, "sofa_front");
placeItem(8, 29, "sofa_front");
placeItem(4, 28, "plant_1");

// ── Central Hall ─────────────────────────────────────────────
// Orchestrator desk (top of hall)
placeDesk(23, 4, "desk_front"); placeChair(23, 5, "chair_front");
placeItem(22, 3, "plant_1");
placeItem(25, 3, "plant_2");

// HR Agent desk (middle of hall)
placeDesk(23, 14, "desk_front"); placeChair(23, 15, "chair_front");
placeItem(22, 13, "plant_1");
placeItem(25, 13, "plant_2");

// Server Room (right of HR desk)
placeItem(30, 14, "server_rack");
placeItem(32, 14, "server_rack");
placeItem(34, 14, "server_rack");

// Hall decorations
placeItem(14, 22, "plant_1");
placeItem(20, 22, "plant_2");
placeItem(14, 10, "plant_1");
placeItem(20, 10, "plant_2");

// ── Build Output ─────────────────────────────────────────────
const layout = {
  version: 1,
  cols: COLS,
  rows: ROWS,
  tiles,
  furniture,
  tileColors,
  areas,
  areaTiles,
  pets: [],
  carpetTiles: new Array(COLS * ROWS).fill(null),
  layoutRevision: 2,
};

const outputPath = resolve(__dirname, '../public/assets/mycel-layout.json');
writeFileSync(outputPath, JSON.stringify(layout));

console.log(`✅ Generated mycel-layout.json`);
console.log(`   Grid: ${COLS}×${ROWS} = ${COLS * ROWS} tiles`);
console.log(`   Furniture items: ${furniture.length}`);
console.log(`   Zones: ${areas.length}`);
console.log(`   Output: ${outputPath}`);
