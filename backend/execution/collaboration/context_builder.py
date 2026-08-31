"""
Collaboration Context Builder (Phase 11 Minimal Context Projection)

Responsibilities:
- Builds a pruned minimal CollaborationContext for a receiving WorkUnit.
- Filters out non-essential data:
    - NO chain-of-thought or hidden reasoning traces.
    - NO internal tools or knowledge spaces of the producing team.
    - NO full chat history or company-wide employee lists.
    - NO credentials, API keys, or secret tokens.
- Projects only required inputs, relevant constraints, and ArtifactReferences.
"""

import logging
from typing import List, Dict, Any, Optional

from tasks.models import Task, TaskPlan, WorkUnit
from execution.collaboration.models import TeamCollaborationContract
from execution.collaboration.session import (
    CollaborationContext,
    CollaborationHandoff,
    ArtifactReference,
)

logger = logging.getLogger(__name__)

PROHIBITED_KEYS = {
    "api_key", "secret", "password", "token", "credentials",
    "chain_of_thought", "reasoning_trace", "think", "hidden_prompt",
    "private_tools", "private_knowledge", "internal_logs",
}


class CollaborationContextBuilder:
    """
    Constructs minimal, pruned CollaborationContext for receiving WorkUnits.
    """

    def build_context(
        self,
        task: Task,
        plan: TaskPlan,
        work_unit: WorkUnit,
        contract: Optional[TeamCollaborationContract] = None,
        handoffs: Optional[List[CollaborationHandoff]] = None,
    ) -> CollaborationContext:
        """
        Derives minimal context for work_unit.
        """
        received_outputs: Dict[str, Any] = {}
        artifact_refs: List[ArtifactReference] = []
        seen_art_ids = set()

        if handoffs:
            for handoff in handoffs:
                # Merge clean payload (excluding prohibited fields)
                clean_payload = self._sanitize_dict(handoff.payload)
                received_outputs.update(clean_payload)

                # Collect artifact references
                for ref in handoff.artifact_references:
                    if ref.artifact_id not in seen_art_ids:
                        seen_art_ids.add(ref.artifact_id)
                        artifact_refs.append(ref)

        contract_id = contract.contract_id if contract else work_unit.collaboration_contract_id

        # Prune constraints to relevant ones
        relevant_constraints = {
            "format": task.constraints.format,
            "language": task.constraints.language,
            "quality_level": task.constraints.quality_level,
        }

        return CollaborationContext(
            task_id=task.task_id,
            work_unit_id=work_unit.work_unit_id,
            objective=work_unit.objective,
            constraints=relevant_constraints,
            required_inputs=list(work_unit.inputs),
            received_outputs=received_outputs,
            artifact_references=artifact_refs,
            relevant_contract_id=contract_id,
            quality_requirements=list(work_unit.quality_requirements),
        )

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively removes prohibited fields (keys containing secrets/reasoning)."""
        clean: Dict[str, Any] = {}
        for k, v in data.items():
            if any(p_key in k.lower() for p_key in PROHIBITED_KEYS):
                continue
            if isinstance(v, dict):
                clean[k] = self._sanitize_dict(v)
            else:
                clean[k] = v
        return clean
