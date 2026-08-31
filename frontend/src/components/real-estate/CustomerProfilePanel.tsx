import React from "react";
import { CustomerProfile } from "../../hooks/useRealEstateDemo";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 8px 8px 0 6px rgba(0,0,0,0.4)",
  imageRendering: "pixelated",
};

interface Props {
  customer: CustomerProfile;
}

function ProfileRow({
  icon,
  label,
  value,
  color = "#c8d2e4",
  unknown = false,
}: {
  icon: string;
  label: string;
  value: string;
  color?: string;
  unknown?: boolean;
}) {
  return (
    <div
      className="flex flex-col gap-1 px-4 py-3"
      style={{ borderBottom: "1px solid #1b2230" }}
    >
      <span className="text-[7px] tracking-widest text-[#4e5a70] flex items-center gap-1.5" style={{ fontFamily: PIXEL }}>
        <span className="text-sm">{icon}</span>
        {label}
      </span>
      <span
        className="text-[20px] leading-tight"
        style={{
          fontFamily: TERM,
          color: unknown ? "#3a4356" : color,
          fontStyle: unknown ? "italic" : "normal",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export default function CustomerProfilePanel({ customer }: Props) {
  const reqs = customer.requirements || {};
  const budget = reqs.budget_max
    ? `₹${(reqs.budget_max / 100000).toFixed(1)} Lakh`
    : "Unknown";
  const location = reqs.location || "Unknown";
  const bhk = reqs.bhk ? `${reqs.bhk} BHK` : "Unknown";

  return (
    <div style={pixelPanel} className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div
        className="shrink-0 px-4 py-3 flex items-center gap-3"
        style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
      >
        <span className="text-[9px] font-bold tracking-widest text-[#f28a1f]" style={{ fontFamily: PIXEL }}>
          👤 CUSTOMER FILE
        </span>
      </div>

      {/* Avatar area */}
      <div
        className="shrink-0 flex flex-col items-center py-5 gap-2"
        style={{ background: "#0d1117", borderBottom: "3px solid #1b2230" }}
      >
        {/* Pixel avatar */}
        <div
          className="w-16 h-16 flex items-center justify-center text-4xl"
          style={{
            background: "#1b2230",
            boxShadow:
              "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 4px 4px 0 6px rgba(0,0,0,0.4)",
          }}
        >
          🧑
        </div>
        <div className="text-[22px] font-bold text-[#eceff4]" style={{ fontFamily: TERM }}>
          {customer.name}
        </div>
        <div
          className="px-3 py-0.5 text-[7px] tracking-widest"
          style={{
            fontFamily: PIXEL,
            background: "#1a2a1a",
            color: "#a3be8c",
            border: "2px solid #a3be8c",
          }}
        >
          PIONEER MEMBER
        </div>
      </div>

      {/* Profile rows */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <ProfileRow
          icon="💰"
          label="BUDGET"
          value={budget}
          color="#ebcb8b"
          unknown={!reqs.budget_max}
        />
        <ProfileRow
          icon="📍"
          label="LOCATION"
          value={location}
          color="#88c0d0"
          unknown={!reqs.location}
        />
        <ProfileRow
          icon="🏠"
          label="CONFIGURATION"
          value={bhk}
          color="#a3be8c"
          unknown={!reqs.bhk}
        />

        {/* Tip */}
        <div className="mt-auto px-4 py-4">
          <div
            className="p-3 text-[13px] leading-snug"
            style={{
              fontFamily: TERM,
              background: "#1a2a1a",
              borderLeft: "3px solid #a3be8c",
              color: "#7f8ca5",
            }}
          >
            Profile is updated automatically as the AI extracts details from your conversation.
          </div>
        </div>
      </div>
    </div>
  );
}
