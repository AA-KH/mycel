import json
import aiohttp

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────
VIKRAM_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_active_disaster_alerts",
            "description": "Fetches live disaster and geopolitical alerts from GDACS (Global Disaster Alert and Coordination System). Use this FIRST to check if active threats (earthquakes, floods, hurricanes, conflicts) are currently impacting any of the supply chain's sourcing regions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "alert_level": {
                        "type": "string",
                        "enum": ["red", "orange", "green"],
                        "description": "Filter by severity. 'red' = critical events only. 'orange' = significant events. 'green' = all events."
                    }
                },
                "required": ["alert_level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "score_supply_chain_resilience",
            "description": "Scores the overall structural resilience of a supply chain setup (0=fragile, 100=highly resilient). Evaluates supplier count, geographic spread, inventory buffers, lead time, and single-source concentration.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_category": {"type": "string"},
                    "num_active_suppliers": {"type": "integer", "description": "Number of active, qualified suppliers for this category."},
                    "num_countries_sourced_from": {"type": "integer", "description": "Number of distinct countries in the supplier base."},
                    "avg_lead_time_days": {"type": "number", "description": "Average lead time from order to delivery in days."},
                    "safety_stock_days": {"type": "number", "description": "Days of safety stock held."},
                    "single_source_pct": {"type": "number", "description": "Percentage of volume sourced from a single supplier (0-100)."}
                },
                "required": ["product_category", "num_active_suppliers", "num_countries_sourced_from", "avg_lead_time_days", "safety_stock_days", "single_source_pct"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "map_single_points_of_failure",
            "description": "Identifies every node in the supply chain where a single event causes total production stoppage. Maps SPOFs by tier, severity, and substitutability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_chain_name": {"type": "string"},
                    "nodes": {
                        "type": "array",
                        "description": "List of supply chain nodes to evaluate.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "node_name": {"type": "string", "description": "Name of the node (supplier, port, warehouse, etc.)"},
                                "node_type": {"type": "string", "description": "Type: 'supplier', 'port', 'warehouse', 'manufacturer', 'logistics_partner'"},
                                "country": {"type": "string"},
                                "num_alternatives": {"type": "integer", "description": "Number of qualified backup alternatives. 0 = pure SPOF."},
                                "volume_pct_of_total": {"type": "number", "description": "Percentage of total throughput flowing through this node."},
                                "switchover_days": {"type": "integer", "description": "Days required to switch to an alternative if this node fails."}
                            }
                        }
                    }
                },
                "required": ["supply_chain_name", "nodes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_geographic_concentration",
            "description": "Quantifies geographic concentration risk: what % of supply, manufacturing, and logistics comes from each region. Flags dangerous concentration (>50% from one country) and cross-references with active geopolitical risk zones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_chain_name": {"type": "string"},
                    "regional_breakdown": {
                        "type": "array",
                        "description": "Breakdown of supply by country/region.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "country": {"type": "string"},
                                "volume_pct": {"type": "number", "description": "% of total supply sourced from this country."},
                                "category": {"type": "string", "description": "What is sourced here (e.g., 'Raw Materials', 'Assembly', 'Finished Goods')."}
                            }
                        }
                    }
                },
                "required": ["supply_chain_name", "regional_breakdown"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_business_impact_of_failure",
            "description": "Calculates the exact financial impact (revenue loss + recovery cost) if a specific supply chain node fails. Converts abstract risk into a concrete dollar figure for the Council and CFO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_name": {"type": "string", "description": "The supply chain node that fails (e.g., 'Taiwan Semiconductor Plant')."},
                    "daily_revenue_at_risk_usd": {"type": "number", "description": "Revenue lost per day if this node goes down."},
                    "estimated_downtime_days": {"type": "number", "description": "Estimated days of disruption if this node fails."},
                    "emergency_sourcing_cost_usd": {"type": "number", "description": "One-time cost to activate emergency alternative sourcing."},
                    "customer_penalty_clauses_usd": {"type": "number", "description": "Contractual penalties for missed deliveries.", "default": 0},
                    "reputational_impact_multiplier": {"type": "number", "description": "Multiplier for reputational damage (1.0 = no extra damage, 1.5 = significant brand impact).", "default": 1.0}
                },
                "required": ["node_name", "daily_revenue_at_risk_usd", "estimated_downtime_days", "emergency_sourcing_cost_usd"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_recovery_readiness",
            "description": "Assesses how quickly the supply chain can return to full operation after a disruption. Evaluates backup supplier readiness, inventory runway, and crisis response protocol maturity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "supply_chain_name": {"type": "string"},
                    "has_documented_bcp": {"type": "boolean", "description": "Does the company have a documented Business Continuity Plan for this supply chain?"},
                    "backup_supplier_qualification_days": {"type": "integer", "description": "Days required to qualify and onboard a backup supplier from scratch."},
                    "current_safety_stock_days": {"type": "number", "description": "Days of stock on hand (your runway before stockout)."},
                    "last_bcp_test_months_ago": {"type": "integer", "description": "Months since the BCP was last tested in a drill. Use 999 if never tested."},
                    "has_dual_sourcing_contracts": {"type": "boolean", "description": "Are there pre-negotiated contracts with backup suppliers?"},
                    "logistics_alternative_available": {"type": "boolean", "description": "Is there an alternative logistics/freight route pre-arranged?"}
                },
                "required": ["supply_chain_name", "has_documented_bcp", "backup_supplier_qualification_days",
                             "current_safety_stock_days", "last_bcp_test_months_ago",
                             "has_dual_sourcing_contracts", "logistics_alternative_available"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_country_political_stability",
            "description": "Fetches a country's Political Stability and Absence of Violence score from World Bank Governance Indicators (WGI). Returns a real, data-driven stability score (-2.5 = very unstable → +2.5 = very stable). Use this in STEP 4 (Geographic Concentration) to replace hardcoded country risk assumptions with actual World Bank data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_code": {
                        "type": "string",
                        "description": "World Bank 2-letter ISO country code (e.g., 'CN' for China, 'VN' for Vietnam, 'BD' for Bangladesh, 'IN' for India, 'DE' for Germany, 'TW' for Taiwan, 'MX' for Mexico, 'PK' for Pakistan)."
                    },
                    "country_name": {
                        "type": "string",
                        "description": "Human-readable country name for the report."
                    }
                },
                "required": ["country_code", "country_name"]
            }
        }
    }
]


