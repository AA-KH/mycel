import json
import math
import aiohttp
from datetime import datetime, timedelta

# ─────────────────────────────────────────────────────────────
# TOOL SCHEMAS
# ─────────────────────────────────────────────────────────────
NISHA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "audit_operational_efficiency",
            "description": "Calculates OEE (Overall Equipment Effectiveness = Availability × Performance × Quality) for a process. World-class OEE is ≥85%. Below 50% is critical. Use this FIRST to establish the operational baseline before evaluating any new initiative.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {"type": "string"},
                    "theoretical_capacity_units_per_day": {"type": "number", "description": "Maximum theoretical output per day at 100% utilization."},
                    "actual_output_units_per_day": {"type": "number", "description": "Current actual daily output."},
                    "avg_cycle_time_minutes": {"type": "number", "description": "Average time to complete one unit/order."},
                    "target_cycle_time_minutes": {"type": "number", "description": "Target (ideal) cycle time per unit/order."},
                    "defect_rate_pct": {"type": "number", "description": "Percentage of outputs that are defective or require rework."},
                    "downtime_hours_per_week": {"type": "number", "description": "Average unplanned downtime hours per week."}
                },
                "required": ["process_name", "theoretical_capacity_units_per_day", "actual_output_units_per_day",
                             "avg_cycle_time_minutes", "target_cycle_time_minutes", "defect_rate_pct", "downtime_hours_per_week"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "identify_process_bottlenecks",
            "description": "Applies Theory of Constraints (TOC) to identify the ONE process step that is limiting total system throughput. Optimizing any step that is NOT the bottleneck is waste. Always fix the constraint first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {"type": "string"},
                    "process_steps": {
                        "type": "array",
                        "description": "List of process steps in order of execution.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "step_name": {"type": "string"},
                                "capacity_units_per_hour": {"type": "number", "description": "How many units this step can handle per hour."},
                                "actual_throughput_units_per_hour": {"type": "number", "description": "Current actual throughput at this step."},
                                "avg_queue_time_minutes": {"type": "number", "description": "How long work waits in queue before this step."},
                                "utilization_pct": {"type": "number", "description": "Current utilization of this step (0-100%)."}
                            }
                        }
                    },
                    "demand_units_per_hour": {"type": "number", "description": "Total market/customer demand in units per hour."}
                },
                "required": ["process_name", "process_steps", "demand_units_per_hour"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_workforce_capacity",
            "description": "Evaluates whether the organization has sufficient human resource capacity to absorb a new initiative. Flags burnout risk and mandates trade-offs when utilization exceeds safe thresholds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "department_name": {"type": "string"},
                    "total_fte": {"type": "number", "description": "Total Full-Time Equivalent employees available."},
                    "current_utilization_pct": {"type": "number", "description": "Current workforce utilization percentage (0-100). Above 85% is a burnout risk."},
                    "new_initiative_fte_required": {"type": "number", "description": "Additional FTE capacity the new initiative will consume."},
                    "avg_skill_match_pct": {"type": "number", "description": "Percentage of the team with skills matching the new initiative requirements (0-100)."},
                    "training_days_required": {"type": "integer", "description": "Days of training required before team can execute the new initiative."},
                    "has_change_management_plan": {"type": "boolean", "description": "Is there a formal change management and communication plan?"}
                },
                "required": ["department_name", "total_fte", "current_utilization_pct",
                             "new_initiative_fte_required", "avg_skill_match_pct",
                             "training_days_required", "has_change_management_plan"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_six_sigma_analysis",
            "description": "Converts a defect rate into DPMO (Defects Per Million Opportunities) and Sigma Level. Quantifies the annual cost of poor quality (COPQ). A process below 3-sigma has fundamentally broken quality — do NOT scale it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {"type": "string"},
                    "defects_observed": {"type": "integer", "description": "Number of defects found in the sample."},
                    "sample_size": {"type": "integer", "description": "Total units inspected."},
                    "opportunities_per_unit": {"type": "integer", "description": "Number of ways a defect can occur per unit (typically 1-10). Use 1 for simple processes."},
                    "unit_revenue_usd": {"type": "number", "description": "Revenue value of one good unit in USD."},
                    "rework_cost_per_defect_usd": {"type": "number", "description": "Cost to rework or replace one defective unit in USD."},
                    "annual_production_volume": {"type": "integer", "description": "Annual production volume in units."}
                },
                "required": ["process_name", "defects_observed", "sample_size", "opportunities_per_unit",
                             "unit_revenue_usd", "rework_cost_per_defect_usd", "annual_production_volume"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "assess_implementation_feasibility",
            "description": "Scores the operational feasibility of implementing a proposed initiative (0-100). Evaluates timeline realism, resource availability, process readiness, and change complexity. Grade A (≥80): Proceed. Grade B (60-79): Proceed with conditions. Grade C (<60): Send back for redesign.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initiative_name": {"type": "string"},
                    "proposed_timeline_weeks": {"type": "integer", "description": "Proposed implementation timeline in weeks."},
                    "similar_projects_completed": {"type": "integer", "description": "Number of similar projects the organization has successfully completed before."},
                    "budget_confidence_pct": {"type": "number", "description": "How confident is the budget estimate? (0-100). Below 70% means significant cost uncertainty."},
                    "executive_sponsorship": {"type": "boolean", "description": "Is there a named executive sponsor accountable for delivery?"},
                    "cross_team_dependencies": {"type": "integer", "description": "Number of other teams this initiative depends on. More dependencies = higher risk."},
                    "technology_readiness_level": {"type": "integer", "description": "Technology Readiness Level (TRL) 1-9. TRL ≥7 = production-ready. Below 5 = still experimental."},
                    "has_pilot_been_run": {"type": "boolean", "description": "Has a pilot or proof-of-concept been successfully completed?"}
                },
                "required": ["initiative_name", "proposed_timeline_weeks", "similar_projects_completed",
                             "budget_confidence_pct", "executive_sponsorship", "cross_team_dependencies",
                             "technology_readiness_level", "has_pilot_been_run"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_operations_kpi_targets",
            "description": "Generates a SMART KPI dashboard for an approved operational initiative. Every Council approval must include measurable targets — not vague outcomes. KPIs are the accountability contract between Nisha and the operating team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "initiative_name": {"type": "string"},
                    "current_oee_pct": {"type": "number", "description": "Current OEE baseline."},
                    "current_defect_rate_pct": {"type": "number"},
                    "current_cycle_time_minutes": {"type": "number"},
                    "current_workforce_utilization_pct": {"type": "number"},
                    "target_completion_weeks": {"type": "integer", "description": "Weeks until full implementation."}
                },
                "required": ["initiative_name", "current_oee_pct", "current_defect_rate_pct",
                             "current_cycle_time_minutes", "current_workforce_utilization_pct",
                             "target_completion_weeks"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_labor_productivity_benchmark",
            "description": "Fetches GDP per person employed (labor productivity) from World Bank for a specific country. Use in STEP 3 (Workforce Capacity) when planning operations or evaluating workforce expansion in a specific country. Prevents applying developed-country OEE and FTE assumptions to lower-productivity labor markets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country_name": {
                        "type": "string",
                        "description": "Country where operations are planned or being evaluated (e.g., 'Vietnam', 'Bangladesh', 'Germany', 'India', 'Mexico', 'China')."
                    }
                },
                "required": ["country_name"]
            }
        }
    }
]

