import json

NISHA_SPECIFIC_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "audit_operational_efficiency",
            "description": "Audits the operational efficiency of a process or department. Returns an OEE-style (Overall Equipment Effectiveness) score and identifies the top bottlenecks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "process_name": {"type": "string", "description": "Name of the process/department being audited."},
                    "theoretical_capacity_units_per_day": {"type": "number", "description": "Max theoretical output per day."},
                    "actual_output_units_per_day": {"type": "number", "description": "Current actual daily output."},
                    "avg_cycle_time_minutes": {"type": "number", "description": "Average time to complete one unit/order."},
                    "target_cycle_time_minutes": {"type": "number", "description": "Target cycle time per unit/order."},
                    "defect_rate_pct": {"type": "number", "description": "Percentage of outputs that are defective or require rework."},
                    "downtime_hours_per_week": {"type": "number", "description": "Average unplanned downtime per week in hours."}
                },
                "required": ["process_name", "theoretical_capacity_units_per_day", "actual_output_units_per_day",
                             "avg_cycle_time_minutes", "target_cycle_time_minutes", "defect_rate_pct", "downtime_hours_per_week"]
            }
        }
    }
]

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
        # OEE = Availability × Performance × Quality
        availability = max(0, (5 * 8 - downtime_hours_per_week) / (5 * 8))  # assuming 5-day, 8hr work week
        performance = min(1.0, target_cycle_time_minutes / avg_cycle_time_minutes) if avg_cycle_time_minutes > 0 else 0
        quality = max(0, 1 - (defect_rate_pct / 100))
        oee_score = availability * performance * quality * 100

        # Utilization
        utilization_pct = (actual_output_units_per_day / theoretical_capacity_units_per_day * 100) if theoretical_capacity_units_per_day > 0 else 0

        bottlenecks = []
        if availability < 0.85:
            bottlenecks.append(f"HIGH DOWNTIME: {downtime_hours_per_week:.1f} hrs/week lost — root cause analysis required")
        if performance < 0.85:
            bottlenecks.append(f"SLOW CYCLE TIME: {avg_cycle_time_minutes:.0f} min vs {target_cycle_time_minutes:.0f} min target — process redesign needed")
        if defect_rate_pct > 3:
            bottlenecks.append(f"QUALITY ISSUES: {defect_rate_pct:.1f}% defect rate — Six Sigma review recommended")
        if utilization_pct < 70:
            bottlenecks.append(f"UNDERUTILIZATION: Only {utilization_pct:.0f}% of capacity used — demand planning gap")

        if oee_score >= 85:
            verdict = "WORLD-CLASS — Operations are highly efficient. Approved for scale-up."
        elif oee_score >= 65:
            verdict = "ACCEPTABLE — Minor improvements needed. Conditional approval."
        elif oee_score >= 40:
            verdict = "BELOW TARGET — Significant operational gaps. Fix bottlenecks before scaling."
        else:
            verdict = "CRITICAL — Operations are severely underperforming. BLOCK expansion until resolved."

        return json.dumps({
            "process": process_name,
            "oee_score": round(oee_score, 1),
            "utilization_pct": round(utilization_pct, 1),
            "availability_pct": round(availability * 100, 1),
            "performance_pct": round(performance * 100, 1),
            "quality_pct": round(quality * 100, 1),
            "bottlenecks_identified": bottlenecks if bottlenecks else ["No critical bottlenecks detected"],
            "nisha_verdict": verdict
        }, indent=2)
    except Exception as e:
        return f"Error auditing operational efficiency: {str(e)}"
