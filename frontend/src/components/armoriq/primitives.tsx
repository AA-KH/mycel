import type { CSSProperties, ReactNode } from "react";
import type { DecisionStatus, RiskLevel } from "@/lib/armoriq/engine";

export const PIXEL = "'Press Start 2P', monospace";
export const TERM = "'VT323', monospace";

export const C = {
  bg: "#0b0e15",
  panel: "#12161f",
  raise: "#1b2230",
  border: "#3a4356",
  orange: "#f28a1f",
  green: "#a3be8c",
  red: "#bf616a",
  yellow: "#ebcb8b",
  blue: "#5e81ac",
  cyan: "#88c0d0",
  text: "#c8d2e4",
  muted: "#7f8ca5",
  dim: "#4e5a70",
} as const;

export const pixelPanel: CSSProperties = {
  background: C.panel,
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

export const STATUS_COLOR: Record<DecisionStatus, string> = {
  ALLOW: C.green,
  DENY: C.red,
  REQUIRE_APPROVAL: C.orange,
  REQUIRE_REVIEW: C.yellow,
};

export const STATUS_GLYPH: Record<DecisionStatus, string> = {
  ALLOW: "✓",
  DENY: "✕",
  REQUIRE_APPROVAL: "!",
  REQUIRE_REVIEW: "?",
};

export const RISK_COLOR: Record<RiskLevel, string> = {
  LOW: C.green,
  MEDIUM: C.yellow,
  HIGH: C.orange,
  CRITICAL: C.red,
};

/* ─────────────────────────── building blocks ─────────────────────────── */

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={className}
      style={{
        background: C.panel,
        boxShadow: `0 0 0 3px ${C.border}, 4px 4px 0 3px rgba(0,0,0,0.4)`,
      }}
    >
      {children}
    </div>
  );
}

export function CardHead({
  icon,
  title,
  right,
}: {
  icon: string;
  title: string;
  right?: ReactNode;
}) {
  return (
    <div
      className="flex items-center justify-between gap-3 px-3 py-2.5"
      style={{ background: C.bg, borderBottom: `3px solid ${C.border}` }}
    >
      <div
        className="flex items-center gap-2 text-[8px] tracking-widest"
        style={{ fontFamily: PIXEL, color: C.orange }}
      >
        <span aria-hidden="true">{icon}</span>
        <span>{title}</span>
      </div>
      {right}
    </div>
  );
}

/** Small uppercase pixel tag. */
export function Tag({
  children,
  color = C.muted,
  solid = false,
}: {
  children: ReactNode;
  color?: string;
  solid?: boolean;
}) {
  return (
    <span
      className="inline-block px-1.5 py-1 text-[7px] tracking-wider whitespace-nowrap"
      style={{
        fontFamily: PIXEL,
        color: solid ? C.bg : color,
        background: solid ? color : "transparent",
        boxShadow: solid ? "none" : `inset 0 0 0 2px ${color}`,
      }}
    >
      {children}
    </span>
  );
}

/** Terminal-style key/value line. */
export function KV({
  label,
  value,
  valueColor = C.text,
}: {
  label: string;
  value: ReactNode;
  valueColor?: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1">
      <span
        className="text-[14px] shrink-0"
        style={{ fontFamily: TERM, color: C.dim }}
      >
        {label}
      </span>
      <span
        className="text-[15px] text-right break-all"
        style={{ fontFamily: TERM, color: valueColor }}
      >
        {value}
      </span>
    </div>
  );
}

export function LedDot({
  color = C.green,
  pulse = true,
}: {
  color?: string;
  pulse?: boolean;
}) {
  return (
    <span
      className={`inline-block w-2 h-2 shrink-0 ${pulse ? "aq-pulse" : ""}`}
      style={{ background: color, boxShadow: `0 0 6px ${color}` }}
    />
  );
}

/** Chunky pixel meter. */
export function Meter({
  value,
  color = C.green,
  height = 8,
}: {
  value: number;
  color?: string;
  height?: number;
}) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div
      className="w-full"
      style={{ height, background: "#080b11", boxShadow: `inset 0 0 0 2px ${C.border}` }}
    >
      <div
        className="h-full transition-all duration-500"
        style={{ width: `${pct}%`, background: color }}
      />
    </div>
  );
}

/** Pixel push-button. */
export function PixelButton({
  children,
  onClick,
  color = C.orange,
  textColor = "#241303",
  size = "md",
  title,
}: {
  children: ReactNode;
  onClick?: () => void;
  color?: string;
  textColor?: string;
  size?: "sm" | "md";
  title?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={`transition-transform active:translate-y-[2px] ${
        size === "sm" ? "px-2.5 py-1.5" : "px-4 py-2.5"
      }`}
      style={{
        fontFamily: PIXEL,
        fontSize: size === "sm" ? "7px" : "9px",
        letterSpacing: "0.08em",
        background: color,
        color: textColor,
        boxShadow: `0 0 0 3px ${C.bg}, inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.32), 0 4px 0 3px ${C.bg}`,
      }}
    >
      {children}
    </button>
  );
}

export function relTime(ts: number, now: number): string {
  const s = Math.max(0, Math.round((now - ts) / 1000));
  if (s < 1) return "now";
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  return `${Math.floor(m / 60)}h ago`;
}

export function clockTime(ts: number): string {
  return new Date(ts).toLocaleTimeString("en-GB", { hour12: false });
}