# ─────────────────────────────────────────────────────────────
# COUNTRY CODE MAP for World Bank labor productivity queries
# ─────────────────────────────────────────────────────────────
LABOR_PRODUCTIVITY_COUNTRY_CODES = {
    "china": "CN", "vietnam": "VN", "bangladesh": "BD", "india": "IN",
    "germany": "DE", "usa": "US", "united states": "US", "mexico": "MX",
    "indonesia": "ID", "thailand": "TH", "pakistan": "PK", "turkey": "TR",
    "brazil": "BR", "poland": "PL", "malaysia": "MY", "philippines": "PH",
    "south korea": "KR", "japan": "JP", "taiwan": "TW", "france": "FR",
    "united kingdom": "GB", "uk": "GB", "australia": "AU", "canada": "CA",
    "singapore": "SG", "egypt": "EG", "nigeria": "NG", "ethiopia": "ET"
}

# ─────────────────────────────────────────────────────────────
# TOOL 1: OEE Audit
# ─────────────────────────────────────────────────────────────
async def audit_operational_efficiency(
    process_name: str,
    theoretical_capacity_units_per_day: float,
    actual_output_units_per_day: float,
    avg_cycle_time_minutes: float,
    target_cycle_time_minutes: float,
    defect_rate_pct: float,
    downtime_hours_per_week: float
) -> str:
    try:
        WORK_HOURS_PER_WEEK = 40.0
        availability = max(0.0, (WORK_HOURS_PER_WEEK - downtime_hours_per_week) / WORK_HOURS_PER_WEEK)
        performance = min(1.0, target_cycle_time_minutes / avg_cycle_time_minutes) if avg_cycle_time_minutes > 0 else 0
        quality = max(0.0, 1 - (defect_rate_pct / 100))
        oee = availability * performance * quality * 100
        utilization = (actual_output_units_per_day / theoretical_capacity_units_per_day * 100) if theoretical_capacity_units_per_day > 0 else 0

        bottlenecks = []
        if availability < 0.85:
            bottlenecks.append(f"⏱️ HIGH DOWNTIME: {downtime_hours_per_week:.1f} hrs/wk lost ({(1-availability)*100:.0f}% unavailability)")
        if performance < 0.85:
            bottlenecks.append(f"🐢 SLOW CYCLE: {avg_cycle_time_minutes:.0f}min vs {target_cycle_time_minutes:.0f}min target — {((avg_cycle_time_minutes/target_cycle_time_minutes)-1)*100:.0f}% slower than ideal")
        if defect_rate_pct > 3:
            bottlenecks.append(f"❌ QUALITY: {defect_rate_pct:.1f}% defect rate — Six Sigma analysis required")
        if utilization < 70:
            bottlenecks.append(f"📉 UNDERUTILIZED: {utilization:.0f}% capacity — demand-side or planning gap")

        if oee >= 85:
            verdict = "WORLD-CLASS ✅ — Operations are highly efficient. Capacity exists for new initiatives."
        elif oee >= 65:
            verdict = "ACCEPTABLE ⚠️ — Minor inefficiencies present. New initiatives may stress the system."
        elif oee >= 40:
            verdict = "BELOW TARGET 🔴 — Significant operational gaps. Fix before adding load."
        else:
            verdict = "CRITICAL ⛔ — Operations are severely underperforming. BLOCK all expansion until fixed."

        return json.dumps({
            "process": process_name,
            "oee_score": round(oee, 1),
            "oee_components": {
                "availability": f"{availability*100:.1f}%",
                "performance": f"{performance*100:.1f}%",
                "quality": f"{quality*100:.1f}%"
            },
            "capacity_utilization": f"{utilization:.1f}%",
            "bottlenecks": bottlenecks if bottlenecks else ["No critical bottlenecks detected"],
            "nisha_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error auditing OEE: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 2: Theory of Constraints — Bottleneck Identifier
# ─────────────────────────────────────────────────────────────
async def identify_process_bottlenecks(
    process_name: str,
    process_steps: list,
    demand_units_per_hour: float
) -> str:
    try:
        if not process_steps:
            return "No process steps provided."

        enriched = []
        bottleneck = None
        min_capacity = float('inf')

        for step in process_steps:
            name = step.get("step_name", "Unknown")
            capacity = step.get("capacity_units_per_hour", 0)
            actual = step.get("actual_throughput_units_per_hour", capacity)
            queue = step.get("avg_queue_time_minutes", 0)
            util = step.get("utilization_pct", (actual / capacity * 100) if capacity > 0 else 0)

            gap_to_demand = demand_units_per_hour - capacity
            is_constraint = capacity < min_capacity

            if is_constraint:
                min_capacity = capacity
                bottleneck = name

            flags = []
            if util >= 95:
                flags.append("⛔ SATURATED — This IS the constraint")
            elif util >= 85:
                flags.append("⚠️ Near-capacity — secondary constraint risk")
            if queue > 30:
                flags.append(f"📦 Long queue: {queue}min avg wait — upstream starvation")
            if capacity < demand_units_per_hour:
                flags.append(f"📉 Insufficient capacity: {capacity:.1f}/hr vs {demand_units_per_hour:.1f}/hr demand")

            enriched.append({
                "step": name,
                "capacity_per_hour": capacity,
                "actual_throughput_per_hour": actual,
                "utilization_pct": round(util, 1),
                "avg_queue_minutes": queue,
                "flags": flags if flags else ["✅ No constraint"]
            })

        capacity_gap = demand_units_per_hour - min_capacity
        throughput_loss_pct = (capacity_gap / demand_units_per_hour * 100) if demand_units_per_hour > 0 and capacity_gap > 0 else 0

        return json.dumps({
            "process": process_name,
            "demand_units_per_hour": demand_units_per_hour,
            "system_constraint_bottleneck": bottleneck,
            "bottleneck_capacity": f"{min_capacity:.1f} units/hr",
            "throughput_gap": f"{max(0, capacity_gap):.1f} units/hr ({throughput_loss_pct:.1f}% unmet demand)",
            "toc_principle": f"Fix '{bottleneck}' FIRST. All other improvements are waste until this constraint is elevated.",
            "nisha_mandate": f"Invest exclusively in '{bottleneck}' to unlock system throughput. Do NOT improve other steps until the constraint shifts.",
            "step_analysis": enriched
        }, indent=2)
    except Exception as e:
        return f"Error identifying bottlenecks: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 3: Workforce Capacity Assessment
# ─────────────────────────────────────────────────────────────
async def assess_workforce_capacity(
    department_name: str,
    total_fte: float,
    current_utilization_pct: float,
    new_initiative_fte_required: float,
    avg_skill_match_pct: float,
    training_days_required: int,
    has_change_management_plan: bool
) -> str:
    try:
        available_capacity_pct = max(0, 100 - current_utilization_pct)
        additional_utilization = (new_initiative_fte_required / total_fte * 100) if total_fte > 0 else 0
        projected_utilization = current_utilization_pct + additional_utilization
        fte_gap = max(0, new_initiative_fte_required - (total_fte * available_capacity_pct / 100))

        issues = []
        strengths = []

        if projected_utilization > 95:
            issues.append(f"⛔ BURNOUT RISK: Projected utilization {projected_utilization:.0f}% — unsustainable. Mandate {math.ceil(fte_gap)} additional FTEs or defer another project.")
        elif projected_utilization > 85:
            issues.append(f"⚠️ HIGH STRESS: Projected utilization {projected_utilization:.0f}% — teams will feel the strain. Monitor closely; any further requests must be rejected.")
        else:
            strengths.append(f"✅ Capacity OK: Projected utilization {projected_utilization:.0f}% is within safe range.")

        if avg_skill_match_pct < 60:
            issues.append(f"❌ SKILL GAP: Only {avg_skill_match_pct:.0f}% of team has relevant skills. Significant ramp-up period required — factor {training_days_required}d training into timeline.")
        elif avg_skill_match_pct < 80:
            issues.append(f"⚠️ PARTIAL SKILL MATCH: {avg_skill_match_pct:.0f}% skill coverage — targeted upskilling needed.")
        else:
            strengths.append(f"✅ Strong Skill Match: {avg_skill_match_pct:.0f}% of team is ready.")

        if training_days_required > 30:
            issues.append(f"⏱️ LONG TRAINING: {training_days_required}d onboarding will delay go-live by at least {training_days_required // 5} weeks.")

        if not has_change_management_plan:
            issues.append("📋 NO CHANGE MANAGEMENT PLAN: Without structured communication and adoption support, initiatives fail at the people layer even when technically sound.")
        else:
            strengths.append("✅ Change Management Plan exists.")

        if projected_utilization > 90 or avg_skill_match_pct < 60:
            status = "OVERLOADED"
            verdict = f"BLOCK this initiative until {math.ceil(fte_gap)} FTE are added OR an equivalent project is deprioritized."
        elif projected_utilization > 80 or avg_skill_match_pct < 75:
            status = "CONSTRAINED"
            verdict = "CONDITIONAL — Proceed only with explicit trade-off decision on deprioritizing lower-value work."
        else:
            status = "AVAILABLE"
            verdict = "Workforce can absorb this initiative. Ensure training plan is locked before kickoff."

        return json.dumps({
            "department": department_name,
            "total_fte": total_fte,
            "current_utilization": f"{current_utilization_pct:.0f}%",
            "initiative_requires": f"{new_initiative_fte_required:.1f} FTE equivalent",
            "projected_utilization": f"{projected_utilization:.0f}%",
            "fte_gap_to_hire": math.ceil(fte_gap) if fte_gap > 0 else 0,
            "capacity_status": status,
            "issues": issues if issues else ["None"],
            "strengths": strengths if strengths else ["None"],
            "nisha_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error assessing workforce capacity: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 4: Six Sigma Quality Analysis
# ─────────────────────────────────────────────────────────────
async def run_six_sigma_analysis(
    process_name: str,
    defects_observed: int,
    sample_size: int,
    opportunities_per_unit: int,
    unit_revenue_usd: float,
    rework_cost_per_defect_usd: float,
    annual_production_volume: int
) -> str:
    try:
        total_opportunities = sample_size * opportunities_per_unit
        dpo = defects_observed / total_opportunities if total_opportunities > 0 else 0  # Defects Per Opportunity
        dpmo = dpo * 1_000_000  # Defects Per Million Opportunities

        # Sigma level lookup (approximation using normal distribution inverse)
        sigma_level_map = [
            (3.4, 6.0), (233, 5.0), (6210, 4.0),
            (66807, 3.0), (308537, 2.0), (690000, 1.0)
        ]
        sigma_level = 1.0
        for dpmo_threshold, sigma in sigma_level_map:
            if dpmo <= dpmo_threshold:
                sigma_level = sigma
                break

        # Cost of Poor Quality (COPQ)
        annual_defects = int(annual_production_volume * (defects_observed / sample_size))
        annual_copq = annual_defects * rework_cost_per_defect_usd
        revenue_at_risk = annual_defects * unit_revenue_usd

        if sigma_level >= 5:
            verdict = "EXCELLENT ✅ — Near world-class quality. Scale with confidence."
            action = "Maintain current quality systems. Conduct quarterly audits."
        elif sigma_level >= 4:
            verdict = "GOOD ⚠️ — Minor quality issues. Addressable with targeted improvement."
            action = f"Launch targeted defect elimination. Target: <6,210 DPMO (4-sigma). Estimated COPQ saving: ${annual_copq*0.9:,.0f}/yr."
        elif sigma_level >= 3:
            verdict = "BELOW TARGET 🔴 — Significant quality failures. Do NOT scale this process."
            action = f"Mandatory Six Sigma DMAIC project required. Annual COPQ: ${annual_copq:,.0f}. ROI on fixing quality is massive."
        else:
            verdict = "CRITICAL QUALITY FAILURE ⛔ — Process is fundamentally broken. Cannot proceed."
            action = f"BLOCK all scaling. Process generates {dpmo:,.0f} DPMO. Annual COPQ: ${annual_copq:,.0f}. Full process redesign required."

        return json.dumps({
            "process": process_name,
            "defects_observed": defects_observed,
            "sample_size": sample_size,
            "dpmo": round(dpmo, 1),
            "sigma_level": sigma_level,
            "sigma_benchmarks": {"world_class": "6σ = 3.4 DPMO", "good": "4σ = 6,210 DPMO", "acceptable": "3σ = 66,807 DPMO"},
            "annual_defects_projected": annual_defects,
            "annual_copq": f"${annual_copq:,.2f}",
            "annual_revenue_at_risk": f"${revenue_at_risk:,.2f}",
            "quality_verdict": verdict,
            "nisha_action": action
        }, indent=2)
    except Exception as e:
        return f"Error running Six Sigma analysis: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 5: Implementation Feasibility Scorer
# ─────────────────────────────────────────────────────────────
async def assess_implementation_feasibility(
    initiative_name: str,
    proposed_timeline_weeks: int,
    similar_projects_completed: int,
    budget_confidence_pct: float,
    executive_sponsorship: bool,
    cross_team_dependencies: int,
    technology_readiness_level: int,
    has_pilot_been_run: bool
) -> str:
    try:
        score = 0
        factors = []

        # Experience
        if similar_projects_completed >= 3:
            score += 20; factors.append(f"✅ {similar_projects_completed} similar projects completed: +20 (Proven capability)")
        elif similar_projects_completed >= 1:
            score += 12; factors.append(f"⚠️ {similar_projects_completed} similar project(s): +12 (Limited track record)")
        else:
            factors.append("❌ No prior experience: +0 (First-time = high execution risk)")

        # Budget confidence
        if budget_confidence_pct >= 80:
            score += 20; factors.append(f"✅ Budget confidence {budget_confidence_pct:.0f}%: +20")
        elif budget_confidence_pct >= 60:
            score += 12; factors.append(f"⚠️ Budget confidence {budget_confidence_pct:.0f}%: +12 (Uncertainty present)")
        else:
            factors.append(f"❌ Budget confidence {budget_confidence_pct:.0f}%: +0 (Significant cost risk)")

        # Executive sponsorship
        if executive_sponsorship:
            score += 15; factors.append("✅ Executive sponsor named: +15")
        else:
            factors.append("❌ No executive sponsor: +0 (Initiatives without sponsors fail 70% of the time)")

        # Cross-team dependencies
        if cross_team_dependencies <= 2:
            score += 15; factors.append(f"✅ {cross_team_dependencies} dependencies: +15 (Low coordination complexity)")
        elif cross_team_dependencies <= 5:
            score += 8; factors.append(f"⚠️ {cross_team_dependencies} dependencies: +8 (Moderate coordination risk)")
        else:
            factors.append(f"❌ {cross_team_dependencies} dependencies: +0 (High coordination failure risk)")

        # Technology readiness
        if technology_readiness_level >= 7:
            score += 15; factors.append(f"✅ TRL {technology_readiness_level}: +15 (Production-ready technology)")
        elif technology_readiness_level >= 5:
            score += 8; factors.append(f"⚠️ TRL {technology_readiness_level}: +8 (Prototype stage — some tech risk)")
        else:
            factors.append(f"❌ TRL {technology_readiness_level}: +0 (Experimental — not ready for production rollout)")

        # Pilot
        if has_pilot_been_run:
            score += 15; factors.append("✅ Pilot completed: +15 (Proven in real conditions)")
        else:
            factors.append("⚠️ No pilot: +0 (First time at scale — add 40% buffer to timeline)")

        score = min(score, 100)

        if score >= 80:
            grade = "A"
            verdict = "APPROVE — Initiative is operationally feasible as designed."
        elif score >= 60:
            grade = "B"
            verdict = "CONDITIONAL — Feasible with conditions. Resolve flagged gaps before kickoff."
        else:
            grade = "C"
            verdict = "SEND BACK FOR REDESIGN — Too many execution risks. Do not approve in current form."

        # Timeline buffer recommendation
        timeline_buffer = 1.2 if similar_projects_completed >= 2 else (1.5 if has_pilot_been_run else 2.0)
        recommended_timeline = math.ceil(proposed_timeline_weeks * timeline_buffer)

        return json.dumps({
            "initiative": initiative_name,
            "feasibility_score": score,
            "grade": grade,
            "proposed_timeline_weeks": proposed_timeline_weeks,
            "nisha_recommended_timeline_weeks": recommended_timeline,
            "timeline_buffer_applied": f"×{timeline_buffer}",
            "scoring_factors": factors,
            "nisha_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error assessing feasibility: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 6: Operations KPI Target Generator
# ─────────────────────────────────────────────────────────────
async def generate_operations_kpi_targets(
    initiative_name: str,
    current_oee_pct: float,
    current_defect_rate_pct: float,
    current_cycle_time_minutes: float,
    current_workforce_utilization_pct: float,
    target_completion_weeks: int
) -> str:
    try:
        review_date_90d = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        review_date_180d = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")
        completion_date = (datetime.now() + timedelta(weeks=target_completion_weeks)).strftime("%Y-%m-%d")

        # Calculate SMART targets (20% improvement minimum)
        oee_target = min(85, current_oee_pct * 1.20)
        defect_target = max(0.5, current_defect_rate_pct * 0.70)
        cycle_time_target = current_cycle_time_minutes * 0.85
        utilization_target = min(85, current_workforce_utilization_pct)

        kpis = [
            {
                "metric": "Overall Equipment Effectiveness (OEE)",
                "baseline": f"{current_oee_pct:.1f}%",
                "target": f"{oee_target:.1f}%",
                "improvement": f"+{oee_target - current_oee_pct:.1f} percentage points",
                "measurement": "Weekly OEE report from operations system",
                "deadline": review_date_90d
            },
            {
                "metric": "Defect Rate",
                "baseline": f"{current_defect_rate_pct:.2f}%",
                "target": f"{defect_target:.2f}%",
                "improvement": f"-{current_defect_rate_pct - defect_target:.2f} percentage points",
                "measurement": "Daily quality control log",
                "deadline": review_date_90d
            },
            {
                "metric": "Cycle Time per Unit",
                "baseline": f"{current_cycle_time_minutes:.1f} minutes",
                "target": f"{cycle_time_target:.1f} minutes",
                "improvement": f"-{current_cycle_time_minutes - cycle_time_target:.1f} minutes ({15:.0f}% reduction)",
                "measurement": "Process timing system / stopwatch audit",
                "deadline": review_date_180d
            },
            {
                "metric": "Workforce Utilization",
                "baseline": f"{current_workforce_utilization_pct:.0f}%",
                "target": f"≤{utilization_target:.0f}%",
                "improvement": "Maintain safe utilization after initiative absorption",
                "measurement": "Capacity planning tool / time tracking",
                "deadline": completion_date
            },
            {
                "metric": "Full Initiative Implementation",
                "baseline": "0%",
                "target": "100% rollout",
                "improvement": "Complete operational handover",
                "measurement": "Project milestone tracker sign-off",
                "deadline": completion_date
            }
        ]

        return json.dumps({
            "initiative": initiative_name,
            "kpi_dashboard": kpis,
            "review_schedule": {
                "90_day_checkpoint": review_date_90d,
                "180_day_checkpoint": review_date_180d,
                "completion_target": completion_date
            },
            "nisha_note": "These KPIs are BINDING. If 90-day targets are missed by >20%, the initiative must be paused and root cause analyzed before proceeding."
        }, indent=2)
    except Exception as e:
        return f"Error generating KPI targets: {str(e)}"


# ─────────────────────────────────────────────────────────────
# TOOL 7: World Bank Labor Productivity Benchmark (FREE, no key)
# Indicator: SL.GDP.PCAP.EM.KD (GDP per person employed, 2017 USD PPP)
# ─────────────────────────────────────────────────────────────
async def fetch_labor_productivity_benchmark(country_name: str) -> str:
    """
    Fetches GDP per person employed (labor productivity) from World Bank.
    Constant 2017 USD PPP — enables apples-to-apples cross-country comparison.
    Use when planning workforce capacity across different countries/regions.
    """
    try:
        country_code = LABOR_PRODUCTIVITY_COUNTRY_CODES.get(country_name.lower().strip())
        if not country_code:
            return json.dumps({
                "error": f"Country '{country_name}' not in supported list.",
                "supported_countries": list(LABOR_PRODUCTIVITY_COUNTRY_CODES.keys())
            }, indent=2)

        url = (
            f"https://api.worldbank.org/v2/country/{country_code}/indicator/SL.GDP.PCAP.EM.KD"
            f"?format=json&mrv=3"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return f"World Bank API error: {response.status}"
                data = await response.json()

        records = data[1] if len(data) > 1 and data[1] else []
        productivity_value = None
        period = "Unknown"
        for record in records:
            if record.get("value") is not None:
                productivity_value = record["value"]
                period = record.get("date", "Unknown")
                break

        if productivity_value is None:
            return json.dumps({
                "country": country_name,
                "note": "No labor productivity data available from World Bank."
            }, indent=2)

        # Benchmark tiers (USD PPP per employed person per year)
        if productivity_value >= 80_000:
            tier = "VERY HIGH"
            oee_expectation = "≥80% OEE achievable. High automation + skilled workforce."
            capacity_note = "Premium labor market. Higher FTE cost offset by higher throughput per worker."
        elif productivity_value >= 40_000:
            tier = "HIGH"
            oee_expectation = "70-80% OEE typical. Good infrastructure and skill base."
            capacity_note = "Strong operational base. Standard FTE capacity planning applies."
        elif productivity_value >= 15_000:
            tier = "MEDIUM"
            oee_expectation = "55-70% OEE typical. Process standardization investment needed."
            capacity_note = "Factor 20-30% productivity discount vs. high-income countries in FTE calculations."
        else:
            tier = "LOW"
            oee_expectation = "40-55% OEE baseline. Significant training and process support required."
            capacity_note = "Factor 40-50% productivity discount in FTE planning. Higher headcount required for same output."

        return json.dumps({
            "country": country_name,
            "country_code": country_code,
            "gdp_per_person_employed_usd_ppp": f"${productivity_value:,.0f}",
            "data_period": period,
            "source": "World Bank Indicator SL.GDP.PCAP.EM.KD (constant 2017 USD PPP)",
            "productivity_tier": tier,
            "expected_oee_range": oee_expectation,
            "nisha_capacity_planning_note": capacity_note,
            "nisha_insight": (
                f"When planning {country_name} operations, calibrate OEE targets and FTE requirements "
                f"against this ${productivity_value:,.0f}/worker/year productivity baseline. "
                f"Do NOT apply developed-country capacity assumptions to a {tier.lower()}-productivity labor market."
            )
        }, indent=2)
    except Exception as e:
        return f"Error fetching labor productivity: {str(e)}"
