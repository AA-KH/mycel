/**
 * ArmorIQ decision engine simulation.
 *
 * Mirrors the evaluation pipeline implemented in backend/security:
 *   intent extraction -> risk classification -> policy evaluation
 *   -> ArmorIQ provider verdict -> immutable audit commit
 *
 * Enums intentionally match backend/security/models.py so the console
 * renders the same vocabulary the gateway emits.
 */

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type DecisionStatus =
  | "ALLOW"
  | "DENY"
  | "REQUIRE_APPROVAL"
  | "REQUIRE_REVIEW";

export type ActionType =
  | "LLM_CALL"
  | "TOOL_EXECUTION"
  | "AGENT_HANDOFF"
  | "ARTIFACT_ACCESS"
  | "EXTERNAL_API_CALL"
  | "EXTERNAL_MESSAGE"
  | "FILE_OPERATION"
  | "DATABASE_OPERATION"
  | "AUTONOMOUS_DECISION"
  | "DEPLOYMENT"
  | "DATA_ACCESS";

export type StageId = "intent" | "risk" | "policy" | "armoriq" | "audit";

export interface StageResult {
  id: StageId;
  label: string;
  detail: string;
  latencyMs: number;
  ok: boolean;
}

export interface DecisionRecord {
  decisionId: string;
  requestId: string;
  traceId: string;
  ts: number;
  agentId: string;
  agentLabel: string;
  actionType: ActionType;
  resource: string;
  intent: string;
  toolId: string | null;
  riskLevel: RiskLevel;
  status: DecisionStatus;
  reason: string;
  policyId: string;
  environment: "production" | "staging" | "development";
  latencyMs: number;
  stages: StageResult[];
  signals: { key: string; value: string }[];
  auditRef: string;
  /** Set once a human resolves a REQUIRE_APPROVAL decision. */
  resolution?: { by: string; status: "ALLOW" | "DENY"; ts: number };
}

/* ────────────────────────────── helpers ────────────────────────────── */

const HEX = "0123456789abcdef";

function hex(n: number): string {
  let out = "";
  for (let i = 0; i < n; i++) out += HEX[Math.floor(Math.random() * 16)];
  return out;
}

function pick<T>(arr: readonly T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}

function rand(min: number, max: number): number {
  return min + Math.random() * (max - min);
}

function randInt(min: number, max: number): number {
  return Math.floor(rand(min, max + 1));
}

/* ────────────────────────────── actors ────────────────────────────── */

const AGENTS: readonly { id: string; label: string }[] = [
  { id: "agt_orchestrator_01", label: "Orchestrator" },
  { id: "agt_backend_04", label: "Backend Eng" },
  { id: "agt_frontend_02", label: "Frontend Eng" },
  { id: "agt_devops_07", label: "DevOps" },
  { id: "agt_analyst_03", label: "Data Analyst" },
  { id: "agt_qa_05", label: "QA Runner" },
  { id: "agt_recruiter_09", label: "Recruiter" },
  { id: "agt_realestate_06", label: "RE Scout" },
];

const REVIEWERS: readonly string[] = [
  "owner@mycel.dev",
  "secops@mycel.dev",
];

/* ───────────────────────────── scenarios ───────────────────────────── */

interface Scenario {
  actionType: ActionType;
  resource: string;
  intent: string;
  toolId: string | null;
  risk: RiskLevel;
  policyId: string;
  weight: number;
}

