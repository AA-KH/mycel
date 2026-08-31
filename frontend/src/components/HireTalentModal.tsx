import { useState } from 'react';
import { ROLE_CONFIGS } from '../config/agent-roles';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onHire: (role: string) => void;
}

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

export default function HireTalentModal({ isOpen, onClose, onHire }: Props) {
  const [searchTerm, setSearchTerm] = useState('');

  if (!isOpen) return null;

  const roles = Object.entries(ROLE_CONFIGS).filter(([key]) => {
    return key.toLowerCase().includes(searchTerm.toLowerCase());
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
      style={{ background: "rgba(4, 10, 22, 0.72)", backdropFilter: "blur(3px)" }}
      role="dialog"
      aria-modal="true"
      aria-label="Hire talent"
    >
      <div
        className="w-full max-w-[800px] max-h-[85vh] flex flex-col"
        style={{ ...pixelPanel, fontFamily: TERM, color: "#e8edf4" }}
      >
        {/* ── Header ── */}
        <div
          className="flex items-center justify-between gap-4 px-5 md:px-8 py-5 shrink-0"
          style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
        >
          <div className="flex flex-col gap-2 min-w-0">
            <h2
              className="text-[13px] md:text-[15px] text-[#f2b01f] tracking-wider"
              style={{ fontFamily: PIXEL }}
            >
              <span aria-hidden="true" className="text-[#c8d2e4]">{"\u2500\u25B6 "}</span>
              TALENT MARKET
              <span aria-hidden="true" className="text-[#c8d2e4]">{" \u25C0\u2500"}</span>
            </h2>
            <p className="text-[19px] md:text-[21px] text-[#aeb9cf] leading-snug">
              Browse available roles and expand your team
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close talent market"
            className="shrink-0 w-11 h-11 flex items-center justify-center text-[14px] text-[#ffd7d8] transition-transform active:translate-y-0.5 cursor-pointer"
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

        {/* ── Search bar ── */}
        <div
          className="px-5 md:px-8 py-4 shrink-0"
          style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
        >
          <label
            className="block mb-2 text-[9px] tracking-widest text-[#c8d2e4]"
            style={{ fontFamily: PIXEL }}
            htmlFor="talent-search"
          >
            SEARCH ROLES
          </label>
          <input
            id="talent-search"
            type="text"
            placeholder="Type to filter (e.g. backend, marketing...)"
            className="w-full px-3 py-2.5 focus:outline-none placeholder:text-[#4e5a70]"
            style={{
              fontFamily: TERM,
              fontSize: "20px",
              background: "#0b0e15",
              color: "#e8edf4",
              border: "none",
              boxShadow: "0 0 0 2px #3a4356, inset 3px 3px 0 rgba(0,0,0,0.6)",
              caretColor: "#f28a1f",
            }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* ── Role Grid ── */}
        <div className="flex-1 overflow-y-auto px-5 md:px-8 py-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {roles.map(([role, config]) => (
              <button
                key={role}
                className="group flex items-center gap-4 p-4 text-left transition-transform duration-150 hover:-translate-y-0.5 cursor-pointer"
                style={{
                  background: "#1b2230",
                  boxShadow: `0 0 0 3px #3a4356, 4px 4px 0 3px rgba(0,0,0,0.35)`,
                }}
                onClick={() => {
                  onHire(role);
                  onClose();
                }}
              >
                {/* Emoji tile */}
                <span
                  className="flex items-center justify-center shrink-0 w-12 h-12 text-xl"
                  style={{
                    background: "#0b0e15",
                    boxShadow: `0 0 0 2px ${config.color}, inset -3px -3px 0 rgba(0,0,0,0.45), inset 3px 3px 0 rgba(255,255,255,0.06)`,
                  }}
                >
                  {config.emoji}
                </span>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div
                    className="text-[11px] md:text-[12px] tracking-wider truncate"
                    style={{ fontFamily: PIXEL, color: config.color }}
                  >
                    {config.label.toUpperCase()}
                  </div>
                  <div className="text-[17px] text-[#7f8ca5] truncate mt-0.5">
                    {role}
                  </div>
                </div>

                {/* HIRE chip */}
                <span
                  className="shrink-0 px-3 py-2 text-[9px] tracking-widest transition-transform group-hover:translate-y-[-2px]"
                  style={{
                    fontFamily: PIXEL,
                    background: "#f28a1f",
                    color: "#241303",
                    boxShadow:
                      "0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.35), 0 3px 0 2px #12161f",
                  }}
                >
                  HIRE
                </span>
              </button>
            ))}

            {roles.length === 0 && (
              <div
                className="col-span-2 text-center py-12"
                style={{ fontFamily: TERM }}
              >
                <p className="text-[24px] text-[#7f8ca5]">No matching talent found</p>
                <p className="text-[18px] text-[#4e5a70] mt-2">Try a different search term</p>
              </div>
            )}
          </div>
        </div>

        {/* ── Footer HUD ── */}
        <div
          className="flex items-center justify-center gap-6 px-6 py-3 shrink-0"
          style={{ borderTop: "3px solid #3a4356", background: "#1b2230" }}
        >
          <span className="text-[9px] tracking-widest text-[#c8d2e4]" style={{ fontFamily: PIXEL }}>
            {roles.length} ROLES AVAILABLE
          </span>
          <span className="text-[17px] text-[#7f8ca5]">
            Click any role to hire instantly
          </span>
        </div>
      </div>
    </div>
  );
}
