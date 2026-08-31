"use client";

import { useState } from "react";
import { TEAM_REGISTRY, getAllMembers } from "../config/agent-roles";
import { getAgentAvatar } from "../config/agent-avatars";

/* ════════════════════════════════════════════════════════════════════
   MYCEL — TEAM ROSTER (retro pixel-art personnel terminal)
   Matches the LoginPage theme: Press Start 2P + VT323, chunky
   double-stepped pixel panels, orange accent (#f28a1f).
   ════════════════════════════════════════════════════════════════════ */

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

const teamIds = Object.keys(TEAM_REGISTRY);
const TOTAL_AGENTS = getAllMembers().length;

export default function RosterModal({ isOpen, onClose }: Props) {
  const [activeTeam, setActiveTeam] = useState<string>("all");

  if (!isOpen) return null;

  const teams = activeTeam === "all" ? teamIds : [activeTeam];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8"
      style={{ background: "rgba(4, 10, 22, 0.72)", backdropFilter: "blur(3px)" }}
      role="dialog"
      aria-modal="true"
      aria-label="Mycel team roster"
    >
      <div
        className="w-full max-w-[1100px] max-h-[88vh] flex flex-col"
        style={{ ...pixelPanel, fontFamily: TERM, color: "#e8edf4" }}
      >
        {/* ── Header ── */}
        <div
          className="flex items-center justify-between gap-4 px-5 md:px-8 py-5 shrink-0"
          style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
        >
          <div className="flex flex-col gap-2 min-w-0">
            <h2
              className="text-[13px] md:text-[17px] text-[#f2b01f] tracking-wider text-balance"
              style={{ fontFamily: PIXEL }}
            >
              <span aria-hidden="true" className="text-[#c8d2e4]">{"\u2500\u25B6 "}</span>
              PERSONNEL FILE
              <span aria-hidden="true" className="text-[#c8d2e4]">{" \u25C0\u2500"}</span>
            </h2>
            <p className="text-[19px] md:text-[21px] text-[#aeb9cf] leading-snug">
              {TOTAL_AGENTS} pioneers on payroll &middot; {teamIds.length} departments &middot; all
              badges verified
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close roster"
            className="shrink-0 w-11 h-11 flex items-center justify-center text-[14px] text-[#ffd7d8] transition-transform active:translate-y-0.5"
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

        {/* ── Team tabs ── */}
        <div
          className="flex overflow-x-auto shrink-0"
          style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
          role="tablist"
          aria-label="Filter by team"
        >
          <button
            role="tab"
            aria-selected={activeTeam === "all"}
            onClick={() => setActiveTeam("all")}
            className="px-5 py-4 text-[10px] md:text-[11px] tracking-wider whitespace-nowrap transition-colors"
            style={{
              fontFamily: PIXEL,
              background: activeTeam === "all" ? "#f28a1f" : "transparent",
              color: activeTeam === "all" ? "#241303" : "#7f8ca5",
              borderRight: "3px solid #232a38",
              boxShadow:
                activeTeam === "all"
                  ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)"
                  : "none",
            }}
          >
            {"\u2605"} ALL ({TOTAL_AGENTS})
          </button>
          {teamIds.map((tid) => {
            const team = TEAM_REGISTRY[tid];
            const active = activeTeam === tid;
            return (
              <button
                key={tid}
                role="tab"
                aria-selected={active}
                onClick={() => setActiveTeam(tid)}
                className="px-4 md:px-5 py-4 text-[10px] md:text-[11px] tracking-wider whitespace-nowrap transition-colors"
                style={{
                  fontFamily: PIXEL,
                  background: active ? team.color : "transparent",
                  color: active ? "#12161f" : "#7f8ca5",
                  borderRight: "3px solid #232a38",
                  boxShadow: active
                    ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)"
                    : "none",
                }}
              >
                {team.label.toUpperCase()}
              </button>
            );
          })}
        </div>

        {/* ── Body ── */}
        <div className="flex-1 overflow-y-auto px-5 md:px-8 py-6">
          {teams.map((tid) => {
            const team = TEAM_REGISTRY[tid];
            return (
              <section key={tid} className="mb-10 last:mb-2">
                {/* Team banner */}
                <div className="flex items-center gap-4 mb-5">
                  <span
                    className="px-4 py-2 text-[10px] md:text-[12px] tracking-widest whitespace-nowrap"
                    style={{
                      fontFamily: PIXEL,
                      background: team.color,
                      color: "#12161f",
                      boxShadow:
                        "0 0 0 3px #12161f, 0 0 0 5px " +
                        team.color +
                        "55, 4px 4px 0 5px rgba(0,0,0,0.35)",
                    }}
                  >
                    {team.label.toUpperCase()} DEPT.
                  </span>
                  <span className="text-[20px] text-[#7f8ca5]">
                    {team.members.length} agents on this floor
                  </span>
                  <span
                    aria-hidden="true"
                    className="flex-1 h-[3px]"
                    style={{ background: `${team.color}40` }}
                  />
                </div>

                {/* Agent cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                  {team.members.map((member) => (
                    <article
                      key={member.id}
                      className="group flex flex-col transition-transform duration-150 hover:-translate-y-1"
                      style={{
                        background: "#1b2230",
                        boxShadow: `0 0 0 3px #3a4356, 6px 6px 0 3px rgba(0,0,0,0.4)`,
                      }}
                    >
                      {/* Portrait */}
                      <div
                        className="relative overflow-hidden"
                        style={{
                          background: "#0b0e15",
                          borderBottom: `4px solid ${team.color}`,
                        }}
                      >
                        <img
                          src={getAgentAvatar(member.id) || "/placeholder.svg"}
                          alt={`Pixel-art portrait of ${member.name}, ${member.title}`}
                          className="w-full aspect-square object-cover transition-transform duration-200 group-hover:scale-[1.06]"
                          style={{ imageRendering: "pixelated" }}
                          loading="lazy"
                        />
                        {/* scanline overlay */}
                        <div
                          aria-hidden="true"
                          className="absolute inset-0 pointer-events-none opacity-[0.08]"
                          style={{
                            backgroundImage:
                              "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
                            backgroundSize: "100% 3px",
                          }}
                        />
                        {/* status LED */}
                        <span
                          className="absolute top-2.5 right-2.5 flex items-center gap-2 px-2.5 py-1.5 text-[15px] leading-none text-[#79d97c]"
                          style={{
                            background: "rgba(11,14,21,0.85)",
                            boxShadow: "0 0 0 2px #3a4356",
                          }}
                        >
                          <span
                            aria-hidden="true"
                            className="w-2.5 h-2.5 animate-roster-blink"
                            style={{ background: "#57c94f" }}
                          />
                          ONLINE
                        </span>
                      </div>

                      {/* Info */}
                      <div className="flex flex-col gap-2 px-4 py-4">
                        <h3
                          className="text-[11px] md:text-[12px] leading-relaxed text-[#e8edf4] text-balance"
                          style={{ fontFamily: PIXEL }}
                        >
                          {member.name.toUpperCase()}
                        </h3>
                        <p className="text-[21px] leading-tight" style={{ color: team.color }}>
                          {member.title}
                        </p>
                        <div className="flex items-center justify-between gap-2 mt-1">
                          <span
                            className="px-2 py-1 text-[8px] tracking-widest"
                            style={{
                              fontFamily: PIXEL,
                              background: `${team.color}22`,
                              color: team.color,
                              boxShadow: `0 0 0 2px ${team.color}55`,
                            }}
                          >
                            {team.label.toUpperCase()}
                          </span>
                          <span className="text-[16px] text-[#4e5a70]">{member.id}</span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            );
          })}
        </div>

        {/* ── Footer HUD ── */}
        <div
          className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 px-6 py-4 shrink-0 text-center"
          style={{ borderTop: "3px solid #3a4356", background: "#1b2230" }}
        >
          <span className="text-[9px] tracking-widest text-[#c8d2e4]" style={{ fontFamily: PIXEL }}>
            {TOTAL_AGENTS} EMPLOYEES {"\u2605"} {teamIds.length} TEAMS
          </span>
          <span className="text-[19px] text-[#7f8ca5]">
            Work is assigned by the Orchestrator in real time
          </span>
          <span
            className="text-[9px] tracking-widest text-[#79d97c]"
            style={{ fontFamily: PIXEL }}
          >
            ALL SYSTEMS OPERATIONAL<span className="animate-roster-blink">_</span>
          </span>
        </div>
      </div>

      <style>{`
        @keyframes roster-blink {
          0%, 60% { opacity: 1; }
          61%, 100% { opacity: 0.2; }
        }
        .animate-roster-blink { animation: roster-blink 1.2s steps(1) infinite; }
        @media (prefers-reduced-motion: reduce) {
          .animate-roster-blink { animation: none; }
        }
      `}</style>
    </div>
  );
}
