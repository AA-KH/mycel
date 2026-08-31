import type { ArmorIQMetrics } from "@/lib/armoriq/useArmorIQ";
import type { RiskLevel } from "@/lib/armoriq/engine";
import { C, Card, CardHead, Meter, PIXEL, RISK_COLOR, TERM } from "./primitives";

function Stat({
  label,
  value,
  color,
  suffix,
}: {
  label: string;
  value: string;
  color: string;
  suffix?: string;
}) {
  return (
    <div
      className="flex flex-col gap-1 px-2.5 py-2"
      style={{ boxShadow: `inset 0 0 0 2px ${C.border}`, background: "#0e121b" }}
    >
      <span
        className="text-[6px] tracking-widest"
        style={{ fontFamily: PIXEL, color: C.dim }}
      >
        {label}
      </span>
      <span className="flex items-baseline gap-1">
        <span
          className="text-[22px] leading-none"
          style={{ fontFamily: TERM, color }}
        >
          {value}
        </span>
        {suffix && (
          <span
            className="text-[13px] leading-none"
            style={{ fontFamily: TERM, color: C.dim }}
          >
            {suffix}
          </span>
        )}
      </span>
    </div>
  );
}

const RISKS: RiskLevel[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function MetricsStrip({ metrics }: { metrics: ArmorIQMetrics }) {
  const peak = Math.max(1, ...metrics.throughput);

  return (
    <Card>
      <CardHead
        icon="📊"
        title="AUTHORIZATION THROUGHPUT"
        right={
          <span
            className="text-[13px] tracking-wide"
            style={{ fontFamily: TERM, color: C.muted }}
          >
            {metrics.rpm} req/min
          </span>
        }
      />

      <div className="p-3 flex flex-col gap-3">
        {/* ── sparkline ── */}
        <div
          className="flex items-end gap-[2px] h-14 px-2 py-1.5"
          style={{ background: "#080b11", boxShadow: `inset 0 0 0 2px ${C.border}` }}
          role="img"
          aria-label={`Request throughput over the last ${metrics.throughput.length * 2} seconds`}
        >
          {metrics.throughput.map((v, i) => {
            const h = Math.max(6, (v / peak) * 100);
            const isLast = i === metrics.throughput.length - 1;
            return (
              <div
                key={i}
                className="flex-1 transition-all duration-300"
                style={{
                  height: `${h}%`,
                  background: isLast ? C.orange : C.blue,
                  opacity: isLast ? 1 : 0.45 + (i / metrics.throughput.length) * 0.55,
                }}
              />
            );
          })}
        </div>

        {/* ── stat tiles ── */}
        <div className="grid grid-cols-4 gap-2">
          <Stat
            label="ALLOW"
            value={`${(metrics.allowRate * 100).toFixed(1)}`}
            suffix="%"
            color={C.green}
          />
          <Stat label="DENIED" value={String(metrics.denied)} color={C.red} />
          <Stat
            label="GATED"
            value={String(metrics.pendingApproval)}
            color={C.orange}
          />
          <Stat
            label="P95"
            value={String(metrics.p95)}
            suffix="ms"
            color={C.cyan}
          />
        </div>

        {/* ── risk distribution ── */}
        <div className="flex flex-col gap-1.5 pt-0.5">
          <span
            className="text-[6px] tracking-widest"
            style={{ fontFamily: PIXEL, color: C.dim }}
          >
            RISK DISTRIBUTION · WINDOW {metrics.total}
          </span>
          {RISKS.map(r => {
            const n = metrics.riskCounts[r];
            const frac = metrics.total ? n / metrics.total : 0;
            return (
              <div key={r} className="flex items-center gap-2">
                <span
                  className="text-[13px] w-[62px] shrink-0"
                  style={{ fontFamily: TERM, color: RISK_COLOR[r] }}
                >
                  {r}
                </span>
                <div className="flex-1">
                  <Meter value={frac} color={RISK_COLOR[r]} height={7} />
                </div>
                <span
                  className="text-[13px] w-7 text-right shrink-0"
                  style={{ fontFamily: TERM, color: C.muted }}
                >
                  {n}
                </span>
              </div>
            );
          })}
        </div>

        <div
          className="flex items-center justify-between pt-1"
          style={{ borderTop: `2px solid ${C.border}` }}
        >
          <span className="text-[13px]" style={{ fontFamily: TERM, color: C.dim }}>
            p50 {metrics.p50}ms · p95 {metrics.p95}ms
          </span>
          <span className="text-[13px]" style={{ fontFamily: TERM, color: C.dim }}>
            {metrics.review} queued for review
          </span>
        </div>
      </div>
    </Card>
  );
}
