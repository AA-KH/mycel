"""
Collaboration Service (Phase 11 Multi-Agent Collaboration Facade)

Coordinates:
- Session Creation & Contract Pairing (CollaborationRouter)
- Deterministic Handoff Validation (HandoffValidator)
- Minimal Context Projection (CollaborationContextBuilder)
- Handoff Delivery, Acknowledgement, & Rejection
- Bounded Clarification Loops (max 2 clarifications, max 5 handoffs per session)
- Session Completion, Blocking, & Error Handling

Strict Boundaries:
- Does NOT execute Agents, call LLMs, hire Employees, or invoke Tools.
- Does NOT upload physical binaries or call Cloudinary.
"""

import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from tasks.models import Task, TaskPlan, WorkUnit
from execution.collaboration.registry import TeamCollaborationContractRegistry
from execution.collaboration.models import TeamCollaborationContract
from execution.collaboration.session import (
    CollaborationSession,
    CollaborationSessionStatus,
    CollaborationHandoff,
    HandoffAckStatus,
    CollaborationClarification,
    ClarificationSessionStatus,
    CollaborationContext,
    ArtifactReference,
    CollaborationErrorCode,
)
from execution.collaboration.collaboration_router import CollaborationRouter
from execution.collaboration.handoff_validator import HandoffValidator
from execution.collaboration.context_builder import CollaborationContextBuilder

logger = logging.getLogger(__name__)


