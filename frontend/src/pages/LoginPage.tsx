"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

/* ════════════════════════════════════════════════════════════════════
   MYCEL — retro pixel-art authentication terminal
   Fonts: 'Press Start 2P' (headings/UI) + 'VT323' (terminal body)
   ════════════════════════════════════════════════════════════════════ */

const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

/* ── Chunky pixel border (double-stepped, like a game dialog) ── */
const pixelPanel: React.CSSProperties = {
  background: "#12161f",
  boxShadow:
    "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

/* ── Pixel cloud (crisp SVG rects) ── */
function PixelCloud({
  x,
  y,
  scale = 1,
  duration = 60,
  delay = 0,
}: {
  x: string;
  y: string;
  scale?: number;
  duration?: number;
  delay?: number;
}) {
  const u = 8 * scale;
  const cells: [number, number, number, number][] = [
    [2, 1, 5, 1],
    [1, 2, 8, 1],
    [0, 3, 10, 1],
    [3, 0, 3, 1],
  ];
  return (
    <svg
      aria-hidden="true"
      width={10 * u}
      height={4 * u}
      viewBox={`0 0 ${10 * u} ${4 * u}`}
      shapeRendering="crispEdges"
      className="absolute pointer-events-none animate-cloud-drift"
      style={{
        left: x,
        top: y,
        animationDuration: `${duration}s`,
        animationDelay: `${delay}s`,
        opacity: 0.9,
      }}
    >
      {cells.map(([cx, cy, cw, ch], i) => (
        <rect key={i} x={cx * u} y={cy * u} width={cw * u} height={ch * u} fill="#ffffff" />
      ))}
      <rect x={0} y={3 * u} width={10 * u} height={u} fill="#dbe9f4" opacity={0.6} />
    </svg>
  );
}

/* ── Pixel blimp with MYCEL banner ── */
function PixelBlimp() {
  const u = 4;
  return (
    <div
      aria-hidden="true"
      className="absolute pointer-events-none animate-blimp-float hidden lg:block"
      style={{ right: "4%", top: "6%" }}
    >
      <svg width={40 * u} height={16 * u} viewBox={`0 0 ${40 * u} ${16 * u}`} shapeRendering="crispEdges">
        {/* balloon body */}
        <rect x={4 * u} y={2 * u} width={30 * u} height={6 * u} fill="#e8edf4" />
        <rect x={2 * u} y={3 * u} width={2 * u} height={4 * u} fill="#e8edf4" />
        <rect x={34 * u} y={3 * u} width={3 * u} height={4 * u} fill="#e8edf4" />
        {/* shading */}
        <rect x={4 * u} y={7 * u} width={30 * u} height={u} fill="#a9b8cc" />
        <rect x={4 * u} y={2 * u} width={30 * u} height={u} fill="#ffffff" />
        {/* tail fins */}
        <rect x={35 * u} y={1 * u} width={3 * u} height={2 * u} fill="#e2603b" />
        <rect x={35 * u} y={7 * u} width={3 * u} height={2 * u} fill="#e2603b" />
        {/* gondola */}
        <rect x={15 * u} y={8 * u} width={8 * u} height={2 * u} fill="#2b3242" />
        {/* banner text */}
        <text
          x={19 * u}
          y={6 * u}
          textAnchor="middle"
          fontFamily={PIXEL}
          fontSize={3.4 * u}
          fill="#2b3242"
        >
          MYCEL
        </text>
      </svg>
    </div>
  );
}

/* ── Retro chip / tag button ── */
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
      className="inline-block px-4 py-2 text-[10px] md:text-[11px] tracking-wider whitespace-nowrap"
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

/* ── HUD hearts / HP bar segments ── */
function HpBar({ filled, total }: { filled: number; total: number }) {
  return (
    <div className="flex gap-1" role="img" aria-label={`Company health ${filled} of ${total}`}>
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          className="block w-3 h-4"
          style={{
            background: i < filled ? (i > total - 4 ? "#e8c33a" : "#57c94f") : "#2b3242",
            boxShadow: "inset -2px -2px 0 rgba(0,0,0,0.35), inset 2px 2px 0 rgba(255,255,255,0.25)",
          }}
        />
      ))}
    </div>
  );
}

