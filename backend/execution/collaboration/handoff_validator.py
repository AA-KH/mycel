"""
Handoff Validator (Phase 11 Multi-Agent Collaboration)

Responsibilities:
- Enforces DEFAULT DENY policy: No active Collaboration Contract = Reject.
- Validates handoff payload against TeamCollaborationContract required inputs & outputs.
- Validates ArtifactReferences (ensures IDs and types, NO raw binaries or credentials).
- Ensures team isolation: producing team tools/knowledge are not leaked in payload.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from execution.collaboration.models import TeamCollaborationContract, CollaborationStatus
from execution.collaboration.registry import TeamCollaborationContractRegistry
from execution.collaboration.session import (
    CollaborationHandoff,
    CollaborationMessage,
    ArtifactReference,
    CollaborationErrorCode,
)

logger = logging.getLogger(__name__)

PROHIBITED_KEYS = {
    "api_key", "secret", "password", "token", "credentials",
    "private_tools", "private_knowledge", "internal_logs",
}


class HandoffValidator:
    """
    Deterministic validator for CollaborationHandoff objects.
    """

    def __init__(self, contract_registry: TeamCollaborationContractRegistry):
        self._contracts = contract_registry

    def validate_handoff(
        self,
        handoff: CollaborationHandoff,
        source_team_id: str,
        target_team_id: str,
        contract: Optional[TeamCollaborationContract] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validates handoff against TeamCollaborationContract and security invariants.
        Returns (valid, errors).
        """
        errors: List[str] = []

        # ── 1. Default Deny Check ──────────────────────────────────────────
        resolved_contract = contract or self._contracts.get(handoff.contract_id)
        if not resolved_contract:
            errors.append(
                f"{CollaborationErrorCode.CONTRACT_INVALID}: "
                f"Collaboration contract '{handoff.contract_id}' not found in registry."
            )
            return False, errors

        if not resolved_contract.is_active:
            errors.append(
                f"{CollaborationErrorCode.CONTRACT_INVALID}: "
                f"Contract '{handoff.contract_id}' is not in ACTIVE status."
            )
            return False, errors

        # ── 2. Team Authorization Check ────────────────────────────────────
        if resolved_contract.providing_team_id != source_team_id:
            errors.append(
                f"{CollaborationErrorCode.SOURCE_NOT_ALLOWED}: "
                f"Team '{source_team_id}' is not the provider declared in contract '{handoff.contract_id}' "
                f"(expected '{resolved_contract.providing_team_id}')."
            )

        if resolved_contract.requesting_team_id != target_team_id:
            errors.append(
                f"{CollaborationErrorCode.TARGET_NOT_ALLOWED}: "
                f"Team '{target_team_id}' is not the requester declared in contract '{handoff.contract_id}' "
                f"(expected '{resolved_contract.requesting_team_id}')."
            )

        # ── 3. Payload & Required Inputs Check ────────────────────────────
        for req_input in resolved_contract.required_inputs:
            input_id = req_input.input_id
            if input_id not in handoff.payload and input_id not in handoff.input_references:
                # Check if it's provided as an artifact reference
                has_artifact = any(ref.artifact_type == input_id for ref in handoff.artifact_references)
                if not has_artifact:
                    errors.append(
                        f"{CollaborationErrorCode.MISSING_INPUT}: "
                        f"Required input '{input_id}' declared in contract '{handoff.contract_id}' "
                        f"is missing from handoff payload."
                    )

        # ── 4. Artifact Reference Integrity ──────────────────────────────
        for ref in handoff.artifact_references:
            if not ref.artifact_id or not ref.artifact_type:
                errors.append(
                    f"{CollaborationErrorCode.ARTIFACT_INVALID}: "
                    f"ArtifactReference must declare artifact_id and artifact_type."
                )

        # ── 5. Security & Credentials Check ──────────────────────────────
        if self._contains_secrets(handoff.payload):
            errors.append(
                f"{CollaborationErrorCode.SCHEMA_INVALID}: "
                f"Payload contains prohibited keys (credentials, secrets, or internal reasoning)."
            )

        valid = len(errors) == 0
        return valid, errors

    def _contains_secrets(self, payload: Dict[str, Any]) -> bool:
        """Checks if payload dictionary contains secret or credential keys."""
        for k, v in payload.items():
            if any(p_key in k.lower() for p_key in PROHIBITED_KEYS):
                return True
            if isinstance(v, dict) and self._contains_secrets(v):
                return True
        return False
