'use client'

import { useCallback, useEffect, useRef, useState } from 'react';
import type { MissionState } from '@/lib/mission-sim';
import { useSimulation } from '@/lib/simulation/use-simulation';
import type { SimAgent } from '@/lib/simulation/types';
import { CHAR_SHEET_W, CHAR_SHEET_H } from '@/lib/simulation/types';
import { resolveAgentSprite, agentHitBox } from '@/lib/simulation/sprite';
import {
  T, COLS, ROWS, WORLD_W, WORLD_H,
  ROOMS, DOORS, FURNITURE, AGENT_SEATS, GRID, SEAT_OVERLAY_TILES, isChair,
  type RoomDef, type FurnitureDef,
} from '@/lib/simulation/map-data';

// ═══════════════════════════════════════════════════════════════════
// RENDERING CONSTANTS
// ═══════════════════════════════════════════════════════════════════
const VOID_COLOR = '#0e0e14';
const WALL_FACE_COLOR = '#2c2c48';
const ATLAS_GLOW = '#ffd700';

// ═══════════════════════════════════════════════════════════════════
// ASSET PATH MAP
// ═══════════════════════════════════════════════════════════════════
const PA = '/assets/pixel-agents';

const FURN_PATHS: Record<string, string> = {
  'DESK_FRONT': `${PA}/furniture/DESK/DESK_FRONT.png`,
  'DESK_SIDE': `${PA}/furniture/DESK/DESK_SIDE.png`,
  'PC_FRONT_ON': `${PA}/furniture/PC/PC_FRONT_ON_1.png`,
  'PC_FRONT_ON_1': `${PA}/furniture/PC/PC_FRONT_ON_1.png`,
  'PC_FRONT_ON_2': `${PA}/furniture/PC/PC_FRONT_ON_2.png`,
  'PC_FRONT_ON_3': `${PA}/furniture/PC/PC_FRONT_ON_3.png`,
  'PC_FRONT_OFF': `${PA}/furniture/PC/PC_FRONT_OFF.png`,
  'PC_SIDE': `${PA}/furniture/PC/PC_SIDE.png`,
  'CUSHIONED_CHAIR_FRONT': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_FRONT.png`,
  'CUSHIONED_CHAIR_BACK': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_BACK.png`,
  'CUSHIONED_CHAIR_SIDE': `${PA}/furniture/CUSHIONED_CHAIR/CUSHIONED_CHAIR_SIDE.png`,
  'BOOKSHELF': `${PA}/furniture/BOOKSHELF/BOOKSHELF.png`,
  'DOUBLE_BOOKSHELF': `${PA}/furniture/DOUBLE_BOOKSHELF/DOUBLE_BOOKSHELF.png`,
  'WHITEBOARD': `${PA}/furniture/WHITEBOARD/WHITEBOARD.png`,
  'CLOCK': `${PA}/furniture/CLOCK/CLOCK.png`,
  'COFFEE': `${PA}/furniture/COFFEE/COFFEE.png`,
  'COFFEE_TABLE': `${PA}/furniture/COFFEE_TABLE/COFFEE_TABLE.png`,
  'SOFA_FRONT': `${PA}/furniture/SOFA/SOFA_FRONT.png`,
  'SOFA_BACK': `${PA}/furniture/SOFA/SOFA_BACK.png`,
  'SOFA_SIDE': `${PA}/furniture/SOFA/SOFA_SIDE.png`,
  'LARGE_PAINTING': `${PA}/furniture/LARGE_PAINTING/LARGE_PAINTING.png`,
  'SMALL_PAINTING': `${PA}/furniture/SMALL_PAINTING/SMALL_PAINTING.png`,
  'SMALL_PAINTING_2': `${PA}/furniture/SMALL_PAINTING_2/SMALL_PAINTING_2.png`,
  'PLANT': `${PA}/furniture/PLANT/PLANT.png`,
  'PLANT_2': `${PA}/furniture/PLANT_2/PLANT_2.png`,
  'LARGE_PLANT': `${PA}/furniture/LARGE_PLANT/LARGE_PLANT.png`,
  'HANGING_PLANT': `${PA}/furniture/HANGING_PLANT/HANGING_PLANT.png`,
  'CACTUS': `${PA}/furniture/CACTUS/CACTUS.png`,
  'BIN': `${PA}/furniture/BIN/BIN.png`,
  'POT': `${PA}/furniture/POT/POT.png`,
  'TABLE_FRONT': `${PA}/furniture/TABLE_FRONT/TABLE_FRONT.png`,
  'SMALL_TABLE_FRONT': `${PA}/furniture/SMALL_TABLE/SMALL_TABLE_FRONT.png`,
  'WOODEN_CHAIR_SIDE': `${PA}/furniture/WOODEN_CHAIR/WOODEN_CHAIR_SIDE.png`,
  'WOODEN_CHAIR_FRONT': `${PA}/furniture/WOODEN_CHAIR/WOODEN_CHAIR_FRONT.png`,
  'WOODEN_BENCH': `${PA}/furniture/WOODEN_BENCH/WOODEN_BENCH.png`,
  'CUSHIONED_BENCH': `${PA}/furniture/CUSHIONED_BENCH/CUSHIONED_BENCH.png`,
};

