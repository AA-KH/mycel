import { useState } from "react";
import { BOOT_LINES, CONFIG_GROUPS, type ConfigRow } from "@/lib/armoriq/engine";
import { C, Card, CardHead, LedDot, PIXEL, PixelButton, TERM } from "./primitives";

const KIND_COLOR: Record<NonNullable<ConfigRow["kind"]>, string> = {
  ok: C.green,
  warn: C.yellow,
  secret: C.cyan,
  plain: C.text,
};

function Row({ row, revealed }: { row: ConfigRow; revealed: boolean }) {
  const kind = row.kind ?? "plain";
  const isSecret = kind === "secret";
  const value =
    isSecret && revealed
      ? row.value.replace(/•+/, "sk_7c41f9b2ea8d0356")
      : row.value;

  return (
    <div
      className="flex flex-col gap-0.5 py-1.5"
      style={{ borderBottom: `2px solid ${C.border}` }}
    >
      <div className="flex items-baseline justify-between gap-3">
        <span
          className="text-[13px] shrink-0"
          style={{ fontFamily: TERM, color: C.dim }}
        >
          {row.key}
        </span>
        <span
          className="text-[14px] text-right break-all"
          style={{ fontFamily: TERM, color: KIND_COLOR[kind] }}
        >
          {kind === "ok" && "✓ "}
          {kind === "warn" && "⚠ "}
          {value}
        </span>
      </div>
      {row.note && (
        <span
          className="text-[13px] text-right"
          style={{ fontFamily: TERM, color: C.dim }}
        >
          {row.note}
        </span>
      )}
    </div>
  );
}

export default function ConfigPanel({ bootStep }: { bootStep: number }) {
  const [revealed, setRevealed] = useState(false);
  const visibleBoot = BOOT_LINES.slice(0, Math.min(bootStep, BOOT_LINES.length));
  const booted = bootStep >= BOOT_LINES.length;

  return (
    <div className="flex flex-col gap-3">
      {/* ── handshake log ── */}
      <Card>
        <CardHead
          icon="🔐"
          title="PROVIDER HANDSHAKE"
          right={
            <div className="flex items-center gap-2">
              <LedDot color={booted ? C.green : C.yellow} pulse={!booted} />
              <span
                className="text-[7px] tracking-widest"
                style={{ fontFamily: PIXEL, color: booted ? C.green : C.yellow }}
              >
                {booted ? "ESTABLISHED" : "NEGOTIATING"}
              </span>
            </div>
          }
        />
        <div className="px-3 py-2.5" style={{ background: "#080b11" }}>
          {visibleBoot.map((line, i) => (
            <div
              key={i}
              className="text-[14px] leading-snug flex gap-1.5"
              style={{ fontFamily: TERM }}
            >
              <span style={{ color: C.green }}>[ok]</span>
              <span style={{ color: C.muted }}>{line}</span>
            </div>
          ))}
          {!booted && (
            <div className="text-[14px] leading-snug" style={{ fontFamily: TERM, color: C.orange }}>
              <span className="aq-pulse">▌</span>
            </div>
          )}
        </div>
      </Card>

      {/* ── config groups ── */}
      {CONFIG_GROUPS.map(group => (
        <Card key={group.title}>
          <CardHead
            icon={group.icon}
            title={group.title}
            right={
              group.title === "CONNECTION" ? (
                <PixelButton
                  size="sm"
                  color={revealed ? C.red : C.blue}
                  textColor="#eceff4"
                  onClick={() => setRevealed(r => !r)}
                >
                  {revealed ? "HIDE KEY" : "REVEAL KEY"}
                </PixelButton>
              ) : undefined
            }
          />
          <div className="px-3 py-1.5">
            {group.rows.map(row => (
              <Row key={row.key} row={row} revealed={revealed} />
            ))}
          </div>
        </Card>
      ))}

      {/* ── integration snippet ── */}
      <Card>
        <CardHead icon="🧩" title="GATEWAY BINDING" />
        <div className="px-3 py-2.5 overflow-x-auto" style={{ background: "#080b11" }}>
          <pre
            className="text-[14px] leading-tight"
            style={{ fontFamily: TERM, color: C.muted }}
          >
{`# backend/security/providers/armoriq.py
client = ArmorIQClient(
    api_key=settings.armoriq_api_key,
    timeout=settings.armoriq_timeout_ms / 1000.0,
)

decision = gateway.evaluate(SecurityRequest(
    context=SecurityContext(
        organization_id="org_kbz_8831",
        agent_id=agent.id,
        capabilities=agent.capabilities,
        environment="production",
    ),
    action_type=ActionType.TOOL_EXECUTION,
    resource=tool.uri,
    intent=task.objective,
))

if decision.status is not SecurityDecisionStatus.ALLOW:
    raise SecurityViolation(decision.reason)`}
          </pre>
        </div>
        <div
          className="px-3 py-2 text-[13px]"
          style={{ fontFamily: TERM, color: C.dim, borderTop: `3px solid ${C.border}` }}
        >
          every agent action routes through this gateway before execution
        </div>
      </Card>
    </div>
  );
}
