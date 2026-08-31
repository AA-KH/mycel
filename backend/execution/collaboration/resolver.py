import logging
from typing import List, Optional
from execution.collaboration.models import TeamCollaborationContract, CollaborationStatus
from execution.collaboration.registry import TeamCollaborationContractRegistry

logger = logging.getLogger(__name__)


class TeamCollaborationResolver:
    """
    Deterministically resolves which Collaboration Contract applies to a
    (requesting_team_id, providing_team_id, request_type) triple.

    Rules:
        - Only ACTIVE contracts are returned.
        - Resolution is deterministic: same inputs → same contract, always.
        - No LLM, no semantic matching, no scoring.
        - Does NOT select a provider team — the provider is already known.
        - Does NOT route tasks.
    """

    def __init__(self, registry: TeamCollaborationContractRegistry):
        self.registry = registry

    def find_contract(
        self,
        requesting_team_id: str,
        providing_team_id: str,
        request_type: str,
    ) -> Optional[TeamCollaborationContract]:
        """
        Returns the ACTIVE collaboration contract for the given triple.
        Returns None if no matching ACTIVE contract exists.

        Tie-break: lowest contract_id alphabetically (stable, deterministic).
        """
        candidates = [
            c for c in self.registry.list_active()
            if c.requesting_team_id == requesting_team_id
            and c.providing_team_id == providing_team_id
            and request_type in c.accepted_request_types
        ]

        if not candidates:
            logger.debug(
                f"No ACTIVE collaboration contract for "
                f"requesting='{requesting_team_id}' "
                f"providing='{providing_team_id}' "
                f"request_type='{request_type}'"
            )
            return None

        # Stable deterministic tie-break: (version asc, contract_id asc)
        candidates.sort(key=lambda c: (c.version, c.contract_id))
        return candidates[0]

    def find_contract_by_id(
        self, contract_id: str
    ) -> Optional[TeamCollaborationContract]:
        """Returns an ACTIVE contract by its stable ID."""
        contract = self.registry.get(contract_id)
        if contract and contract.status == CollaborationStatus.ACTIVE:
            return contract
        return None

    def list_for_requesting_team(
        self, requesting_team_id: str
    ) -> List[TeamCollaborationContract]:
        """All ACTIVE contracts where this team is the requester."""
        return self.registry.get_active_by_requesting_team(requesting_team_id)

    def list_for_providing_team(
        self, providing_team_id: str
    ) -> List[TeamCollaborationContract]:
        """All ACTIVE contracts where this team is the provider."""
        return self.registry.get_active_by_providing_team(providing_team_id)

    def can_collaborate(
        self,
        requesting_team_id: str,
        providing_team_id: str,
        request_type: str,
    ) -> bool:
        """True if an ACTIVE contract governs this collaboration."""
        return (
            self.find_contract(requesting_team_id, providing_team_id, request_type)
            is not None
        )
