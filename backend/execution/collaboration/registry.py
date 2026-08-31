import logging
from typing import Dict, List, Optional
from execution.collaboration.models import TeamCollaborationContract, CollaborationStatus

logger = logging.getLogger(__name__)


class CollaborationContractRegistryError(Exception):
    pass


class TeamCollaborationContractRegistry:
    """
    Stores and retrieves TeamCollaborationContracts.

    Boundary:
        - Strictly separate from TeamRegistry, PipelineRegistry,
          ExecutionContractRegistry.
        - Does NOT execute contracts.
        - Does NOT route tasks.
        - Does NOT select teams.
    """

    def __init__(self):
        self._contracts: Dict[str, TeamCollaborationContract] = {}

    # ── Write ──────────────────────────────────────────────────────────────

    def register(self, contract: TeamCollaborationContract) -> None:
        if not contract.contract_id:
            raise CollaborationContractRegistryError(
                "Collaboration contract must have a contract_id."
            )
        if contract.contract_id in self._contracts:
            raise CollaborationContractRegistryError(
                f"Collaboration contract '{contract.contract_id}' is already registered."
            )
        self._contracts[contract.contract_id] = contract
        logger.info(f"Registered collaboration contract: {contract.contract_id}")

    def unregister(self, contract_id: str) -> None:
        self._contracts.pop(contract_id, None)

    # ── Read ───────────────────────────────────────────────────────────────

    def get(self, contract_id: str) -> Optional[TeamCollaborationContract]:
        return self._contracts.get(contract_id)

    def exists(self, contract_id: str) -> bool:
        return contract_id in self._contracts

    def list_all(self) -> List[TeamCollaborationContract]:
        return list(self._contracts.values())

    def list_active(self) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if c.status == CollaborationStatus.ACTIVE
        ]

    def get_by_requesting_team(self, team_id: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if c.requesting_team_id == team_id
        ]

    def get_active_by_requesting_team(self, team_id: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if c.requesting_team_id == team_id
            and c.status == CollaborationStatus.ACTIVE
        ]

    def get_by_providing_team(self, team_id: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if c.providing_team_id == team_id
        ]

    def get_active_by_providing_team(self, team_id: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if c.providing_team_id == team_id
            and c.status == CollaborationStatus.ACTIVE
        ]

    def get_by_request_type(self, request_type: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if request_type in c.accepted_request_types
        ]

    def get_active_by_request_type(self, request_type: str) -> List[TeamCollaborationContract]:
        return [
            c for c in self._contracts.values()
            if request_type in c.accepted_request_types
            and c.status == CollaborationStatus.ACTIVE
        ]

    # ── Summary ────────────────────────────────────────────────────────────

    def count(self) -> int:
        return len(self._contracts)

    def requesting_team_ids(self) -> List[str]:
        return list({c.requesting_team_id for c in self._contracts.values()})

    def providing_team_ids(self) -> List[str]:
        return list({c.providing_team_id for c in self._contracts.values()})
