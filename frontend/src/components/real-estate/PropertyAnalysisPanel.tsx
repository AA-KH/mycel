import React from "react";
import { Property } from "../../hooks/useRealEstateDemo";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 8px 8px 0 6px rgba(0,0,0,0.4)",
  imageRendering: "pixelated",
};

interface Props {
  properties: Property[];
}

function MatchBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2 mt-2 pt-2" style={{ borderTop: "1px solid #232a38" }}>
      <span className="text-[7px] tracking-widest text-[#4e5a70]" style={{ fontFamily: PIXEL }}>
        MATCH
      </span>
      <div className="flex-1 h-2 relative" style={{ background: "#1b2230" }}>
        <div
          className="absolute inset-y-0 left-0 transition-all duration-500"
          style={{
            width: `${score}%`,
            background: score >= 90 ? "#a3be8c" : score >= 75 ? "#ebcb8b" : "#bf616a",
            boxShadow: `0 0 4px ${score >= 90 ? "#a3be8c" : "#ebcb8b"}55`,
          }}
        />
      </div>
      <span
        className="text-[14px] font-bold"
        style={{
          fontFamily: TERM,
          color: score >= 90 ? "#a3be8c" : score >= 75 ? "#ebcb8b" : "#bf616a",
        }}
      >
        {score}%
      </span>
    </div>
  );
}

export default function PropertyAnalysisPanel({ properties }: Props) {
  return (
    <div style={pixelPanel} className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="shrink-0 px-4 py-3 flex items-center justify-between"
        style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
      >
        <span className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
          🏠 PROPERTY RESULTS
        </span>
        <span
          className="px-2 py-1 text-[7px] tracking-widest"
          style={{
            fontFamily: PIXEL,
            background: properties.length > 0 ? "#1a2e1a" : "#1b2230",
            color: properties.length > 0 ? "#a3be8c" : "#4e5a70",
            border: `2px solid ${properties.length > 0 ? "#a3be8c" : "#3a4356"}`,
          }}
        >
          {properties.length} FOUND
        </span>
      </div>

      {/* Cards */}
      <div className="flex-1 overflow-y-auto p-3 min-h-0">
        {properties.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <span className="text-4xl opacity-20">🏘️</span>
            <span className="text-[18px] text-[#3a4356]" style={{ fontFamily: TERM }}>
              No properties found yet
            </span>
            <span className="text-[7px] text-[#232a38] tracking-widest" style={{ fontFamily: PIXEL }}>
              SEND A QUERY TO SEARCH
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {properties.map((p, idx) => (
              <div
                key={p.property_id}
                className="p-3 transition-all duration-200"
                style={{
                  background: "#1b2230",
                  boxShadow: "0 0 0 2px #3a4356, 4px 4px 0 rgba(0,0,0,0.35)",
                }}
              >
                {/* Rank + Title */}
                <div className="flex items-start gap-3 mb-2">
                  <span
                    className="shrink-0 w-7 h-7 flex items-center justify-center text-[9px] font-bold"
                    style={{
                      fontFamily: PIXEL,
                      background: idx === 0 ? "#f28a1f" : "#232a38",
                      color: idx === 0 ? "#241303" : "#7f8ca5",
                      boxShadow: idx === 0
                        ? "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.3)"
                        : "0 0 0 2px #3a4356",
                    }}
                  >
                    #{idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div
                      className="text-[17px] font-bold text-[#eceff4] truncate"
                      style={{ fontFamily: TERM }}
                      title={p.title}
                    >
                      {p.title}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-[14px] text-[#88c0d0]" style={{ fontFamily: TERM }}>
                        📍 {p.location}
                      </span>
                      <span
                        className="px-2 text-[12px]"
                        style={{
                          fontFamily: TERM,
                          background: "#232a38",
                          color: "#a3be8c",
                        }}
                      >
                        {p.bhk} BHK
                      </span>
                    </div>
                  </div>
                  {/* Price */}
                  <div className="shrink-0 text-right">
                    <div className="text-[9px] text-[#4e5a70]" style={{ fontFamily: PIXEL }}>
                      PRICE
                    </div>
                    <div className="text-[20px] font-bold text-[#ebcb8b]" style={{ fontFamily: TERM }}>
                      ₹{(p.price / 100000).toFixed(1)}L
                    </div>
                  </div>
                </div>

                {/* Match bar */}
                {p.match_score && <MatchBar score={p.match_score} />}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
