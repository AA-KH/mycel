import React from "react";
import { ActiveEmployee } from "../../hooks/useRealEstateDemo";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 8px 8px 0 6px rgba(0,0,0,0.4)",
  imageRendering: "pixelated",
};

const STATUS_COLORS: Record<string, string> = {
  Running: "#f28a1f",
  Idle: "#4e5a70",
  Complete: "#a3be8c",
  Error: "#bf616a",
};

interface Props {
  activeEmployee: ActiveEmployee;
  currentStage: string;
}

function DataRow({ label, value, color = "#c8d2e4" }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-start gap-3 py-2" style={{ borderBottom: "1px solid #232a38" }}>
      <span
        className="text-[7px] tracking-widest text-[#4e5a70] min-w-[80px] pt-0.5 uppercase"
        style={{ fontFamily: PIXEL }}
      >
        {label}
      </span>
      <span className="text-[18px] leading-tight flex-1" style={{ fontFamily: TERM, color }}>
        {value}
      </span>
    </div>
  );
}

export default function ActiveEmployeePanel({ activeEmployee, currentStage }: Props) {
  const status = activeEmployee.status || "Idle";
  const statusColor = STATUS_COLORS[status] || "#4e5a70";

  return (
    <div style={pixelPanel} className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="shrink-0 px-4 py-3 flex items-center justify-between"
        style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
      >
        <span className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
          ⚡ ACTIVE WORK
        </span>

        {/* Status chip */}
        <span
          className="px-3 py-1 text-[7px] font-bold tracking-widest"
          style={{
            fontFamily: PIXEL,
            background: statusColor,
            color: "#0b0e15",
            boxShadow: `0 0 0 2px #12161f, 0 0 8px ${statusColor}55`,
          }}
        >
          {status.toUpperCase()}
          {status === "running" && (
            <span className="ml-1 inline-block animate-work-blink">█</span>
          )}
        </span>
      </div>

      {/* Body */}
      <div className="flex-1 px-4 py-3 flex flex-col justify-between overflow-hidden">
        <div>
          <DataRow label="Team" value={activeEmployee.team || "—"} color="#88c0d0" />
          <DataRow label="Employee" value={activeEmployee.member || "Waiting..."} color="#eceff4" />
          {activeEmployee.source && (
            <DataRow label="Source" value={activeEmployee.source} color="#a3be8c" />
          )}
        </div>

        {/* Current task */}
        <div className="mt-3">
          <span className="text-[7px] tracking-widest text-[#4e5a70]" style={{ fontFamily: PIXEL }}>
            CURRENT TASK
          </span>
          <div
            className="mt-1 px-3 py-2 text-[16px] text-[#aeb9cf] leading-snug"
            style={{
              fontFamily: TERM,
              background: "#1b2230",
              borderLeft: "3px solid #3a4356",
            }}
          >
            {activeEmployee.task || "Idle — awaiting user input"}
          </div>
        </div>

        {/* Stage */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[7px] tracking-widest text-[#4e5a70]" style={{ fontFamily: PIXEL }}>
            STAGE
          </span>
          <span
            className="text-[17px]"
            style={{ fontFamily: TERM, color: statusColor }}
          >
            {currentStage}
          </span>
        </div>

        {/* Special handoff notice */}
        {(activeEmployee.team === "Legal" || activeEmployee.team === "Finance") && (
          <div
            className="mt-3 px-3 py-2 text-[13px] leading-tight"
            style={{
              fontFamily: TERM,
              background: "#2e1a1a",
              borderLeft: "3px solid #bf616a",
              color: "#bf616a",
            }}
          >
            ⚠ SPECIALIST HANDOFF — {activeEmployee.team} expertise required
          </div>
        )}
      </div>

      <style>{`
        @keyframes work-blink { 0%,50%{opacity:1} 51%,100%{opacity:0} }
        .animate-work-blink { animation: work-blink 0.8s steps(1) infinite; }
      `}</style>
    </div>
  );
}
