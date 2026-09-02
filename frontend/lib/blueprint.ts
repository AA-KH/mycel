/**
 * The final supply-network architecture produced by the mission.
 * Shared by the Blueprint tab (visual flow) and the Architect chatbot
 * (system-prompt context) so both always describe the same network.
 */

export type BlueprintNode = {
  id: string
  stage: string
  name: string
  meta: string[]
  share?: string
  risk?: 'low' | 'medium' | 'high'

  location?: string

  function?: string

  detail?: { label: string; value: string }[]
  /** Fallback plan if this node degrades or fails. */
  fallback?: string
  /** Downstream node ids. Defaults to every node in the next stage. */
  flowsTo?: string[]
  /** Label drawn on the outgoing edges of this node. */
  flowLabel?: string
}

export type BlueprintStage = {
  id: string
  label: string
  owner: string
  /** The question this layer of the network answers. */
  question?: string
  nodes: BlueprintNode[]
}

export const BLUEPRINT_STAGES: BlueprintStage[] = [
  {
    id: 'suppliers',
    label: 'Tier-1 Suppliers',
    owner: 'Ravi · Dev',
    question: 'Who feeds the network?',
    nodes: [
      {
        id: 'sup-a', stage: 'suppliers', name: 'Supplier A', share: '60%', risk: 'medium',
        location: 'Germany',
        function: 'Primary source — lowest landed cost, carries the base volume.',
        flowLabel: '60% · 21d',
        meta: ['Primary — lowest landed cost', 'Lead time 21 days', 'Landed ₹9.70 / unit', 'VERIFIED'],
        detail: [
          { label: 'Allocation', value: '60% of annual volume (60k units)' },
          { label: 'Landed cost', value: '₹9.70 / unit — ₹8.20 unit + ₹0.80 freight + ₹0.40 duty + ₹0.30 carry' },
          { label: 'Lead time', value: '21 days ± 4 days variability' },
          { label: 'Capacity', value: '95k units / yr — headroom at high-demand scenario' },
          { label: 'Certifications', value: 'ISO 9001, ISO 14001 (VERIFIED)' },
          { label: 'Exposure', value: 'Single-country dependency; tariff-sensitive lane' },
        ],
        fallback: 'On outage > 72h, Supplier B absorbs 40% and Supplier C steps to 25%; Central DC releases safety stock.',
      },
      {
        id: 'sup-b', stage: 'suppliers', name: 'Supplier B', share: '25%', risk: 'low',
        location: 'Vietnam',
        function: 'Geographic hedge against the primary lane, shortest lead time.',
        flowLabel: '25% · 14d',
        meta: ['Geographic diversification', 'Lead time 14 days', 'Landed ₹10.40 / unit', 'VERIFIED'],
        detail: [
          { label: 'Allocation', value: '25% of annual volume (25k units)' },
          { label: 'Landed cost', value: '₹10.40 / unit — +7.2% vs Supplier A' },
          { label: 'Lead time', value: '14 days ± 2 days — fastest lane in the network' },
          { label: 'Capacity', value: '45k units / yr — can surge to 40% allocation' },
          { label: 'Certifications', value: 'ISO 9001 (VERIFIED)' },
          { label: 'Strategic role', value: 'Different geopolitical bloc from A — decorrelated risk' },
        ],
        fallback: 'Volume reverts to Supplier A within one order cycle; no safety-stock release required.',
      },
      {
        id: 'sup-c', stage: 'suppliers', name: 'Supplier C', share: '15%', risk: 'low',
        location: 'India · domestic',
        function: 'Qualified contingency held at low allocation to stay warm.',
        flowLabel: '15% · 18d',
        meta: ['Qualified contingency', 'Lead time 18 days', 'Landed ₹10.90 / unit', 'ESTIMATED'],
        detail: [
          { label: 'Allocation', value: '15% of annual volume (15k units)' },
          { label: 'Landed cost', value: '₹10.90 / unit (ESTIMATED — no public quote)' },
          { label: 'Lead time', value: '18 days — domestic, no customs exposure' },
          { label: 'Capacity', value: '30k units / yr (ESTIMATED)' },
          { label: 'Why held warm', value: 'A qualified supplier at 0% takes 60+ days to reactivate' },
          { label: 'Open action', value: 'Requires commercial negotiation — see Phase 5' },
        ],
        fallback: 'Lowest-consequence node: A and B jointly cover its volume with zero stockout days.',
      },
    ],
  },
  {
    id: 'manufacturing',
    label: 'Manufacturing',
    owner: 'Aanya · Nisha',
    question: 'Where is value added?',
    nodes: [
      {
        id: 'mfg-1', stage: 'manufacturing', name: 'Primary Plant', risk: 'medium',
        location: 'India · West',
        function: 'Single conversion point where all three inbound streams are pooled.',
        flowLabel: '100k / yr',
        flowsTo: ['wh-1', 'wh-2'],
        meta: ['Capacity 140k units / yr', 'Utilization 71% at base demand', 'Dual inbound lanes'],
        detail: [
          { label: 'Capacity', value: '140k units / yr — 40% headroom over base demand' },
          { label: 'Utilization', value: '71% at base (100k) · 100% at high scenario (180k) → constraint' },
          { label: 'Inbound', value: 'Dual qualified lanes; no single inbound dependency' },
          { label: 'Bottleneck', value: 'Becomes the binding constraint above 140k units — flagged by Nisha' },
          { label: 'Concentration', value: 'Only conversion node in the network — highest structural exposure' },
        ],
        fallback: 'No alternate plant qualified. Continuity relies on 30-day Central DC cover plus demand allocation.',
      },
    ],
  },
  {
    id: 'warehousing',
    label: 'Warehousing',
    owner: 'Tara · Kabir',
    question: 'Where does inventory rest?',
    nodes: [
      {
        id: 'wh-1', stage: 'warehousing', name: 'Central DC', risk: 'low',
        location: 'India · West',
        function: 'Main inventory pool and the network\u2019s primary shock absorber.',
        flowLabel: '78% volume',
        meta: ['Safety stock 30 days', 'Reorder point 18 days demand', 'Covers 12 demand clusters'],
        detail: [
          { label: 'Safety stock', value: '30 days of base demand (~8.2k units)' },
          { label: 'Reorder point', value: '18 days of demand — covers Supplier B lead time outright' },
          { label: 'Coverage', value: 'All 12 demand clusters; 78% of dispatch volume' },
          { label: 'Carrying cost', value: '₹0.30 / unit / cycle — the price paid for resilience' },
          { label: 'Role in stress tests', value: 'Absorbs Supplier A outage for 30 days with zero stockout days' },
        ],
        fallback: 'Regional Buffer takes the top-3 clusters while inbound is re-routed.',
      },
      {
        id: 'wh-2', stage: 'warehousing', name: 'Regional Buffer', risk: 'low',
        location: 'India · North',
        function: 'Standby node that de-risks the Central DC and the primary lanes.',
        flowLabel: '22% volume',
        meta: ['Safety stock 12 days', 'Activated on lane disruption', 'Serves top-3 clusters'],
        detail: [
          { label: 'Safety stock', value: '12 days of base demand (~3.3k units)' },
          { label: 'Trigger', value: 'Activated on Central DC outage or primary-lane disruption' },
          { label: 'Coverage', value: 'Top-3 demand clusters — 22% of dispatch volume' },
          { label: 'Status', value: 'Requires validation — site not yet contracted (Phase 3)' },
        ],
        fallback: 'Central DC serves all clusters at +3 days average transit.',
      },
    ],
  },
  {
    id: 'distribution',
    label: 'Distribution',
    owner: 'Kabir',
    question: 'How does product move?',
    nodes: [
      {
        id: 'dist-1', stage: 'distribution', name: 'Primary Lanes', risk: 'medium',
        location: '22 routes',
        function: 'Outbound transport layer connecting both warehouses to demand.',
        flowLabel: '\u2264 21d fulfillment',
        meta: ['22 routes priced', 'Cheapest lane 18% under benchmark', '2 high-risk lanes flagged with alternates'],
        detail: [
          { label: 'Routes', value: '22 lanes priced and transit-timed by Kabir' },
          { label: 'Cost position', value: 'Cheapest qualified lane sits 18% under industry benchmark' },
          { label: 'Risk flags', value: '2 lanes flagged high-risk (port + monsoon exposure)' },
          { label: 'Mitigation', value: 'Every flagged lane has a priced alternate and a mode switch' },
          { label: 'Service level', value: 'Meets ≤ 21-day fulfillment on 20 of 22 lanes' },
        ],
        fallback: 'Mode switch to air on the 2 flagged lanes: +₹1.10 / unit, transit held under 21 days.',
      },
    ],
  },
  {
    id: 'customers',
    label: 'Customers',
    owner: 'Mira',
    question: 'Who is being served?',
    nodes: [
      {
        id: 'cust-1', stage: 'customers', name: '12 Demand Clusters', risk: 'low',
        location: 'India · national',
        function: 'The demand the whole network is sized against.',
        meta: ['Base 100k units / yr', 'Low 70k · High 180k', 'Fulfillment ≤ 21 days'],
        detail: [
          { label: 'Base demand', value: '100k units / yr' },
          { label: 'Scenario range', value: 'Low 70k · High 180k — high case exceeds plant capacity' },
          { label: 'Geography', value: '12 clusters; top-3 carry 46% of volume' },
          { label: 'Service promise', value: 'Fulfillment within 21 days' },
          { label: 'Volatility', value: 'Seasonal peak concentrated in 2 quarters — drives buffer sizing' },
        ],
        fallback: 'High-demand case is served by surging Supplier B and adding a second shift at the plant.',
      },
    ],
  },
]