// ═══════════════════════════════════════════════════════════════════
// ASSET LOADER
// ═══════════════════════════════════════════════════════════════════
function loadImg(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => resolve(img);
    img.src = src;
  });
}

interface AssetBundle {
  floors: HTMLImageElement[];
  wall: HTMLImageElement;
  carpets: HTMLImageElement[];
  characters: HTMLImageElement[];
  furniture: Record<string, HTMLImageElement>;
}

async function loadAllAssets(): Promise<AssetBundle> {
  const floorPromises = Array.from({ length: 9 }, (_, i) =>
    loadImg(`${PA}/floors/floor_${i}.png`)
  );
  const wallPromise = loadImg(`${PA}/walls/wall_0.png`);
  const carpetPromises = Array.from({ length: 3 }, (_, i) =>
    loadImg(`${PA}/carpets/carpet_${i}.png`)
  );
  const charPromises = Array.from({ length: 6 }, (_, i) =>
    loadImg(`${PA}/characters/char_${i}.png`)
  );
  const furnEntries = Object.entries(FURN_PATHS);
  const furnPromises = furnEntries.map(([, path]) => loadImg(path));

  const [floors, wall, carpets, characters, ...furnImgs] = await Promise.all([
    Promise.all(floorPromises),
    wallPromise,
    Promise.all(carpetPromises),
    Promise.all(charPromises),
    ...furnPromises,
  ]);

  const furniture: Record<string, HTMLImageElement> = {};
  furnEntries.forEach(([key], i) => {
    furniture[key] = furnImgs[i];
  });

  return { floors, wall, carpets, characters, furniture };
}

// ═══════════════════════════════════════════════════════════════════
// RENDERING ENGINE
// ═══════════════════════════════════════════════════════════════════

