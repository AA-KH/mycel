'use client'

/**
 * Renders an agent's pixel-art portrait cropped from the character
 * spritesheets used by the pixel office
 * (/assets/pixel-agents/characters/char_{n}.png).
 *
 * Each sheet is 112x96 px = 7 cols x 3 rows of 16x32 frames — the same
 * geometry the canvas office uses (CHAR_FRAME_* in lib/simulation/types).
 * Frame (0,0) is the front-facing (DOWN) standing pose.
 *
 * This module previously declared 7x4 frames of 16x24. That grid does not
 * divide the sheet (4 * 24 = 96 by luck, but the art is laid out in three
 * 32px bands), so a 24px crop sliced frame (0,0) at y=23 and lopped off
 * the feet, which end at y=29. Portraits rendered as legless torsos.
 */

const SHEET_W = 112
const SHEET_H = 96
const FRAME_W = 16
const FRAME_H = 32

export function AgentSprite({
  charIdx,
  scale = 3,
  className,
}: {
  charIdx: number
  /** integer pixel multiplier — 3 renders a 48x96 portrait */
  scale?: number
  className?: string
}) {
  return (
    <span
      aria-hidden="true"
      className={className}
      style={{
        display: 'inline-block',
        width: FRAME_W * scale,
        height: FRAME_H * scale,
        backgroundImage: `url(/assets/pixel-agents/characters/char_${charIdx}.png)`,
        backgroundPosition: '0 0',
        backgroundRepeat: 'no-repeat',
        backgroundSize: `${SHEET_W * scale}px ${SHEET_H * scale}px`,
        imageRendering: 'pixelated',
      }}
    />
  )
}
