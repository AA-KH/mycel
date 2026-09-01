import type { Team } from './agents'

/**
 * Rich per-agent dossier content shown in the detail card when a
 * team member is clicked in the org chart.
 */
export type AgentDossier = {
  /* one-sentence summary shown at the top of the card */
  mission: string
  /* what this agent is responsible for */
  responsibilities: string[]
  /* MCP tools the agent calls (omitted for pure reasoning agents) */
  tools?: string[]
  /* how the agent actually works, step by step */
  workflow?: string[]
  /* an example of the artifact this agent produces */
  output?: { title: string; lines: string[] }
}

/* one-line taglines for the compact directory list */
export const AGENT_TAGLINES: Record<string, string> = {
  Maya: 'The AI hiring engine — reads the brief and assembles the task force before anyone else wakes up.',
  Atlas: 'The organizational brain — plans, delegates, and decides when research is done.',
  Mira: 'Maps demand, assortment, and category trends into base / low / high scenarios.',
  Ravi: 'Builds the supplier universe for every required category and component.',
  Anika: 'Benchmarks how comparable businesses structure their categories and sourcing.',
  Noor: 'Tracks tariffs, geopolitics, and disruption risk across the outside world.',
  Aanya: 'Designs the physical flow of products through the whole network.',
  Dev: 'Computes total landed cost — never just the unit price.',
  Kabir: 'Plans transport modes, routes, lanes, and last-mile fulfillment.',
  Tara: 'Sizes safety stock, buffers, and capacity per SKU and location.',
  Zoya: 'Maps failure exposure across supplier, category, SKU, route, and region.',
  Ishaan: 'Generates plausible, research-informed disruption scenarios at every level.',
  Leena: 'Stress-tests the whole business against every disruption scenario.',
  Arjun: 'Writes the recovery playbook for when things actually break.',
  Helena: 'Argues for the most economically efficient network.',
  Vikram: 'Argues for protection from disruption — challenges cheap fragility.',
  Nisha: 'Asks "can this actually run?" — challenges operational fantasy.',
  Omar: 'Asks "what are we missing?" — challenges compliance and hidden risk.',
  Sofia: 'Chairs the adversarial debate and records the final decision.',
  Rohan: 'Assembles the final supply network architecture, node by node.',
  Priya: 'Turns the architecture into a phased, executable rollout.',
  Ethan: 'Attacks the blueprint before sign-off — fails it back to the council.',
}