/** Flat lookup of every node in the network. */
export const BLUEPRINT_NODES: BlueprintNode[] = BLUEPRINT_STAGES.flatMap((s) => s.nodes)

export function findNode(id: string): BlueprintNode | undefined {
  return BLUEPRINT_NODES.find((n) => n.id === id)
}

export function findStage(stageId: string): BlueprintStage | undefined {
  return BLUEPRINT_STAGES.find((s) => s.id === stageId)
}

/** Downstream node ids for a node — defaults to every node in the next stage. */
export function downstreamIds(node: BlueprintNode): string[] {
  if (node.flowsTo?.length) return node.flowsTo
  const i = BLUEPRINT_STAGES.findIndex((s) => s.id === node.stage)
  return BLUEPRINT_STAGES[i + 1]?.nodes.map((n) => n.id) ?? []
}

/** Upstream node ids for a node. */
export function upstreamIds(node: BlueprintNode): string[] {
  return BLUEPRINT_NODES.filter((n) => downstreamIds(n).includes(node.id)).map((n) => n.id)
}

/** Every directed edge in the network. */
export type BlueprintEdge = { from: string; to: string; label?: string }

export const BLUEPRINT_EDGES: BlueprintEdge[] = BLUEPRINT_NODES.flatMap((n) =>
  downstreamIds(n).map((to) => ({ from: n.id, to, label: n.flowLabel })),
)

