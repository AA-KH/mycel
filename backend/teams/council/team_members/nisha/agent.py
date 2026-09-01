from teams.council.base import CouncilBaseAgent
from teams.council.team_members.nisha.prompt import NISHA_SYSTEM_PROMPT
from teams.council.team_members.nisha.tools import (
    NISHA_SPECIFIC_TOOLS,
    audit_operational_efficiency,
    identify_process_bottlenecks,
    assess_workforce_capacity,
    run_six_sigma_analysis,
    assess_implementation_feasibility,
    generate_operations_kpi_targets,
    fetch_labor_productivity_benchmark
)

class NishaAgent(CouncilBaseAgent):
    def __init__(self, task_id: str = "default"):
        super().__init__(
            name="Nisha",
            role="Operations Strategist (Council)",
            system_prompt=NISHA_SYSTEM_PROMPT,
            tools=NISHA_SPECIFIC_TOOLS,
            user_id=task_id
        )

    async def execute_tool(self, function_name: str, arguments: dict):
        if function_name == "audit_operational_efficiency":
            return await audit_operational_efficiency(
                arguments.get("process_name", ""),
                arguments.get("theoretical_capacity_units_per_day", 100.0),
                arguments.get("actual_output_units_per_day", 0.0),
                arguments.get("avg_cycle_time_minutes", 0.0),
                arguments.get("target_cycle_time_minutes", 0.0),
                arguments.get("defect_rate_pct", 0.0),
                arguments.get("downtime_hours_per_week", 0.0)
            )
        elif function_name == "identify_process_bottlenecks":
            return await identify_process_bottlenecks(
                arguments.get("process_name", ""),
                arguments.get("process_steps", []),
                arguments.get("demand_units_per_hour", 0.0)
            )
        elif function_name == "assess_workforce_capacity":
            return await assess_workforce_capacity(
                arguments.get("department_name", ""),
                arguments.get("total_fte", 0.0),
                arguments.get("current_utilization_pct", 0.0),
                arguments.get("new_initiative_fte_required", 0.0),
                arguments.get("avg_skill_match_pct", 0.0),
                arguments.get("training_days_required", 0),
                arguments.get("has_change_management_plan", False)
            )
        elif function_name == "run_six_sigma_analysis":
            return await run_six_sigma_analysis(
                arguments.get("process_name", ""),
                arguments.get("defects_observed", 0),
                arguments.get("sample_size", 1),
                arguments.get("opportunities_per_unit", 1),
                arguments.get("unit_revenue_usd", 0.0),
                arguments.get("rework_cost_per_defect_usd", 0.0),
                arguments.get("annual_production_volume", 0)
            )
        elif function_name == "assess_implementation_feasibility":
            return await assess_implementation_feasibility(
                arguments.get("initiative_name", ""),
                arguments.get("proposed_timeline_weeks", 12),
                arguments.get("similar_projects_completed", 0),
                arguments.get("budget_confidence_pct", 50.0),
                arguments.get("executive_sponsorship", False),
                arguments.get("cross_team_dependencies", 0),
                arguments.get("technology_readiness_level", 5),
                arguments.get("has_pilot_been_run", False)
            )
        elif function_name == "generate_operations_kpi_targets":
            return await generate_operations_kpi_targets(
                arguments.get("initiative_name", ""),
                arguments.get("current_oee_pct", 0.0),
                arguments.get("current_defect_rate_pct", 0.0),
                arguments.get("current_cycle_time_minutes", 0.0),
                arguments.get("current_workforce_utilization_pct", 0.0),
                arguments.get("target_completion_weeks", 12)
            )
        elif function_name == "fetch_labor_productivity_benchmark":
            return await fetch_labor_productivity_benchmark(
                arguments.get("country_name", "")
            )

        # Fall through to shared Council tools
        return await super().execute_tool(function_name, arguments)
