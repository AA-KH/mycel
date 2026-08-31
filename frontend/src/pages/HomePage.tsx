"use client";

import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";

import PixelLayout from "@components/PixelLayout";
import WelcomeSplash from "@components/WelcomeSplash";
import RosterModal from "@components/RosterModal";
import { TEAM_REGISTRY, getAllMembers } from "../config/agent-roles";
import { getAgentAvatar } from "../config/agent-avatars";

/* ════════════════════════════════════════════════════════════════════
   MYCEL — MISSION SELECT (retro pixel-art main menu)
   Matches the LoginPage theme: sky gradient + blueprint grid +
   scanlines + skyline, Press Start 2P + VT323, orange accent.
   ════════════════════════════════════════════════════════════════════ */

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

const TEAM_IDS = Object.keys(TEAM_REGISTRY);
const TOTAL_AGENTS = getAllMembers().length;

/* ── Retro chip ── */
function PixelChip({
  children,
  color = "#f28a1f",
  textColor = "#1a1f2c",
}: {
  children: React.ReactNode;
  color?: string;
  textColor?: string;
}) {
  return (
    <span
      className="inline-block px-4 py-2 text-[9px] md:text-[10px] tracking-wider whitespace-nowrap"
      style={{
        fontFamily: PIXEL,
        background: color,
        color: textColor,
        boxShadow: "0 0 0 3px #1a1f2c, 0 0 0 5px #f4f6f9, 4px 4px 0 5px rgba(0,0,0,0.35)",
      }}
    >
      {children}
    </span>
  );
}

/* ── Big menu button (login-screen style) ── */
function MenuButton({
  children,
  hint,
  onClick,
  color = "#f28a1f",
  textColor = "#241303",
}: {
  children: React.ReactNode;
  hint: string;
  onClick: () => void;
  color?: string;
  textColor?: string;
}) {
  return (
    <button
      onClick={onClick}
      className="group relative w-full py-5 px-6 text-left transition-transform active:translate-y-1"
      style={{
        fontFamily: PIXEL,
        background: color,
        color: textColor,
        boxShadow:
          "0 0 0 3px #12161f, inset -4px -4px 0 rgba(0,0,0,0.25), inset 4px 4px 0 rgba(255,255,255,0.35), 0 6px 0 3px #12161f",
      }}
    >
      <span className="block text-[13px] md:text-[15px] tracking-[0.15em]">{children}</span>
      <span
        className="block mt-2 text-[19px] md:text-[20px] tracking-normal opacity-80"
        style={{ fontFamily: TERM }}
      >
        {hint}
      </span>
      <span
        aria-hidden="true"
        className="absolute right-5 top-1/2 -translate-y-1/2 text-[16px] group-hover:translate-x-1 transition-transform"
      >
        {"\u25B6"}
      </span>
    </button>
  );
}

