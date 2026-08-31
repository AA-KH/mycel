import { useEffect, useState } from "react";
import type { DecisionRecord } from "@/lib/armoriq/engine";
import {
  C,
  Card,
  CardHead,
  PIXEL,
  PixelButton,
  RISK_COLOR,
  TERM,
  relTime,
} from "./primitives";

function ApprovalCard({
  d,
  now,
  onResolve,
}: {
  d: DecisionRecord;
  now: number;
  onResolve: (status: "ALLOW" | "DENY") => void;
}) {
  // Gated requests expire; surface the countdown so the queue feels urgent.
  const ageSecs = Math.round((now - d.ts) / 1000);
  const ttl = Math.max(0, 300 - ageSecs);
  const mins = String(Math.floor(ttl / 60)).padStart(2, "0");
  const secs = String(ttl % 60).padStart(2, "0");
  const urgent = ttl < 90;

  return (
    <div
      className="px-3 py-2.5 flex flex-col gap-2"
      style={{
        borderBottom: `2px solid ${C.border}`,
        borderLeft: `4px solid ${C.orange}`,
      }}
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span
          className="text-[7px] tracking-wider px-1.5 py-1"
          style={{
            fontFamily: PIXEL,
            color: C.bg,
            background: RISK_COLOR[d.riskLevel],
          }}
        >
          {d.riskLevel}
        </span>
        <span className="text-[15px] flex-1 truncate" style={{ fontFamily: TERM, color: C.text }}>
          {d.actionType}
        </span>
        <span
          className="text-[14px] shrink-0"
          style={{ fontFamily: TERM, color: urgent ? C.red : C.muted }}
        >
          expires {mins}:{secs}
        </span>
      </div>

      <div className="text-[14px] leading-snug" style={{ fontFamily: TERM, color: C.muted }}>
        <span style={{ color: C.dim }}>actor </span>
        {d.agentId}
        <span style={{ color: C.dim }}> · target </span>
        {d.resource}
      </div>
      <div className="text-[14px] leading-snug" style={{ fontFamily: TERM, color: C.orange }}>
        {d.reason}
      </div>
      <div className="text-[13px]" style={{ fontFamily: TERM, color: C.dim }}>
        {d.policyId} · {d.requestId} · raised {relTime(d.ts, now)}
      </div>

      <div className="flex gap-2 pt-0.5">
        <PixelButton size="sm" onClick={() => onResolve("ALLOW")} color={C.green} textColor="#1b2a12">
          ✓ APPROVE
        </PixelButton>
        <PixelButton size="sm" onClick={() => onResolve("DENY")} color={C.red} textColor="#2a1114">
          ✕ DENY
        </PixelButton>
      </div>
    </div>
  );
}

export default function ApprovalsPanel({
  approvals,
  onResolve,
}: {
  approvals: DecisionRecord[];
  onResolve: (decisionId: string, status: "ALLOW" | "DENY") => void;
}) {
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);

  return (
    <Card>
      <CardHead
        icon="✋"
        title="HUMAN APPROVAL QUEUE"
        right={
          <span
            className="text-[7px] tracking-wider px-1.5 py-1"
            style={{
              fontFamily: PIXEL,
              color: approvals.length ? C.bg : C.dim,
              background: approvals.length ? C.orange : "transparent",
              boxShadow: approvals.length ? "none" : `inset 0 0 0 2px ${C.border}`,
            }}
          >
            {approvals.length} PENDING
          </span>
        }
      />

      <div className="overflow-y-auto" style={{ maxHeight: 360 }}>
        {approvals.length === 0 ? (
          <div className="px-3 py-8 flex flex-col items-center gap-2">
            <span className="text-[24px]" style={{ fontFamily: TERM, color: C.green }}>
              ✓
            </span>
            <span
              className="text-[8px] tracking-widest text-center"
              style={{ fontFamily: PIXEL, color: C.green }}
            >
              QUEUE CLEAR
            </span>
            <span className="text-[14px] text-center" style={{ fontFamily: TERM, color: C.dim }}>
              no actions awaiting human authorization
            </span>
          </div>
        ) : (
          approvals.map(d => (
            <ApprovalCard
              key={d.decisionId}
              d={d}
              now={now}
              onResolve={status => onResolve(d.decisionId, status)}
            />
          ))
        )}
      </div>

      <div
        className="px-3 py-2 text-[13px]"
        style={{
          fontFamily: TERM,
          color: C.dim,
          background: "#080b11",
          borderTop: `3px solid ${C.border}`,
        }}
      >
        unresolved requests fail closed at expiry
      </div>
    </Card>
  );
}
