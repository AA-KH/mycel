"""
Collaboration Router (Phase 11 Multi-Agent Collaboration)

Responsibilities:
- Resolves target WorkUnit and Team for a collaboration request.
- Validates active TeamCollaborationContract between providing and requesting teams.
- Creates and initializes a CollaborationSession.
- Does NOT execute Agents, hire Employees, or invoke Tools.
"""

import uuid
import logging
from typing import Tuple, Optional

from tasks.models import TaskPlan, WorkUnit
from execution.collaboration.registry import TeamCollaborationContractRegistry
from execution.collaboration.models import TeamCollaborationContract
from execution.collaboration.session import (
    CollaborationSession,
    CollaborationSessionStatus,
    CollaborationErrorCode,
)

logger = logging.getLogger(__name__)


class CollaborationRouter:
    """
    Resolves collaboration routing and contract pairing between WorkUnits.
    """

    def __init__(self, contract_registry: TeamCollaborationContractRegistry):
        self._contracts = contract_registry

    def resolve_and_create_session(
        self,
        task_id: str,
        source_work_unit: WorkUnit,
        target_work_unit: WorkUnit,
    ) -> Tuple[Optional[CollaborationSession], Optional[str]]:
        """
        Resolves active CollaborationContract between source_work_unit (provider)
        and target_work_unit (requester) and returns initialized CollaborationSession.
        """
        source_team = source_work_unit.team_id
        target_team = target_work_unit.team_id

        # 1. Search active contracts where source_team is provider and target_team is requester
        collab_contracts = self._contracts.get_active_by_providing_team(source_team)
        matching = [c for c in collab_contracts if c.requesting_team_id == target_team]

        if not matching:
            error_msg = (
                f"{CollaborationErrorCode.CONTRACT_INVALID}: "
                f"No active TeamCollaborationContract found between provider '{source_team}' "
                f"and requester '{target_team}' (Default Deny enforced)."
            )
            logger.warning(error_msg)
            return None, error_msg

        contract = matching[0]
        session_id = f"session_{task_id[:8]}_{source_work_unit.work_unit_id}_to_{target_work_unit.work_unit_id}"

        session = CollaborationSession(
            session_id=session_id,
            task_id=task_id,
            source_work_unit_id=source_work_unit.work_unit_id,
            target_work_unit_id=target_work_unit.work_unit_id,
            source_team_id=source_team,
            target_team_id=target_team,
            contract_id=contract.contract_id,
            status=CollaborationSessionStatus.CREATED,
            max_handoffs=contract.collaboration_constraints.max_round_trips * 5,
            max_clarifications=2,
        )

        return session, None