# ─────────────────────────────────────────────────────────────
# TOOL 1: Live Disaster Alerts (GDACS API — FREE, no key)
# ─────────────────────────────────────────────────────────────
async def fetch_active_disaster_alerts(alert_level: str = "red") -> str:
    """Fetches live global disaster alerts from GDACS API."""
    try:
        url = f"https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH?alertlevel={alert_level}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"GDACS API error: {response.status}"
                data = await response.json()

        features = data.get("features", [])
        if not features:
            return json.dumps({
                "alert_level": alert_level.upper(),
                "active_alerts": 0,
                "events": [],
                "vikram_insight": f"No active {alert_level.upper()} alerts globally. Threat environment is currently calm for this alert level."
            }, indent=2)

        events = []
        for f in features[:8]:  # Top 8 events
            props = f.get("properties", {})
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [None, None])
            events.append({
                "event_type": props.get("eventtype", "Unknown"),
                "alert_level": props.get("alertlevel", "Unknown"),
                "country": props.get("country", "Unknown"),
                "title": props.get("htmldescription", props.get("eventname", "No description")),
                "date": props.get("fromdate", "Unknown"),
                "coordinates": {"lon": coords[0], "lat": coords[1]}
            })

        high_risk_countries = list({e["country"] for e in events if e["alert_level"].lower() in ["red", "orange"]})

        return json.dumps({
            "alert_level_filter": alert_level.upper(),
            "total_active_alerts": len(features),
            "showing_top": len(events),
            "high_risk_countries": high_risk_countries,
            "events": events,
            "vikram_insight": f"Cross-reference these {len(events)} active events with the supply chain's sourcing countries. Any overlap is a LIVE THREAT requiring immediate Council attention.",
            "source": "GDACS — Global Disaster Alert and Coordination System (UN)"
        }, indent=2)
    except Exception as e:
        return f"Error fetching disaster alerts: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Supply Chain Resilience Score