export default function HomePage() {
  const navigate = useNavigate();
  const [splashDone, setSplashDone] = useState(
    () => sessionStorage.getItem("mycel_splash_seen") === "true"
  );
  const [rosterOpen, setRosterOpen] = useState(false);
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 100);
    return () => clearTimeout(t);
  }, []);

  const handleSplashDismiss = useCallback(() => {
    setSplashDone(true);
  }, []);

  return (
    <PixelLayout>
      {!splashDone && <WelcomeSplash onDismiss={handleSplashDismiss} />}
      <RosterModal isOpen={rosterOpen} onClose={() => setRosterOpen(false)} />

      {/* ── Sky backdrop (login theme) ── */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ background: "linear-gradient(180deg, #4da3e8 0%, #58aeef 45%, #3f8fd6 100%)" }}
      >
        {/* blueprint grid */}
        <div
          aria-hidden="true"
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.10) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        {/* scanlines */}
        <div
          aria-hidden="true"
          className="absolute inset-0 pointer-events-none opacity-[0.07]"
          style={{
            backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
            backgroundSize: "100% 3px",
          }}
        />
        {/* skyline */}
        <div
          aria-hidden="true"
          className="fixed bottom-0 left-0 right-0 h-[34vh] pointer-events-none opacity-40"
          style={{
            background: "#1d4e7e",
            clipPath:
              "polygon(0 62%, 4% 62%, 4% 38%, 9% 38%, 9% 55%, 14% 55%, 14% 22%, 16% 22%, 16% 14%, 18% 14%, 18% 22%, 20% 22%, 20% 58%, 26% 58%, 26% 34%, 31% 34%, 31% 64%, 37% 64%, 37% 44%, 42% 44%, 42% 70%, 50% 70%, 50% 30%, 54% 30%, 54% 18%, 56% 18%, 56% 30%, 60% 30%, 60% 60%, 66% 60%, 66% 40%, 72% 40%, 72% 66%, 78% 66%, 78% 26%, 82% 26%, 82% 50%, 88% 50%, 88% 36%, 93% 36%, 93% 58%, 100% 58%, 100% 100%, 0 100%)",
          }}
        />

        {/* ── Centered menu panel ── */}
        <div className="relative z-10 h-full flex items-center justify-center px-4 py-10">
          <div
            className={`w-full max-w-180 transition-all duration-700 ${booted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}`}
          >
            <div className="px-6 py-8 md:px-12 md:py-10" style={pixelPanel}>
              {/* chips */}
              <div className="flex flex-wrap items-center justify-center gap-4 mb-8">
                <span className="animate-home-blink">
                  <PixelChip>MISSION SELECT</PixelChip>
                </span>
                <PixelChip color="#79d97c" textColor="#0e2a12">
                  {TOTAL_AGENTS} AGENTS ONLINE
                </PixelChip>
              </div>

              {/* logotype */}
              <h1
                className="text-center text-[clamp(1.8rem,5vw,3.2rem)] leading-none text-[#e8edf4] mb-4 text-balance"
                style={{
                  fontFamily: PIXEL,
                  textShadow: "4px 4px 0 #f28a1f",
                }}
              >
                MYCEL
              </h1>
              <p
                className="text-center text-[10px] md:text-[12px] text-[#c8d2e4] tracking-widest mb-8"
                style={{ fontFamily: PIXEL }}
              >
                THE AUTONOMOUS{" "}
                <span className="px-2 py-1" style={{ background: "#79d97c", color: "#0e2a12" }}>
                  AI COMPANY
                </span>
              </p>

              <p
                className="text-center text-[21px] md:text-[23px] text-[#aeb9cf] mb-8 leading-relaxed text-pretty"
                style={{ fontFamily: TERM }}
              >
                Welcome back, pioneer. Your company never sleeps — pick where to jump in.
              </p>

              {/* ── Department parade with portraits ── */}
              <div className="mb-9">
                <p
                  className="text-center text-[9px] tracking-widest text-[#7f8ca5] mb-4"
                  style={{ fontFamily: PIXEL }}
                >
                  {"\u2500\u2500"} 7 DEPARTMENTS ON DUTY {"\u2500\u2500"}
                </p>
                <div className="flex justify-center gap-3 md:gap-4 flex-wrap">
                  {TEAM_IDS.map((tid, i) => {
                    const team = TEAM_REGISTRY[tid];
                    const lead = team.members[0];
                    return (
                      <button
                        key={tid}
                        onClick={() => setRosterOpen(true)}
                        className="flex flex-col items-center gap-2 transition-transform hover:-translate-y-1 animate-home-rise"
                        style={{ animationDelay: `${0.15 + i * 0.07}s` }}
                        aria-label={`View the ${team.label} team roster`}
                      >
                        <span
                          className="block w-14 h-14 md:w-16 md:h-16 overflow-hidden"
                          style={{
                            background: "#0b0e15",
                            boxShadow: `0 0 0 3px ${team.color}, 4px 4px 0 3px rgba(0,0,0,0.35)`,
                          }}
                        >
                          <img
                            src={getAgentAvatar(lead.id) || "/placeholder.svg"}
                            alt=""
                            className="w-full h-full object-cover"
                            style={{ imageRendering: "pixelated" }}
                          />
                        </span>
                        <span
                          className="text-[8px] tracking-wider"
                          style={{ fontFamily: PIXEL, color: team.color }}
                        >
                          {team.label.toUpperCase()}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* ── Menu buttons ── */}
              <nav className="flex flex-col gap-5" aria-label="Main menu">
                <MenuButton
                  hint="Watch your AI agents work the floor in real time"
                  onClick={() => navigate("/office")}
                >
                  ENTER OFFICE
                </MenuButton>
                <MenuButton
                  color="#6aa9ff"
                  textColor="#0c1c38"
                  hint={`Browse all ${TOTAL_AGENTS} pioneers across 7 departments`}
                  onClick={() => setRosterOpen(true)}
                >
                  MEET THE TEAM
                </MenuButton>
                <MenuButton
                  color="#57c94f"
                  textColor="#0e2a12"
                  hint="Wire up API keys and company configuration"
                  onClick={() => navigate("/dashboard")}
                >
                  API KEY SETUP
                </MenuButton>
              </nav>
            </div>

            <p
              className="text-center mt-8 text-[9px] tracking-widest text-[#0e2a4a]/80"
              style={{ fontFamily: PIXEL }}
            >
              MYCEL &middot; BUILT BY TEAM EVOLVE AI &middot; V1.0
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes home-blink {
          0%, 55% { opacity: 1; }
          56%, 100% { opacity: 0.35; }
        }
        .animate-home-blink { animation: home-blink 1.4s steps(1) infinite; display: inline-block; }

        @keyframes home-rise {
          from { transform: translateY(14px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-home-rise { animation: home-rise 0.55s cubic-bezier(0.22, 1, 0.36, 1) both; }

        @media (prefers-reduced-motion: reduce) {
          .animate-home-blink, .animate-home-rise { animation: none; }
        }
      `}</style>
    </PixelLayout>
  );
}
