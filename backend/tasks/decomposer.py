"""
Task Decomposer (Phase 10 Task Orchestration)

Responsibilities:
- Converts a TaskOutcome into a list of WorkUnit proposals.
- Enforces WORK UNIT PRINCIPLE: 1 coherent piece of work owned by EXACTLY 1 team.
- No micro-action decomposition (e.g., 'open browser', 'click button').
- Maps outputs/objectives to candidate teams deterministically.
- Does NOT assign individual employees or create agents.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional

from tasks.models import TaskOutcome, WorkUnit, WorkUnitStatus

logger = logging.getLogger(__name__)

# Output / Intent -> Primary Owning Team mapping
OUTPUT_TEAM_MAPPING: Dict[str, str] = {
    "video": "creative",
    "promotional_video": "creative",
    "image": "creative",
    "creative_asset": "creative",

    "research_report": "research",
    "market_research": "research",
    "competitor_analysis": "research",
    "fact_verification": "research",

    "software": "developer",
    "landing_page": "developer",
    "bug_fix": "developer",
    "api_development": "developer",

    "legal_review": "legal",
    "contract_analysis": "legal",
    "compliance_review": "legal",

    "financial_analysis": "finance",
    "budget": "finance",
    "financial_report": "finance",

    "campaign": "marketing",
    "marketing_plan": "marketing",

    "operations_plan": "operations",
    "workflow_execution": "operations",
}

DEFAULT_POSITIONS: Dict[str, str] = {
    "creative": "video_editor",
    "research": "researcher",
    "developer": "backend_engineer",
    "legal": "legal_researcher",
    "finance": "financial_analyst",
    "marketing": "content_strategist",
    "operations": "operations_manager",
}


class TaskDecomposer:
    """
    Decomposes TaskOutcome into WorkUnit objects.
    """

    def decompose(self, task_id: str, outcome: TaskOutcome) -> List[WorkUnit]:
        """
        Derives WorkUnits required to achieve TaskOutcome.
        """
        work_units: List[WorkUnit] = []
        outputs_by_team: Dict[str, List[str]] = {}

        # Group requested outputs by candidate owning team
        for output_type in outcome.required_outputs:
            team_id = OUTPUT_TEAM_MAPPING.get(output_type, "developer")
            outputs_by_team.setdefault(team_id, []).append(output_type)

        if not outputs_by_team:
            # Fallback single developer work unit
            outputs_by_team["developer"] = ["text_report"]

        wu_index = 1
        for team_id, team_outputs in outputs_by_team.items():
            wu_id = f"wu_{task_id[:8]}_{wu_index:03d}"
            title = f"{team_id.title()} — {', '.join(team_outputs).replace('_', ' ').title()}"
            objective = f"Execute {team_id} work to produce deliverables: {', '.join(team_outputs)}"
            position_id = DEFAULT_POSITIONS.get(team_id, "specialist")

            work_unit = WorkUnit(
                work_unit_id=wu_id,
                task_id=task_id,
                team_id=team_id,
                title=title,
                objective=objective,
                expected_outputs=team_outputs,
                required_position=position_id,
                status=WorkUnitStatus.PENDING,
            )
            work_units.append(work_unit)
            wu_index += 1

        return work_units
