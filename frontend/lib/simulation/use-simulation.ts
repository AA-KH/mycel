'use client'

/* ------------------------------------------------------------------ */
/* React Hook — useSimulation                                          */
/* Creates and returns a stable SimulationEngine instance.             */
/* The PixelOffice rAF loop calls engine.syncWithMission() and         */
/* engine.tick(dt) every frame — no extra re-renders.                  */
/* ------------------------------------------------------------------ */

import { useRef } from 'react';
import { createSimulationEngine, type SimulationEngine } from './engine';

/**
 * Returns a stable SimulationEngine that persists across renders.
 * The engine is created once and never re-created.
 *
 * Usage inside PixelOffice:
 *   const engine = useSimulation();
 *   // In rAF loop:
 *   engine.syncWithMission(missionRef.current.agents);
 *   engine.tick(dt);
 *   // Read engine.agents for rendering
 */
export function useSimulation(): SimulationEngine {
  const engineRef = useRef<SimulationEngine | null>(null);
  if (!engineRef.current) {
    engineRef.current = createSimulationEngine();
  }
  return engineRef.current;
}
