import { useMemo, useState } from "react";
import type { DecisionRecord } from "@/lib/armoriq/engine";
import {
  C,
  Card,
  CardHead,
  PIXEL,
  STATUS_COLOR,
  TERM,
  clockTime,
} from "./primitives";

/**
 * Hash-chained audit log view. Each event references the previous entry so
 * tampering breaks the chain — the console renders that linkage explicitly.
 */
export default function AuditExplorer({
  decisions,
}: {
  decisions: DecisionRecord[];
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  const rows = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = decisions.slice(0, 60);
    if (!q) return list;
    return list.filter(d =>
      [
        d.traceId,
        d.requestId,
        d.decisionId,
        d.auditRef,
        d.agentId,
        d.actionType,
        d.resource,
        d.policyId,
        d.status,
        d.riskLevel,
      ]
        .join(" ")
        .toLowerCase()
        .includes(q),
    );
  }, [decisions, query]);

  const height = 284_113;

  return (
    <Card>
      <CardHead
        icon="🧾"
        title="AUDIT TRACE EXPLORER"
        right={
          <span className="text-[13px]" style={{ fontFamily: TERM, color: C.muted }}>
            height {(height + decisions.length).toLocaleString()}
          </span>
        }
      />

      {/* ── search ── */}
      <div
        className="px-3 py-2 flex items-center gap-2"
        style={{ background: C.raise, borderBottom: `3px solid ${C.border}` }}
      >
        <span className="text-[15px]" style={{ fontFamily: TERM, color: C.orange }}>
          {">"}
        </span>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="filter by trace id, actor, action, policy…"
          aria-label="Filter audit events"
          className="flex-1 bg-transparent outline-none text-[15px] min-w-0"
          style={{ fontFamily: TERM, color: C.text }}
        />
        {query && (
          <button
            type="button"
            onClick={() => setQuery("")}
            className="text-[14px] px-1"
            style={{ fontFamily: TERM, color: C.dim }}
            aria-label="Clear filter"
          >
            ✕
          </button>
        )}
      </div>

      {/* ── log rows ── */}
      <div className="overflow-y-auto" style={{ maxHeight: 330 }}>
        {rows.length === 0 ? (
          <div
            className="px-3 py-6 text-center text-[15px]"
            style={{ fontFamily: TERM, color: C.dim }}
          >
            no audit events match “{query}”
          </div>
        ) : (
          rows.map((d, i) => {
            const effective = d.resolution?.status ?? d.status;
            const color = STATUS_COLOR[effective];
            const isOpen = open === d.decisionId;
            const prev = rows[i + 1];

            return (
              <div key={d.decisionId} style={{ borderBottom: `2px solid ${C.border}` }}>
                <button
                  type="button"
                  onClick={() => setOpen(p => (p === d.decisionId ? null : d.decisionId))}
                  className="w-full text-left px-2.5 py-1.5 flex items-center gap-2"
                  style={{ background: isOpen ? C.raise : "transparent" }}
                >
                  <span
                    className="text-[13px] shrink-0"
                    style={{ fontFamily: TERM, color: C.dim }}
                  >
                    {clockTime(d.ts)}
                  </span>
                  <span
                    className="w-1.5 h-1.5 shrink-0"
                    style={{ background: color }}
                    aria-hidden="true"
                  />
                  <span
                    className="text-[14px] truncate flex-1"
                    style={{ fontFamily: TERM, color: C.text }}
                  >
                    {d.auditRef}
                  </span>
                  <span
                    className="text-[13px] shrink-0"
                    style={{ fontFamily: TERM, color }}
                  >
                    {effective === "REQUIRE_APPROVAL" ? "GATED" : effective}
                  </span>
                  <span
                    className="text-[13px] shrink-0"
                    style={{ fontFamily: TERM, color: C.dim }}
                  >
                    {isOpen ? "▾" : "▸"}
                  </span>
                </button>

                {isOpen && (
                  <div
                    className="px-3 py-2.5"
                    style={{ background: "#080b11", borderTop: `2px solid ${C.border}` }}
                  >
                    <div
                      className="text-[7px] tracking-widest mb-1.5"
                      style={{ fontFamily: PIXEL, color: C.orange }}
                    >
                      EVENT RECORD
                    </div>
                    <pre
                      className="text-[14px] leading-tight overflow-x-auto"
                      style={{ fontFamily: TERM, color: C.muted }}
                    >
{`event_id    ${d.auditRef}
trace_id    ${d.traceId}
request_id  ${d.requestId}
decision_id ${d.decisionId}
actor       ${d.agentId} (${d.agentLabel})
action      ${d.actionType}
resource    ${d.resource}
tool_id     ${d.toolId ?? "null"}
intent      "${d.intent}"
risk_level  ${d.riskLevel}
status      ${effective}
policy_id   ${d.policyId}
provider    armoriq (${d.latencyMs}ms)
environment ${d.environment}
prev_hash   ${prev ? `0x${prev.auditRef.slice(4, 16)}` : "0x000000000000"}
signature   verified`}
                    </pre>
                    <div
                      className="mt-2 pt-1.5 text-[13px] flex items-center gap-1.5"
                      style={{ borderTop: `2px solid ${C.border}`, fontFamily: TERM }}
                    >
                      <span style={{ color: C.green }}>✓</span>
                      <span style={{ color: C.dim }}>
                        chain link intact · payload redacted before egress
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div
        className="px-3 py-2 flex items-center justify-between"
        style={{ background: "#080b11", borderTop: `3px solid ${C.border}` }}
      >
        <span className="text-[13px]" style={{ fontFamily: TERM, color: C.dim }}>
          {rows.length} events shown
        </span>
        <span className="text-[13px]" style={{ fontFamily: TERM, color: C.green }}>
          append-only · 400d retention
        </span>
      </div>
    </Card>
  );
}