# ─────────────────────────────────────────────────────────────
async def score_supply_chain_resilience(
    product_category: str,
    num_active_suppliers: int,
    num_countries_sourced_from: int,
    avg_lead_time_days: float,
    safety_stock_days: float,
    single_source_pct: float
) -> str:
    try:
        score = 0
        factors = []

        if num_active_suppliers >= 5:
            score += 25; factors.append(f"{num_active_suppliers} suppliers: +25 (Excellent diversity)")
        elif num_active_suppliers >= 3:
            score += 15; factors.append(f"{num_active_suppliers} suppliers: +15 (Good)")
        elif num_active_suppliers == 2:
            score += 7; factors.append("2 suppliers: +7 (Minimal backup)")
        else:
            factors.append("1 supplier: +0 ❌ CRITICAL single-source risk")

        if num_countries_sourced_from >= 4:
            score += 25; factors.append(f"{num_countries_sourced_from} countries: +25 (Excellent geo-spread)")
        elif num_countries_sourced_from >= 2:
            score += 15; factors.append(f"{num_countries_sourced_from} countries: +15 (Moderate)")
        else:
            factors.append("Single-country sourcing: +0 ❌ Geopolitical concentration risk")

        if avg_lead_time_days <= 14:
            score += 20; factors.append(f"Lead time {avg_lead_time_days}d: +20 (Agile)")
        elif avg_lead_time_days <= 30:
            score += 12; factors.append(f"Lead time {avg_lead_time_days}d: +12 (Acceptable)")
        elif avg_lead_time_days <= 60:
            score += 5; factors.append(f"Lead time {avg_lead_time_days}d: +5 ⚠️ Long")
        else:
            factors.append(f"Lead time {avg_lead_time_days}d: +0 ❌ CRITICAL — over 60 days")

        if safety_stock_days >= 45:
            score += 20; factors.append(f"{safety_stock_days}d safety stock: +20 (Strong buffer)")
        elif safety_stock_days >= 21:
            score += 12; factors.append(f"{safety_stock_days}d safety stock: +12 (Adequate)")
        elif safety_stock_days >= 7:
            score += 5; factors.append(f"{safety_stock_days}d safety stock: +5 ⚠️ Thin")
        else:
            factors.append(f"{safety_stock_days}d safety stock: +0 ❌ CRITICAL — near zero buffer")

        if single_source_pct <= 20:
            score += 10; factors.append(f"Single-source %: {single_source_pct}%: +10 (Well-diversified)")
        elif single_source_pct <= 50:
            score += 5; factors.append(f"Single-source %: {single_source_pct}%: +5 ⚠️ Concentration building")
        else:
            factors.append(f"Single-source %: {single_source_pct}%: +0 ❌ DANGEROUS concentration")

        score = min(score, 100)

        if score >= 75:
            verdict = "RESILIENT — Approve with standard annual review."
        elif score >= 50:
            verdict = "MODERATE — Require dual-source contingency plan within 90 days before Council approval."
        else:
            verdict = "FRAGILE — BLOCK approval. Mandate immediate supplier diversification program."

        return json.dumps({
            "product_category": product_category,
            "resilience_score": score,
            "verdict": verdict,
            "scoring_breakdown": factors,
            "vikram_mandate": verdict
        }, indent=2)
    except Exception as e:
        return f"Error scoring resilience: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: Single Point of Failure Mapper
# ─────────────────────────────────────────────────────────────
async def map_single_points_of_failure(supply_chain_name: str, nodes: list) -> str:
    try:
        spofs = []
        warnings = []
        safe_nodes = []

        HIGH_RISK_COUNTRIES = ["China", "Russia", "Taiwan", "Bangladesh", "Myanmar", "Iran"]

        for node in nodes:
            name = node.get("node_name", "Unknown")
            alternatives = node.get("num_alternatives", 0)
            volume_pct = node.get("volume_pct_of_total", 0)
            switchover = node.get("switchover_days", 999)
            country = node.get("country", "Unknown")
            node_type = node.get("node_type", "Unknown")

            severity_flags = []
            severity = "SAFE"

            if alternatives == 0:
                severity = "CRITICAL_SPOF"
                severity_flags.append("Zero alternatives — single point of failure")
            elif alternatives == 1:
                severity = "WARNING"
                severity_flags.append("Only 1 backup — limited redundancy")

            if volume_pct > 50:
                severity = "CRITICAL_SPOF" if severity != "CRITICAL_SPOF" else severity
                severity_flags.append(f"Flows {volume_pct}% of total volume — catastrophic if lost")

            if switchover > 30:
                severity_flags.append(f"Switchover takes {switchover} days — exceeds safety stock window for most setups")

            if country in HIGH_RISK_COUNTRIES:
                severity_flags.append(f"Located in high geopolitical risk country: {country}")
                if severity == "SAFE":
                    severity = "WARNING"

            entry = {
                "node": name,
                "type": node_type,
                "country": country,
                "severity": severity,
                "volume_pct": f"{volume_pct}%",
                "alternatives": alternatives,
                "switchover_days": switchover,
                "risk_flags": severity_flags if severity_flags else ["No critical flags"]
            }

            if severity == "CRITICAL_SPOF":
                spofs.append(entry)
            elif severity == "WARNING":
                warnings.append(entry)
            else:
                safe_nodes.append(entry)

        overall = "CRITICAL" if spofs else ("WARNING" if warnings else "RESILIENT")
        mandate = (
            f"BLOCK — {len(spofs)} CRITICAL single points of failure must be remediated before any contract expansion."
            if spofs else
            f"CONDITIONAL — {len(warnings)} nodes need backup qualification within 90 days."
            if warnings else
            "APPROVE — No single points of failure detected."
        )

        return json.dumps({
            "supply_chain": supply_chain_name,
            "total_nodes_evaluated": len(nodes),
            "critical_spofs": spofs,
            "warning_nodes": warnings,
            "safe_nodes": [n["node"] for n in safe_nodes],
            "overall_spof_risk": overall,
            "vikram_mandate": mandate
        }, indent=2)
    except Exception as e:
        return f"Error mapping SPOFs: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: Geographic Concentration Analyzer