export const COUNCIL_DECISION = {
  verdict: 'Topology B with dual-sourcing on critical components',
  allocation: 'Supplier A 60% · Supplier B 25% · Supplier C 15%',
  reason:
    'A minimizes landed cost. B provides geographic diversification. C is a qualified contingency supplier held at low allocation.',
  tradeoff: 'Estimated landed cost +6.4% vs cheapest single-source design; expected disruption loss reduced by 41%.',
  resilience: 'Survives 13 of 14 disruption scenarios with zero stockout days; worst case 4-day service degradation.',
}

export const ROLLOUT_PHASES = [
  { phase: 'Phase 1', action: 'Qualify Supplier A', status: 'Ready now' },
  { phase: 'Phase 2', action: 'Qualify Supplier B', status: 'Ready now' },
  { phase: 'Phase 3', action: 'Establish Central DC + Regional Buffer', status: 'Requires validation' },
  { phase: 'Phase 4', action: 'Validate primary logistics lanes', status: 'Requires validation' },
  { phase: 'Phase 5', action: 'Build 30-day safety stock', status: 'Requires negotiation' },
  { phase: 'Phase 6', action: 'Run supplier-outage contingency exercise', status: 'Requires user action' },
]

/** Plain-text rendering of the blueprint for the chatbot system prompt. */
export function blueprintAsText(): string {
  const stages = BLUEPRINT_STAGES.map((stage) => {
    const nodes = stage.nodes
      .map(
        (n) =>
          `  - ${n.name}${n.share ? ` (${n.share} allocation)` : ''} [risk: ${n.risk ?? 'n/a'}]: ${n.meta.join('; ')}`,
      )
      .join('\n')
    return `${stage.label} (owned by ${stage.owner}):\n${nodes}`
  }).join('\n\n')

  const phases = ROLLOUT_PHASES.map((p) => `  ${p.phase}: ${p.action} — ${p.status}`).join('\n')

  return [
    'SUPPLY NETWORK ARCHITECTURE (flow: Suppliers -> Manufacturing -> Warehousing -> Distribution -> Customers)',
    '',
    stages,
    '',
    'COUNCIL DECISION:',
    `  Verdict: ${COUNCIL_DECISION.verdict}`,
    `  Allocation: ${COUNCIL_DECISION.allocation}`,
    `  Reason: ${COUNCIL_DECISION.reason}`,
    `  Trade-off: ${COUNCIL_DECISION.tradeoff}`,
    `  Resilience: ${COUNCIL_DECISION.resilience}`,
    '',
    'IMPLEMENTATION ROLLOUT:',
    phases,
  ].join('\n')
}
