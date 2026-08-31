import logging
from typing import Optional
from execution.contracts.models import TeamExecutionContract, ContractStatus
from execution.contracts.registry import ExecutionContractRegistry

logger = logging.getLogger(__name__)


class TeamExecutionContractResolver:
    """
    Deterministically resolves which Execution Contract applies to a
    given team_id + task_type combination.

    Rules:
        - Only ACTIVE contracts are returned.
        - Resolution is deterministic: same inputs → same contract, always.
        - No LLM, no semantic matching, no scoring, no ranking.
        - Does NOT select the Team — it resolves an already-known Team's contract.
    """

    def __init__(self, registry: ExecutionContractRegistry):
        self.registry = registry

    def find_contract(
        self,
        team_id: str,
        task_type: str,
    ) -> Optional[TeamExecutionContract]:
        """
        Returns the ACTIVE contract for the given team + task_type.
        Returns None if no matching ACTIVE contract exists.

        Deterministic: sorted by contract_id ascending when multiple
        contracts match (should not happen with stable IDs, but provides
        a reliable fallback).
        """
        candidates = [
            c for c in self.registry.get_active_by_team(team_id)
            if task_type in c.accepted_task_types
        ]

        if not candidates:
            logger.debug(
                f"No ACTIVE contract found for team='{team_id}', task_type='{task_type}'"
            )
            return None

        # Stable deterministic ordering — lowest contract_id wins
        candidates.sort(key=lambda c: (c.version, c.contract_id))
        return candidates[0]

    def find_contract_by_id(self, contract_id: str) -> Optional[TeamExecutionContract]:
        """Returns an ACTIVE contract by its stable ID."""
        contract = self.registry.get(contract_id)
        if contract and contract.status == ContractStatus.ACTIVE:
            return contract
        return None

    def list_contracts_for_team(self, team_id: str):
        """Lists all ACTIVE contracts for a team."""
        return self.registry.get_active_by_team(team_id)

    def supports_task_type(self, team_id: str, task_type: str) -> bool:
        """Returns True if the team has an ACTIVE contract accepting this task type."""
        return self.find_contract(team_id, task_type) is not None
