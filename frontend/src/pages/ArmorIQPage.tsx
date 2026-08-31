import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useArmorIQ } from "@/lib/armoriq/useArmorIQ";
import type { DecisionRecord } from "@/lib/armoriq/engine";

/* ── Design tokens matching Mycel theme ── */
const PIXEL  = "'Press Start 2P', monospace";
const TERM   = "'VT323', monospace";
const BG     = "#12161f";
const RAISE  = "#1b2230";
const PANEL  = "#0b0e15";
const BORDER = "#3a4356";
const ORANGE = "#f28a1f";
const GREEN  = "#57c94f";
const RED    = "#e5484d";
const YELLOW = "#f2b01f";
const CYAN   = "#88c0d0";
const BLUE   = "#6aa9ff";
const TEXT   = "#e8edf4";
const MUTED  = "#7f8ca5";
const DIM    = "#4e5a70";

const pixelPanel: React.CSSProperties = {
  background: BG,
  boxShadow: "0 0 0 3px #3a4356, 0 0 0 6px #12161f, 0 0 0 9px #232a38, 12px 12px 0 9px rgba(0,0,0,0.45)",
  imageRendering: "pixelated",
};

/* ── Nav items (same as OfficePage) ── */
const NAV_ITEMS = [
  { to: "/",          label: "HOME"    },
  { to: "/office",    label: "OFFICE"  },
  { to: "/dashboard", label: "CONFIG"  },
  { to: "/armoriq",   label: "ARMORIQ" },
];

/* ── Helpers ── */
function fmtUptime(s: number) {
  const h = Math.floor(s / 3600).toString().padStart(2, "0");
  const m = Math.floor((s % 3600) / 60).toString().padStart(2, "0");
  const sec = (s % 60).toString().padStart(2, "0");
  return `${h}:${m}:${sec}`;
}
function relTime(ts: number) {
  const s = Math.round((Date.now() - ts) / 1000);
  if (s < 60)   return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}
function pct(n: number, total: number) {
  return total ? Math.round((n / total) * 100) : 0;
}

/* ── Status/Risk configs ── */
const STATUS_CFG: Record<string, { label: string; color: string; bg: string }> = {
  ALLOW:            { label: "ALLOW",  color: GREEN,  bg: "#0e2a12" },
  DENY:             { label: "DENY",   color: RED,    bg: "#3a1418" },
  REQUIRE_APPROVAL: { label: "GATED", color: YELLOW, bg: "#3a2c00" },
  REQUIRE_REVIEW:   { label: "REVIEW",color: CYAN,   bg: "#0d2830" },
};
const RISK_COLOR: Record<string, string> = {
  LOW: GREEN, MEDIUM: YELLOW, HIGH: ORANGE, CRITICAL: RED,
};

