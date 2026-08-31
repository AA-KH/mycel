"""
Delivery Resolver (Phase 14)

Resolves which Artifacts from the internal store should be included in a
delivery package for a given Task and OutputContract.

The resolver:
- Loads Artifact records from the artifact repository (in-memory for Phase 14).
- Matches artifacts against the OutputContract policy (format, artifact_policy).
- Produces a list of DeliveryItems ready for packaging.

It does NOT:
- Generate or modify artifacts.
- Call the LLM or any external inference service.
- Mutate the TaskPlan.
"""

import logging
from typing import List, Optional, Dict

from artifacts.models import Artifact, ArtifactStatus
from outputs.models import OutputContract, ArtifactPolicy
from delivery.models import DeliveryItem, DeliveryItemStatus

logger = logging.getLogger(__name__)


class DeliveryResolutionError(Exception):
    """Raised when resolution cannot produce a valid DeliveryItem set."""


class DeliveryResolver:
    """
    Resolves Artifacts into DeliveryItems for a given Task.
    """

    def __init__(self, artifact_store: Optional[Dict[str, List[Artifact]]] = None):
        # artifact_store maps task_id -> list of Artifact records.
        # In production this would be an injected ArtifactRepository.
        self._store: Dict[str, List[Artifact]] = artifact_store or {}

    def register_artifact(self, artifact: Artifact) -> None:
        """Register an artifact into the resolver's store (used in tests)."""
        self._store.setdefault(artifact.task_id, []).append(artifact)

    def resolve(
        self,
        task_id: str,
        contract: Optional[OutputContract] = None,
    ) -> List[DeliveryItem]:
        """
        Returns a list of DeliveryItems for the given task.

        If an OutputContract is provided:
        - Enforces artifact_policy (REQUIRED → error if none found).
        - Filters by allowed formats if specified.
        """
        artifacts = self._store.get(task_id, [])

        # Only deliver artifacts that are in READY state
        ready_artifacts = [a for a in artifacts if a.status == ArtifactStatus.READY]

        if contract is not None:
            if contract.artifact_policy == ArtifactPolicy.REQUIRED and not ready_artifacts:
                raise DeliveryResolutionError(
                    f"OutputContract '{contract.output_contract_id}' requires an artifact "
                    f"for task '{task_id}', but none were found in READY state."
                )

            # Filter by allowed formats (mime extension matching)
            if contract.formats:
                ready_artifacts = [
                    a for a in ready_artifacts
                    if any(a.filename.lower().endswith(f".{fmt.lower()}") for fmt in contract.formats)
                ]

                if contract.artifact_policy == ArtifactPolicy.REQUIRED and not ready_artifacts:
                    raise DeliveryResolutionError(
                        f"No READY artifacts in allowed formats {contract.formats} "
                        f"for task '{task_id}'."
                    )

        return [self._to_delivery_item(a) for a in ready_artifacts]

    @staticmethod
    def _to_delivery_item(artifact: Artifact) -> DeliveryItem:
        return DeliveryItem(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.type,
            mime_type=artifact.mime_type,
            filename=artifact.filename,
            size_bytes=artifact.size_bytes,
            storage_provider=artifact.storage_provider,
            url=artifact.url,
            secure_url=artifact.secure_url,
            status=DeliveryItemStatus.PENDING,  # Will be updated by signer
            metadata=artifact.metadata,
        )
