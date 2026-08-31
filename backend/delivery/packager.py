"""
Delivery Packager (Phase 14)

Assembles a DeliveryPackage from a list of resolved DeliveryItems
based on the delivery format and OutputContract delivery policy.

Packager responsibilities:
- Apply the chosen DeliveryFormat.
- Set expiry windows from the request TTL or contract default.
- Produce a coherent DeliveryPackage ready for URL signing.

Packager does NOT:
- Sign URLs (that is the Signer's responsibility).
- Persist the package (that is the Repository's responsibility).
- Call any LLM or inference service.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from delivery.models import (
    DeliveryPackage, DeliveryItem, DeliveryFormat, DeliveryStatus, DeliveryRequest
)
from outputs.models import OutputContract

logger = logging.getLogger(__name__)


class DeliveryPackager:
    """
    Assembles a DeliveryPackage from a resolved list of DeliveryItems.
    """

    DEFAULT_TTL_SECONDS = 3600  # 1 hour if not specified

    def package(
        self,
        request: DeliveryRequest,
        items: List[DeliveryItem],
        contract: Optional[OutputContract] = None,
    ) -> DeliveryPackage:
        """
        Builds a DeliveryPackage according to the requested format.
        """
        if not items:
            return DeliveryPackage(
                task_id=request.task_id,
                output_contract_id=request.output_contract_id,
                output_contract_version=contract.version if contract else None,
                format=request.format,
                status=DeliveryStatus.FAILED,
                items=[],
                metadata={"reason": "No deliverable artifacts found."},
            )

        ttl = request.signed_url_ttl_seconds or self.DEFAULT_TTL_SECONDS
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)

        # Set the expiry on each item before handing to the signer
        for item in items:
            item.expires_at = expires_at

        # Determine format — honour the request, but coerce to DOWNLOAD_BUNDLE
        # when multiple items exist and DIRECT_URL was requested.
        effective_format = request.format
        if effective_format == DeliveryFormat.DIRECT_URL and len(items) > 1:
            effective_format = DeliveryFormat.DOWNLOAD_BUNDLE
            logger.info(
                f"Coerced format to DOWNLOAD_BUNDLE for task '{request.task_id}' "
                f"because multiple artifacts ({len(items)}) were resolved."
            )

        package = DeliveryPackage(
            task_id=request.task_id,
            output_contract_id=request.output_contract_id,
            output_contract_version=contract.version if contract else None,
            format=effective_format,
            status=DeliveryStatus.PACKAGING,
            items=items,
            expires_at=expires_at,
            packaged_at=datetime.now(timezone.utc),
            metadata=request.metadata,
        )

        return package