/* ── Sparkline ── */
function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data, 1);
  const w = 100, h = 24;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - (v / max) * h}`).join(" ");
  return (
    <svg width={w} height={h} style={{ overflow: "visible", display: "block" }}>
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={pts} strokeLinejoin="round" />
      <polygon fill={color} fillOpacity="0.1" points={`0,${h} ${pts} ${w},${h}`} />
    </svg>
  );
}

/* ── Meter bar ── */
function Meter({ value, color }: { value: number; color: string }) {
  return (
    <div style={{ flex: 1, height: 6, background: "#080b11", boxShadow: `inset 0 0 0 2px ${BORDER}` }}>
      <div style={{ width: `${Math.min(value, 1) * 100}%`, height: "100%", background: color, transition: "width 0.5s ease" }} />
    </div>
  );
}

/* ── Pixel stat card ── */
function StatCard({ label, value, sub, color, trend }: { label: string; value: string | number; sub?: string; color?: string; trend?: number[] }) {
  return (
    <div style={{ background: PANEL, boxShadow: `0 0 0 3px ${BORDER}, 4px 4px 0 3px rgba(0,0,0,0.4)` }}>
      <div style={{ borderBottom: `3px solid ${BORDER}`, background: RAISE, padding: "6px 12px" }}>
        <span style={{ fontFamily: PIXEL, fontSize: 7, letterSpacing: "0.06em", color: ORANGE }}>{label}</span>
      </div>
      <div style={{ padding: "12px" }}>
        <div style={{ fontFamily: TERM, fontSize: 32, color: color ?? TEXT, lineHeight: 1 }}>{value}</div>
        {sub && <div style={{ fontFamily: TERM, fontSize: 14, color: MUTED, marginTop: 4 }}>{sub}</div>}
        {trend && <div style={{ marginTop: 8 }}><Sparkline data={trend} color={color ?? ORANGE} /></div>}
      </div>
    </div>
  );
}

/* ── Decision table row ── */
function DecisionRow({ d, selected, onSelect }: { d: DecisionRecord; selected: boolean; onSelect: () => void }) {
  const eff = (d.resolution?.status ?? d.status) as string;
  const sc  = STATUS_CFG[eff] ?? { label: eff, color: MUTED, bg: RAISE };
  return (
    <tr onClick={onSelect} style={{ cursor: "pointer", background: selected ? RAISE : "transparent", borderBottom: `2px solid ${BORDER}`, borderLeft: `4px solid ${sc.color}` }}>
      <td style={{ padding: "8px 10px" }}>
        <span style={{ fontFamily: PIXEL, fontSize: 7, color: sc.color, background: sc.bg, padding: "3px 6px" }}>{sc.label}</span>
      </td>
      <td style={{ padding: "8px 10px", fontFamily: TERM, fontSize: 15, color: TEXT, maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {d.actionType}
      </td>
      <td style={{ padding: "8px 10px", fontFamily: TERM, fontSize: 14, color: MUTED }}>
        {d.agentId}
      </td>
      <td style={{ padding: "8px 10px", fontFamily: TERM, fontSize: 14, color: MUTED, maxWidth: 130, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {d.resource}
      </td>
      <td style={{ padding: "8px 10px" }}>
        <span style={{ fontFamily: PIXEL, fontSize: 7, color: RISK_COLOR[d.riskLevel] ?? MUTED }}>{d.riskLevel}</span>
      </td>
      <td style={{ padding: "8px 10px", fontFamily: TERM, fontSize: 14, color: DIM, textAlign: "right" }}>{d.latencyMs}ms</td>
      <td style={{ padding: "8px 10px", fontFamily: TERM, fontSize: 14, color: DIM, textAlign: "right" }}>{relTime(d.ts)}</td>
    </tr>
  );
}

/* ── Detail drawer ── */
function DetailDrawer({ d }: { d: DecisionRecord }) {
  const eff = (d.resolution?.status ?? d.status) as string;
  const sc  = STATUS_CFG[eff] ?? { label: eff, color: MUTED, bg: RAISE };
  return (
    <div style={{ background: "#080b11", borderTop: `3px solid ${BORDER}`, padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ fontFamily: PIXEL, fontSize: 7, color: ORANGE, letterSpacing: "0.08em" }}>DECISION DETAIL</div>
      <div style={{ fontFamily: TERM, fontSize: 15, color: TEXT }}>
        <span style={{ color: DIM }}>intent&nbsp;&nbsp;</span>{d.intent}
      </div>
      <div style={{ fontFamily: TERM, fontSize: 15 }}>
        <span style={{ color: DIM }}>reason&nbsp;&nbsp;</span>
        <span style={{ color: sc.color }}>{d.reason}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        {[["decision", d.decisionId], ["trace", d.traceId.slice(0, 14) + "…"], ["policy", d.policyId], ["env", d.environment], ["tool", d.toolId ?? "—"], ["audit", d.auditRef]].map(([k, v]) => (
          <div key={k} style={{ fontFamily: TERM, fontSize: 14 }}>
            <span style={{ color: DIM }}>{k}&nbsp;</span>
            <span style={{ color: MUTED }}>{v}</span>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, paddingTop: 6, borderTop: `2px solid ${BORDER}` }}>
        {d.signals.map(s => (
          <span key={s.key} style={{ fontFamily: TERM, fontSize: 14 }}>
            <span style={{ color: DIM }}>{s.key}=</span>
            <span style={{ color: CYAN }}>{s.value}</span>
          </span>
        ))}
      </div>
      {d.resolution && (
        <div style={{ fontFamily: TERM, fontSize: 14, color: MUTED, paddingTop: 6, borderTop: `2px solid ${BORDER}` }}>
          resolved <span style={{ color: sc.color }}>{d.resolution.status}</span> by {d.resolution.by} at {new Date(d.resolution.ts).toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

/* ── Approvals ── */
function ApprovalsView({ approvals, onResolve }: { approvals: DecisionRecord[]; onResolve: (id: string, s: "ALLOW" | "DENY") => void }) {
  if (approvals.length === 0)
    return (
      <div style={{ textAlign: "center", padding: "48px 20px" }}>
        <div style={{ fontFamily: PIXEL, fontSize: 9, color: GREEN, letterSpacing: "0.06em" }}>✓ NO PENDING APPROVALS</div>
        <div style={{ fontFamily: TERM, fontSize: 17, color: DIM, marginTop: 10 }}>All decisions resolved.</div>
      </div>
    );
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {approvals.map(d => (
        <div key={d.decisionId} style={{ background: PANEL, boxShadow: `0 0 0 3px ${BORDER}`, padding: 16, display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontFamily: TERM, fontSize: 18, color: TEXT, marginBottom: 4 }}>{d.actionType}</div>
            <div style={{ fontFamily: TERM, fontSize: 15, color: MUTED, marginBottom: 8 }}>{d.agentId} → {d.resource}</div>
            <div style={{ fontFamily: TERM, fontSize: 15, color: DIM }}>{d.intent}</div>
            <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
              <span style={{ fontFamily: PIXEL, fontSize: 7, color: YELLOW, background: "#3a2c00", padding: "3px 6px" }}>RISK: {d.riskLevel}</span>
              <span style={{ fontFamily: PIXEL, fontSize: 7, color: DIM, background: RAISE, padding: "3px 6px" }}>{d.policyId}</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => onResolve(d.decisionId, "ALLOW")} style={{ fontFamily: PIXEL, fontSize: 7, letterSpacing: "0.06em", padding: "8px 14px", background: "#0e2a12", color: GREEN, border: `2px solid ${GREEN}`, cursor: "pointer" }}>APPROVE</button>
            <button onClick={() => onResolve(d.decisionId, "DENY")} style={{ fontFamily: PIXEL, fontSize: 7, letterSpacing: "0.06em", padding: "8px 14px", background: "#3a1418", color: RED, border: `2px solid ${RED}`, cursor: "pointer" }}>DENY</button>
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Config ── */
function ConfigView() {
  const rows = [
    { label: "Default Policy",    value: "mycel-v3-strict", color: GREEN },
    { label: "Enforcement Mode",  value: "ENFORCING",         color: GREEN },
    { label: "Approval TTL",      value: "300s" },
    { label: "Max Retry",         value: "3" },
    { label: "Audit Retention",   value: "90 days" },
    { label: "Region",            value: "us-east-1" },
    { label: "Org ID",            value: "org_kbz_8831" },
    { label: "SDK",               value: "armoriq-sdk 2.7.1" },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {rows.map((r, i) => (
        <div key={r.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", borderBottom: i < rows.length - 1 ? `2px solid ${BORDER}` : "none" }}>
          <span style={{ fontFamily: TERM, fontSize: 16, color: MUTED }}>{r.label}</span>
          <span style={{ fontFamily: TERM, fontSize: 17, color: r.color ?? TEXT, fontWeight: 600 }}>{r.value}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Pipeline ── */
function PipelineView({ d }: { d?: DecisionRecord }) {
  const stages = [
    { name: "AUTH",    icon: "🔐", ok: true },
    { name: "POLICY",  icon: "📋", ok: true },
    { name: "RISK",    icon: "⚡", ok: !d || (d.riskLevel !== "CRITICAL" && d.riskLevel !== "HIGH") },
    { name: "RULES",   icon: "🔍", ok: true },
    { name: "DECISION",icon: "⚖", ok: !d || d.status !== "DENY" },
    { name: "AUDIT",   icon: "📝", ok: true },
  ];
  return (
    <div>
      <div style={{ fontFamily: TERM, fontSize: 15, color: MUTED, marginBottom: 20 }}>
        {d ? `Trace: ${d.traceId.slice(0, 22)}…` : "No decision selected — showing last pipeline run."}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 0, overflowX: "auto", paddingBottom: 8 }}>
        {stages.map((st, i) => {
          const col = st.ok ? GREEN : RED;
          return (
            <div key={st.name} style={{ display: "flex", alignItems: "center" }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, minWidth: 72 }}>
                <div style={{ width: 48, height: 48, background: col + "18", boxShadow: `0 0 0 3px ${col}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22 }}>
                  {st.icon}
                </div>
                <span style={{ fontFamily: PIXEL, fontSize: 6, color: col, textAlign: "center", letterSpacing: "0.04em" }}>{st.name}</span>
              </div>
              {i < stages.length - 1 && (
                <div style={{ width: 24, height: 3, background: BORDER, flexShrink: 0, margin: "0 2px", position: "relative", top: -10 }} />
              )}
            </div>
          );
        })}
      </div>
      {d && (
        <div style={{ marginTop: 20, display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
          {[["Latency", `${d.latencyMs}ms`, CYAN], ["Policy", d.policyId, MUTED], ["Env", d.environment, MUTED]].map(([k, v, c]) => (
            <div key={k as string} style={{ background: PANEL, boxShadow: `0 0 0 2px ${BORDER}`, padding: "10px 14px" }}>
              <div style={{ fontFamily: PIXEL, fontSize: 6, color: DIM, marginBottom: 6 }}>{k as string}</div>
              <div style={{ fontFamily: TERM, fontSize: 18, color: c as string }}>{v as string}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════ */
type TabId = "stream" | "pipeline" | "gate" | "audit" | "config";
const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: "stream",   label: "STREAM",   icon: "📡" },
  { id: "pipeline", label: "PIPELINE", icon: "⚙" },
  { id: "gate",     label: "GATE",     icon: "✋" },
  { id: "audit",    label: "AUDIT",    icon: "🧾" },
  { id: "config",   label: "CONFIG",   icon: "🔐" },
];

export default function ArmorIQPage() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const [tab, setTab]         = useState<TabId>("stream");
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter]   = useState<"ALL" | "BLOCKED">("ALL");
  const { decisions, approvals, metrics, live, setLive, uptime, resolveApproval } = useArmorIQ();

  const rows = decisions.filter(d =>
    filter === "ALL" ? true : (d.resolution?.status ?? d.status) !== "ALLOW"
  );
  const activeDecision = decisions.find(d => d.decisionId === selected);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden" style={{ background: BG }}>

      {/* ══ Game HUD top bar — same as OfficePage ══ */}
      <header className="shrink-0 z-30 flex items-stretch justify-between" style={{ background: BG, borderBottom: "4px solid #3a4356", imageRendering: "pixelated" }}>
        {/* Left: logo + nav */}
        <div className="flex items-stretch">
          <Link to="/" className="flex items-center gap-2 px-4 text-[11px] tracking-wider text-[#e8edf4]" style={{ fontFamily: PIXEL, borderRight: "3px solid #3a4356", textShadow: "2px 2px 0 #f28a1f" }}>
            MYCEL
          </Link>
          {NAV_ITEMS.map(item => {
            const active = pathname === item.to;
            return (
              <Link key={item.to} to={item.to} className="flex items-center px-4 py-3 text-[9px] tracking-widest transition-colors" style={{ fontFamily: PIXEL, background: active ? ORANGE : "transparent", color: active ? "#241303" : MUTED, borderRight: `3px solid ${BORDER}`, boxShadow: active ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)" : "none" }}>
                {item.label}
              </Link>
            );
          })}
        </div>
        {/* Right: user + quit */}
        <div className="flex items-stretch">
          <div className="hidden sm:flex items-center gap-2 px-4" style={{ borderLeft: `3px solid ${BORDER}` }}>
            <span className="w-2 h-2 inline-block" style={{ background: GREEN }} />
            <span className="text-[17px] text-[#aeb9cf]" style={{ fontFamily: TERM }}>{user?.email || "pioneer"}</span>
          </div>
          <button onClick={() => { localStorage.clear(); logout(); }} className="px-4 py-3 text-[9px] tracking-widest cursor-pointer transition-colors hover:text-[#ffd7d8]" style={{ fontFamily: PIXEL, color: "#e5484d", background: BG, borderLeft: `3px solid ${BORDER}` }}>
            X QUIT
          </button>
        </div>
      </header>

      {/* ══ Main scrollable content ══ */}
      <div className="flex-1 overflow-y-auto" style={{ background: "#0e131c" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "20px 20px 32px" }}>

          {/* ── Dashboard header ── */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
            <div>
              <div style={{ fontFamily: PIXEL, fontSize: 10, color: ORANGE, letterSpacing: "0.08em" }}>🛡 ARMORIQ</div>
              <div style={{ fontFamily: TERM, fontSize: 18, color: MUTED, marginTop: 4 }}>Agent Authorization Plane · org_kbz_8831</div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 8, height: 8, background: GREEN, boxShadow: `0 0 6px ${GREEN}`, display: "inline-block" }} />
                <span style={{ fontFamily: PIXEL, fontSize: 7, color: GREEN, letterSpacing: "0.06em" }}>ENFORCING</span>
              </div>
              <span style={{ fontFamily: TERM, fontSize: 16, color: DIM }}>up {fmtUptime(uptime)}</span>
            </div>
          </div>

          {/* ── Stats row ── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
            <StatCard label="TOTAL DECISIONS" value={metrics.total} sub={`${metrics.rpm} req/min`} trend={metrics.throughput} color={BLUE} />
            <StatCard label="ALLOW RATE" value={`${pct(metrics.allowed, metrics.total)}%`} sub={`${metrics.allowed} allowed`} color={GREEN} />
            <StatCard label="BLOCKED" value={metrics.denied} sub={`${pct(metrics.denied, metrics.total)}% deny rate`} color={RED} />
            <StatCard label="PENDING GATE" value={metrics.pendingApproval} sub={`P95 · ${metrics.p95}ms`} color={YELLOW} />
          </div>

          {/* ── Risk bars ── */}
          <div style={{ background: PANEL, boxShadow: `0 0 0 3px ${BORDER}`, padding: "14px 16px", marginBottom: 20 }}>
            <div style={{ fontFamily: PIXEL, fontSize: 7, color: ORANGE, letterSpacing: "0.06em", marginBottom: 14 }}>RISK DISTRIBUTION</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {(["LOW","MEDIUM","HIGH","CRITICAL"] as const).map(level => (
                <div key={level} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontFamily: PIXEL, fontSize: 6, color: RISK_COLOR[level], width: 52 }}>{level}</span>
                  <Meter value={metrics.riskCounts[level] / Math.max(metrics.total, 1)} color={RISK_COLOR[level]} />
                  <span style={{ fontFamily: TERM, fontSize: 15, color: MUTED, width: 30, textAlign: "right" }}>{metrics.riskCounts[level]}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── Tab panel ── */}
          <div style={pixelPanel}>
            {/* Tab bar */}
            <div style={{ display: "flex", background: PANEL, borderBottom: `3px solid ${BORDER}` }}>
              {TABS.map(t => {
                const active = tab === t.id;
                const badge  = t.id === "gate" && approvals.length > 0;
                return (
                  <button key={t.id} type="button" onClick={() => setTab(t.id)} style={{ flex: 1, position: "relative", fontFamily: PIXEL, fontSize: 7, letterSpacing: "0.06em", padding: "12px 6px", color: active ? "#241303" : MUTED, background: active ? ORANGE : "transparent", borderRight: `2px solid ${BORDER}`, cursor: "pointer", boxShadow: active ? "inset -3px -3px 0 rgba(0,0,0,0.25), inset 3px 3px 0 rgba(255,255,255,0.3)" : "none", whiteSpace: "nowrap" }}>
                    <span style={{ marginRight: 4 }}>{t.icon}</span>
                    {t.label}
                    {badge && <span style={{ position: "absolute", top: 8, right: 8, width: 7, height: 7, borderRadius: "50%", background: active ? "#241303" : RED, animation: "aq-blink 1.4s ease-in-out infinite" }} />}
                  </button>
                );
              })}

              {/* Live toggle for stream tab */}
              {tab === "stream" && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 12px", borderLeft: `2px solid ${BORDER}` }}>
                  <button onClick={() => setFilter(f => f === "ALL" ? "BLOCKED" : "ALL")} style={{ fontFamily: PIXEL, fontSize: 6, color: filter === "BLOCKED" ? YELLOW : DIM, background: "transparent", border: `2px solid ${filter === "BLOCKED" ? YELLOW : BORDER}`, padding: "4px 8px", cursor: "pointer" }}>
                    {filter === "BLOCKED" ? "BLOCKED" : "ALL"}
                  </button>
                  <button onClick={() => setLive(v => !v)} style={{ fontFamily: PIXEL, fontSize: 6, color: live ? GREEN : DIM, background: "transparent", border: `2px solid ${live ? GREEN : BORDER}`, padding: "4px 8px", cursor: "pointer", display: "flex", alignItems: "center", gap: 4 }}>
                    {live && <span style={{ width: 5, height: 5, borderRadius: "50%", background: GREEN, animation: "aq-blink 1s ease-in-out infinite", display: "inline-block" }} />}
                    {live ? "LIVE" : "PAUSED"}
                  </button>
                </div>
              )}
            </div>

            {/* Tab content */}
            <div style={{ padding: 16, background: BG }}>

              {/* STREAM */}
              {tab === "stream" && (
                <>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                      <thead>
                        <tr style={{ borderBottom: `3px solid ${BORDER}` }}>
                          {["STATUS","ACTION","AGENT","RESOURCE","RISK","LATENCY","TIME"].map(h => (
                            <th key={h} style={{ fontFamily: PIXEL, fontSize: 6, color: DIM, letterSpacing: "0.06em", padding: "8px 10px", textAlign: "left" }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {rows.slice(0, 40).map(d => (
                          <DecisionRow key={d.decisionId} d={d} selected={d.decisionId === selected} onSelect={() => setSelected(p => p === d.decisionId ? null : d.decisionId)} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {activeDecision && <DetailDrawer d={activeDecision} />}
                </>
              )}

              {/* PIPELINE */}
              {tab === "pipeline" && <PipelineView d={decisions[0]} />}

              {/* GATE */}
              {tab === "gate" && <ApprovalsView approvals={approvals} onResolve={resolveApproval} />}

              {/* AUDIT */}
              {tab === "audit" && (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: `3px solid ${BORDER}` }}>
                        {["TIME","AGENT","ACTION","DECISION","RISK","AUDIT REF"].map(h => (
                          <th key={h} style={{ fontFamily: PIXEL, fontSize: 6, color: DIM, letterSpacing: "0.06em", padding: "8px 10px", textAlign: "left" }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {decisions.slice(0, 60).map(d => {
                        const eff = (d.resolution?.status ?? d.status) as string;
                        const sc  = STATUS_CFG[eff] ?? { label: eff, color: MUTED, bg: RAISE };
                        return (
                          <tr key={d.decisionId} style={{ borderBottom: `2px solid ${BORDER}` }}>
                            <td style={{ fontFamily: TERM, fontSize: 14, color: DIM, padding: "8px 10px", whiteSpace: "nowrap" }}>{new Date(d.ts).toLocaleTimeString()}</td>
                            <td style={{ fontFamily: TERM, fontSize: 14, color: MUTED, padding: "8px 10px" }}>{d.agentId}</td>
                            <td style={{ fontFamily: TERM, fontSize: 14, color: TEXT, padding: "8px 10px" }}>{d.actionType}</td>
                            <td style={{ padding: "8px 10px" }}><span style={{ fontFamily: PIXEL, fontSize: 6, color: sc.color, background: sc.bg, padding: "2px 5px" }}>{sc.label}</span></td>
                            <td style={{ padding: "8px 10px" }}><span style={{ fontFamily: PIXEL, fontSize: 6, color: RISK_COLOR[d.riskLevel] ?? MUTED }}>{d.riskLevel}</span></td>
                            <td style={{ fontFamily: TERM, fontSize: 13, color: DIM, padding: "8px 10px" }}>{d.auditRef}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              {/* CONFIG */}
              {tab === "config" && <ConfigView />}
            </div>

            {/* Footer */}
            <div style={{ background: PANEL, borderTop: `3px solid ${BORDER}`, padding: "8px 16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontFamily: TERM, fontSize: 14, color: DIM }}>armoriq-sdk 2.7.1 · us-east-1</span>
              <span style={{ fontFamily: TERM, fontSize: 14, color: DIM }}>P50: {metrics.p50}ms · P95: {metrics.p95}ms · {metrics.rpm} rpm</span>
            </div>
          </div>

        </div>
      </div>

      <style>{`
        @keyframes aq-blink { 0%,100%{opacity:1} 50%{opacity:0.25} }
      `}</style>
    </div>
  );
}
