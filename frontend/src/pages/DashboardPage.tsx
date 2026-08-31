import { useState } from "react";
import { useNavigate } from "react-router-dom";
import CoderHostSetting from "@components/CoderHostSetting";
import ApiKeyManager from "@components/ApiKeyManager";
import McpConfigSnippet from "@components/McpConfigSnippet";

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

/* ── Chunky pixel border matching login/home panels ── */
const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

/* ── Step badge ── */
function StepBadge({ n }: { n: number }) {
  return (
    <span
      className="inline-flex items-center justify-center w-7 h-7 text-[8px] font-bold shrink-0"
      style={{
        fontFamily: PIXEL,
        background: "#f28a1f",
        color: "#241303",
        boxShadow:
          "0 0 0 3px #12161f, inset -2px -2px 0 rgba(0,0,0,0.3), inset 2px 2px 0 rgba(255,255,255,0.3)",
      }}
    >
      {n}
    </span>
  );
}

/* ── Section header bar (orange strip like home menu buttons) ── */
function SectionHeader({
  step,
  icon,
  title,
  subtitle,
}: {
  step: number;
  icon: string;
  title: string;
  subtitle: string;
}) {
  return (
    <div
      className="flex items-center gap-4 px-5 py-4"
      style={{ borderBottom: "3px solid #3a4356", background: "#1b2230" }}
    >
      <StepBadge n={step} />
      <div>
        <div
          className="text-[10px] md:text-[11px] font-bold tracking-wider text-[#f28a1f] flex items-center gap-2"
          style={{ fontFamily: PIXEL }}
        >
          <span>{icon}</span>
          {title}
        </div>
        <div className="text-[15px] text-[#7f8ca5] mt-0.5" style={{ fontFamily: TERM }}>
          {subtitle}
        </div>
      </div>
    </div>
  );
}

