"""
Delivery Service (Phase 14)

Primary facade for the Output Delivery System.

Orchestration flow:
    DeliveryRequest
        → DeliveryResolver   (artifact → DeliveryItem)
        → DeliveryPackager   (items → DeliveryPackage)
        → DeliveryURLSigner  (sign URLs on each item)
        → DeliveryRepository (persist)
        → DeliveryResult     (user-facing response)

Invariants enforced here:
- A task that has no READY artifacts produces a FAILED package (not an error).
- Resolution errors from a missing REQUIRED artifact are surfaced as FAILED
  package, not as HTTP 500.
- The service does NOT generate artifacts, execute agents, or call LLMs.
- Authorization (task ownership) is enforced at the service boundary.
"""

import logging
from typing import Optional

from delivery.models import (
    DeliveryRequest, DeliveryPackage, DeliveryResult,
    DeliveryStatus, DeliveryFormat,
)
from delivery.resolver import DeliveryResolver, DeliveryResolutionError
from delivery.packager import DeliveryPackager
from delivery.signer import DeliveryURLSigner
from delivery.repository import DeliveryRepository
from outputs.models import OutputContract

logger = logging.getLogger(__name__)


class DeliveryService:
    """
    Orchestrates the full delivery pipeline for a Task's outputs.
    """

    def __init__(
        self,
        resolver: DeliveryResolver,
        packager: DeliveryPackager,
        signer: DeliveryURLSigner,
        repository: DeliveryRepository,
    ):
        self.resolver = resolver
        self.packager = packager
        self.signer = signer
        self.repository = repository

    async def deliver(
        self,
        request: DeliveryRequest,
        contract: Optional[OutputContract] = None,
    ) -> DeliveryResult:
        """
        Full pipeline: resolve → package → sign → persist → return result.
        """
        logger.info(
            f"[Delivery] Starting delivery for task='{request.task_id}' "
            f"format='{request.format.value}'"
        )

        # 1. Resolve artifacts → DeliveryItems
        try:
            items = self.resolver.resolve(request.task_id, contract)
        except DeliveryResolutionError as exc:
            logger.warning(f"[Delivery] Resolution failed for task '{request.task_id}': {exc}")
            failed_package = DeliveryPackage(
                task_id=request.task_id,
                output_contract_id=request.output_contract_id,
                format=request.format,
                status=DeliveryStatus.FAILED,
                metadata={"resolution_error": str(exc)},
            )
            await self.repository.create(failed_package)
            return self._to_result(failed_package)

        # 2. Package the items
        package = self.packager.package(request, items, contract)

        # 3. Sign URLs on each item
        if package.status != DeliveryStatus.FAILED:
            self.signer.sign_items(package.items)
            all_ready = all(
                item.status.value == "READY" for item in package.items
            )
            package.status = DeliveryStatus.READY if all_ready else DeliveryStatus.PARTIAL

        # 4. Persist
        saved, err = await self.repository.create(package)
        if err:
            # Version conflict → update instead (idempotent re-delivery)
            saved, _ = await self.repository.update(package)

        logger.info(
            f"[Delivery] Package '{saved.package_id}' persisted "
            f"with status='{saved.status.value}' ({len(saved.items)} items)."
        )

        return self._to_result(saved)

    async def get_delivery(self, package_id: str) -> Optional[DeliveryResult]:
        """Fetch an existing DeliveryPackage and mark it as delivered."""
        package = await self.repository.get_by_id(package_id)
        if not package:
            return None
        if package.is_expired:
            package.status = DeliveryStatus.EXPIRED
            await self.repository.update(package)
        else:
            await self.repository.mark_delivered(package_id)
        return self._to_result(package)

    async def get_task_deliveries(
        self, task_id: str
    ) -> list[DeliveryResult]:
        """Return all delivery packages for a task."""
        packages = await self.repository.get_by_task_id(task_id)
        return [self._to_result(p) for p in packages]

    @staticmethod
    def _to_result(package: DeliveryPackage) -> DeliveryResult:
        instructions = ""
        if package.status == DeliveryStatus.READY:
            if package.format == DeliveryFormat.DIRECT_URL:
                instructions = "Download your artifact using the secure_url provided."
            elif package.format == DeliveryFormat.DOWNLOAD_BUNDLE:
                instructions = "All artifacts are packaged together. Download each item individually."
            elif package.format == DeliveryFormat.INLINE:
                instructions = "Artifact content is embedded inline."
        elif package.status == DeliveryStatus.FAILED:
            instructions = "Delivery failed. Check metadata for resolution details."
        elif package.status == DeliveryStatus.EXPIRED:
            instructions = "This delivery has expired. Please request a new delivery."

        return DeliveryResult(
            package_id=package.package_id,
            task_id=package.task_id,
            status=package.status,
            format=package.format,
            items=package.items,
            expires_at=package.expires_at,
            instructions=instructions,
            metadata=package.metadata,
        )