const SCENARIOS: readonly Scenario[] = [
  {
    actionType: "LLM_CALL",
    resource: "model:claude-sonnet-4",
    intent: "Draft implementation plan for task decomposition",
    toolId: null,
    risk: "LOW",
    policyId: "pol.llm.inference.baseline",
    weight: 14,
  },
  {
    actionType: "TOOL_EXECUTION",
    resource: "tool:coder.workspace.exec",
    intent: "Run unit test suite inside sandboxed workspace",
    toolId: "coder.workspace.exec",
    risk: "MEDIUM",
    policyId: "pol.tool.exec.allowlist",
    weight: 12,
  },
  {
    actionType: "FILE_OPERATION",
    resource: "fs:/workspace/src/components",
    intent: "Write generated component to project source tree",
    toolId: "fs.write",
    risk: "LOW",
    policyId: "pol.fs.scope.workspace",
    weight: 11,
  },
  {
    actionType: "AGENT_HANDOFF",
    resource: "agent:agt_qa_05",
    intent: "Delegate verification subtask to QA runner",
    toolId: null,
    risk: "LOW",
    policyId: "pol.handoff.capability.match",
    weight: 9,
  },
  {
    actionType: "DATA_ACCESS",
    resource: "table:employees",
    intent: "Read roster metadata to resolve agent capabilities",
    toolId: "db.select",
    risk: "MEDIUM",
    policyId: "pol.data.read.tenant_scoped",
    weight: 9,
  },
  {
    actionType: "EXTERNAL_API_CALL",
    resource: "api:github.com/repos",
    intent: "Open pull request against feature branch",
    toolId: "github.pr.create",
    risk: "MEDIUM",
    policyId: "pol.egress.domain.allowlist",
    weight: 8,
  },
  {
    actionType: "ARTIFACT_ACCESS",
    resource: "artifact:build/dist.tar.gz",
    intent: "Fetch prior build artifact for regression diff",
    toolId: null,
    risk: "LOW",
    policyId: "pol.artifact.read.same_objective",
    weight: 7,
  },
  {
    actionType: "DATABASE_OPERATION",
    resource: "table:api_keys",
    intent: "Rotate stale integration credential row",
    toolId: "db.update",
    risk: "HIGH",
    policyId: "pol.db.write.secrets_guard",
    weight: 5,
  },
  {
    actionType: "EXTERNAL_MESSAGE",
    resource: "channel:slack#general",
    intent: "Post build status summary to shared channel",
    toolId: "slack.postMessage",
    risk: "MEDIUM",
    policyId: "pol.egress.message.review",
    weight: 5,
  },
  {
    actionType: "DEPLOYMENT",
    resource: "env:production",
    intent: "Promote release candidate to production",
    toolId: "deploy.promote",
    risk: "CRITICAL",
    policyId: "pol.deploy.prod.human_gate",
    weight: 4,
  },
  {
    actionType: "AUTONOMOUS_DECISION",
    resource: "budget:wallet.spend",
    intent: "Authorize compute spend above soft ceiling",
    toolId: null,
    risk: "HIGH",
    policyId: "pol.autonomy.spend.ceiling",
    weight: 4,
  },
  {
    actionType: "DATA_ACCESS",
    resource: "table:audit_events",
    intent: "Bulk export decision history outside tenant scope",
    toolId: "db.export",
    risk: "CRITICAL",
    policyId: "pol.data.exfil.blocklist",
    weight: 3,
  },
  {
    actionType: "FILE_OPERATION",
    resource: "fs:/etc/ssh/authorized_keys",
    intent: "Append public key to host trust store",
    toolId: "fs.write",
    risk: "CRITICAL",
    policyId: "pol.fs.scope.workspace",
    weight: 2,
  },
];

const WEIGHT_TOTAL = SCENARIOS.reduce((s, x) => s + x.weight, 0);

function pickScenario(): Scenario {
  let r = Math.random() * WEIGHT_TOTAL;
  for (const s of SCENARIOS) {
    r -= s.weight;
    if (r <= 0) return s;
  }
  return SCENARIOS[0];
}

/* ─────────────────────────── verdict logic ─────────────────────────── */

const REASONS: Record<DecisionStatus, readonly string[]> = {
  ALLOW: [
    "Intent consistent with declared objective; within capability grant",
    "Actor trust score above threshold; resource in allowlist",
    "Action scoped to workspace; no egress boundary crossed",
    "Behavioral baseline match; no anomaly signal raised",
  ],
  DENY: [
    "Resource outside tenant boundary; exfiltration pattern matched",
    "Requested scope exceeds capability grant for actor",
    "Target path is host-protected; write blocked by policy",
    "Intent diverges from task objective; possible injection",
  ],
  REQUIRE_APPROVAL: [
    "Irreversible action on production surface; human gate required",
    "Spend exceeds autonomous ceiling; owner approval required",
    "Secret-bearing table write; second-party confirmation required",
    "Outbound message to external audience; review required",
  ],
  REQUIRE_REVIEW: [
    "Novel tool invocation; queued for asynchronous review",
    "Low-confidence intent classification; flagged for review",
  ],
};

