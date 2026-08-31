import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AgentLifecycle, type LifecycleAgent } from '../../pixel-office/engine/agentLifecycle';
import { OfficeState } from '../../pixel-office/engine/officeState';
import { renderFrame } from '../../pixel-office/engine/renderer';
import {
  buildMycelLayout,
  MYCEL_COLS,
  MYCEL_ROWS,
  TEAM_AREA_MAP,
} from '../../pixel-office/layout/mycelOfficeLayout';
import { getLoadedCharacterCount } from '../../pixel-office/sprites/spriteData';
import { TILE_SIZE } from '../../pixel-office/types';
import { initBrowserMock, loadOfficeAssets } from '../../utils/browserMock';

interface CanvasOfficeProps {
  agentStatuses: Record<string, LifecycleAgent>;
  onAgentClick: (agentId: string) => void;
}

const MIN_ZOOM = 1;
const MAX_ZOOM = 4;

/** Largest whole-ish zoom that still shows the entire floor plan. */
function fitZoom(width: number, height: number): number {
  if (width === 0 || height === 0) return 2;
  const z = Math.min(width / (MYCEL_COLS * TILE_SIZE), height / (MYCEL_ROWS * TILE_SIZE));
  return Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.round(z * 4) / 4));
}

export function CanvasOffice({ agentStatuses, onAgentClick }: CanvasOfficeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const officeStateRef = useRef<OfficeState>(new OfficeState());
  const lifecycleRef = useRef<AgentLifecycle | null>(null);
  const zoomRef = useRef(2);
  const [ready, setReady] = useState(false);
  const panRef = useRef({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, panX: 0, panY: 0 });
  const pendingRef = useRef<Record<string, LifecycleAgent>>({});

  if (!lifecycleRef.current) {
    lifecycleRef.current = new AgentLifecycle(officeStateRef.current);
  }

  // Build the Mycel floor plan once the sprite assets are decoded.
  useEffect(() => {
    let mounted = true;
    initBrowserMock().then(() => {
      if (!mounted) return;
      // Push the decoded characters / floors / walls / furniture catalog into
      // the engine before any layout is built from it.
      loadOfficeAssets();
      const state = officeStateRef.current;
      state.rebuildFromLayout(buildMycelLayout());
      state.setAreaMappings(TEAM_AREA_MAP);
      setReady(true);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Keep the latest roster around so the lifecycle can pick it up as soon as
  // the character sprites finish loading.
  useEffect(() => {
    pendingRef.current = agentStatuses;
  }, [agentStatuses]);

  // Feed the roster into the lifecycle (hire / status change / walk-out).
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    const trySync = () => {
      if (cancelled) return true;
      if (getLoadedCharacterCount() === 0) return false;
      lifecycleRef.current?.sync(pendingRef.current);
      return true;
    };
    if (trySync()) return;
    const interval = setInterval(() => {
      if (trySync()) clearInterval(interval);
    }, 120);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [agentStatuses, ready]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animationFrameId: number;
    let lastTime = performance.now();

    const loop = (now: number) => {
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      const state = officeStateRef.current;
      state.update(dt);
      lifecycleRef.current?.tick(dt);

      const ctx = canvas.getContext('2d');
      if (ctx) {
        const displayWidth = canvas.clientWidth;
        const displayHeight = canvas.clientHeight;
        if (canvas.width !== displayWidth || canvas.height !== displayHeight) {
          canvas.width = displayWidth;
          canvas.height = displayHeight;
          zoomRef.current = fitZoom(displayWidth, displayHeight);
        }

        const layout = state.getLayout();
        renderFrame(
          ctx,
          canvas.width,
          canvas.height,
          state.tileMap,
          state.furniture,
          state.getCharacters(),
          zoomRef.current,
          panRef.current.x,
          panRef.current.y,
          undefined,
          undefined,
          layout.tileColors,
          layout.cols,
          layout.rows,
          layout.carpetTiles,
          layout.areas,
          layout.areaTiles,
          false, // keep the area system available without washing out the art
          null,
          true, // compact centroid room plaques remain visible in normal view
          state.getPets(),
        );
      }

      animationFrameId = requestAnimationFrame(loop);
    };

    animationFrameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const next = zoomRef.current + (e.deltaY < 0 ? 0.25 : -0.25);
      zoomRef.current = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, next));
    };
    canvas.addEventListener('wheel', onWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', onWheel);
  }, []);

  const handlePointerDown = (e: React.PointerEvent) => {
    isDraggingRef.current = true;
    dragStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      panX: panRef.current.x,
      panY: panRef.current.y,
    };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.mouseX;
    const dy = e.clientY - dragStartRef.current.mouseY;
    panRef.current.x = dragStartRef.current.panX + dx;
    panRef.current.y = dragStartRef.current.panY + dy;
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    isDraggingRef.current = false;
    (e.target as HTMLElement).releasePointerCapture(e.pointerId);
  };

  // Click-through: canvas hit-test → character id → session id.
  const handleClick = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    const lifecycle = lifecycleRef.current;
    if (!canvas || !lifecycle) return;
    const rect = canvas.getBoundingClientRect();
    const state = officeStateRef.current;
    const layout = state.getLayout();
    const zoom = zoomRef.current;
    const mapW = layout.cols * TILE_SIZE * zoom;
    const mapH = layout.rows * TILE_SIZE * zoom;
    const offsetX = Math.floor((canvas.width - mapW) / 2) + Math.round(panRef.current.x);
    const offsetY = Math.floor((canvas.height - mapH) / 2) + Math.round(panRef.current.y);
    const worldX = (e.clientX - rect.left - offsetX) / zoom;
    const worldY = (e.clientY - rect.top - offsetY) / zoom;
    const charId = state.getCharacterAt(worldX, worldY);
    if (charId === null) return;
    const sessionId = lifecycle.sessionIdFor(charId);
    if (sessionId) onAgentClick(sessionId);
  };

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', overflow: 'hidden', background: 'transparent' }}
    >
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          cursor: isDraggingRef.current ? 'grabbing' : 'grab',
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onClick={handleClick}
      />
    </div>
  );
}
