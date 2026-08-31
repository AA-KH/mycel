import { useAuth } from "../contexts/AuthContext";
import { Link, useLocation } from "react-router-dom";

/* ── Login-theme HUD chrome: Press Start 2P + dark pixel panels ── */
const PIXEL = "'Press Start 2P', monospace";
const TERM = "'VT323', monospace";

const NAV_ITEMS = [
  { to: "/", label: "HOME" },
  { to: "/office", label: "OFFICE" },
  { to: "/dashboard", label: "CONFIG" },
  { to: "/armoriq", label: "ARMORIQ" },
];

export default function PixelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();

  return (
    <div
      className="h-screen w-screen flex flex-col overflow-hidden"
      style={{ background: "#12161f" }}
    >
      {/* ── Game HUD top bar ── */}
      <header
        className="shrink-0 z-30 flex items-stretch justify-between"
        style={{
          background: "#12161f",
          borderBottom: "4px solid #3a4356",
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
              style={{ background: "#57c94f" }}
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
              background: "#12161f",
              borderLeft: "3px solid #3a4356",
            }}
          >
            X QUIT
          </button>
        </div>
      </header>

      {/* ── Full-screen game world ── */}
      <main
        className="flex-1 overflow-auto relative"
        style={{
          backgroundColor: "#3c5956",
          backgroundImage: `url("/assets/tiles/green-floor-3x3.png")`,
          backgroundSize: "96px 96px",
          backgroundRepeat: "repeat",
          imageRendering: "pixelated",
        }}
      >
        {children}
      </main>
    </div>
  );
}