# ─────────────────────────────────────────────────────────────
async def analyze_geographic_concentration(supply_chain_name: str, regional_breakdown: list) -> str:
    try:
        HIGH_RISK_ZONES = {
            "China": "US-China trade war + Taiwan Strait tensions",
            "Taiwan": "Military conflict risk with China",
            "Russia": "Under international sanctions",
            "Ukraine": "Active conflict zone",
            "Bangladesh": "Political instability + climate flood risk",
            "Myanmar": "Military junta + sanctions",
            "Iran": "Under comprehensive OFAC sanctions",
            "Pakistan": "Political instability + IMF crisis"
        }

        sorted_regions = sorted(regional_breakdown, key=lambda x: x.get("volume_pct", 0), reverse=True)
        total_pct = sum(r.get("volume_pct", 0) for r in sorted_regions)

        enriched = []
        critical_zones = []
        top_country_pct = sorted_regions[0].get("volume_pct", 0) if sorted_regions else 0

        for region in sorted_regions:
            country = region.get("country", "Unknown")
            pct = region.get("volume_pct", 0)
            category = region.get("category", "General Supply")
            geo_risk = HIGH_RISK_ZONES.get(country)

            flags = []
            if pct > 60:
                flags.append(f"⛔ CRITICAL: {pct}% of supply — single-country catastrophic exposure")
                critical_zones.append(country)
            elif pct > 40:
                flags.append(f"⚠️ HIGH: {pct}% of supply — reduce below 30% target")
            elif pct > 25:
                flags.append(f"🔶 MODERATE: {pct}% — monitor quarterly")

            if geo_risk:
                flags.append(f"🌐 Geopolitical: {geo_risk}")
                if country not in critical_zones and pct > 20:
                    critical_zones.append(country)

            enriched.append({
                "country": country,
                "supply_category": category,
                "volume_pct": f"{pct}%",
                "geopolitical_risk": geo_risk or "No specific active flag",
                "concentration_flags": flags if flags else ["✅ Acceptable concentration"]
            })

        if top_country_pct > 60:
            risk_level = "CRITICAL"
            action = f"BLOCK expansion. Top country ({sorted_regions[0].get('country')}) holds {top_country_pct}% of supply. Mandate 3-country diversification strategy within 180 days."
        elif top_country_pct > 40 or len(critical_zones) >= 2:
            risk_level = "HIGH"
            action = f"Reduce top-country concentration below 30% within 12 months. Qualify suppliers in at least 2 additional countries."
        elif top_country_pct > 25:
            risk_level = "MODERATE"
            action = "Develop geographic diversification roadmap. Target: no single country > 30% within 24 months."
        else:
            risk_level = "LOW"
            action = "Geographic distribution is healthy. Maintain and review annually."

        return json.dumps({
            "supply_chain": supply_chain_name,
            "total_regions": len(sorted_regions),
            "top_country_concentration": f"{top_country_pct}%",
            "geopolitical_hotspot_countries": critical_zones if critical_zones else ["None"],
            "concentration_risk": risk_level,
            "regional_breakdown": enriched,
            "vikram_action": action
        }, indent=2)
    except Exception as e:
        return f"Error analyzing geographic concentration: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 5: Business Impact of Failure Calculator