function verdictFor(risk: RiskLevel): DecisionStatus {
  const r = Math.random();
  switch (risk) {
    case "LOW":
      return r < 0.97 ? "ALLOW" : "REQUIRE_REVIEW";
    case "MEDIUM":
      if (r < 0.86) return "ALLOW";
      if (r < 0.95) return "REQUIRE_APPROVAL";
      return r < 0.98 ? "REQUIRE_REVIEW" : "DENY";
    case "HIGH":
      if (r < 0.18) return "ALLOW";
      if (r < 0.74) return "REQUIRE_APPROVAL";
      return "DENY";
    case "CRITICAL":
      return r < 0.42 ? "REQUIRE_APPROVAL" : "DENY";
  }
}

function buildSignals(risk: RiskLevel, status: DecisionStatus) {
  const hostile = status === "DENY";
  const intentScore = hostile ? rand(0.24, 0.58) : rand(0.86, 0.99);
  const anomaly = hostile
    ? rand(0.61, 0.94)
    : risk === "HIGH" || risk === "CRITICAL"
      ? rand(0.22, 0.52)
      : rand(0.01, 0.16);
  const trust = hostile ? rand(0.31, 0.62) : rand(0.72, 0.97);
  return [
    { key: "intent.consistency", value: intentScore.toFixed(2) },
    { key: "anomaly.score", value: anomaly.toFixed(2) },
    { key: "actor.trust", value: trust.toFixed(2) },
    { key: "capability.match", value: hostile ? "partial" : "exact" },
    { key: "blast.radius", value: risk === "CRITICAL" ? "tenant" : risk === "HIGH" ? "objective" : "task" },
  ];
}

function buildStages(
  scenario: Scenario,
  risk: RiskLevel,
  status: DecisionStatus,
  reason: string,
): StageResult[] {
  const denied = status === "DENY";
  return [
    {
      id: "intent",
      label: "INTENT EXTRACT",
      detail: `classified as ${scenario.actionType}`,
      latencyMs: Math.round(rand(7, 21)),
      ok: true,
    },
    {
      id: "risk",
      label: "RISK CLASSIFY",
      detail: `risk=${risk}`,
      latencyMs: Math.round(rand(2, 6)),
      ok: true,
    },
    {
      id: "policy",
      label: "POLICY EVAL",
      detail: `matched ${scenario.policyId}`,
      latencyMs: Math.round(rand(1, 5)),
      ok: !denied,
    },
    {
      id: "armoriq",
      label: "ARMORIQ VERDICT",
      detail: `${status} — ${reason.slice(0, 34)}…`,
      latencyMs: Math.round(rand(38, 174)),
      ok: !denied,
    },
    {
      id: "audit",
      label: "AUDIT COMMIT",
      detail: "appended to immutable log",
      latencyMs: Math.round(rand(3, 9)),
      ok: true,
    },
  ];
}

/** Generate a single decision as the gateway would emit it. */
export function generateDecision(tsOverride?: number): DecisionRecord {
  const scenario = pickScenario();
  const agent = pick(AGENTS);
  const risk = scenario.risk;
  const status = verdictFor(risk);
  const reason = pick(REASONS[status]);
  const stages = buildStages(scenario, risk, status, reason);
  const latencyMs = stages.reduce((s, x) => s + x.latencyMs, 0);

  return {
    decisionId: `dec_${hex(10)}`,
    requestId: `req_${hex(10)}`,
    traceId: `trc_${hex(16)}`,
    ts: tsOverride ?? Date.now(),
    agentId: agent.id,
    agentLabel: agent.label,
    actionType: scenario.actionType,
    resource: scenario.resource,
    intent: scenario.intent,
    toolId: scenario.toolId,
    riskLevel: risk,
    status,
    reason,
    policyId: scenario.policyId,
    environment:
      scenario.resource === "env:production"
        ? "production"
        : Math.random() < 0.68
          ? "production"
          : "staging",
    latencyMs,
    stages,
    signals: buildSignals(risk, status),
    auditRef: `aud_${hex(12)}`,
  };
}