/* ── Pixel heart ── */
function PixelHeart() {
  const u = 3;
  return (
    <svg width={9 * u} height={8 * u} viewBox={`0 0 ${9 * u} ${8 * u}`} shapeRendering="crispEdges" className="animate-heart-beat" aria-hidden="true">
      {(
        [
          [1, 0, 2, 1],
          [6, 0, 2, 1],
          [0, 1, 4, 2],
          [5, 1, 4, 2],
          [0, 3, 9, 1],
          [1, 4, 7, 1],
          [2, 5, 5, 1],
          [3, 6, 3, 1],
          [4, 7, 1, 1],
        ] as [number, number, number, number][]
      ).map(([x, y, w, h], i) => (
        <rect key={i} x={x * u} y={y * u} width={w * u} height={h * u} fill="#e5484d" />
      ))}
      <rect x={1 * u} y={1 * u} width={u} height={u} fill="#ff8a8d" />
    </svg>
  );
}

/* ── Pixel ghost mascot ── */
function PixelGhost() {
  const u = 4;
  return (
    <svg width={10 * u} height={10 * u} viewBox={`0 0 ${10 * u} ${10 * u}`} shapeRendering="crispEdges" className="animate-ghost-bob" aria-hidden="true">
      <rect x={2 * u} y={0} width={6 * u} height={u} fill="#8ecbff" />
      <rect x={1 * u} y={u} width={8 * u} height={u} fill="#8ecbff" />
      <rect x={0} y={2 * u} width={10 * u} height={6 * u} fill="#8ecbff" />
      {/* feet */}
      <rect x={0} y={8 * u} width={2 * u} height={u} fill="#8ecbff" />
      <rect x={3 * u} y={8 * u} width={2 * u} height={u} fill="#8ecbff" />
      <rect x={6 * u} y={8 * u} width={2 * u} height={u} fill="#8ecbff" />
      {/* eyes */}
      <rect x={2 * u} y={3 * u} width={2 * u} height={2 * u} fill="#12161f" />
      <rect x={6 * u} y={3 * u} width={2 * u} height={2 * u} fill="#12161f" />
      {/* mouth */}
      <rect x={3 * u} y={6 * u} width={u} height={u} fill="#12161f" />
      <rect x={5 * u} y={6 * u} width={u} height={u} fill="#12161f" />
      <rect x={4 * u} y={7 * u} width={u} height={u} fill="#12161f" />
    </svg>
  );
}

/* ── Field icon tile ── */
function IconTile({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="flex items-center justify-center shrink-0 w-12 h-12"
      style={{
        background: "#1b2230",
        boxShadow: "0 0 0 2px #3a4356, inset -3px -3px 0 rgba(0,0,0,0.45), inset 3px 3px 0 rgba(255,255,255,0.06)",
      }}
      aria-hidden="true"
    >
      {children}
    </div>
  );
}

function UserIcon() {
  const u = 3;
  return (
    <svg width={8 * u} height={8 * u} viewBox={`0 0 ${8 * u} ${8 * u}`} shapeRendering="crispEdges">
      <rect x={2 * u} y={0} width={4 * u} height={4 * u} fill="#6aa9ff" />
      <rect x={0} y={5 * u} width={8 * u} height={3 * u} fill="#6aa9ff" />
      <rect x={1 * u} y={4 * u} width={6 * u} height={u} fill="#6aa9ff" />
    </svg>
  );
}

function LockIcon() {
  const u = 3;
  return (
    <svg width={8 * u} height={8 * u} viewBox={`0 0 ${8 * u} ${8 * u}`} shapeRendering="crispEdges">
      <rect x={2 * u} y={0} width={u} height={3 * u} fill="#f2b01f" />
      <rect x={5 * u} y={0} width={u} height={3 * u} fill="#f2b01f" />
      <rect x={2 * u} y={0} width={4 * u} height={u} fill="#f2b01f" />
      <rect x={1 * u} y={3 * u} width={6 * u} height={5 * u} fill="#f2b01f" />
      <rect x={3.5 * u} y={4.5 * u} width={u} height={2 * u} fill="#12161f" />
    </svg>
  );
}

function BadgeIcon() {
  const u = 3;
  return (
    <svg width={8 * u} height={8 * u} viewBox={`0 0 ${8 * u} ${8 * u}`} shapeRendering="crispEdges">
      <rect x={0} y={u} width={8 * u} height={6 * u} fill="#57c94f" />
      <rect x={u} y={2 * u} width={2 * u} height={2 * u} fill="#12161f" />
      <rect x={4 * u} y={2 * u} width={3 * u} height={u} fill="#12161f" />
      <rect x={4 * u} y={4 * u} width={3 * u} height={u} fill="#12161f" />
      <rect x={u} y={5 * u} width={6 * u} height={u} fill="#12161f" />
    </svg>
  );
}

