export type Team =
  | 'Executive'
  | 'Intelligence'
  | 'Network'
  | 'Resilience'
  | 'Council'
  | 'Architecture'

export type AgentDef = {
  name: string
  team: Team
  role: string
  /* two-letter initials for the pixel portrait */
  initials: string
  /* character sprite index (0-5) — matches /assets/pixel-agents/characters/char_{n}.png */
  charIdx: number
  /* detailed description of the work this agent does */
  detail: string
}

export const TEAM_COLORS: Record<Team, { bg: string; text: string; chip: string }> = {
  Executive: { bg: 'bg-secondary', text: 'text-secondary-foreground', chip: 'bg-secondary' },
  Intelligence: { bg: 'bg-[#bcd8ce]', text: 'text-foreground', chip: 'bg-[#bcd8ce]' },
  Network: { bg: 'bg-[#aebfdd]', text: 'text-foreground', chip: 'bg-[#aebfdd]' },
  Resilience: { bg: 'bg-[#b9d8ac]', text: 'text-foreground', chip: 'bg-[#b9d8ac]' },
  Council: { bg: 'bg-[#e3c1c8]', text: 'text-foreground', chip: 'bg-[#e3c1c8]' },
  Architecture: { bg: 'bg-[#c9bede]', text: 'text-foreground', chip: 'bg-[#c9bede]' },
}