/** Backfill so the console never renders an empty stream on mount. */
export function seedDecisions(count: number): DecisionRecord[] {
  const now = Date.now();
  const out: DecisionRecord[] = [];
  for (let i = count - 1; i >= 0; i--) {
    out.push(generateDecision(now - i * randInt(900, 2400)));
  }
  return out;
}

export function nextReviewer(): string {
  return pick(REVIEWERS);
}

/* ─────────────────────────── static config ─────────────────────────── */

export interface ConfigRow {
  key: string;
  value: string;
  kind?: "secret" | "ok" | "warn" | "plain";
  note?: string;
}

export const CONFIG_GROUPS: readonly {
  title: string;
  icon: string;
  rows: readonly ConfigRow[];
}[] = [
  {
    title: "CONNECTION",
    icon: "🔌",
    rows: [
      { key: "ARMORIQ_ENDPOINT", value: "https://gateway.armoriq.io/v2", kind: "plain" },
      { key: "ARMORIQ_REGION", value: "us-east-1 (primary) · eu-west-1 (failover)", kind: "plain" },
      { key: "ARMORIQ_API_KEY", value: "aiq_live_sk_•••••••••••••••••4f2a", kind: "secret", note: "rotated 6d ago" },
      { key: "ARMORIQ_TIMEOUT_MS", value: "5000", kind: "plain" },
      { key: "TRANSPORT", value: "TLS 1.3 · mTLS pinned", kind: "ok" },
      { key: "CERT_FINGERPRINT", value: "SHA256:9c:41:b7:e0:2d:8a:66:f3", kind: "plain" },
    ],
  },
  {
    title: "ENFORCEMENT",
    icon: "🛡",
    rows: [
      { key: "MODE", value: "ENFORCE (blocking)", kind: "ok" },
      { key: "FAIL_MODE", value: "fail-closed on HIGH / CRITICAL", kind: "ok" },
      { key: "DEFAULT_DENY", value: "true", kind: "ok" },
      { key: "HUMAN_GATE", value: "DEPLOYMENT · AUTONOMOUS_DECISION", kind: "plain" },
      { key: "SANDBOX_EGRESS", value: "domain allowlist (12 entries)", kind: "plain" },
      { key: "SHADOW_EVAL", value: "disabled", kind: "warn", note: "enable for policy dry-runs" },
    ],
  },
  {
    title: "POLICY BUNDLE",
    icon: "📜",
    rows: [
      { key: "BUNDLE_ID", value: "mycel-core@2026.08.3", kind: "plain" },
      { key: "SIGNATURE", value: "verified · cosign", kind: "ok" },
      { key: "RULES_LOADED", value: "148 active · 6 deprecated", kind: "plain" },
      { key: "LAST_SYNC", value: "42s ago", kind: "ok" },
      { key: "DRIFT_CHECK", value: "no drift detected", kind: "ok" },
    ],
  },
  {
    title: "AUDIT & TELEMETRY",
    icon: "🧾",
    rows: [
      { key: "AUDIT_SINK", value: "append-only · hash-chained", kind: "ok" },
      { key: "CHAIN_HEAD", value: "0x8f3a…c1d9 (height 284,113)", kind: "plain" },
      { key: "RETENTION", value: "400 days", kind: "plain" },
      { key: "PII_REDACTION", value: "payloads stripped pre-egress", kind: "ok" },
      { key: "WEBHOOK", value: "POST /api/security/armoriq/events", kind: "plain" },
      { key: "SDK_VERSION", value: "armoriq-sdk 2.7.1 (python)", kind: "plain" },
    ],
  },
];

export const BOOT_LINES: readonly string[] = [
  "resolving gateway.armoriq.io … 34ms",
  "TLS 1.3 handshake · mTLS client cert accepted",
  "authenticating aiq_live_sk_••••4f2a … ok",
  "tenant org_kbz_8831 bound · scope=agent-authz",
  "policy bundle mycel-core@2026.08.3 · signature verified",
  "148 rules compiled · 0 conflicts",
  "audit chain head 0x8f3a…c1d9 verified",
  "enforcement mode ENFORCE · fail-closed armed",
  "authorization plane ready",
];