/* ── Nav pill button (bottom bar style) ── */
function NavPill({
  children,
  onClick,
  color = "#f28a1f",
  textColor = "#241303",
}: {
  children: React.ReactNode;
  onClick: () => void;
  color?: string;
  textColor?: string;
}) {
  return (
    <button
      onClick={onClick}
      className="group relative py-4 px-8 text-left transition-transform active:translate-y-1 w-full"
      style={{
        fontFamily: PIXEL,
        background: color,
        color: textColor,
        fontSize: "10px",
        letterSpacing: "0.08em",
        boxShadow:
          "0 0 0 3px #12161f, inset -4px -4px 0 rgba(0,0,0,0.25), inset 4px 4px 0 rgba(255,255,255,0.35), 0 6px 0 3px #12161f",
      }}
    >
      <span className="block">{children}</span>
      <span
        className="absolute right-5 top-1/2 -translate-y-1/2 text-[14px] opacity-60 group-hover:opacity-100 transition-opacity"
        style={{ fontFamily: TERM }}
      >
        ▶
      </span>
    </button>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const [openSection, setOpenSection] = useState<number | null>(null);

  const toggle = (n: number) => setOpenSection(prev => (prev === n ? null : n));

  return (
    <main
      className="relative h-screen overflow-hidden select-none"
      style={{
        background: "linear-gradient(180deg, #4da3e8 0%, #58aeef 45%, #3f8fd6 100%)",
      }}
    >
      {/* ── Blueprint grid ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      {/* ── Scanlines ── */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-[0.07]"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
          backgroundSize: "100% 3px",
        }}
      />
      {/* ── City skyline ── */}
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-0 right-0 h-[32vh] pointer-events-none opacity-35"
        style={{
          background: "#1d4e7e",
          clipPath:
            "polygon(0 62%, 4% 62%, 4% 38%, 9% 38%, 9% 55%, 14% 55%, 14% 22%, 16% 22%, 16% 14%, 18% 14%, 18% 22%, 20% 22%, 20% 58%, 26% 58%, 26% 34%, 31% 34%, 31% 64%, 37% 64%, 37% 44%, 42% 44%, 42% 70%, 50% 70%, 50% 30%, 54% 30%, 54% 18%, 56% 18%, 56% 30%, 60% 30%, 60% 60%, 66% 60%, 66% 40%, 72% 40%, 72% 66%, 78% 66%, 78% 26%, 82% 26%, 82% 50%, 88% 50%, 88% 36%, 93% 36%, 93% 58%, 100% 58%, 100% 100%, 0 100%)",
        }}
      />

      {/* ── Content ── */}
      <div className="relative z-10 h-full flex items-center justify-center px-4 py-6">
        <div className="w-full max-w-2xl flex flex-col gap-0" style={pixelPanel}>

          {/* ═══ Header ═══ */}
          <div
            className="px-6 py-5 flex items-center justify-between"
            style={{ borderBottom: "3px solid #3a4356", background: "#0b0e15" }}
          >
            <div>
              <div
                className="text-[10px] tracking-widest text-[#f28a1f] flex items-center gap-2"
                style={{ fontFamily: PIXEL }}
              >
                <span className="text-[#c8d2e4]">{"─▶ "}</span>
                SYSTEM CONFIG
              </div>
              <div
                className="text-[22px] text-[#7f8ca5] mt-1"
                style={{ fontFamily: TERM }}
              >
                Wire up API keys · connect agents · go live
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 inline-block animate-pulse"
                style={{ background: "#a3be8c", boxShadow: "0 0 6px #a3be8c" }}
              />
              <span
                className="text-[8px] tracking-widest text-[#a3be8c]"
                style={{ fontFamily: PIXEL }}
              >
                ONLINE
              </span>
            </div>
          </div>

          {/* ═══ Step 1 — Coder Host ═══ */}
          <div>
            <button
              className="w-full text-left transition-colors hover:bg-[#1b2230]"
              onClick={() => toggle(1)}
            >
              <SectionHeader
                step={1}
                icon="🌐"
                title="SETUP CODER HOST"
                subtitle="Point agents to your Coder deployment workspace"
              />
            </button>
            {openSection === 1 && (
              <div className="px-6 py-5" style={{ background: "#12161f", borderBottom: "3px solid #3a4356" }}>
                <CoderHostSetting />
              </div>
            )}
          </div>

          {/* ═══ Step 2 — API Key ═══ */}
          <div>
            <button
              className="w-full text-left transition-colors hover:bg-[#1b2230]"
              onClick={() => toggle(2)}
            >
              <SectionHeader
                step={2}
                icon="🔑"
                title="GET API KEY"
                subtitle="Generate a key to connect your AI clients to Mycel"
              />
            </button>
            {openSection === 2 && (
              <div className="px-6 py-5" style={{ background: "#12161f", borderBottom: "3px solid #3a4356" }}>
                <ApiKeyManager />
              </div>
            )}
          </div>

          {/* ═══ Step 3 — MCP Config ═══ */}
          <div>
            <button
              className="w-full text-left transition-colors hover:bg-[#1b2230]"
              onClick={() => toggle(3)}
            >
              <SectionHeader
                step={3}
                icon="🔧"
                title="SETUP MYCEL"
                subtitle="Add the MCP config to Claude / Cursor and go"
              />
            </button>
            {openSection === 3 && (
              <div
                className="px-6 py-5 overflow-y-auto"
                style={{ background: "#12161f", borderBottom: "3px solid #3a4356", maxHeight: "40vh" }}
              >
                <McpConfigSnippet />
              </div>
            )}
          </div>

          {/* ═══ Navigation buttons ═══ */}
          <div className="grid grid-cols-2">
            <NavPill onClick={() => navigate("/office")} color="#f28a1f" textColor="#241303">
              🏢 ENTER OFFICE
            </NavPill>
            <NavPill onClick={() => navigate("/real-estate")} color="#5e81ac" textColor="#eceff4">
              🏠 REAL ESTATE
            </NavPill>
          </div>

          {/* ═══ Footer ══ */}
          <div
            className="px-6 py-3 flex items-center justify-between"
            style={{ background: "#0b0e15", borderTop: "3px solid #3a4356" }}
          >
            <span
              className="text-[7px] tracking-widest text-[#4e5a70]"
              style={{ fontFamily: PIXEL }}
            >
              MYCEL · SYSTEM CONFIG · v1.0
            </span>
            <span
              className="text-[16px] text-[#4e5a70] flex items-center gap-1.5"
              style={{ fontFamily: TERM }}
            >
              <span
                className="w-2 h-2 inline-block"
                style={{ background: "#f28a1f", boxShadow: "0 0 4px #f28a1f" }}
              />
              ALL SYSTEMS OPERATIONAL
            </span>
          </div>
        </div>
      </div>

      {/* ── Page-scoped keyframes ── */}
      <style>{`
        @keyframes pulse-glow {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        .animate-pulse { animation: pulse-glow 2s ease-in-out infinite; }
      `}</style>
    </main>
  );
}
