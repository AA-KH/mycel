import React, { useEffect, useRef } from "react";
import { TimelineEvent } from "../../hooks/useRealEstateDemo";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 8px 8px 0 6px rgba(0,0,0,0.4)",
  imageRendering: "pixelated",
};

interface Props {
  events: TimelineEvent[];
}

const TYPE_CONFIG: Record<string, { color: string; icon: string; bg: string }> = {
  info:    { color: "#88c0d0", icon: "►", bg: "#1b2a38" },
  success: { color: "#a3be8c", icon: "✓", bg: "#1a2e1a" },
  error:   { color: "#bf616a", icon: "✕", bg: "#2e1a1a" },
};

export default function ActivityTimelinePanel({ events }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div style={pixelPanel} className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="shrink-0 px-4 py-3 flex items-center gap-3"
        style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
      >
        <span className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
          ⬡ ACTIVITY LOG
        </span>
        <span
          className="ml-auto text-[14px] text-[#4e5a70]"
          style={{ fontFamily: TERM }}
        >
          {events.length} events
        </span>
      </div>

      {/* Events */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1 min-h-0">
        {events.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <span className="text-2xl opacity-20">📡</span>
            <span className="text-[16px] text-[#3a4356]" style={{ fontFamily: TERM }}>
              Awaiting events...
            </span>
          </div>
        ) : (
          events.map((ev) => {
            const cfg = TYPE_CONFIG[ev.type] || TYPE_CONFIG.info;
            return (
              <div
                key={ev.id}
                className="flex items-start gap-2 px-2 py-1.5"
                style={{ background: cfg.bg, borderLeft: `3px solid ${cfg.color}` }}
              >
                {/* Timestamp */}
                <span
                  className="shrink-0 text-[13px] text-[#4e5a70] mt-0.5 min-w-[52px]"
                  style={{ fontFamily: TERM }}
                >
                  {ev.timestamp}
                </span>
                {/* Icon */}
                <span
                  className="shrink-0 text-[9px] font-bold w-4"
                  style={{ fontFamily: PIXEL, color: cfg.color }}
                >
                  {cfg.icon}
                </span>
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <span
                    className="text-[8px] font-bold tracking-wide"
                    style={{ fontFamily: PIXEL, color: cfg.color }}
                  >
                    {ev.label}:{" "}
                  </span>
                  <span className="text-[14px] text-[#aeb9cf]" style={{ fontFamily: TERM }}>
                    {ev.summary}
                  </span>
                </div>
              </div>
            );
          })
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
