import logging
from typing import Dict, List, Optional
from execution.contracts.models import TeamExecutionContract, ContractStatus

logger = logging.getLogger(__name__)


class ExecutionContractRegistryError(Exception):
    pass


class ExecutionContractRegistry:
    """
    Stores and provides access to TeamExecutionContracts.

    Responsibilities:
        - register / unregister contracts
        - lookup by contract_id
        - list all / list by team / list by task_type

    NOT responsible for:
        - executing contracts
        - matching tasks to teams
        - selecting members
    """

    def __init__(self):
        self._contracts: Dict[str, TeamExecutionContract] = {}

    # ── Write ──────────────────────────────────────────────────────────────

    def register(self, contract: TeamExecutionContract) -> None:
        if not contract.contract_id:
            raise ExecutionContractRegistryError("Contract must have a contract_id.")
        if contract.contract_id in self._contracts:
            raise ExecutionContractRegistryError(
                f"Contract '{contract.contract_id}' is already registered."
            )
        self._contracts[contract.contract_id] = contract
        logger.info(f"Registered execution contract: {contract.contract_id}")

    def unregister(self, contract_id: str) -> None:
        self._contracts.pop(contract_id, None)

    # ── Read ───────────────────────────────────────────────────────────────

    def get(self, contract_id: str) -> Optional[TeamExecutionContract]:
        return self._contracts.get(contract_id)

    def exists(self, contract_id: str) -> bool:
        return contract_id in self._contracts

    def list_all(self) -> List[TeamExecutionContract]:
        return list(self._contracts.values())

    def list_active(self) -> List[TeamExecutionContract]:
        return [c for c in self._contracts.values() if c.status == ContractStatus.ACTIVE]

    def get_by_team(self, team_id: str) -> List[TeamExecutionContract]:
        return [c for c in self._contracts.values() if c.team_id == team_id]

    def get_active_by_team(self, team_id: str) -> List[TeamExecutionContract]:
        return [
            c for c in self._contracts.values()
            if c.team_id == team_id and c.status == ContractStatus.ACTIVE
        ]

    def get_by_task_type(self, task_type: str) -> List[TeamExecutionContract]:
        return [
            c for c in self._contracts.values()
            if task_type in c.accepted_task_types
        ]

    def get_active_by_task_type(self, task_type: str) -> List[TeamExecutionContract]:
        return [
            c for c in self._contracts.values()
            if task_type in c.accepted_task_types
            and c.status == ContractStatus.ACTIVE
        ]

    # ── Summary ────────────────────────────────────────────────────────────

    def count(self) -> int:
        return len(self._contracts)

    def team_ids(self) -> List[str]:
        return list({c.team_id for c in self._contracts.values()})