/* ── Input row styled like the reference terminal ── */
function PixelField({
  label,
  icon,
  htmlFor,
  children,
}: {
  label: string;
  icon: React.ReactNode;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-end gap-3">
      <IconTile>{icon}</IconTile>
      <div className="flex-1 min-w-0">
        <label
          htmlFor={htmlFor}
          className="block mb-2 text-[9px] tracking-widest text-[#c8d2e4]"
          style={{ fontFamily: PIXEL }}
        >
          {label}
        </label>
        {children}
      </div>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  fontFamily: TERM,
  fontSize: "20px",
  background: "#0b0e15",
  color: "#e8edf4",
  border: "none",
  boxShadow: "0 0 0 2px #3a4356, inset 3px 3px 0 rgba(0,0,0,0.6)",
  caretColor: "#f28a1f",
};

/* ════════════════════════════════ MAIN PAGE ═══════════════════════════════ */

const LoginPage = () => {
  const { isAuthenticated, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [booted, setBooted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 100);
    return () => clearTimeout(t);
  }, []);

  if (isAuthenticated) {
    window.location.href = "/";
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const endpoint = isSignUp ? "/api/auth/register" : "/api/auth/login";
      const payload = isSignUp ? { email, password, name } : { email, password };

      const res = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok)
        throw new Error(data.detail || (isSignUp ? "Registration failed" : "Login failed"));

      login(data.access_token, data.user);
      window.location.href = "/";
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main
      className="relative h-screen overflow-hidden select-none"
      style={{
        background: "linear-gradient(180deg, #4da3e8 0%, #58aeef 45%, #3f8fd6 100%)",
      }}
    >
      {/* blueprint grid overlay */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.10) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.10) 1px, transparent 1px)",
          backgroundSize: "28px 28px",
        }}
      />
      {/* horizontal scanlines */}
      <div
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-[0.07]"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,1) 1px, transparent 1px)",
          backgroundSize: "100% 3px",
        }}
      />

      {/* city skyline silhouette */}
      <div
        aria-hidden="true"
        className="absolute bottom-0 left-0 right-0 h-[38vh] pointer-events-none opacity-40"
        style={{
          background: "#1d4e7e",
          clipPath:
            "polygon(0 62%, 4% 62%, 4% 38%, 9% 38%, 9% 55%, 14% 55%, 14% 22%, 16% 22%, 16% 14%, 18% 14%, 18% 22%, 20% 22%, 20% 58%, 26% 58%, 26% 34%, 31% 34%, 31% 64%, 37% 64%, 37% 44%, 42% 44%, 42% 70%, 50% 70%, 50% 30%, 54% 30%, 54% 18%, 56% 18%, 56% 30%, 60% 30%, 60% 60%, 66% 60%, 66% 40%, 72% 40%, 72% 66%, 78% 66%, 78% 26%, 82% 26%, 82% 50%, 88% 50%, 88% 36%, 93% 36%, 93% 58%, 100% 58%, 100% 100%, 0 100%)",
        }}
      />

      {/* clouds + blimp */}
      <PixelCloud x="8%" y="9%" scale={1.2} duration={90} />
      <PixelCloud x="55%" y="4%" scale={0.8} duration={70} delay={-30} />
      <PixelCloud x="78%" y="20%" scale={1} duration={110} delay={-60} />
      <PixelCloud x="30%" y="16%" scale={0.6} duration={80} delay={-15} />
      <PixelBlimp />

      {/* ═══════════ CONTENT GRID ═══════════ */}
      <div className="relative z-10 mx-auto max-w-375 px-4 md:px-8 pt-6 pb-8 md:pb-36 grid grid-cols-1 md:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)] gap-8 lg:gap-10 items-start">
        {/* ─────────── LEFT: branding + building ─────────── */}
        <section
          className={`flex flex-col transition-all duration-700 ${booted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}`}
        >
          <header className="flex flex-wrap items-center gap-5 mb-8 mt-2 ml-1">
            <span className="animate-press-start">
              <PixelChip>PRESS START</PixelChip>
            </span>
            <PixelChip color="#f4f6f9" textColor="#1a1f2c">
              THEME : ARMORIQ
            </PixelChip>
          </header>

          {/* Giant pixel logotype */}
          <h1
            className="text-[clamp(2.6rem,6.5vw,5.2rem)] leading-none text-[#1a2338] mb-5 text-balance"
            style={{
              fontFamily: PIXEL,
              textShadow:
                "3px 0 0 #fff, -3px 0 0 #fff, 0 3px 0 #fff, 0 -3px 0 #fff, 3px 3px 0 #fff, -3px -3px 0 #fff, 3px -3px 0 #fff, -3px 3px 0 #fff, 7px 7px 0 #f28a1f",
            }}
          >
            MYCEL
          </h1>

          <p
            className="text-sm md:text-lg text-[#12233c] tracking-widest mb-8"
            style={{ fontFamily: PIXEL }}
          >
            THE AUTONOMOUS{" "}
            <span className="px-2 py-1" style={{ background: "#79d97c", color: "#0e2a12" }}>
              AI COMPANY
            </span>
          </p>

          {/* marquee ticker */}
          <div
            className="mb-8 overflow-hidden py-3 px-1"
            style={{
              background: "#12161f",
              boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 6px 6px 0 6px rgba(0,0,0,0.35)",
            }}
          >
            <div
              className="whitespace-nowrap animate-ticker text-[#7fd4ff]"
              style={{ fontFamily: PIXEL, fontSize: 11 }}
            >
              BUILDING THE FUTURE, TOGETHER. ★ 30 AGENTS ONLINE ★ ALL SYSTEMS OPERATIONAL ★
              SERVER ROOM: STABLE ★ COFFEE MACHINE: FULL ★ BUILDING THE FUTURE, TOGETHER. ★ 30
              AGENTS ONLINE ★ ALL SYSTEMS OPERATIONAL ★ SERVER ROOM: STABLE ★ COFFEE MACHINE:
              FULL ★
            </div>
          </div>

          {/* the building */}
          <div className="relative self-center lg:self-start w-full max-w-140">
            <img
              src="/login/mycel-building.png"
              alt="Pixel-art cross-section of the Mycel headquarters, every floor staffed by AI agents"
              className="w-full h-auto animate-building-rise"
              style={{
                imageRendering: "pixelated",
                filter: "drop-shadow(0 18px 40px rgba(6,28,55,0.5))",
              }}
            />
          </div>
        </section>

        {/* ─────────── RIGHT: auth terminal ─────────── */}
        <section
          className={`md:sticky md:top-8 mt-4 md:mt-24 transition-all duration-700 delay-150 ${booted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-6"}`}
        >
          <div className="px-6 py-8 md:px-10 md:py-10 mx-auto max-w-140" style={pixelPanel}>
            {/* heading */}
            <div className="text-center mb-2">
              <p
                className="text-[13px] md:text-[15px] leading-relaxed text-[#f2b01f]"
                style={{ fontFamily: PIXEL }}
              >
                <span aria-hidden="true" className="text-[#c8d2e4]">{"\u2500\u2500\u25B6 "}</span>
                {isSignUp ? "JOIN THE COMPANY!" : "WELCOME BACK, PIONEER!"}
                <span aria-hidden="true" className="text-[#c8d2e4]">{" \u25C0\u2500\u2500"}</span>
              </p>
            </div>
            <p
              className="text-center text-[19px] text-[#aeb9cf] mb-8 leading-relaxed text-pretty"
              style={{ fontFamily: TERM }}
            >
              {isSignUp
                ? "Register your pioneer badge and start building the future."
                : "Log in to your dashboard and keep the company running."}
            </p>

            <form onSubmit={handleSubmit} className="flex flex-col gap-6" aria-busy={loading}>
              {isSignUp && (
                <PixelField label="DISPLAY NAME" icon={<BadgeIcon />} htmlFor="signup-name">
                  <input
                    id="signup-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Choose your pioneer name"
                    required
                    autoComplete="name"
                    className="w-full px-3 py-2.5 focus:outline-none focus-visible:ring-0 placeholder:text-[#4e5a70]"
                    style={inputStyle}
                  />
                </PixelField>
              )}

              <PixelField label="USERNAME OR EMAIL" icon={<UserIcon />} htmlFor="auth-email">
                <input
                  id="auth-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your username or email"
                  required
                  autoComplete="email"
                  className="w-full px-3 py-2.5 focus:outline-none focus-visible:ring-0 placeholder:text-[#4e5a70]"
                  style={inputStyle}
                />
              </PixelField>

              <PixelField label="PASSWORD" icon={<LockIcon />} htmlFor="auth-password">
                <div className="relative">
                  <input
                    id="auth-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                    autoComplete={isSignUp ? "new-password" : "current-password"}
                    className="w-full px-3 py-2.5 pr-12 focus:outline-none focus-visible:ring-0 placeholder:text-[#4e5a70]"
                    style={inputStyle}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-[#7f8ca5] hover:text-[#e8edf4]"
                  >
                    <svg width={22} height={16} viewBox="0 0 22 16" shapeRendering="crispEdges" aria-hidden="true">
                      <rect x={2} y={6} width={18} height={4} fill="currentColor" opacity={0.35} />
                      <rect x={4} y={4} width={14} height={8} fill="currentColor" opacity={0.35} />
                      <rect x={8} y={5} width={6} height={6} fill="currentColor" />
                      {!showPassword && <rect x={0} y={7} width={22} height={2} fill="#e5484d" />}
                    </svg>
                  </button>
                </div>
              </PixelField>

              {/* remember / forgot */}
              {!isSignUp && (
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <label
                    className="flex items-center gap-3 cursor-pointer text-[9px] tracking-widest text-[#c8d2e4]"
                    style={{ fontFamily: PIXEL }}
                  >
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      className="sr-only"
                    />
                    <span
                      aria-hidden="true"
                      className="w-4 h-4 flex items-center justify-center"
                      style={{
                        background: "#0b0e15",
                        boxShadow: "0 0 0 2px #3a4356",
                      }}
                    >
                      {remember && <span className="w-2.5 h-2.5" style={{ background: "#57c94f" }} />}
                    </span>
                    REMEMBER ME
                  </label>
                  <button
                    type="button"
                    className="text-[9px] tracking-widest text-[#f2b01f] hover:text-[#ffd24d]"
                    style={{ fontFamily: PIXEL }}
                  >
                    FORGOT PASSWORD?
                  </button>
                </div>
              )}

              {/* error alert */}
              {error && (
                <div
                  role="alert"
                  className="px-4 py-3 text-[16px] leading-snug text-[#ffd7d8]"
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

              {/* the big orange button */}
              <button
                type="submit"
                disabled={loading}
                className="group relative w-full py-4 text-[15px] tracking-[0.2em] text-[#241303] transition-transform active:translate-y-1 disabled:opacity-70"
                style={{
                  fontFamily: PIXEL,
                  background: loading ? "#c7761e" : "#f28a1f",
                  boxShadow:
                    "0 0 0 3px #12161f, inset -4px -4px 0 rgba(0,0,0,0.25), inset 4px 4px 0 rgba(255,255,255,0.35), 0 6px 0 3px #12161f",
                }}
              >
                {loading ? (
                  <span className="animate-blink">CONNECTING...</span>
                ) : (
                  <>
                    {isSignUp ? "CREATE ACCOUNT" : "LOG IN"}
                    <span aria-hidden="true" className="absolute right-5 group-hover:translate-x-1 transition-transform">
                      {"\u25B6"}
                    </span>
                  </>
                )}
              </button>
            </form>

            {/* divider */}
            <div className="flex items-center gap-4 my-7" aria-hidden="true">
              <span className="flex-1 h-0.5 bg-[#3a4356]" />
              <span
                className="text-[9px] text-[#7f8ca5] px-3 py-1.5"
                style={{ fontFamily: PIXEL, boxShadow: "0 0 0 2px #3a4356" }}
              >
                OR
              </span>
              <span className="flex-1 h-0.5 bg-[#3a4356]" />
            </div>

            {/* toggle */}
            <p className="text-center text-[10px] tracking-wider leading-loose" style={{ fontFamily: PIXEL }}>
              <span className="text-[#c8d2e4]">{isSignUp ? "ALREADY A PIONEER? " : "NEW HERE? "}</span>
              <button
                type="button"
                onClick={() => {
                  setIsSignUp((v) => !v);
                  setError("");
                }}
                className="text-[#79d97c] hover:text-[#a8f0aa] underline underline-offset-4 decoration-2"
              >
                {isSignUp ? "LOG IN INSTEAD" : "CREATE AN ACCOUNT"}
              </button>
            </p>
          </div>

          <p
            className="text-center mt-6 text-[10px] tracking-widest text-[#0e2a4a]/80"
            style={{ fontFamily: PIXEL }}
          >
            MYCEL &middot; BUILT BY TEAM EVOLVE AI &middot; V1.0
          </p>
        </section>
      </div>

      {/* ═══════════ BOTTOM HUD STATUS BAR ═══════════ */}
      <footer className="relative md:fixed md:bottom-0 md:left-0 md:right-0 z-20 px-3 pb-3 pointer-events-none mt-4 md:mt-0">
        <div className="mx-auto max-w-375 grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* company status */}
          <div className="flex items-center gap-4 px-5 py-3" style={pixelPanel}>
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2">
                <span className="text-[8px] tracking-widest text-[#c8d2e4]" style={{ fontFamily: PIXEL }}>
                  COMPANY STATUS
                </span>
                <PixelHeart />
              </div>
              <HpBar filled={11} total={13} />
            </div>
            <div className="ml-auto flex flex-col gap-1.5 items-end">
              <span className="text-[8px] tracking-widest text-[#c8d2e4]" style={{ fontFamily: PIXEL }}>
                ONLINE AGENTS
              </span>
              <span className="text-[13px] text-[#79d97c]" style={{ fontFamily: PIXEL }}>
                30 / 30
              </span>
            </div>
          </div>

          {/* system online */}
          <div className="flex items-center gap-4 px-5 py-3" style={pixelPanel}>
            <PixelGhost />
            <div className="flex flex-col gap-1">
              <span className="text-[10px] tracking-widest text-[#e8edf4]" style={{ fontFamily: PIXEL }}>
                SYSTEM ONLINE<span className="animate-blink">_</span>
              </span>
              <span className="text-[9px] tracking-widest text-[#79d97c]" style={{ fontFamily: PIXEL }}>
                ALL SYSTEMS OPERATIONAL.
              </span>
            </div>
          </div>

          {/* secure connection */}
          <div className="flex items-center justify-center gap-3 px-5 py-3" style={pixelPanel}>
            <LockIcon />
            <span className="text-[9px] tracking-widest text-[#c8d2e4]" style={{ fontFamily: PIXEL }}>
              SECURE CONNECTION ESTABLISHED
            </span>
          </div>
        </div>
      </footer>

      {/* page-scoped keyframes */}
      <style>{`
        @keyframes cloud-drift {
          from { transform: translateX(-8vw); }
          to { transform: translateX(108vw); }
        }
        .animate-cloud-drift { animation: cloud-drift linear infinite; }

        @keyframes blimp-float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-14px); }
        }
        .animate-blimp-float { animation: blimp-float 6s ease-in-out infinite; }

        @keyframes press-start-blink {
          0%, 55% { opacity: 1; }
          56%, 100% { opacity: 0.35; }
        }
        .animate-press-start { animation: press-start-blink 1.4s steps(1) infinite; }

        @keyframes ticker {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        .animate-ticker { animation: ticker 24s linear infinite; display: inline-block; }

        @keyframes blink {
          0%, 60% { opacity: 1; }
          61%, 100% { opacity: 0; }
        }
        .animate-blink { animation: blink 1s steps(1) infinite; }

        @keyframes heart-beat {
          0%, 70%, 100% { transform: scale(1); }
          15% { transform: scale(1.25); }
          30% { transform: scale(1); }
          45% { transform: scale(1.15); }
        }
        .animate-heart-beat { animation: heart-beat 1.6s ease-in-out infinite; transform-origin: center; }

        @keyframes ghost-bob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-ghost-bob { animation: ghost-bob 2s ease-in-out infinite; }

        @keyframes building-rise {
          from { transform: translateY(24px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-building-rise { animation: building-rise 0.9s cubic-bezier(0.22, 1, 0.36, 1) both; animation-delay: 0.2s; }

        @media (prefers-reduced-motion: reduce) {
          .animate-cloud-drift, .animate-blimp-float, .animate-press-start,
          .animate-ticker, .animate-blink, .animate-heart-beat,
          .animate-ghost-bob, .animate-building-rise {
            animation: none;
          }
        }
      `}</style>
    </main>
  );
};

export default LoginPage;