# ─────────────────────────────────────────────────────────────
async def calculate_business_impact_of_failure(
    node_name: str,
    daily_revenue_at_risk_usd: float,
    estimated_downtime_days: float,
    emergency_sourcing_cost_usd: float,
    customer_penalty_clauses_usd: float = 0,
    reputational_impact_multiplier: float = 1.0
) -> str:
    try:
        revenue_loss = daily_revenue_at_risk_usd * estimated_downtime_days
        total_base_impact = revenue_loss + emergency_sourcing_cost_usd + customer_penalty_clauses_usd
        total_with_reputational = total_base_impact * reputational_impact_multiplier

        if total_with_reputational > 5_000_000:
            severity = "CATASTROPHIC"
            mandate = "IMMEDIATE Council escalation. Requires Board-level approval for remediation budget."
        elif total_with_reputational > 1_000_000:
            severity = "CRITICAL"
            mandate = "Council must approve resilience investment within 30 days."
        elif total_with_reputational > 250_000:
            severity = "SIGNIFICANT"
            mandate = "Include resilience improvement as condition of next contract renewal."
        else:
            severity = "MANAGEABLE"
            mandate = "Standard risk monitoring. Review in quarterly resilience audit."

        return json.dumps({
            "node_at_risk": node_name,
            "estimated_downtime": f"{estimated_downtime_days} days",
            "financial_impact_breakdown": {
                "revenue_loss": f"${revenue_loss:,.2f}",
                "emergency_sourcing_cost": f"${emergency_sourcing_cost_usd:,.2f}",
                "customer_penalty_clauses": f"${customer_penalty_clauses_usd:,.2f}",
                "reputational_multiplier": f"×{reputational_impact_multiplier}",
                "TOTAL_FINANCIAL_EXPOSURE": f"${total_with_reputational:,.2f}"
            },
            "failure_severity": severity,
            "vikram_mandate": mandate
        }, indent=2)
    except Exception as e:
        return f"Error calculating business impact: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 6: Recovery Readiness Assessment
