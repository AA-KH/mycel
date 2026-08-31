import React from "react";
import { useWalletCards } from "../hooks/useWalletCards";
import { TEAM_REGISTRY } from "../config/agent-roles";
import type { WalletCard, WalletCardStatus } from "../types/agent";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const STATUS_BADGE: Record<WalletCardStatus, { bg: string; label: string; textColor: string }> = {
  assigned: { bg: "#f2b01f", label: "ASSIGNED", textColor: "#241303" },
  in_progress: { bg: "#79d97c", label: "WORKING", textColor: "#0e2a12" },
  done: { bg: "#88c0d0", label: "DONE", textColor: "#12161f" },
};

function CardItem({ card }: { card: WalletCard }) {
  const teamInfo = TEAM_REGISTRY[card.team];
  const badge = STATUS_BADGE[card.status] || STATUS_BADGE.assigned;

  return (
    <div
      className="transition-transform duration-150 hover:-translate-y-0.5"
      style={{
        background: "#1b2230",
        boxShadow: `0 0 0 3px ${teamInfo?.color || "#3a4356"}, 4px 4px 0 3px rgba(0,0,0,0.35)`,
        animation: card.status === "assigned" ? "wallet-slideIn 0.4s ease-out" : undefined,
      }}
    >
      {/* Header row: emoji + name + status */}
      <div
        className="flex items-center gap-3 px-4 py-3"
        style={{ borderBottom: `3px solid ${teamInfo?.color || "#3a4356"}33` }}
      >
        {/* Emoji tile */}
        <span
          className="flex items-center justify-center shrink-0 w-10 h-10 text-lg"
          style={{
            background: "#0b0e15",
            boxShadow: `0 0 0 2px ${teamInfo?.color || "#3a4356"}, inset -2px -2px 0 rgba(0,0,0,0.45), inset 2px 2px 0 rgba(255,255,255,0.06)`,
          }}
        >
          {teamInfo?.emoji || "👤"}
        </span>

        <div className="flex-1 min-w-0">
          <div
            className="text-[10px] tracking-wider truncate"
            style={{ fontFamily: PIXEL, color: "#e8edf4" }}
          >
            {card.agent_name.toUpperCase()}
          </div>
          <div
            className="text-[17px] truncate mt-0.5"
            style={{ fontFamily: TERM, color: teamInfo?.color || "#8892a6" }}
          >
            {teamInfo?.label || card.team}
          </div>
        </div>

        {/* Status badge */}
        <span
          className="shrink-0 px-2 py-1.5 text-[8px] tracking-widest"
          style={{
            fontFamily: PIXEL,
            background: badge.bg,
            color: badge.textColor,
            boxShadow:
              "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)",
          }}
        >
          {badge.label}
        </span>
      </div>

      {/* Task title */}
      <div className="px-4 py-3">
        <div
          className="text-[19px] leading-snug"
          style={{
            fontFamily: TERM,
            color: "#d8dee9",
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
          }}
        >
          {card.task_title}
        </div>

        {/* Completed summary */}
        {card.status === "done" && card.completed_summary && (
          <div
            className="mt-2 pt-2 text-[17px] leading-snug"
            style={{
              fontFamily: TERM,
              color: "#88c0d0",
              borderTop: "2px solid #3a4356",
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
            }}
          >
            ✅ {card.completed_summary}
          </div>
        )}

        {/* Timestamp */}
        <div
          className="text-[15px] mt-2"
          style={{ fontFamily: TERM, color: "#4e5a70" }}
        >
          {new Date(card.issued_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

export default function WalletPanel({ isOpen, onClose }: Props) {
  const { cards, loading, error } = useWalletCards();

  if (!isOpen) return null;

  const assigned = cards.filter((c) => c.status === "assigned" || c.status === "in_progress");
  const done = cards.filter((c) => c.status === "done");

  return (
    <div
      style={{
        ...pixelPanel,
        position: "absolute",
        right: 12,
        top: 12,
        bottom: 12,
        width: 380,
        zIndex: 40,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* ── Header ── */}
      <div
        className="flex items-center justify-between gap-3 px-5 py-4 shrink-0"
        style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
      >
        <div className="flex flex-col gap-1 min-w-0">
          <span
            className="text-[11px] md:text-[13px] tracking-wider text-[#f2b01f]"
            style={{ fontFamily: PIXEL }}
          >
            <span aria-hidden="true" className="text-[#c8d2e4]">{"\u2500\u25B6 "}</span>
            HR WALLET
          </span>
          <span className="text-[17px] text-[#aeb9cf]" style={{ fontFamily: TERM }}>
            Agent task assignments
          </span>
        </div>
        <button
          onClick={onClose}
          aria-label="Close wallet"
          className="shrink-0 w-9 h-9 flex items-center justify-center text-[12px] text-[#ffd7d8] cursor-pointer transition-transform active:translate-y-0.5"
          style={{
            fontFamily: PIXEL,
            background: "#3a1418",
            boxShadow:
              "0 0 0 3px #e5484d, inset -3px -3px 0 rgba(0,0,0,0.4), inset 3px 3px 0 rgba(255,255,255,0.12)",
          }}
        >
          X
        </button>
      </div>

      {/* ── Body ── */}
      <div
        className="flex-1 overflow-y-auto px-4 py-4"
        style={{ display: "flex", flexDirection: "column", gap: 12 }}
      >
        {loading && (
          <div className="text-center py-10">
            <div
              className="text-[9px] tracking-widest text-[#c8d2e4] animate-wallet-blink"
              style={{ fontFamily: PIXEL }}
            >
              LOADING...
            </div>
            <div className="text-[19px] text-[#7f8ca5] mt-2" style={{ fontFamily: TERM }}>
              Fetching wallet cards
            </div>
          </div>
        )}

        {error && (
          <div
            className="px-4 py-3 text-[17px] leading-snug text-[#ffd7d8]"
            style={{
              fontFamily: TERM,
              background: "#3a1418",
              boxShadow: "0 0 0 2px #e5484d",
            }}
          >
            {"! ERROR: "}
            {error}
          </div>
        )}

        {!loading && cards.length === 0 && (
          <div className="text-center py-10">
            <div
              className="text-[9px] tracking-widest text-[#7f8ca5]"
              style={{ fontFamily: PIXEL }}
            >
              NO ASSIGNMENTS
            </div>
            <div className="text-[19px] text-[#4e5a70] mt-3 leading-relaxed" style={{ fontFamily: TERM }}>
              Submit a task to see agents
              <br />
              get hired and assigned work.
            </div>
          </div>
        )}

        {/* Active assignments */}
        {assigned.length > 0 && (
          <>
            <div className="flex items-center gap-3">
              <span
                className="px-3 py-1.5 text-[8px] tracking-widest"
                style={{
                  fontFamily: PIXEL,
                  background: "#79d97c",
                  color: "#0e2a12",
                  boxShadow:
                    "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.2), inset 2px 2px 0 rgba(255,255,255,0.3)",
                }}
              >
                ACTIVE ({assigned.length})
              </span>
              <span aria-hidden="true" className="flex-1 h-[3px]" style={{ background: "#79d97c33" }} />
            </div>
            {assigned.map((card) => (
              <CardItem key={card.id} card={card} />
            ))}
          </>
        )}

        {/* Completed */}
        {done.length > 0 && (
          <>
            <div className="flex items-center gap-3 mt-2">
              <span
                className="px-3 py-1.5 text-[8px] tracking-widest"
                style={{
                  fontFamily: PIXEL,
                  background: "#88c0d0",
                  color: "#12161f",
                  boxShadow:
                    "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.2), inset 2px 2px 0 rgba(255,255,255,0.3)",
                }}
              >
                COMPLETED ({done.length})
              </span>
              <span aria-hidden="true" className="flex-1 h-[3px]" style={{ background: "#88c0d033" }} />
            </div>
            {done.map((card) => (
              <CardItem key={card.id} card={card} />
            ))}
          </>
        )}
      </div>

      {/* Inline keyframes */}
      <style>{`
        @keyframes wallet-slideIn {
          from { transform: translateX(40px); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
        @keyframes wallet-blink {
          0%, 60% { opacity: 1; }
          61%, 100% { opacity: 0.3; }
        }
        .animate-wallet-blink { animation: wallet-blink 1.2s steps(1) infinite; }
      `}</style>
    </div>
  );
}
