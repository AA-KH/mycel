import { getCoderHost } from "@components/CoderHostSetting";
import TaskPanel from "@components/TaskPanel";
import VirtualOffice from "@components/office/VirtualOffice";
import HireTalentModal from "@components/HireTalentModal";
import WalletPanel from "@components/WalletPanel";
import OrchestrationPanel from "@components/OrchestrationPanel";
import { useEffect, useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { ROLE_CONFIGS, STATUS_COLORS } from "../config/agent-roles";
import { useAgentSessions } from "../hooks/useAgentSessions";
import { useOrchestrationPipeline } from "../hooks/useOrchestrationPipeline";
import { playChime, useCompletionSound } from "../hooks/useCompletionSound";
import { useSessionNicknames } from "../hooks/useSessionNicknames";
import { useAuth } from "../contexts/AuthContext";
import type { AgentRole } from "../types/agent";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

function formatDuration(startedAt: string): string {
  const diff = Date.now() - new Date(startedAt).getTime();
  const secs = Math.floor(diff / 1000);
  if (secs < 60) return `${secs}s`;
  const mins = Math.floor(secs / 60);
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  const remainMins = mins % 60;
  return remainMins > 0 ? `${hrs}h ${remainMins}m` : `${hrs}h`;
}

/* ── Bottom bar button ── */
function BarButton({
  children,
  active = false,
  activeColor = "#f28a1f",
  onClick,
}: {
  children: React.ReactNode;
  active?: boolean;
  activeColor?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex h-9 items-center justify-center gap-1.5 px-2.5 md:px-3 text-[8px] md:text-[9px] tracking-widest cursor-pointer transition-transform active:translate-y-0.5 whitespace-nowrap"
      style={{
        fontFamily: PIXEL,
        background: active ? activeColor : "#1b2230",
        color: active ? "#12161f" : "#aeb9cf",
        boxShadow: active
          ? `0 0 0 2px #12161f, inset -2px -2px 0 rgba(0,0,0,0.24), inset 2px 2px 0 rgba(255,255,255,0.24), 0 3px 0 2px #12161f`
          : "0 0 0 2px #3a4356, 0 3px 0 2px #12161f",
      }}
    >
      {children}
    </button>
  );
}

/* ── Nav item (for top bar) ── */
const NAV_ITEMS = [
  { to: "/", label: "HOME" },
  { to: "/office", label: "OFFICE" },
  { to: "/dashboard", label: "CONFIG" },
  { to: "/armoriq", label: "ARMORIQ" },
];

export default function OfficePage() {
  const { sessions, loading, error } = useAgentSessions();
  const { soundEnabled, toggleSound } = useCompletionSound(sessions);
  const { getNickname, setNickname } = useSessionNicknames();
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const [panelOpen, setPanelOpen] = useState(false);
  const [hireOpen, setHireOpen] = useState(false);
  const [walletOpen, setWalletOpen] = useState(false);
  const [orchestrationOpen, setOrchestrationOpen] = useState(false);
  const [highlightStatus, setHighlightStatus] = useState<string | null>(null);
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [, setTick] = useState(0);
  const { state: orchestrationState } = useOrchestrationPipeline();

  // Re-render every 30s to update session durations
  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(id);
  }, []);

  const statusCounts = {
    working: sessions.filter((s) => s.status === "working").length,
    walking: sessions.filter((s) => s.status === "walking").length,
    on_break: sessions.filter((s) => s.status === "on_break").length,
    complete: sessions.filter((s) => s.status === "complete").length,
    failure: sessions.filter((s) => s.status === "failure").length,
  };

  // Auto-open Orchestration Panel when an active task is assembling
  useEffect(() => {
    if (orchestrationState.task_id && !orchestrationState.is_workforce_assembled) {
      setOrchestrationOpen(true);
    }
  }, [orchestrationState.task_id, orchestrationState.is_workforce_assembled]);

  return (
    <>
    <div
      className="h-screen w-screen flex flex-col overflow-hidden select-none"
      style={{
        background: "linear-gradient(180deg, #4da3e8 0%, #58aeef 45%, #3f8fd6 100%)",
      }}
    >
      {/* ── Blueprint grid ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none z-0"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      {/* ── Scanlines ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-[0.07] z-0"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
          backgroundSize: "100% 3px",
        }}
      />
      {/* ── City skyline ── */}
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-0 right-0 h-[28vh] pointer-events-none opacity-25 z-0"
        style={{
          background: "#1d4e7e",
          clipPath:
            "polygon(0 62%, 4% 62%, 4% 38%, 9% 38%, 9% 55%, 14% 55%, 14% 22%, 16% 22%, 16% 14%, 18% 14%, 18% 22%, 20% 22%, 20% 58%, 26% 58%, 26% 34%, 31% 34%, 31% 64%, 37% 64%, 37% 44%, 42% 44%, 42% 70%, 50% 70%, 50% 30%, 54% 30%, 54% 18%, 56% 18%, 56% 30%, 60% 30%, 60% 60%, 66% 60%, 66% 40%, 72% 40%, 72% 66%, 78% 66%, 78% 26%, 82% 26%, 82% 50%, 88% 50%, 88% 36%, 93% 36%, 93% 58%, 100% 58%, 100% 100%, 0 100%)",
        }}
      />

      {/* ═══ TOP NAV BAR ═══ */}
      <header
        className="shrink-0 z-30 flex items-stretch justify-between relative"
        style={{
          background: "#0b0e15ee",
          borderBottom: "3px solid #3a4356",
          boxShadow: "0 4px 12px rgba(0,0,0,0.5), inset 0 -1px 0 rgba(255,255,255,0.03)",
          imageRendering: "pixelated",
        }}
      >
        {/* Left: logo + nav */}
        <div className="flex items-stretch">
          <Link
            to="/"
            className="flex items-center gap-2 px-4 text-[11px] tracking-wider text-[#e8edf4]"
            style={{
              fontFamily: PIXEL,
              borderRight: "3px solid #3a4356",
              textShadow: "2px 2px 0 #f28a1f",
            }}
          >
            MYCEL
          </Link>
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className="flex items-center px-4 py-3 text-[9px] tracking-widest transition-colors"
                style={{
                  fontFamily: PIXEL,
                  background: active ? "#f28a1f" : "transparent",
                  color: active ? "#241303" : "#7f8ca5",
                  borderRight: "3px solid #3a4356",
                  boxShadow: active
                    ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)"
                    : "none",
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* Right: user + quit */}
        <div className="flex items-stretch">
          <div
            className="hidden sm:flex items-center gap-2 px-4"
            style={{ borderLeft: "3px solid #3a4356" }}
          >
            <span
              aria-hidden="true"
              className="w-2 h-2 inline-block"
              style={{ background: "#57c94f", boxShadow: "0 0 5px #57c94f" }}
            />
            <span className="text-[17px] text-[#aeb9cf]" style={{ fontFamily: TERM }}>
              {user?.email || "pioneer"}
            </span>
          </div>
          <button
            onClick={() => {
              localStorage.clear();
              logout();
            }}
            className="px-4 py-3 text-[9px] tracking-widest cursor-pointer transition-colors hover:text-[#ffd7d8]"
            style={{
              fontFamily: PIXEL,
              color: "#e5484d",
              background: "transparent",
              borderLeft: "3px solid #3a4356",
            }}
          >
            X QUIT
          </button>
        </div>
      </header>

      {/* ═══ MAIN CONTENT ═══ */}
      <div className="flex-1 relative overflow-hidden z-10 flex">
        
        {/* HR Command Center */}
        <div 
          className={`h-full z-20 md:relative absolute left-0 top-0 bottom-0 shadow-2xl transition-all duration-300 ${orchestrationOpen ? "w-[380px] translate-x-0" : "w-[0px] -translate-x-full"}`}
        >
          {orchestrationOpen && (
            <OrchestrationPanel
              orchestration={orchestrationState}
              isOpen={orchestrationOpen}
              onClose={() => setOrchestrationOpen(false)}
            />
          )}
        </div>

        {/* Office Map */}
        <div className="flex-1 relative overflow-hidden z-10">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center" style={pixelPanel}>
                <div className="px-8 py-6">
                  <div className="w-8 h-8 mx-auto mb-3 border-2 border-white/20 border-t-[#f28a1f] rounded-full animate-spin" />
                  <p
                    className="text-[9px] tracking-widest text-[#7f8ca5]"
                    style={{ fontFamily: PIXEL }}
                  >
                    LOADING OFFICE...
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <>
              <VirtualOffice
                agents={sessions}
                highlightStatus={highlightStatus}
              />
              {error && (
                <div
                  className="absolute left-3 top-3 z-40 px-4 py-2 flex items-center gap-2"
                  style={{
                    ...pixelPanel,
                    boxShadow: "0 0 0 3px #e5484d, 0 0 0 6px #12161f",
                  }}
                  title={error.message}
                >
                  <span
                    className="w-2.5 h-2.5 inline-block animate-office-blink"
                    style={{ background: "#e5484d" }}
                  />
                  <span
                    className="text-[9px] tracking-widest text-[#ffd7d8]"
                    style={{ fontFamily: PIXEL }}
                  >
                    OFFLINE · DEMO FLOOR
                  </span>
                </div>
              )}
            </>
          )}
        </div>

        {/* ─── FLOATING USERS PANEL ─── */}
        {panelOpen && (
          <div
            className="absolute right-4 top-4 w-85 flex flex-col z-40 overflow-hidden"
            style={{
              ...pixelPanel,
              maxHeight: "calc(100% - 80px)",
            }}
          >
            {/* Panel header */}
            <div
              className="px-5 py-4 flex items-center justify-between shrink-0"
              style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
            >
              <div className="flex flex-col gap-1">
                <span
                  className="text-[10px] tracking-wider text-[#f28a1f]"
                  style={{ fontFamily: PIXEL }}
                >
                  <span aria-hidden="true" className="text-[#c8d2e4]">{"\u2500\u25B6 "}</span>
                  USERS ({sessions.length})
                </span>
                <span className="text-[16px] text-[#aeb9cf]" style={{ fontFamily: TERM }}>
                  Active agents on the floor
                </span>
              </div>
              <button
                onClick={() => setPanelOpen(false)}
                className="shrink-0 w-8 h-8 flex items-center justify-center text-[11px] text-[#ffd7d8] cursor-pointer transition-transform active:translate-y-0.5"
                style={{
                  fontFamily: PIXEL,
                  background: "#3a1418",
                  boxShadow:
                    "0 0 0 2px #e5484d, inset -2px -2px 0 rgba(0,0,0,0.4), inset 2px 2px 0 rgba(255,255,255,0.12)",
                }}
              >
                X
              </button>
            </div>

            {/* Status filter bar */}
            <div
              className="px-4 py-3 flex gap-2 flex-wrap shrink-0"
              style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
            >
              {Object.entries(statusCounts).map(([status, count]) => {
                if (count === 0) return null;
                const config =
                  STATUS_COLORS[status as keyof typeof STATUS_COLORS];
                const isActive = highlightStatus === status;
                return (
                  <button
                    key={status}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 cursor-pointer transition-colors"
                    style={{
                      fontFamily: PIXEL,
                      fontSize: "8px",
                      letterSpacing: "0.08em",
                      background: isActive ? config.bg : "transparent",
                      color: isActive ? "#12161f" : "#7f8ca5",
                      boxShadow: isActive
                        ? "inset -2px -2px 0 rgba(0,0,0,0.25), inset 2px 2px 0 rgba(255,255,255,0.3)"
                        : "none",
                    }}
                    onClick={() =>
                      setHighlightStatus(isActive ? null : status)
                    }
                  >
                    <span
                      className={`w-2.5 h-2.5 inline-block shrink-0 ${
                        status === "working" ? "animate-office-blink" : ""
                      }`}
                      style={{ background: isActive ? "#12161f" : config.bg }}
                    />
                    {config.label}
                    <span className="font-bold">{count}</span>
                  </button>
                );
              })}
            </div>

            {/* Agent list */}
            <div
              className="flex-1 overflow-auto px-3 py-3"
              style={{ background: "#12161f" }}
            >
              {(() => {
                const groups = new Map<string, typeof sessions>();
                for (const agent of sessions) {
                  const key = agent.session_id || agent.id;
                  const group = groups.get(key) || [];
                  group.push(agent);
                  groups.set(key, group);
                }

                return Array.from(groups.entries()).map(
                  ([sessionId, groupAgents]) => (
                    <div key={sessionId} className="mb-3">
                      {groups.size > 1 && (
                        <div
                          className="flex items-center gap-2 px-3 py-2 mt-1 group/header"
                        >
                          {editingSession === sessionId ? (
                            <input
                              autoFocus
                              className="text-[16px] text-[#e8edf4] bg-[#0b0e15] px-2 py-1 outline-none w-28"
                              style={{
                                fontFamily: TERM,
                                boxShadow: "0 0 0 2px #3a4356, inset 2px 2px 0 rgba(0,0,0,0.6)",
                                caretColor: "#f28a1f",
                              }}
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              onBlur={() => {
                                setNickname(sessionId, editValue);
                                setEditingSession(null);
                              }}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  setNickname(sessionId, editValue);
                                  setEditingSession(null);
                                }
                                if (e.key === "Escape") {
                                  setEditingSession(null);
                                }
                              }}
                            />
                          ) : (
                            <span
                              className="text-[8px] tracking-widest text-[#7f8ca5] cursor-pointer hover:text-[#c8d2e4] transition-colors truncate"
                              style={{ fontFamily: PIXEL }}
                              title="Click to rename"
                              onClick={() => {
                                setEditingSession(sessionId);
                                setEditValue(
                                  getNickname(sessionId) ||
                                  groupAgents[0].workspace ||
                                  sessionId.slice(0, 8),
                                );
                              }}
                            >
                              {getNickname(sessionId) ||
                                groupAgents[0].workspace ||
                                sessionId.slice(0, 8)}
                            </span>
                          )}
                          <span
                            className="text-[14px] text-[#4e5a70]"
                            style={{ fontFamily: TERM }}
                          >
                            ({groupAgents.length})
                          </span>
                          <div className="flex-1 h-0.5 bg-[#3a4356]" />
                        </div>
                      )}

                      {groupAgents.map((agent) => {
                        const config =
                          ROLE_CONFIGS[agent.role as AgentRole] ||
                          ROLE_CONFIGS.Developer;
                        const status =
                          STATUS_COLORS[agent.status] || STATUS_COLORS.working;
                        const coderHost = getCoderHost();
                        const wsUrl =
                          agent.workspace && coderHost
                            ? `${coderHost}/@me/${agent.workspace}`
                            : null;

                        return (
                          <div
                            key={agent.id}
                            className="flex items-start gap-3 px-3 py-2.5 transition-colors hover:bg-[#1b2230]"
                            style={{ borderBottom: "1px solid #232a38" }}
                          >
                            <span
                              className={`w-2.5 h-2.5 mt-1.5 inline-block shrink-0 ${
                                agent.status === "working"
                                  ? "animate-office-blink"
                                  : ""
                              }`}
                              style={{ background: status.bg }}
                            />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="text-base">{config.emoji}</span>
                                <span
                                  className="text-[10px] tracking-wider truncate"
                                  style={{ fontFamily: PIXEL, color: config.color }}
                                >
                                  {config.label.toUpperCase()}
                                </span>
                                <span
                                  className="text-[15px] text-[#4e5a70] ml-auto shrink-0"
                                  style={{ fontFamily: TERM }}
                                >
                                  ⏱ {formatDuration(agent.started_at)}
                                </span>
                              </div>
                              {agent.summary && (
                                <p
                                  className="text-[16px] text-[#7f8ca5] leading-snug mt-1 line-clamp-2"
                                  style={{ fontFamily: TERM }}
                                >
                                  {agent.summary}
                                </p>
                              )}
                              <div className="flex gap-3 mt-1">
                                {agent.link && (
                                  <a
                                    href={agent.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[14px] hover:underline"
                                    style={{ fontFamily: TERM, color: "#6aa9ff" }}
                                  >
                                    ↗ link
                                  </a>
                                )}
                                {wsUrl && (
                                  <a
                                    href={wsUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-[14px] hover:underline"
                                    style={{ fontFamily: TERM, color: "#79d97c" }}
                                  >
                                    ↗ workspace
                                  </a>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ),
                );
              })()}

              {sessions.length === 0 && (
                <div className="text-center py-8">
                  <p
                    className="text-[9px] tracking-widest text-[#7f8ca5]"
                    style={{ fontFamily: PIXEL }}
                  >
                    NO AGENTS ONLINE
                  </p>
                  <p className="text-[18px] text-[#4e5a70] mt-2" style={{ fontFamily: TERM }}>
                    The office is empty right now
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ─── WALLET PANEL ─── */}
        <WalletPanel isOpen={walletOpen} onClose={() => setWalletOpen(false)} />


      </div>

      {/* ═══ BOTTOM ACTION BAR ═══ */}
      <div
        className="shrink-0 z-30 px-2 py-2 md:px-3 relative"
        style={{
          background: "#0b0e15ee",
          borderTop: "3px solid #3a4356",
          boxShadow: "0 -4px 12px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.03)",
          imageRendering: "pixelated",
        }}
      >
        <div className="h-full flex items-center gap-2 md:gap-3">
          {/* Brand */}
          <div
            className="h-9 flex items-center gap-2 px-2.5 md:px-3 shrink-0"
            style={{
              background: "#1b2230",
              boxShadow: "0 0 0 2px #3a4356, 0 3px 0 2px #12161f",
            }}
          >
            <span className="text-sm">🏢</span>
            <span
              className="text-[9px] md:text-[10px] tracking-wider text-[#e8edf4]"
              style={{ fontFamily: PIXEL, textShadow: "2px 2px 0 #b85f1c" }}
            >
              MYCEL
            </span>
          </div>

          {/* Live status counters */}
          <div
            className="h-9 flex min-w-0 items-center gap-1 px-1.5 overflow-x-auto"
            style={{
              background: "#1b2230",
              boxShadow: "0 0 0 2px #3a4356, 0 3px 0 2px #12161f",
            }}
          >
            <span
              className="hidden xl:inline px-1 text-[7px] tracking-widest text-[#66758e] whitespace-nowrap"
              style={{ fontFamily: PIXEL }}
            >
              LIVE
            </span>
            {Object.entries(statusCounts).map(([status, count]) => {
              const config = STATUS_COLORS[status as keyof typeof STATUS_COLORS];
              return (
                <div key={status} className="flex items-center gap-1 px-1.5 whitespace-nowrap">
                  <span
                    className={`w-2 h-2 inline-block shrink-0 ${status === "working" ? "animate-office-blink" : ""}`}
                    style={{ background: config.bg, boxShadow: `0 0 0 1px ${config.bg}55` }}
                  />
                  <span
                    className="text-[7px] tracking-wider text-[#7f8ca5] hidden lg:inline"
                    style={{ fontFamily: PIXEL }}
                  >
                    {config.label}
                  </span>
                  <span className="text-[17px] leading-none text-[#d9e1ef]" style={{ fontFamily: TERM }}>
                    {count}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="flex-1" />

          <div className="flex items-center gap-1 shrink-0">
            <BarButton active={soundEnabled} activeColor="#79d97c" onClick={toggleSound}>
              {soundEnabled ? "🔔" : "🔕"}
            </BarButton>
            <BarButton onClick={() => setTimeout(playChime, 3000)}>🔊 <span className="hidden md:inline">TEST</span></BarButton>
            <BarButton active={hireOpen} activeColor="#f28a1f" onClick={() => setHireOpen(true)}>
              🏪 <span className="hidden lg:inline">HIRE</span>
            </BarButton>
            <BarButton active={panelOpen} activeColor="#6aa9ff" onClick={() => setPanelOpen(!panelOpen)}>
              👥 <span className="hidden lg:inline">USERS</span>
            </BarButton>
            <BarButton active={walletOpen} activeColor="#f2b01f" onClick={() => setWalletOpen(!walletOpen)}>
              📇 <span className="hidden xl:inline">WALLET</span>
            </BarButton>
            <BarButton active={orchestrationOpen} activeColor="#4ecdc4" onClick={() => setOrchestrationOpen(!orchestrationOpen)}>
              🏗️ <span className="hidden xl:inline">PIPELINE</span>
            </BarButton>
          </div>
        </div>
      </div>
    </div>
    {/* Task assignment panel — floating over the virtual office */}
    <TaskPanel />
    
    <HireTalentModal 
      isOpen={hireOpen} 
      onClose={() => setHireOpen(false)} 
      onHire={(role) => {
        console.log("Hiring agent with role:", role);
        setHireOpen(false);
      }} 
    />

    {/* Page-scoped keyframes */}
    <style>{`
      @keyframes office-blink {
        0%, 60% { opacity: 1; }
        61%, 100% { opacity: 0.3; }
      }
      .animate-office-blink { animation: office-blink 1.2s steps(1) infinite; }
      @media (prefers-reduced-motion: reduce) {
        .animate-office-blink { animation: none; }
      }
    `}</style>
    </>
  );
}
