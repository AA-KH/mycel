import { useEffect, useState } from "react";
import type { DecisionRecord } from "@/lib/armoriq/engine";
import {
  C,
  Card,
  CardHead,
  PIXEL,
  RISK_COLOR,
  STATUS_COLOR,
  TERM,
} from "./primitives";

/**
 * Replays the newest decision through the gateway stages so the operator
 * can watch intent -> risk -> policy -> provider -> audit resolve.
 */
export default function PipelineVisualizer({
  decision,
}: {
  decision: DecisionRecord | undefined;
}) {
  const [step, setStep] = useState(0);

  // Restart the replay whenever a new decision arrives.
  useEffect(() => {
    if (!decision) return;
    setStep(0);
    const timers: number[] = [];
    decision.stages.forEach((_, i) => {
      timers.push(window.setTimeout(() => setStep(i + 1), 160 + i * 150));
    });
    return () => timers.forEach(t => window.clearTimeout(t));
  }, [decision?.decisionId, decision]);

  if (!decision) return null;

  const effective = decision.resolution?.status ?? decision.status;
  const verdictColor = STATUS_COLOR[effective];
  const halted = decision.stages.findIndex(s => !s.ok);

  return (
    <Card>
      <CardHead
        icon="⚙"
        title="EVALUATION PIPELINE"
        right={
          <span
            className="text-[13px]"
            style={{ fontFamily: TERM, color: C.muted }}
          >
            {decision.requestId}
          </span>
        }
      />

      {/* ── request summary ── */}
      <div
        className="px-3 py-2.5 flex flex-col gap-1"
        style={{ background: C.raise, borderBottom: `3px solid ${C.border}` }}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className="text-[7px] tracking-wider px-1.5 py-1"
            style={{
              fontFamily: PIXEL,
              color: C.bg,
              background: RISK_COLOR[decision.riskLevel],
            }}
          >
            {decision.riskLevel}
          </span>
          <span
            className="text-[15px]"
            style={{ fontFamily: TERM, color: C.text }}
          >
            {decision.actionType}
          </span>
          <span className="text-[14px]" style={{ fontFamily: TERM, color: C.dim }}>
            · {decision.environment}
          </span>
        </div>
        <div
          className="text-[14px] leading-snug"
          style={{ fontFamily: TERM, color: C.muted }}
        >
          {decision.agentLabel} ({decision.agentId}) → {decision.resource}
        </div>
      </div>

      {/* ── stages ── */}
      <div className="px-3 py-3 flex flex-col">
        {decision.stages.map((s, i) => {
          const reached = step > i;
          const skipped = halted !== -1 && i > halted;
          const isLast = i === decision.stages.length - 1;
          const color = !reached
            ? C.dim
            : skipped
              ? C.dim
              : s.ok
                ? C.green
                : C.red;

          return (
            <div key={s.id} className="flex gap-2.5">
              {/* rail */}
              <div className="flex flex-col items-center shrink-0">
                <span
                  className="w-5 h-5 flex items-center justify-center text-[10px] transition-all duration-300"
                  style={{
                    fontFamily: TERM,
                    background: reached ? color : "#080b11",
                    color: reached ? C.bg : C.dim,
                    boxShadow: `0 0 0 2px ${reached ? color : C.border}`,
                    transform: reached ? "scale(1)" : "scale(0.82)",
                  }}
                >
                  {!reached ? "·" : skipped ? "–" : s.ok ? "✓" : "✕"}
                </span>
                {!isLast && (
                  <span
                    className="w-[3px] flex-1 min-h-[26px] transition-colors duration-300"
                    style={{ background: reached ? color : C.border }}
                  />
                )}
              </div>

              {/* body */}
              <div
                className="flex-1 pb-3 transition-opacity duration-300"
                style={{ opacity: reached ? 1 : 0.35 }}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span
                    className="text-[7px] tracking-widest"
                    style={{ fontFamily: PIXEL, color: reached ? color : C.dim }}
                  >
                    {s.label}
                  </span>
                  <span
                    className="text-[13px] shrink-0"
                    style={{ fontFamily: TERM, color: C.dim }}
                  >
                    {reached && !skipped ? `${s.latencyMs}ms` : "—"}
                  </span>
                </div>
                <div
                  className="text-[14px] leading-snug mt-0.5"
                  style={{ fontFamily: TERM, color: C.muted }}
                >
                  {skipped ? "short-circuited by upstream deny" : s.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── verdict ── */}
      <div
        className="px-3 py-2.5 flex items-center justify-between gap-2"
        style={{ background: "#080b11", borderTop: `3px solid ${C.border}` }}
      >
        <span
          className="text-[8px] tracking-widest"
          style={{ fontFamily: PIXEL, color: verdictColor }}
        >
          {effective}
        </span>
        <span
          className="text-[14px] text-right"
          style={{ fontFamily: TERM, color: C.muted }}
        >
          total {decision.latencyMs}ms
        </span>
      </div>
    </Card>
  );
}
