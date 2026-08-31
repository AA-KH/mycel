import { useEffect, useState } from "react";
import type { DecisionRecord } from "@/lib/armoriq/engine";
import {
  C,
  Card,
  CardHead,
  LedDot,
  PIXEL,
  PixelButton,
  RISK_COLOR,
  STATUS_COLOR,
  STATUS_GLYPH,
  TERM,
  clockTime,
  relTime,
} from "./primitives";

function StreamRow({
  d,
  now,
  selected,
  onSelect,
}: {
  d: DecisionRecord;
  now: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const effective = d.resolution?.status ?? d.status;
  const color = STATUS_COLOR[effective];

  return (
    <button
      type="button"
      onClick={onSelect}
      className="w-full text-left px-2.5 py-2 transition-colors"
      style={{
        background: selected ? C.raise : "transparent",
        borderBottom: `2px solid ${C.border}`,
        borderLeft: `4px solid ${color}`,
      }}
    >
      <div className="flex items-center gap-2">
        <span
          className="w-4 h-4 shrink-0 flex items-center justify-center text-[9px]"
          style={{ fontFamily: TERM, background: color, color: C.bg }}
        >
          {STATUS_GLYPH[effective]}
        </span>
        <span
          className="text-[7px] tracking-wider shrink-0"
          style={{ fontFamily: PIXEL, color }}
        >
          {effective === "REQUIRE_APPROVAL" ? "GATED" : effective}
        </span>
        <span
          className="text-[14px] truncate flex-1"
          style={{ fontFamily: TERM, color: C.text }}
        >
          {d.actionType}
        </span>
        <span
          className="text-[13px] shrink-0"
          style={{ fontFamily: TERM, color: RISK_COLOR[d.riskLevel] }}
        >
          {d.riskLevel}
        </span>
      </div>

      <div className="flex items-center gap-2 mt-1 pl-6">
        <span
          className="text-[13px] truncate flex-1"
          style={{ fontFamily: TERM, color: C.muted }}
        >
          {d.agentId} → {d.resource}
        </span>
        <span
          className="text-[12px] shrink-0"
          style={{ fontFamily: TERM, color: C.dim }}
        >
          {d.latencyMs}ms · {relTime(d.ts, now)}
        </span>
      </div>
    </button>
  );
}

function DetailDrawer({ d }: { d: DecisionRecord }) {
  const effective = d.resolution?.status ?? d.status;
  return (
    <div
      className="px-3 py-3 flex flex-col gap-2"
      style={{ background: "#080b11", borderTop: `3px solid ${C.border}` }}
    >
      <div
        className="text-[7px] tracking-widest"
        style={{ fontFamily: PIXEL, color: C.orange }}
      >
        DECISION DETAIL
      </div>

      <div className="text-[15px] leading-snug" style={{ fontFamily: TERM }}>
        <span style={{ color: C.dim }}>intent&nbsp;&nbsp;</span>
        <span style={{ color: C.text }}>{d.intent}</span>
      </div>
      <div className="text-[15px] leading-snug" style={{ fontFamily: TERM }}>
        <span style={{ color: C.dim }}>reason&nbsp;&nbsp;</span>
        <span style={{ color: STATUS_COLOR[effective] }}>{d.reason}</span>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-0.5 pt-1">
        {[
          ["decision", d.decisionId],
          ["trace", d.traceId.slice(0, 14) + "…"],
          ["policy", d.policyId],
          ["env", d.environment],
          ["tool", d.toolId ?? "—"],
          ["audit", d.auditRef],
        ].map(([k, v]) => (
          <div key={k} className="flex gap-1.5 min-w-0">
            <span
              className="text-[13px] shrink-0"
              style={{ fontFamily: TERM, color: C.dim }}
            >
              {k}
            </span>
            <span
              className="text-[13px] truncate"
              style={{ fontFamily: TERM, color: C.muted }}
            >
              {v}
            </span>
          </div>
        ))}
      </div>

      <div
        className="flex flex-wrap gap-x-3 gap-y-1 pt-1.5"
        style={{ borderTop: `2px solid ${C.border}` }}
      >
        {d.signals.map(s => (
          <span key={s.key} className="text-[13px]" style={{ fontFamily: TERM }}>
            <span style={{ color: C.dim }}>{s.key}=</span>
            <span style={{ color: C.cyan }}>{s.value}</span>
          </span>
        ))}
      </div>

      {d.resolution && (
        <div
          className="text-[14px] pt-1.5"
          style={{
            fontFamily: TERM,
            color: C.muted,
            borderTop: `2px solid ${C.border}`,
          }}
        >
          resolved {d.resolution.status} by {d.resolution.by} at{" "}
          {clockTime(d.resolution.ts)}
        </div>
      )}
    </div>
  );
}

export default function DecisionStream({
  decisions,
  live,
  onToggleLive,
}: {
  decisions: DecisionRecord[];
  live: boolean;
  onToggleLive: () => void;
}) {
  const [now, setNow] = useState(Date.now());
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState<"ALL" | "BLOCKED">("ALL");

  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);

  const rows = decisions.filter(d =>
    filter === "ALL"
      ? true
      : (d.resolution?.status ?? d.status) !== "ALLOW",
  );
  const active = decisions.find(d => d.decisionId === selected);

  return (
    <Card>
      <CardHead
        icon="📡"
        title="LIVE DECISION STREAM"
        right={
          <div className="flex items-center gap-2">
            <LedDot color={live ? C.green : C.yellow} pulse={live} />
            <span
              className="text-[7px] tracking-widest"
              style={{ fontFamily: PIXEL, color: live ? C.green : C.yellow }}
            >
              {live ? "STREAMING" : "PAUSED"}
            </span>
          </div>
        }
      />

      {/* ── toolbar ── */}
      <div
        className="flex items-center justify-between gap-2 px-3 py-2"
        style={{ background: C.raise, borderBottom: `3px solid ${C.border}` }}
      >
        <div className="flex gap-1.5">
          {(["ALL", "BLOCKED"] as const).map(f => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className="px-2 py-1 text-[7px] tracking-wider"
              style={{
                fontFamily: PIXEL,
                color: filter === f ? C.bg : C.muted,
                background: filter === f ? C.orange : "transparent",
                boxShadow:
                  filter === f ? "none" : `inset 0 0 0 2px ${C.border}`,
              }}
            >
              {f}
            </button>
          ))}
        </div>
        <PixelButton
          size="sm"
          onClick={onToggleLive}
          color={live ? C.blue : C.green}
          textColor={live ? "#eceff4" : "#1b2a12"}
        >
          {live ? "❚❚ PAUSE" : "▶ RESUME"}
        </PixelButton>
      </div>

      {/* ── rows ── */}
      <div className="overflow-y-auto" style={{ maxHeight: 300 }}>
        {rows.length === 0 ? (
          <div
            className="px-3 py-6 text-center text-[15px]"
            style={{ fontFamily: TERM, color: C.dim }}
          >
            no blocked or gated decisions in window
          </div>
        ) : (
          rows.map(d => (
            <StreamRow
              key={d.decisionId}
              d={d}
              now={now}
              selected={d.decisionId === selected}
              onSelect={() =>
                setSelected(prev => (prev === d.decisionId ? null : d.decisionId))
              }
            />
          ))
        )}
      </div>

      {active ? (
        <DetailDrawer d={active} />
      ) : (
        <div
          className="px-3 py-2 text-[13px]"
          style={{
            fontFamily: TERM,
            color: C.dim,
            background: "#080b11",
            borderTop: `3px solid ${C.border}`,
          }}
        >
          select a decision to inspect signals and policy trace
        </div>
      )}
    </Card>
  );
}
