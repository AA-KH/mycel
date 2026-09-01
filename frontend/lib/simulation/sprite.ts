/* ------------------------------------------------------------------ */
/* Character Sprite Resolver                                            */
/*                                                                      */
/* THE single place that turns an agent's (state, dir, frame) into a     */
/* source rectangle + draw rectangle. The canvas renderer, the hover     */
/* hitbox and the name label all call resolveAgentSprite() so they can   */
/* never disagree about where a character actually is on screen.         */
/*                                                                      */
/* Nothing here is hand-tuned per agent or per room — the numbers all    */
/* come from measured spritesheet baselines in ./types.                  */
/* ------------------------------------------------------------------ */

import { T } from './map-data';
import {
  AgentAnimState,
  CHAR_FRAME_H,
  CHAR_FRAME_W,
  DIR_SHEET,
  SIT_COLS,
  SPRITE_BOUNDS,
  STAND_COL,
  WALK_COLS,
  WORK_COLS,
  type SimAgent,
} from './types';

/** True when the agent's animation state is one of the seated states. */
export function isSeatedState(state: AgentAnimState): boolean {
  return state === AgentAnimState.SIT || state === AgentAnimState.WORK;
}

export interface ResolvedSprite {
  /** Source rect on the 112x96 sheet */
  sx: number;
  sy: number;
  sw: number;
  sh: number;
  /** Destination rect in world px (top-left of the 16x32 frame) */
  dx: number;
  dy: number;
  /** Draw mirrored across its own vertical centre line (LEFT facing) */
  mirror: boolean;
  /** World y of the character's visual baseline (feet, or seat contact) */
  baselineY: number;
  /** World y of the topmost opaque pixel — labels/badges hang off this */
  topY: number;
  /**
   * World y of the frame's bottom edge == bottom edge of the occupied
   * tile. Pose-independent, so anything pinned to it (name labels) holds
   * still when an agent sits down.
   */
  anchorY: number;
}

/**
 * Pick the spritesheet column for the agent's current animation state.
 *
 * Frame groups are kept strictly separate so a working agent never dips
 * back into the seated-idle poses mid-animation.
 *   walk → 1,0,2,0   sit → 3,4   work → 5,6   idle → 0
 */
function columnFor(agent: SimAgent): number {
  switch (agent.state) {
    case AgentAnimState.WALK:
      return WALK_COLS[agent.frame % WALK_COLS.length];
    case AgentAnimState.SIT:
      return SIT_COLS[agent.frame % SIT_COLS.length];
    case AgentAnimState.WORK:
      return WORK_COLS[agent.frame % WORK_COLS.length];
    case AgentAnimState.IDLE:
    default:
      return STAND_COL;
  }
}

/**
 * Resolve an agent into concrete source + destination rectangles.
 *
 * Anchor model — ONE rule, no special cases
 * -----------------------------------------
 * `agent.x` / `agent.y` are the CENTRE of the tile the agent occupies.
 * Every frame of every pose is drawn in the SAME 16x32 box, whose bottom
 * edge sits on the BOTTOM edge of that tile:
 *
 *        anchorY = agent.y + T / 2          (tile bottom)
 *        dy      = anchorY - CHAR_FRAME_H
 *
 * This is the spritesheet's own convention, and it is verifiable from the
 * asset pixels rather than assumed. Per-frame alpha bounds (measured over
 * all six sheets — see SPRITE_BOUNDS) show that the artist already baked
 * the pose relationships into a shared frame box:
 *
 *   row 0 (DOWN)   standing ends y29/30   seated ends y31  (+2: near leg
 *                                                          and foot come
 *                                                          toward camera)
 *   row 1 (UP)     standing ends y29/30   seated ends y25  (-5: seated on
 *                                                          a raised seat,
 *                                                          legs hidden)
 *   row 2 (RIGHT)  standing ends y30      seated ends y29  (-1)
 *
 * Those deltas ARE the sit offsets. Re-pinning each group's last opaque
 * pixel to the tile bottom instead — the previous model — cancels them
 * out and drags the UP-facing seated body 6px down, burying the torso in
 * the chair back and pushing the head into the desk. Nothing needs to be
 * re-derived per direction: honouring the frame box reproduces the intent
 * for free, in every direction and every state.
 *
 * The same box rule governs 32px-tall furniture (see the chair branch in
 * pixel-office), so a 16x32 character and a 16x32 chair on one tile land
 * on a shared floor line by construction.
 *
 * SPRITE_BOUNDS is therefore descriptive only: it positions labels,
 * badges and the hover hitbox, and never moves the character.
 */
export function resolveAgentSprite(agent: SimAgent): ResolvedSprite {
  const { row, mirror } = DIR_SHEET[agent.dir];
  const col = columnFor(agent);
  const seated = isSeatedState(agent.state);

  const bounds = SPRITE_BOUNDS[row];
  const bound = seated ? bounds.seated : bounds.standing;

  // Contact anchor: bottom edge of the occupied tile, for every pose.
  const anchorY = agent.y + T / 2;

  const dx = Math.round(agent.x - CHAR_FRAME_W / 2);
  const dy = Math.round(anchorY) - CHAR_FRAME_H;

  return {
    anchorY: dy + CHAR_FRAME_H,
    sx: col * CHAR_FRAME_W,
    sy: row * CHAR_FRAME_H,
    sw: CHAR_FRAME_W,
    sh: CHAR_FRAME_H,
    dx,
    dy,
    mirror,
    baselineY: dy + bound.baseline + 1,
    // Measured head clearance for this row + pose group. Taken as the min
    // across all sheets and all frames in the group, so labels sit at a
    // consistent height instead of bobbing with the animation.
    topY: dy + bound.top,
  };
}

/**
 * Interaction box for hover/click, in world px.
 * Derived from the resolved sprite so it always tracks the visible body
 * (including the label strip beneath the feet).
 */
export function agentHitBox(agent: SimAgent): { x: number; y: number; w: number; h: number } {
  const s = resolveAgentSprite(agent);
  return {
    x: s.dx,
    y: s.topY,
    w: CHAR_FRAME_W,
    h: s.baselineY + 8 - s.topY,
  };
}
