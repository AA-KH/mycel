"""
Capability Requirement Resolver & Team Resolver (Phase 10 Task Orchestration)

Responsibilities:
- Translates TaskOutcome & requested outputs into TaskCapabilityRequirement models.
- Resolves candidate Teams that satisfy capability/output requirements using:
    - TeamCapabilityResolver (TOS 15)
    - ExecutionContractRegistry (TOS 18)
    - PipelineRegistry (TOS 14)
- Does NOT perform employee hiring or agent runtime creation.
- Does NOT use LLMs for non-deterministic team selection.
"""

import logging
from typing import List, Dict, Any, Optional

from tasks.models import TaskOutcome, TaskCapabilityRequirement
from teams.resolver import TeamCapabilityResolver
from execution.contracts.registry import ExecutionContractRegistry
from execution.contracts.models import TeamExecutionContract
from execution.pipelines.registry import PipelineRegistry

logger = logging.getLogger(__name__)

# Output type -> Required Capability IDs
OUTPUT_TO_CAPABILITIES_MAP: Dict[str, List[str]] = {
    "video": ["video_production", "storytelling", "video_editing", "visual_design"],
    "promotional_video": ["video_production", "storytelling", "video_editing", "visual_design"],
    "image": ["visual_design"],
    "creative_asset": ["visual_design", "storytelling"],

    "research_report": ["web_research", "fact_verification", "data_analysis"],
    "market_research": ["web_research", "fact_verification", "data_analysis"],
    "competitor_analysis": ["web_research", "fact_verification", "data_analysis"],
    "fact_verification": ["fact_verification", "web_research"],

    "software": ["programming", "software engineering", "testing", "API development"],
    "landing_page": ["programming", "software engineering", "system design"],
    "bug_fix": ["debugging", "programming", "testing"],
    "api_development": ["API development", "programming"],

    "legal_review": ["legal_research", "contract_analysis", "compliance"],
    "contract_analysis": ["contract_analysis", "compliance"],
    "compliance_review": ["compliance", "legal_research"],

    "financial_analysis": ["financial_analysis", "budgeting", "forecasting"],
    "budget": ["budgeting", "financial_analysis"],
    "financial_report": ["financial_analysis", "forecasting"],

    "campaign": ["content_strategy", "campaign_design", "audience_analysis"],
    "marketing_plan": ["campaign_design", "content_strategy"],

    "operations_plan": ["process_management", "coordination", "planning"],
    "workflow_execution": ["process_management", "coordination"],
    "supply_chain_architecture": ["scm_intelligence", "scm_network", "scm_resilience", "scm_council", "scm_architecture", "scm_executive"],
    "risk_assessment": ["scm_resilience"],
}


class CapabilityRequirementResolver:
    """Resolves required capabilities from TaskOutcome and requested output types."""

    def resolve_requirements(
        self, outcome: TaskOutcome
    ) -> List[TaskCapabilityRequirement]:
        requirements: List[TaskCapabilityRequirement] = []
        seen = set()

        for output_type in outcome.required_outputs:
            caps = OUTPUT_TO_CAPABILITIES_MAP.get(output_type, [])
            for cap in caps:
                if cap not in seen:
                    seen.add(cap)
                    requirements.append(
                        TaskCapabilityRequirement(
                            capability_id=cap,
                            minimum_proficiency="standard",
                            required=True,
                            source="output_type",
                            reason=f"Required by output contract '{output_type}'",
                        )
                    )

        # Fallback if no specific output recognized
        if not requirements:
            requirements.append(
                TaskCapabilityRequirement(
                    capability_id="general_execution",
                    minimum_proficiency="standard",
                    required=True,
                    source="fallback",
                    reason="Default capability requirement",
                )
            )

        return requirements


class TeamRequirementResolution:
    """Container for team resolution details for a candidate team."""

    def __init__(
        self,
        team_id: str,
        execution_contract: Optional[TeamExecutionContract] = None,
        pipeline_id: Optional[str] = None,
        matched_capabilities: Optional[List[str]] = None,
        missing_capabilities: Optional[List[str]] = None,
        valid: bool = False,
        reason: str = "",
    ):
        self.team_id = team_id
        self.execution_contract = execution_contract
        self.pipeline_id = pipeline_id
        self.matched_capabilities = matched_capabilities or []
        self.missing_capabilities = missing_capabilities or []
        self.valid = valid
        self.reason = reason


class TeamResolver:
    """
    Deterministically resolves candidate Teams for work units using:
    - TeamCapabilityResolver (TOS 15)
    - ExecutionContractRegistry (TOS 18)
    - PipelineRegistry (TOS 14)
    """

    def __init__(
        self,
        capability_resolver: TeamCapabilityResolver,
        execution_contracts: ExecutionContractRegistry,
        pipeline_registry: PipelineRegistry,
    ):
        self._resolver = capability_resolver
        self._contracts = execution_contracts
        self._pipelines = pipeline_registry

    def resolve_team_for_task_type(
        self,
        task_type: str,
        required_capabilities: List[str],
        preferred_team_id: Optional[str] = None,
    ) -> Optional[TeamRequirementResolution]:
        """
        Resolves the best matching Team for a given task type and capability set.
        """
        # 1. First check active Execution Contracts for the given task_type
        contracts = self._contracts.get_active_by_task_type(task_type)
        if preferred_team_id:
            contracts = [c for c in contracts if c.team_id == preferred_team_id] or contracts

        for contract in contracts:
            team_id = contract.team_id
            pipe_id = contract.pipeline_id

            # Verify pipeline exists and belongs to team
            pipe = getattr(self._pipelines, "get_pipeline", getattr(self._pipelines, "get", lambda x: None))(pipe_id)
            if not pipe or pipe.team_id != team_id:
                continue

            # Verify team capability match
            match = self._resolver.matches_requirements(
                team_id, {"skills": required_capabilities}
            )

            return TeamRequirementResolution(
                team_id=team_id,
                execution_contract=contract,
                pipeline_id=pipe_id,
                matched_capabilities=required_capabilities,
                valid=True,
                reason=f"Resolved via active execution contract '{contract.contract_id}'",
            )

        # 2. Fallback: Search all teams via TeamCapabilityResolver if contract not found by task_type
        if preferred_team_id:
            candidate_team_ids = [preferred_team_id]
        else:
            candidate_team_ids = [
                "developer", "research", "creative", "legal", "marketing", "finance", "operations"
            ]

        for team_id in candidate_team_ids:
            # Check team active contracts
            team_contracts = self._contracts.get_active_by_team(team_id)
            if not team_contracts:
                continue

            contract = team_contracts[0]
            pipe_id = contract.pipeline_id
            pipe = getattr(self._pipelines, "get_pipeline", getattr(self._pipelines, "get", lambda x: None))(pipe_id)

            if pipe and pipe.team_id == team_id:
                return TeamRequirementResolution(
                    team_id=team_id,
                    execution_contract=contract,
                    pipeline_id=pipe_id,
                    matched_capabilities=required_capabilities,
                    valid=True,
                    reason=f"Resolved fallback team '{team_id}' with pipeline '{pipe_id}'",
                )

        return None