export const AGENTS: AgentDef[] = [
  {
    name: 'Atlas', team: 'Executive', role: 'Chief Supply Chain Architect / Orchestrator', initials: 'AT', charIdx: 5,
    detail: 'The organizational brain — but not the recruiter. Once Maya has assembled the task force, Atlas interprets the mission brief, determines what information is missing, builds the master research plan, delegates to every cabin, monitors progress, resolves deadlocks, convenes the Strategy Council, and commissions the final architecture.',
  },
  {
    name: 'Maya', team: 'Executive', role: 'Chief Resource Allocator / AI Hiring Engine', initials: 'MA', charIdx: 4,
    detail: 'The first decision-maker on every mission. Maya reads the incoming brief — product, geography, constraints, priorities — queries the live agent registry, and hires only the specialists the project actually needs. She is the reason a 21-agent organization runs as a 4-agent task force when that is all the problem requires.',
  },
  {
    name: 'Mira', team: 'Intelligence', role: 'Demand & assortment intelligence', initials: 'MI', charIdx: 0,
    detail: 'Maps demand, market size, product / category segmentation, sales velocity, seasonality, assortment, demand volatility, product lifecycle, customer geography, and category trends — producing base / low / high demand scenarios.',
  },
  {
    name: 'Ravi', team: 'Intelligence', role: 'Supplier intelligence', initials: 'RA', charIdx: 1,
    detail: 'Builds the supplier universe for every required category and component: capabilities, locations, MOQ, pricing, lead time, capacity, certifications, and reputation. Tags every claim VERIFIED, ESTIMATED, or UNKNOWN.',
  },
  {
    name: 'Anika', team: 'Intelligence', role: 'Category benchmarking', initials: 'AN', charIdx: 2,
    detail: 'Benchmarks industry supply structures: competitor assortment, supplier concentration, typical sourcing models, private-label opportunities, domestic vs imported sourcing, and typical distribution structures.',
  },
  {
    name: 'Noor', team: 'Intelligence', role: 'Geopolitical / external risk intelligence', initials: 'NO', charIdx: 3,
    detail: 'Tracks tariffs, trade restrictions, country risk, natural-disaster exposure, political instability, port and transport risks, commodity volatility, and regulatory changes — the raw risk intelligence the Resilience cell consumes.',
  },
  {
    name: 'Aanya', team: 'Network', role: 'Supply-chain network design', initials: 'AA', charIdx: 4,
    detail: 'Designs the physical flow of products through the network: supplier → processing → manufacturing → warehouse → distribution → customer. Weighs facility locations, transport links, tiers, geographic concentration, and redundancy.',
  },
  {
    name: 'Dev', team: 'Network', role: 'Procurement & total landed cost', initials: 'DE', charIdx: 5,
    detail: 'Computes total landed cost, not just unit price: freight, insurance, duties, handling, warehousing, inventory carrying cost, expected disruption cost, and switching cost for every supplier lane.',
  },
  {
    name: 'Kabir', team: 'Network', role: 'Logistics & fulfillment', initials: 'KA', charIdx: 0,
    detail: 'Plans transport modes, route selection, shipping times, warehouse placement, distribution, lane reliability, route alternatives, and last-mile considerations for every candidate lane.',
  },
  {
    name: 'Tara', team: 'Network', role: 'Inventory & capacity planning', initials: 'TA', charIdx: 1,
    detail: 'Sizes safety stock, reorder points, and inventory buffers per SKU / category and location; validates supplier, manufacturing, and warehouse capacity against demand coverage and stockout exposure.',
  },
  {
    name: 'Zoya', team: 'Resilience', role: 'Failure / risk mapping', initials: 'ZO', charIdx: 2,
    detail: 'Builds the risk map across supplier, category, SKU, warehouse, route, store, and region — surfacing single points of failure, single-source exposure, geographic concentration, and capacity bottlenecks.',
  },
  {
    name: 'Ishaan', team: 'Resilience', role: 'Disruption scenario generation', initials: 'IS', charIdx: 3,
    detail: 'Generates plausible, research-informed disruption scenarios at every level: supplier outage, category demand spikes, warehouse loss, regional disruption, tariff shocks, and fuel-cost surges.',
  },
  {
    name: 'Leena', team: 'Resilience', role: 'Stress testing', initials: 'LE', charIdx: 4,
    detail: 'Runs every disruption scenario against every candidate topology and measures what happens to the whole business — shortage days, incremental cost, and service level — then re-tests with fixes applied.',
  },
  {
    name: 'Arjun', team: 'Resilience', role: 'Continuity & recovery planning', initials: 'AR', charIdx: 5,
    detail: 'Writes the playbook for when things break: trigger → detection → immediate action → fallback supplier / route → inventory release → allocation change → escalation → recovery, for every important scenario.',
  },
  {
    name: 'Helena', team: 'Council', role: 'Cost strategist', initials: 'HE', charIdx: 0,
    detail: 'Advocates the most economically efficient network — optimizing landed cost, working capital, logistics cost, supplier prices, and inventory costs. Challenges expensive redundancy.',
  },
  {
    name: 'Vikram', team: 'Council', role: 'Resilience strategist', initials: 'VI', charIdx: 1,
    detail: 'Advocates protecting the company from disruption — redundancy, alternate suppliers, geographic diversification, recovery time, and service continuity. Deliberately challenges overly cost-optimized designs.',
  },
  {
    name: 'Nisha', team: 'Council', role: 'Operations strategist', initials: 'NI', charIdx: 2,
    detail: 'Asks "Can this actually run?" — challenging unrealistic lead times, impossible capacities, warehouse limitations, supplier qualification gaps, and operational complexity.',
  },
  {
    name: 'Omar', team: 'Council', role: 'Risk / compliance strategist', initials: 'OM', charIdx: 3,
    detail: 'Asks "What are we missing?" — challenging regulatory exposure, geopolitical dependencies, tariffs, quality requirements, hidden single points of failure, and unsupported research claims.',
  },
  {
    name: 'Sofia', team: 'Council', role: 'Council chair', initials: 'SO', charIdx: 4,
    detail: 'Runs the adversarial debate: collects independent proposals, forces cross-examination, requests extra evidence, compares candidate architectures, and records the final decision with explicit trade-offs.',
  },
  {
    name: 'Rohan', team: 'Architecture', role: 'Master supply-chain architect', initials: 'RO', charIdx: 0,
    detail: 'Assembles the final supply network architecture — every node and edge with identity, location, function, capacity, cost, lead time, dependencies, and alternatives.',
  },
  {
    name: 'Priya', team: 'Architecture', role: 'Implementation planner', initials: 'PR', charIdx: 1,
    detail: 'Turns the architecture into an executable rollout: phased supplier qualification, warehouse setup, lane validation, safety-stock build, and contingency exercises — flagging what is ready now vs needs validation or negotiation.',
  },
  {
    name: 'Ethan', team: 'Architecture', role: 'Independent validator', initials: 'ET', charIdx: 2,
    detail: 'Attacks the blueprint before sign-off: every component sourced, capacity supports demand, lead times feasible, costs consistent, resilience scenarios answered, and no recommendation based on fabricated information.',
  },
]

export function getAgent(name: string): AgentDef | undefined {
  return AGENTS.find((a) => a.name === name)
}

/**
 * External ArmorIQ platform log endpoint.
 * Set NEXT_PUBLIC_ARMORIQ_URL to override; falls back to the platform root.
 */
export const ARMORIQ_URL = process.env.NEXT_PUBLIC_ARMORIQ_URL || 'https://armoriq.ai/logs'