# ─────────────────────────────────────────────────────────────
async def assess_recovery_readiness(
    supply_chain_name: str,
    has_documented_bcp: bool,
    backup_supplier_qualification_days: int,
    current_safety_stock_days: float,
    last_bcp_test_months_ago: int,
    has_dual_sourcing_contracts: bool,
    logistics_alternative_available: bool
) -> str:
    try:
        score = 0
        gaps = []
        strengths = []

        if has_documented_bcp:
            score += 20; strengths.append("Documented BCP exists: +20")
        else:
            gaps.append("❌ No documented BCP — this is a governance failure, not just a risk")

        if last_bcp_test_months_ago <= 6:
            score += 20; strengths.append(f"BCP tested {last_bcp_test_months_ago} months ago: +20 (Current)")
        elif last_bcp_test_months_ago <= 18:
            score += 10; strengths.append(f"BCP tested {last_bcp_test_months_ago} months ago: +10 (Aging)")
        else:
            gaps.append(f"⚠️ BCP last tested {last_bcp_test_months_ago} months ago — untested plans fail in real crises")

        if backup_supplier_qualification_days <= 14:
            score += 20; strengths.append(f"Backup qualification in {backup_supplier_qualification_days}d: +20 (Fast)")
        elif backup_supplier_qualification_days <= 30:
            score += 12; strengths.append(f"Backup qualification in {backup_supplier_qualification_days}d: +12 (Acceptable)")
        elif backup_supplier_qualification_days <= 60:
            score += 5; gaps.append(f"⚠️ Backup qualification takes {backup_supplier_qualification_days}d — longer than most safety stock runways")
        else:
            gaps.append(f"❌ Backup qualification takes {backup_supplier_qualification_days}d — catastrophic gap if disruption strikes")

        if current_safety_stock_days >= 45:
            score += 20; strengths.append(f"{current_safety_stock_days}d safety stock: +20 (Strong runway)")
        elif current_safety_stock_days >= 21:
            score += 12; strengths.append(f"{current_safety_stock_days}d safety stock: +12 (Adequate)")
        else:
            gaps.append(f"❌ Only {current_safety_stock_days}d safety stock — insufficient runway to activate backup supplier")

        if has_dual_sourcing_contracts:
            score += 10; strengths.append("Pre-negotiated dual-source contracts: +10")
        else:
            gaps.append("⚠️ No pre-negotiated backup contracts — negotiation under duress costs 30-50% premium")

        if logistics_alternative_available:
            score += 10; strengths.append("Alternative logistics route pre-arranged: +10")
        else:
            gaps.append("⚠️ No alternative freight route — port disruption = complete stoppage")

        score = min(score, 100)
        estimated_rto = max(backup_supplier_qualification_days, int(60 - current_safety_stock_days))
        estimated_rto = max(estimated_rto, 3)

        if score >= 75:
            readiness = "RECOVERY-READY"
            verdict = f"Supply chain can recover within ~{estimated_rto} days. Standard monitoring."
        elif score >= 50:
            readiness = "PARTIALLY READY"
            verdict = f"Recovery possible but gaps extend RTO to ~{estimated_rto} days. Address gaps within 60 days."
        else:
            readiness = "NOT READY"
            verdict = f"CRITICAL: Estimated recovery would take {estimated_rto}+ days. This means extended stockout and revenue loss. BLOCK expansion until BCP is credible."

        return json.dumps({
            "supply_chain": supply_chain_name,
            "recovery_readiness_score": score,
            "estimated_recovery_days": estimated_rto,
            "readiness_level": readiness,
            "strengths": strengths if strengths else ["None"],
            "critical_gaps": gaps if gaps else ["None"],
            "vikram_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error assessing recovery readiness: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 7: World Bank Political Stability Index (WGI — FREE, no key)
# Indicator: PV.EST (Political Stability and Absence of Violence)
# ─────────────────────────────────────────────────────────────
async def fetch_country_political_stability(country_code: str, country_name: str) -> str:
    """
    Fetches a country's Political Stability & Absence of Violence score
    from the World Bank Worldwide Governance Indicators (WGI).
    Score: -2.5 (extremely unstable) to +2.5 (extremely stable).
    """
    try:
        url = (
            f"https://api.worldbank.org/v2/country/{country_code}/indicator/PV.EST"
            f"?format=json&mrv=3"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"World Bank WGI API error: {response.status}. Check country code '{country_code}'."
                data = await response.json()

        records = data[1] if len(data) > 1 and data[1] else []

        # Get latest non-null value
        stability_score = None
        period = "Unknown"
        for record in records:
            if record.get("value") is not None:
                stability_score = record["value"]
                period = record.get("date", "Unknown")
                break

        if stability_score is None:
            return json.dumps({
                "country": country_name,
                "note": "No WGI data available. Cross-reference with GDACS alerts manually."
            }, indent=2)

        # Classify the score
        if stability_score >= 1.0:
            risk_level = "LOW"
            sourcing_flag = "✅ SAFE — Stable political environment. Standard sourcing risk applies."
        elif stability_score >= 0.0:
            risk_level = "LOW-MODERATE"
            sourcing_flag = "🔶 MONITOR — Minor political risks. Include in quarterly resilience review."
        elif stability_score >= -0.5:
            risk_level = "MODERATE"
            sourcing_flag = "⚠️ CAUTION — Moderate instability. Do not increase concentration without dual-source backup."
        elif stability_score >= -1.0:
            risk_level = "HIGH"
            sourcing_flag = "🔴 HIGH RISK — Significant political instability. Cap sourcing at 25% of category spend. Require backup contracts."
        else:
            risk_level = "CRITICAL"
            sourcing_flag = "⛔ CRITICAL — Extreme instability. Immediate diversification mandate. Do not expand any contracts in this country."

        return json.dumps({
            "country": country_name,
            "country_code": country_code.upper(),
            "wgi_political_stability_score": round(stability_score, 3),
            "score_range": "-2.5 (worst) to +2.5 (best)",
            "data_period": period,
            "source": "World Bank Worldwide Governance Indicators (WGI) — PV.EST",
            "risk_level": risk_level,
            "sourcing_recommendation": sourcing_flag,
            "vikram_note": (
                f"Use this score to dynamically adjust the geographic concentration threshold for {country_name}. "
                f"A score of {stability_score:.2f} means it is {'safer than average' if stability_score > 0 else 'riskier than average'} "
                f"compared to the global median of 0.0."
            )
        }, indent=2)
    except Exception as e:
        return f"Error fetching political stability data: {str(e)}"