export const AGENT_DOSSIERS: Record<string, AgentDossier> = {
  /* ---------------- TEAM 0 — EXECUTIVE ---------------- */
  Maya: {
    mission:
      'Chief Resource Allocator — the AI hiring engine and the very first agent to activate on any mission. Maya is not a researcher and not an orchestrator: her single job is to read the brief and decide exactly which specialists get hired onto this project.',
    responsibilities: [
      'Receive and parse the incoming mission payload',
      'Understand product, geography, constraints, and priorities',
      'Query the live agent registry for availability and SCM skills',
      'Match project requirements against each agent\u2019s specialization',
      'Hire the minimum viable task force — never all 21 agents by default',
      'Record the hiring rationale for every agent selected',
      'Hand the assembled task force over to Atlas for orchestration',
    ],
    tools: ['query_available_agents()', 'hire_team()'],
    workflow: [
      'Mission payload arrives \u2192 Maya activates before any other agent',
      'query_available_agents() \u2014 reads the live registry: who is available and what can they do?',
      'Reasons over the brief: what makes this project hard? which skills are actually load-bearing?',
      'hire_team() \u2014 returns the agent IDs plus explicit reasoning for each',
      'Only the hired agents wake up; the rest stay on standby \u2014 saving time, cost, and tokens',
    ],
    output: {
      title: 'Hiring decision \u2014 semiconductors, TW \u2192 US',
      lines: [
        'HIRED:  Vikram   \u2014 tariff & sanction exposure',
        '        Rohan    \u2014 physical port routing (TW\u2192LA)',
        '        Ethan    \u2014 port-blockade resilience test',
        '        Atlas    \u2014 executive blueprint assembly',
        'SKIPPED: 17 agents \u2014 not load-bearing for this brief',
      ],
    },
  },
  Atlas: {
    mission:
      'Chief Supply Chain Officer, program manager, and orchestrator in one. Atlas is not a researcher, not the recruiter, and not the final answer generator — it runs the organization that produces the answer, using the task force Maya hired.',
    responsibilities: [
      'Interpret the user\u2019s inputs and mission brief',
      'Determine what information is missing',
      'Create the master research plan',
      'Establish the org structure for this particular problem',
      'Delegate work and monitor progress',
      'Resolve deadlocks between teams',
      'Decide when research is sufficiently complete',
      'Convene the Strategy Council',
      'Commission and present the final architecture',
    ],
    workflow: [
      'Receives the hired task force from Maya — hiring is not Atlas\u2019s job',
      'Progressive context acquisition — never 50 mandatory questions up front',
      'Starts with: what are you making? where are you selling? expected volume?',
      'Then: "we can produce a better architecture if you provide any of the following\u2026"',
      'Updates its understanding as the user adds BOM, pricing, lead-time, or location detail',
      'Activates the hired cabins and routes findings between them',
    ],
    output: {
      title: 'Master research plan',
      lines: [
        'MISSION: 100,000 pencils / year, India',
        'TASK FORCE: 9 agents hired by Maya',
        'MISSING: BOM detail, target COGS, max lead time',
        'PLAN: Intelligence \u2192 Network \u2192 Resilience',
        '      \u2192 Council debate \u2192 Architecture Studio',
        'STATUS: delegating to hired cabins\u2026',
      ],
    },
  },

  /* ---------------- TEAM 1 — INTELLIGENCE ---------------- */
  Mira: {
    mission:
      'Owns demand and assortment intelligence — not just "market size" but how demand is structured across products, categories, geography, and time.',
    responsibilities: [
      'Demand and market size',
      'Product / category segmentation',
      'Sales velocity and seasonality',
      'Assortment and demand volatility',
      'Product lifecycle stage',
      'Customer geography',
      'Category trends and growth',
      'Expected volume scenarios',
    ],
    tools: ['search_market()', 'search_industry_report()', 'search_demand_data()', 'search_trade_statistics()'],
    workflow: [
      'Segments the business into products and categories',
      'Researches demand structure for each segment',
      'Quantifies volatility, seasonality, and geographic concentration',
      'Publishes a demand profile every downstream team plans against',
    ],
    output: {
      title: 'Demand profile',
      lines: [
        'BASE DEMAND:  100k units / year',
        'LOW SCENARIO:  70k    HIGH: 180k',
        'SEASONALITY:  peaks Jun\u2013Aug (back-to-school)',
        'VOLATILITY:   moderate, category-driven',
        'GEOGRAPHY:    68% concentrated in 3 states',
      ],
    },
  },
  Ravi: {
    mission:
      'The most important research agent. His job is not "find a supplier for this product" — it is "build the supplier universe for every required category and component."',
    responsibilities: [
      'Candidate supplier discovery per category / component',
      'Capabilities, locations, and materials',
      'Certifications, MOQ, pricing, lead time',
      'Capacity and quality indicators',
      'Public reputation and export capability',
      'Dependency indicators',
      'Alternate supplier discovery',
    ],
    tools: [
      'search_suppliers()',
      'search_supplier_catalog()',
      'search_trade_database()',
      'search_certifications()',
      'lookup_supplier_location()',
    ],
    workflow: [
      'Enumerates every category and component that needs a source',
      'Builds a candidate list per component, not per product',
      'Tags every claim: VERIFIED (sourced), ESTIMATED (inferred), UNKNOWN (not public)',
      'Never pretends web research yields exact supplier quotes',
    ],
    output: {
      title: 'Supplier candidate',
      lines: [
        'SUPPLIER:  X GmbH        MATERIAL: graphite',
        'LOCATION:  Germany       MOQ: 5,000 kg',
        'PRICE:     \u20b984/kg [ESTIMATED]',
        'LEAD TIME: 32 days [VERIFIED]',
        'CAPACITY:  [UNKNOWN]  CERTS: ISO 9001 [VERIFIED]',
      ],
    },
  },
  Anika: {
    mission:
      'Category benchmarking — how comparable companies and industries actually structure sourcing and distribution, so the architecture is not based only on whichever suppliers happen to show up in search. Especially valuable for stores and wholesalers.',
    responsibilities: [
      'Industry supply structures',
      'Competitor assortment',
      'Supplier concentration norms',
      'Typical sourcing models',
      'Private-label opportunities',
      'Category norms and lead-time standards',
      'Domestic vs imported sourcing',
      'Typical distribution structures',
    ],
    tools: ['search_industry()', 'search_company_supply_chain()', 'search_trade_news()', 'search_case_study()'],
    workflow: [
      'Studies how comparable businesses source each category',
      'Extracts the industry-normal architecture as a baseline',
      'Flags where the proposed design deviates from category norms — and whether that is smart or risky',
    ],
  },
  Noor: {
    mission:
      'External risk and geopolitical intelligence — the raw risk feed that the entire Resilience cell consumes.',
    responsibilities: [
      'Tariffs and trade restrictions',
      'Geopolitical exposure and country risk',
      'Natural-disaster exposure',
      'Political instability',
      'Port and transport risks',
      'Commodity volatility',
      'Regulatory changes',
      'Known and historical disruptions',
    ],
    tools: [
      'search_tariffs()',
      'search_trade_restrictions()',
      'search_geopolitical_risk()',
      'search_disruption_news()',
      'search_weather_risk()',
    ],
    workflow: [
      'Monitors every country, port, and lane the network touches',
      'Attaches a risk annotation to each supplier region and route',
      'Feeds Zoya and Ishaan the evidence behind their scenarios',
    ],
  },

  /* ---------------- TEAM 2 — NETWORK ---------------- */
  Aanya: {
    mission:
      'Owns network topology. Her job is not "design the pencil network" — it is "design the physical flow of the business\u2019s products through the network."',
    responsibilities: [
      'Overall network topology',
      'Facility and supplier locations',
      'Distribution points and transport links',
      'Number of tiers',
      'Geographic concentration',
      'Redundancy in the flow',
    ],
    tools: ['calculate_distance()', 'map_network()', 'calculate_route()', 'evaluate_network_topology()'],
    output: {
      title: 'Network topology',
      lines: [
        'SUPPLIER \u2192 PROCESSING \u2192 MANUFACTURING',
        '        \u2192 WAREHOUSE \u2192 DISTRIBUTION \u2192 CUSTOMER',
        'TIERS: 3    NODES: 14    LANES: 22',
        'CONCENTRATION: 2 regions flagged for review',
      ],
    },
  },
  Dev: {
    mission:
      'Far more sophisticated than finding the lowest supplier price — Dev calculates total landed cost and total cost of ownership, trading off price, lead time, quality, and risk.',
    responsibilities: [
      'Unit price + freight + insurance + duties',
      'Handling and warehousing cost',
      'Inventory carrying cost',
      'Expected disruption cost',
      'Switching cost between suppliers',
      'Supplier-vs-supplier total cost comparison',
    ],
    tools: ['calculate_landed_cost()', 'calculate_tco()', 'compare_supplier_cost()', 'calculate_tariff_impact()'],
    output: {
      title: 'Landed cost — Supplier A',
      lines: [
        'UNIT COST:   \u20b98.20',
        'FREIGHT:     \u20b90.80    DUTY: \u20b90.40',
        'INVENTORY:   \u20b90.30',
        '\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500',
        'LANDED COST: \u20b99.70 / unit',
      ],
    },
  },
  Kabir: {
    mission: 'Owns how goods physically move — every lane, mode, and mile between nodes of the network.',
    responsibilities: [
      'Transport mode selection',
      'Route selection and shipping times',
      'Warehouse placement input',
      'Distribution planning',
      'Lane reliability assessment',
      'Route alternatives',
      'Last-mile considerations',
    ],
    tools: ['calculate_route()', 'estimate_transit_time()', 'calculate_shipping_cost()', 'find_alternate_route()'],
  },
  Tara: {
    mission:
      'Inventory and capacity planning — critical because resilience often comes at a cost: you survive a supplier outage because you carry 30 days of safety stock, and Tara decides whether that trade is worth it.',
    responsibilities: [
      'Safety stock per product — and per SKU / category / location for stores',
      'Reorder points and inventory buffers',
      'Supplier, manufacturing, and warehouse capacity checks',
      'Demand coverage vs stockout exposure',
      'Where each SKU / category should be kept, and how much',
    ],
    tools: [
      'calculate_safety_stock()',
      'calculate_reorder_point()',
      'calculate_capacity()',
      'simulate_stockout()',
      'calculate_inventory_cost()',
    ],
    workflow: [
      'For a single product: how much safety stock?',
      'For a store: how much of each SKU / category, and where?',
      'Prices every buffer so the Council can trade cost against resilience',
    ],
  },

  /* ---------------- TEAM 3 — RESILIENCE ---------------- */
  Zoya: {
    mission:
      'Builds the risk map — thinking across supplier, category, SKU, warehouse, route, store, and region, not just "Supplier A is a single point of failure."',
    responsibilities: [
      'Single points of failure',
      'Single-source exposure',
      'Geographic concentration',
      'Transport dependency',
      'Capacity bottlenecks',
      'Supplier dependency across categories',
    ],
    tools: ['build_risk_register()', 'score_supplier_risk()', 'map_dependency()', 'identify_single_points()'],
    workflow: [
      'Consumes the proposed network, supplier intel, routes, inventory, and external risks',
      'Traces every critical component: supplier \u2192 plant \u2192 route \u2192 warehouse',
      'Detects compound exposure, e.g. "Supplier A supplies 64% of the store\u2019s high-margin skincare assortment"',
    ],
    output: {
      title: 'Risk register entry',
      lines: [
        'COMPONENT: graphite core',
        'EXPOSURE:  single-source, single-region',
        'FINDING:   Supplier A = 64% of high-margin',
        '           skincare assortment',
        'SEVERITY:  CRITICAL \u2192 sent to Ishaan',
      ],
    },
  },
  Ishaan: {
    mission:
      'Creates plausible disruption scenarios — not random catastrophes — informed by the research data, at every level of the business.',
    responsibilities: [
      'Supplier-level: supplier disappears, capacity falls 50%',
      'Category-level: cosmetics demand +70%',
      'Network-level: warehouse unavailable, port closure',
      'Geographic-level: region disrupted',
      'Economic-level: tariff +20%, fuel cost +30%',
    ],
    tools: ['generate_scenario()', 'parameterize_disruption()', 'lookup_historical_disruptions()'],
    workflow: [
      'Reads Noor\u2019s risk intel and Zoya\u2019s risk map',
      'Generates scenarios grounded in evidence — e.g. "this material is sourced heavily from one country and recent trade restrictions make a tariff scenario particularly relevant"',
      'Parameterizes each scenario so Leena can execute it',
    ],
  },
  Leena: {
    mission:
      'The counterfactual engine. Tests what happens to the whole business — not just one product — under every disruption, then re-tests with fixes applied.',
    responsibilities: [
      'Run every scenario against the candidate architecture',
      'Measure shortage days, incremental cost, service level',
      'Test proposed fixes and re-run',
      'Quantify recovery time',
    ],
    tools: ['simulate_failure()', 'run_supply_scenario()', 'calculate_service_level()', 'calculate_recovery_time()'],
    output: {
      title: 'Stress test — Supplier A outage',
      lines: [
        'NORMAL:  A 70% / B 30%',
        'FAIL A:  B insufficient \u2192 18-day shortage',
        'FIX:     add Supplier C @ 15%',
        'RE-RUN:  A 60% / B 25% / C 15%',
        'RESULT:  stockout 0 days \u2713',
      ],
    },
  },
  Arjun: {
    mission:
      'Doesn\u2019t ask "what could go wrong?" — asks "what do we do when it does?" Turns every important scenario into an executable continuity playbook.',
    responsibilities: [
      'Trigger and detection criteria per scenario',
      'Immediate response actions',
      'Fallback suppliers and routes',
      'Inventory release rules',
      'Allocation changes and escalation',
      'Recovery steps back to normal',
    ],
    workflow: [
      'Trigger \u2192 detection \u2192 immediate action \u2192 fallback supplier / route',
      '\u2192 inventory release \u2192 allocation change \u2192 escalation \u2192 recovery',
    ],
    output: {
      title: 'Playbook — Supplier A outage',
      lines: [
        'TRIGGER: confirmed outage > 72 hours',
        'ACT:     activate Supplier B',
        '         release safety stock',
        '         redirect 40% volume',
        '         switch transport mode if needed',
        'THEN:    notify procurement, review Supplier C',
      ],
    },
  },

  /* ---------------- TEAM 4 — COUNCIL ---------------- */
  Helena: {
    mission: 'Advocates: "Build the most economically efficient network." Challenges every rupee of expensive redundancy.',
    responsibilities: [
      'Landed cost optimization',
      'Working capital minimization',
      'Logistics cost',
      'Supplier price negotiation targets',
      'Inventory cost discipline',
    ],
    workflow: [
      'Round 1: proposes the cheapest viable configuration',
      'Round 2: cross-examines — "your dual-sourcing adds 12% unit cost; what disruption probability justifies that?"',
      'Round 3: revises when the resilience evidence is quantified',
    ],
  },
  Vikram: {
    mission:
      'Advocates: "Protect the company from disruption." Deliberately challenges overly cost-optimized designs with scenario evidence.',
    responsibilities: [
      'Redundancy and alternate suppliers',
      'Geographic diversification',
      'Recovery time objectives',
      'Service continuity guarantees',
    ],
    workflow: [
      'Round 1: proposes the most protected configuration',
      'Round 2: answers Helena with Leena\u2019s stress-test numbers',
      'Round 3: concedes redundancy that scenarios can\u2019t justify',
    ],
  },
  Nisha: {
    mission: 'Advocates: "Can this actually run?" The reality check on every proposal in the room.',
    responsibilities: [
      'Unrealistic lead times',
      'Impossible capacities',
      'Warehouse limitations',
      'Manufacturing constraints',
      'Supplier qualification gaps',
      'Operational complexity',
    ],
    workflow: [
      'Cross-examines both sides — "your cheapest supplier needs 52 days; how is that compatible with 21-day fulfillment?"',
    ],
  },
  Omar: {
    mission: 'Advocates: "What are we missing?" Hunts the blind spots in everyone else\u2019s argument.',
    responsibilities: [
      'Regulatory exposure',
      'Geopolitical dependencies',
      'Tariff exposure',
      'Quality requirements',
      'Hidden single points of failure',
      'Unsupported research claims',
    ],
    workflow: [
      'Challenges both strategists at once — "your preferred suppliers are concentrated in the same geopolitical region"',
    ],
  },
  Sofia: {
    mission:
      'The chair. Not an averager — she runs a real four-round adversarial protocol and records the decision with explicit trade-offs.',
    responsibilities: [
      'Receive independent proposals',
      'Identify disagreements',
      'Force targeted cross-examination',
      'Request additional evidence when needed',
      'Compare candidate architectures',
      'Produce the final recommendation',
    ],
    workflow: [
      'Round 1 — independent proposals from each strategist',
      'Round 2 — cross-examination with evidence',
      'Round 3 — revised proposals',
      'Round 4 — chair decision, trade-offs recorded',
    ],
    output: {
      title: 'Council decision',
      lines: [
        'DECISION: A 60% / B 25% / C 15%',
        'REASON:   A minimizes cost, B diversifies',
        '          geography, C is qualified backup',
        'TRADEOFF: landed cost +6.4%',
        '          expected disruption loss \u221241%',
      ],
    },
  },

  /* ---------------- TEAM 5 — ARCHITECTURE ---------------- */
  Rohan: {
    mission:
      'Produces the final deliverable: a Supply Network Architecture — not just a product supply chain — with every node and edge fully specified.',
    responsibilities: [
      'Full network: supplier \u2192 component \u2192 manufacturing \u2192 warehouse \u2192 distribution \u2192 customer',
      'Per node & edge: identity, location, function',
      'Capacity, cost, and lead time',
      'Dependencies and alternatives',
    ],
    output: {
      title: 'Supply network architecture',
      lines: [
        'NODE: Supplier A (graphite, DE)',
        '  CAP: 12t/mo   COST: \u20b984/kg   LT: 32d',
        '  ALT: Supplier C (qualified backup)',
        'EDGE: A \u2192 Plant 1  (sea, 28d, \u20b90.80/u)',
        '\u2026 14 nodes, 22 edges total',
      ],
    },
  },
  Priya: {
    mission:
      'Turns the architecture into something the customer can actually implement — because web research can identify a supplier, but cannot magically establish a commercial relationship.',
    responsibilities: [
      'Phased rollout planning',
      'Supplier qualification sequencing',
      'Warehouse and lane validation',
      'Safety-stock build schedule',
      'Contingency exercises',
      'Flagging: READY NOW vs REQUIRES VALIDATION vs REQUIRES NEGOTIATION',
    ],
    output: {
      title: 'Implementation plan',
      lines: [
        'PHASE 1: qualify Supplier A   [NEGOTIATION]',
        'PHASE 2: qualify Supplier B   [VALIDATION]',
        'PHASE 3: establish warehouse  [READY]',
        'PHASE 4: validate logistics lane',
        'PHASE 5: build safety stock',
        'PHASE 6: run contingency exercise',
      ],
    },
  },
  Ethan: {
    mission:
      'The final independent reviewer. If validation fails, the architecture goes back to the Council — that feedback loop makes the whole organization stronger.',
    responsibilities: [
      'Every required component has a source',
      'Capacity supports demand',
      'Lead times are feasible',
      'Cost calculations are consistent',
      'Every resilience scenario has a response',
      'Single points of failure are identified',
      'Every claim has evidence — nothing fabricated',
      'Architecture satisfies user constraints',
    ],
    workflow: ['Architecture \u2192 Validator \u2192 PASS \u2192 sign-off', 'Architecture \u2192 Validator \u2192 FAIL \u2192 back to Council'],
  },
}

/* team-level descriptions shown outside the member cards */
export const TEAM_DESCRIPTIONS: Record<Team, string> = {
  Executive:
    'Two agents run the whole floor. Maya goes first — she reads the brief and hires only the specialists the mission needs. Atlas then takes that task force, builds the research plan, delegates to every hired cabin, and decides when the work is done.',
  Intelligence:
    'The research engine — the largest team, because architecture quality is limited by information quality. Four agents map demand, suppliers, category norms, and external risk.',
  Network:
    'Intelligence answers "what exists?" — this team answers "how should we connect it?" Topology, total landed cost, logistics, and inventory buffers.',
  Resilience:
    'This cell answers "how does the network behave when reality stops cooperating?" It maps failure, generates disruptions, stress-tests the design, and writes the recovery playbooks.',
  Council:
    'The research teams produce evidence; the council deliberately disagrees about what to do with it. Four adversarial strategists debate across four rounds, and the chair records the decision.',
  Architecture:
    'The council decides what to do — the studio determines exactly what the final supply chain looks like, how to implement it, and whether it survives independent validation.',
}