class CollaborationService:
    """
    Facade service orchestrating session lifecycle, handoffs, context projection,
    and structured clarification.
    """

    def __init__(self, contract_registry: TeamCollaborationContractRegistry):
        self._contracts = contract_registry
        self._router = CollaborationRouter(contract_registry)
        self._validator = HandoffValidator(contract_registry)
        self._context_builder = CollaborationContextBuilder()

        # In-memory storage for active sessions & handoffs
        self._sessions: Dict[str, CollaborationSession] = {}
        self._handoffs: Dict[str, List[CollaborationHandoff]] = {}
        self._clarifications: Dict[str, List[CollaborationClarification]] = {}

    def request_collaboration(
        self,
        task_id: str,
        source_work_unit: WorkUnit,
        target_work_unit: WorkUnit,
    ) -> Tuple[Optional[CollaborationSession], Optional[str]]:
        """
        Creates and registers a CollaborationSession for dependent WorkUnits.
        Enforces DEFAULT DENY policy via CollaborationRouter.
        """
        session, error = self._router.resolve_and_create_session(
            task_id, source_work_unit, target_work_unit
        )
        if error or not session:
            return None, error

        self._sessions[session.session_id] = session
        self._handoffs[session.session_id] = []
        self._clarifications[session.session_id] = []
        session.status = CollaborationSessionStatus.READY
        return session, None

    def create_and_deliver_handoff(
        self,
        session_id: str,
        payload: Dict[str, Any],
        artifact_references: Optional[List[ArtifactReference]] = None,
        summary: str = "",
        handoff_id: Optional[str] = None,
    ) -> Tuple[Optional[CollaborationHandoff], Optional[str]]:
        """
        Validates and delivers a structured CollaborationHandoff.
        Enforces loop protection (max_handoffs limit).
        """
        session = self._sessions.get(session_id)
        if not session:
            return None, f"CollaborationSession '{session_id}' not found."

        if session.is_terminal:
            return None, f"Cannot deliver handoff to session '{session_id}' in terminal state '{session.status}'."

        # Idempotency check
        hid = handoff_id or f"handoff_{uuid.uuid4().hex[:8]}"
        existing_handoffs = self._handoffs.get(session_id, [])
        for existing in existing_handoffs:
            if existing.handoff_id == hid:
                return existing, None

        # Loop protection check
        if session.handoff_count >= session.max_handoffs:
            session.status = CollaborationSessionStatus.BLOCKED
            err = (
                f"{CollaborationErrorCode.COLLABORATION_LOOP}: "
                f"Session exceeded maximum allowed handoffs ({session.max_handoffs}). Session BLOCKED."
            )
            logger.error(err)
            return None, err

        # Create candidate handoff object
        handoff = CollaborationHandoff(
            handoff_id=hid,
            session_id=session_id,
            source_work_unit_id=session.source_work_unit_id,
            target_work_unit_id=session.target_work_unit_id,
            contract_id=session.contract_id,
            payload=payload,
            artifact_references=artifact_references or [],
            summary=summary or f"Handoff from {session.source_team_id} to {session.target_team_id}",
            status=HandoffAckStatus.ACCEPTED,
        )

        # Deterministic Validation
        contract = self._contracts.get(session.contract_id)
        valid, errors = self._validator.validate_handoff(
            handoff, session.source_team_id, session.target_team_id, contract
        )

        if not valid:
            handoff.status = HandoffAckStatus.REJECTED
            handoff.validation_errors = errors
            session.status = CollaborationSessionStatus.BLOCKED
            err_msg = f"Handoff validation failed: {'; '.join(errors)}"
            logger.warning(err_msg)
            return handoff, err_msg
            
        # Security Gateway Interception (Phase 17)
        from security.gateway import SecurityGateway
        from security.models import SecurityRequest, SecurityContext, ActionType, SecurityDecisionStatus
        
        sec_gateway = SecurityGateway()
        sec_context = SecurityContext(
            team_id=session.source_team_id,
            task_id=session.task_id,
            session_id=session_id
        )
        sec_request = SecurityRequest(
            request_id=hid,
            trace_id=session.task_id,
            context=sec_context,
            action_type=ActionType.AGENT_HANDOFF,
            resource=session.target_work_unit_id,
            intent=summary or f"Handoff to {session.target_team_id}",
            payload_metadata={"keys": list(payload.keys())},
            target_agent_id=session.target_work_unit_id
        )
        decision = sec_gateway.evaluate_request(sec_request)
        
        if decision.status != SecurityDecisionStatus.ALLOW:
            handoff.status = HandoffAckStatus.REJECTED
            handoff.validation_errors = [f"Security Gateway Denied Handoff: {decision.reason}"]
            session.status = CollaborationSessionStatus.BLOCKED
            err_msg = f"Security Gateway Denied Handoff: {decision.reason}"
            logger.warning(err_msg)
            return handoff, err_msg

        # Save delivered handoff & update session status
        session.handoff_count += 1
        session.status = CollaborationSessionStatus.HANDOFF_READY
        session.updated_at = datetime.now(timezone.utc)
        self._handoffs.setdefault(session_id, []).append(handoff)

        return handoff, None

    def acknowledge_handoff(
        self,
        session_id: str,
        handoff_id: str,
        status: HandoffAckStatus,
        feedback: str = "",
    ) -> Tuple[Optional[CollaborationSession], Optional[str]]:
        """
        Acknowledges delivery of handoff (ACCEPTED / REJECTED).
        """
        session = self._sessions.get(session_id)
        if not session:
            return None, f"Session '{session_id}' not found."

        handoffs = self._handoffs.get(session_id, [])
        matching_handoff = next((h for h in handoffs if h.handoff_id == handoff_id), None)
        if not matching_handoff:
            return None, f"Handoff '{handoff_id}' not found in session '{session_id}'."

        matching_handoff.status = status

        if status == HandoffAckStatus.ACCEPTED:
            session.status = CollaborationSessionStatus.COMPLETED
        elif status == HandoffAckStatus.REJECTED:
            session.status = CollaborationSessionStatus.BLOCKED
            matching_handoff.validation_errors.append(f"Handoff rejected by receiver: {feedback}")

        session.updated_at = datetime.now(timezone.utc)
        return session, None

    def request_clarification(
        self,
        session_id: str,
        question: str,
        required_input: str,
        reason: str = "",
    ) -> Tuple[Optional[CollaborationClarification], Optional[str]]:
        """
        Requests structured clarification for a session.
        Enforces maximum clarification limit (max 2).
        """
        session = self._sessions.get(session_id)
        if not session:
            return None, f"Session '{session_id}' not found."

        if session.clarification_count >= session.max_clarifications:
            session.status = CollaborationSessionStatus.BLOCKED
            err = (
                f"{CollaborationErrorCode.MAX_CLARIFICATIONS_EXCEEDED}: "
                f"Session exceeded max allowed clarifications ({session.max_clarifications}). Session BLOCKED."
            )
            logger.error(err)
            return None, err

        cid = f"clar_{uuid.uuid4().hex[:8]}"
        clarification = CollaborationClarification(
            clarification_id=cid,
            session_id=session_id,
            question=question,
            required_input=required_input,
            reason=reason,
            status=ClarificationSessionStatus.PENDING,
        )

        session.clarification_count += 1
        session.status = CollaborationSessionStatus.WAITING_FOR_INPUT
        session.updated_at = datetime.now(timezone.utc)
        self._clarifications.setdefault(session_id, []).append(clarification)

        return clarification, None

    def resolve_clarification(
        self,
        session_id: str,
        clarification_id: str,
        response_payload: Dict[str, Any],
    ) -> Tuple[Optional[CollaborationSession], Optional[str]]:
        """
        Resolves pending clarification and restores session status to ACTIVE.
        """
        session = self._sessions.get(session_id)
        if not session:
            return None, f"Session '{session_id}' not found."

        clarifications = self._clarifications.get(session_id, [])
        clar = next((c for c in clarifications if c.clarification_id == clarification_id), None)
        if not clar:
            return None, f"Clarification '{clarification_id}' not found in session '{session_id}'."

        clar.response_payload = response_payload
        clar.status = ClarificationSessionStatus.RESOLVED
        session.status = CollaborationSessionStatus.ACTIVE
        session.updated_at = datetime.now(timezone.utc)
        return session, None

    def get_context_for_work_unit(
        self, task: Task, plan: TaskPlan, work_unit: WorkUnit
    ) -> CollaborationContext:
        """
        Constructs minimal context for work_unit from delivered session handoffs.
        """
        # Find sessions where work_unit is target
        target_sessions = [
            s for s in self._sessions.values()
            if s.task_id == task.task_id and s.target_work_unit_id == work_unit.work_unit_id
        ]
        all_handoffs: List[CollaborationHandoff] = []
        contract = None

        for s in target_sessions:
            handoffs = self._handoffs.get(s.session_id, [])
            all_handoffs.extend(handoffs)
            if not contract:
                contract = self._contracts.get(s.contract_id)

        return self._context_builder.build_context(
            task, plan, work_unit, contract, all_handoffs
        )

    def get_session(self, session_id: str) -> Optional[CollaborationSession]:
        return self._sessions.get(session_id)

    def get_handoffs(self, session_id: str) -> List[CollaborationHandoff]:
        return self._handoffs.get(session_id, [])