function renderFrame(
  ctx: CanvasRenderingContext2D,
  assets: AssetBundle,
  zoom: number,
  panX: number,
  panY: number,
  time: number,
  hoveredAgent: SimAgent | null,
  canvasW: number,
  canvasH: number,
  simAgents: SimAgent[],
) {
  const dpr = window.devicePixelRatio || 1;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // Clear canvas
  ctx.fillStyle = VOID_COLOR;
  ctx.fillRect(0, 0, canvasW, canvasH);

  ctx.save();
  ctx.translate(panX, panY);
  ctx.scale(zoom, zoom);
  ctx.imageSmoothingEnabled = false;

  // ── Helper: find room for a tile ──────────────────────
  function findRoomForTile(c: number, r: number): RoomDef | undefined {
    return ROOMS.find(rm => c >= rm.c1 && c <= rm.c2 && r >= rm.r1 && r <= rm.r2);
  }
  function findNearestRoom(c: number, r: number): RoomDef | undefined {
    return findRoomForTile(c, r + 1) || findRoomForTile(c, r - 1) ||
      findRoomForTile(c + 1, r) || findRoomForTile(c - 1, r) ||
      findRoomForTile(c, r);
  }

  // ── 1. Draw floor tiles ───────────────────────────────
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = GRID[r][c];
      if (tile.type === 'floor') {
        const floorImg = assets.floors[tile.floorIdx];
        const px = c * T, py = r * T;
        if (floorImg?.complete && floorImg.naturalWidth > 0) {
          ctx.drawImage(floorImg, 0, 0, T, T, px, py, T, T);
        } else {
          ctx.fillStyle = '#4a6b5e';
          ctx.fillRect(px, py, T, T);
        }
        const room = findRoomForTile(c, r);
        if (room) {
          ctx.fillStyle = room.tint;
          ctx.fillRect(px, py, T, T);
        }
      }
    }
  }

  // ── 2. Draw wall tiles ───────────���──���─────────────────
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const tile = GRID[r][c];
      if (tile.type === 'wall') {
        const px = c * T, py = r * T;
        const hasFloorBelow = r + 1 < ROWS && GRID[r + 1][c].type === 'floor';
        const hasFloorAbove = r - 1 >= 0 && GRID[r - 1][c].type === 'floor';
        const nearRoom = findNearestRoom(c, r);
        const wallBase = nearRoom?.wallTint || WALL_FACE_COLOR;

        if (hasFloorBelow && !hasFloorAbove) {
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(255,255,255,0.08)';
          ctx.fillRect(px, py + T - 2, T, 2);
          ctx.fillStyle = 'rgba(0,0,0,0.15)';
          ctx.fillRect(px, py, T, 1);
        } else if (!hasFloorBelow && hasFloorAbove) {
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(0,0,0,0.2)';
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(255,255,255,0.06)';
          ctx.fillRect(px, py, T, 1);
        } else {
          ctx.fillStyle = wallBase;
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(0,0,0,0.1)';
          ctx.fillRect(px, py, T, T);
          ctx.fillStyle = 'rgba(255,255,255,0.04)';
          ctx.fillRect(px, py, 1, T);
          ctx.fillStyle = 'rgba(0,0,0,0.08)';
          ctx.fillRect(px + T - 1, py, 1, T);
        }
      }
    }
  }

  // ── 3. Draw Atlas's Office glow border ────────────────
  const atlasRoom = ROOMS.find(r => r.id === 'atlas')!;
  const glowAlpha = 0.3 + 0.15 * Math.sin(time * 2);
  const glowX = (atlasRoom.c1 - 1) * T;
  const glowY = (atlasRoom.r1 - 1) * T;
  const glowW = (atlasRoom.c2 - atlasRoom.c1 + 3) * T;
  const glowH = (atlasRoom.r2 - atlasRoom.r1 + 3) * T;
  ctx.strokeStyle = ATLAS_GLOW;
  ctx.globalAlpha = glowAlpha;
  ctx.lineWidth = 3;
  ctx.strokeRect(glowX + 1.5, glowY + 1.5, glowW - 3, glowH - 3);
  ctx.strokeStyle = ATLAS_GLOW;
  ctx.globalAlpha = glowAlpha * 0.4;
  ctx.lineWidth = 6;
  ctx.strokeRect(glowX + 3, glowY + 3, glowW - 6, glowH - 6);
  ctx.globalAlpha = 1;
  ctx.lineWidth = 1;

  // ── 4. Collect all drawables for depth sorting ────────
  interface Drawable {
    sortRow: number;
    draw: () => void;
  }
  const drawables: Drawable[] = [];

  // Add furniture
  for (const furn of FURNITURE) {
    // Chairs at an UP-facing seat must paint AFTER the agent so the
    // backrest overlaps the character's lower body — that overlap is
    // what makes them read as sitting *in* the chair. Agents sort at
    // (row + 0.5), so +0.6 puts the chair just past its occupant
    // while staying well before the next tile row.
    const isSeatOverlay = SEAT_OVERLAY_TILES.has(`${furn.col},${furn.row}`);
    const sortRow = isSeatOverlay
      ? furn.row + 0.6
      : (furn.depth ?? furn.row);
    drawables.push({
      sortRow,
      draw: () => {
        let imgKey = furn.img;
        if (furn.animated && imgKey === 'PC_FRONT_ON') {
          const frame = Math.floor(time * 2) % 3;
          imgKey = `PC_FRONT_ON_${frame + 1}`;
        }
        const img = assets.furniture[imgKey];
        if (!img?.complete || img.naturalWidth === 0) return;

        const iw = img.naturalWidth;
        const ih = img.naturalHeight;

        // Anchor conventions differ by furniture kind, and both are real:
        //
        //  • Chairs declare their SEAT tile — the same tile the occupant
        //    stands on (see AGENT_SEATS / CUSHIONED_CHAIR_BACK at 2,5 vs
        //    Mira at 2,5). So a chair's BASE must land on the bottom edge
        //    of that tile, exactly like the character's baseline does.
        //    16px chairs already do; a 32px chair (WOODEN_CHAIR_SIDE) drawn
        //    top-left would spill a whole tile below its occupant.
        //  • Everything else declares the TOP-LEFT of its footprint box,
        //    which is the convention FOOTPRINTS / computeBlockedTiles use.
        //
        // Chairs are NON_BLOCKING, so lifting them changes no collisions.
        const px = furn.col * T;
        const py = isChair(furn.img) ? furn.row * T - (ih - T) : furn.row * T;

        ctx.save();
        if (furn.mirror) {
          ctx.translate(px + iw, py);
          ctx.scale(-1, 1);
          ctx.drawImage(img, 0, 0, iw, ih);
        } else {
          ctx.drawImage(img, px, py, iw, ih);
        }
        ctx.restore();
      },
    });
  }

  // ── Add simulation agents ─────────────────────────────
  for (const agent of simAgents) {
    if (!agent.visible) continue;

    // Depth sort by current pixel row (feet position)
    const agentSortRow = (agent.y + T / 2) / T;

    drawables.push({
      sortRow: agentSortRow,
      draw: () => {
        const charImg = assets.characters[agent.charIdx];
        if (!charImg?.complete || charImg.naturalWidth === 0) return;

        // ── Sprite frame + anchor ───────────────────────
        // Sheet is 112x96 = 7 cols x 3 rows of 16x32 frames.
        //   rows: 0=DOWN 1=UP 2=RIGHT (LEFT = row 2 mirrored)
        //   cols: 0-2 standing/walk, 3-4 sit, 5-6 work
        // All of the geometry lives in resolveAgentSprite() so the
        // hitbox below and the renderer cannot drift apart.
        const s = resolveAgentSprite(agent);

        // Guard against a wrong-sized asset silently producing garbage
        if (
          charImg.naturalWidth !== CHAR_SHEET_W ||
          charImg.naturalHeight !== CHAR_SHEET_H
        ) {
          return;
        }

        if (s.mirror) {
          ctx.save();
          ctx.translate(s.dx + s.sw, s.dy);
          ctx.scale(-1, 1);
          ctx.drawImage(charImg, s.sx, s.sy, s.sw, s.sh, 0, 0, s.sw, s.sh);
          ctx.restore();
        } else {
          ctx.drawImage(charImg, s.sx, s.sy, s.sw, s.sh, s.dx, s.dy, s.sw, s.sh);
        }

        // ── Name label ──────────────────────────────────
        ctx.save();
        ctx.font = '4px "Press Start 2P", monospace';
        ctx.textAlign = 'center';
        const labelX = agent.x;
        // Pin the label to the frame box (== tile bottom), not to the
        // measured baseline. The baseline moves with the pose, so keying
        // off it made a name jump ~6px the instant its owner sat down,
        // and slid it under the chair backrest on UP-facing seats. The
        // frame bottom is pose-independent, so names hold still and clear
        // the chair.
        const labelY = s.anchorY + 5;
        const drawY = s.topY;

        const metrics = ctx.measureText(agent.name);
        const labelW = metrics.width + 4;
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(labelX - labelW / 2, labelY - 4, labelW, 7);

        if (agent.isExecutive) {
          ctx.fillStyle = ATLAS_GLOW;
        } else {
          ctx.fillStyle = '#ffffff';
        }
        ctx.fillText(agent.name, labelX, labelY);

        // ── Executive badge / active indicator ──────────
        if (agent.isExecutive) {
          const pulseR = 3 + Math.sin(time * 3) * 1;
          ctx.beginPath();
          ctx.arc(agent.x, drawY - 4, pulseR, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(255, 215, 0, ${0.5 + 0.3 * Math.sin(time * 3)})`;
          ctx.fill();
          ctx.strokeStyle = ATLAS_GLOW;
          ctx.lineWidth = 0.5;
          ctx.stroke();

          ctx.font = '3px "Press Start 2P", monospace';
          ctx.fillStyle = '#00ff88';
          ctx.textAlign = 'center';
          ctx.fillText('⚡ ACTIVE', labelX, labelY + 8);
        }

        // ── Speech Bubble (Current Task) ──────────────
        if (agent.currentTask) {
          const displayTask = agent.currentTask.length > 15
            ? agent.currentTask.slice(0, 15) + '...'
            : agent.currentTask;
            
          const bubbleY = drawY - 20; // Move up to accommodate larger bubble
          
          ctx.font = '5px "Press Start 2P", monospace';
          const tMetrics = ctx.measureText(displayTask);
          const textW = tMetrics.width;
          const padX = 3;
          const bubbleW = textW + padX * 2;
          const bubbleH = 9;
          
          // White background
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(labelX - bubbleW / 2, bubbleY - bubbleH, bubbleW, bubbleH);
          
          // Black border
          ctx.strokeStyle = '#000000';
          ctx.lineWidth = 0.5;
          ctx.strokeRect(labelX - bubbleW / 2, bubbleY - bubbleH, bubbleW, bubbleH);
          
          // Text
          ctx.fillStyle = '#000000';
          ctx.textAlign = 'center';
          ctx.fillText(displayTask, labelX, bubbleY - 2.5);
          
          // Tail
          ctx.fillStyle = '#ffffff';
          ctx.beginPath();
          ctx.moveTo(labelX - 1.5, bubbleY);
          ctx.lineTo(labelX - 2.5, bubbleY + 2.5); // tail point
          ctx.lineTo(labelX + 0.5, bubbleY);
          ctx.fill();
          
          ctx.beginPath();
          ctx.moveTo(labelX - 1.5, bubbleY);
          ctx.lineTo(labelX - 2.5, bubbleY + 2.5);
          ctx.lineTo(labelX + 0.5, bubbleY);
          ctx.stroke();
          
          // Cover the top line of the tail so it connects seamlessly to the bubble
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(labelX - 1.2, bubbleY - 0.5, 1.4, 1);
        }

        // ── Hovered agent tooltip ───────────────────────
        if (hoveredAgent && hoveredAgent.name === agent.name) {
          const tooltipY = drawY - 12;
          ctx.fillStyle = 'rgba(20, 24, 36, 0.92)';
          const roleText = agent.role;
          ctx.font = '3px "Press Start 2P", monospace';
          const rMetrics = ctx.measureText(roleText);
          const tw = Math.max(rMetrics.width + 8, 40);
          ctx.fillRect(labelX - tw / 2, tooltipY - 10, tw, 12);
          ctx.strokeStyle = agent.isExecutive ? ATLAS_GLOW : '#5070a0';
          ctx.lineWidth = 0.5;
          ctx.strokeRect(labelX - tw / 2, tooltipY - 10, tw, 12);
          ctx.fillStyle = '#95d8ff';
          ctx.textAlign = 'center';
          ctx.fillText(roleText, labelX, tooltipY - 3);
          // Tail
          ctx.fillStyle = 'rgba(20, 24, 36, 0.92)';
          ctx.beginPath();
          ctx.moveTo(labelX - 3, tooltipY + 2);
          ctx.lineTo(labelX, tooltipY + 5);
          ctx.lineTo(labelX + 3, tooltipY + 2);
          ctx.fill();
        }

        ctx.restore();
      },
    });
  }

  // Sort by row for proper depth ordering
  drawables.sort((a, b) => a.sortRow - b.sortRow);

  // Draw all drawables
  for (const d of drawables) {
    d.draw();
  }

  // ── 5. Draw room labels ───────────────────────────────
  ctx.save();
  ctx.font = '7px "Press Start 2P", monospace';
  ctx.textAlign = 'left';
  for (const room of ROOMS) {
    if (!room.name) continue;
    const lx = room.labelX * T;
    const ly = room.labelY * T;
    const rot = room.labelRotation || 0;

    const metrics = ctx.measureText(room.name);
    const textW = metrics.width;
    const padX = 4;
    const padY = 3;
    const bgW = textW + padX * 2;
    const bgH = 7 + padY * 2;

    ctx.save();
    ctx.translate(lx, ly);
    if (rot !== 0) {
      ctx.rotate((rot * Math.PI) / 180);
    }

    const bgX = -padX;
    const bgY = -padY - 1;

    ctx.fillStyle = 'rgba(10, 12, 24, 0.82)';
    ctx.fillRect(bgX, bgY, bgW, bgH);

    ctx.strokeStyle = room.labelColor;
    ctx.globalAlpha = 0.6;
    ctx.lineWidth = 1;
    ctx.strokeRect(bgX + 0.5, bgY + 0.5, bgW - 1, bgH - 1);
    ctx.globalAlpha = 1;

    ctx.fillStyle = room.labelColor;
    ctx.fillText(room.name, 0, 6);

    ctx.restore();
  }
  ctx.restore();

  // ── 6. Draw grid lines (subtle) ───────────────────────
  ctx.save();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
  ctx.lineWidth = 0.5;
  for (let r = 0; r <= ROWS; r++) {
    for (let c = 0; c <= COLS; c++) {
      if (r < ROWS && c < COLS && GRID[r][c].type === 'floor') {
        ctx.strokeRect(c * T, r * T, T, T);
      }
    }
  }
  ctx.restore();

  ctx.restore(); // Undo zoom + pan transform
}

// ═══════════════════════════════════════════════════════════════════
// LOADING SCREEN
// ═══════════════════════════════════════════════════════════════════
function LoadingScreen() {
  return (
    <div style={{
      position: 'absolute', inset: 0, zIndex: 10,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      background: VOID_COLOR, color: '#e7ecf7',
      fontFamily: '"Press Start 2P", monospace',
    }}>
      <div style={{ fontSize: 20, marginBottom: 24, color: '#ffd700' }}>
        Supply Chain HQ
      </div>
      <div style={{ fontSize: 10, marginBottom: 32, color: '#7ecfcf' }}>
        Loading Office Assets...
      </div>
      <div style={{
        width: 200, height: 8,
        background: '#1a1e2e', border: '1px solid #2a3448',
        overflow: 'hidden',
      }}>
        <div style={{
          width: '60%', height: '100%',
          background: 'linear-gradient(90deg, #ffd700, #ff8800)',
          animation: 'loadPulse 1.5s ease-in-out infinite',
        }} />
      </div>
      <style>{`
        @keyframes loadPulse {
          0%, 100% { width: 30%; opacity: 0.6; }
          50% { width: 90%; opacity: 1; }
        }
      `}</style>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════════
/**
 * Pixel office with log-driven agent movement.
 * Accepts MissionState to drive agent behavior:
 * - Agents appear when hired
 * - Walk to desks when working
 * - Wander the Break Lounge when done
 */
export default function PixelOffice({ mission }: { mission: MissionState }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [assets, setAssets] = useState<AssetBundle | null>(null);
  const [loading, setLoading] = useState(true);

  // Fixed camera (recomputed every frame from the canvas size)
  const cameraRef = useRef({ zoom: 3, panX: 0, panY: 0 });
  const hoveredAgentRef = useRef<SimAgent | null>(null);
  const [, forceRender] = useState(0);

  // Simulation engine (created once, stable reference)
  const engine = useSimulation();

  // Store mission in a ref so the rAF closure always sees the latest
  const missionRef = useRef(mission);
  missionRef.current = mission;

  // Previous frame timestamp for delta-time
  const prevTimeRef = useRef<number | null>(null);

  // ── Asset Loading ───────────────────────────────────
  useEffect(() => {
    loadAllAssets().then((bundle) => {
      setAssets(bundle);
      setLoading(false);
    });
  }, []);

  // ── Animation Loop (renders + ticks simulation) ────
  useEffect(() => {
    if (!assets) return;
    let animId: number;

    const loop = (now: number) => {
      const canvas = canvasRef.current;
      if (!canvas) { animId = requestAnimationFrame(loop); return; }
      const ctx = canvas.getContext('2d');
      if (!ctx) { animId = requestAnimationFrame(loop); return; }

      const dpr = window.devicePixelRatio || 1;
      const cw = canvas.clientWidth;
      const ch = canvas.clientHeight;

      if (canvas.width !== cw * dpr || canvas.height !== ch * dpr) {
        canvas.width = cw * dpr;
        canvas.height = ch * dpr;
      }

      // Fixed fit-to-viewport camera
      const fitZoom = Math.min(cw / WORLD_W, ch / WORLD_H) * 0.97;
      const zoom = Math.max(0.5, fitZoom);
      const vpPanX = (cw - WORLD_W * zoom) / 2;
      const vpPanY = (ch - WORLD_H * zoom) / 2;
      cameraRef.current = { zoom, panX: vpPanX, panY: vpPanY };

      // ── Tick simulation ─────────────────────────────
      const dt = prevTimeRef.current !== null
        ? Math.min((now - prevTimeRef.current) / 1000, 0.1) // cap at 100ms to avoid huge jumps
        : 0;
      prevTimeRef.current = now;

      // Sync mission → simulation (checks for phase changes internally)
      engine.syncWithMission(missionRef.current.agents);
      // Advance agent FSMs
      engine.tick(dt);

      // ── Render ──────────────────────────────────────
      renderFrame(
        ctx, assets,
        zoom, vpPanX, vpPanY,
        now / 1000,
        hoveredAgentRef.current,
        cw, ch,
        engine.agents,
      );

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [assets, engine]);

  // ── Hover detection ───────────────────��─────────────
  const onPointerMove = useCallback((e: React.PointerEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const { zoom, panX, panY } = cameraRef.current;
    const worldX = (mx - panX) / zoom;
    const worldY = (my - panY) / zoom;

    let found: SimAgent | null = null;
    for (const agent of engine.agents) {
      if (!agent.visible) continue;
      // Same resolver the renderer uses, so the hover target always
      // matches the body actually drawn on screen (seated included).
      const box = agentHitBox(agent);
      if (worldX >= box.x && worldX <= box.x + box.w &&
        worldY >= box.y && worldY <= box.y + box.h) {
        found = agent;
        break;
      }
    }

    if (found !== hoveredAgentRef.current) {
      hoveredAgentRef.current = found;
      forceRender(n => n + 1);
    }
  }, [engine]);

  const onPointerLeave = useCallback(() => {
    if (hoveredAgentRef.current !== null) {
      hoveredAgentRef.current = null;
      forceRender(n => n + 1);
    }
  }, []);

  return (
    <div
      id="pixel-office-root"
      style={{ width: '100%', height: '100%', overflow: 'hidden', background: VOID_COLOR, position: 'relative', touchAction: 'none' }}
    >
      {loading && <LoadingScreen />}
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
          cursor: hoveredAgentRef.current ? 'pointer' : 'default',
          imageRendering: 'pixelated',
        }}
        onPointerMove={onPointerMove}
        onPointerLeave={onPointerLeave}
      />
    </div>
  );
}
