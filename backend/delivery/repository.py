"""
Delivery Repository (Phase 14)

Provides CRUD and search capabilities over DeliveryPackage entities.

Implementation:
- In-memory dictionary compatible with the MongoDB repository interface.
- Versioned: each re-delivery creates a new version record; old records are
  never silently overwritten (idempotency + audit trail).
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from delivery.models import DeliveryPackage, DeliveryStatus

logger = logging.getLogger(__name__)


class DeliveryRepository:
    """
    Thread-safe in-memory repository for DeliveryPackages.
    Format: { package_id: { version: DeliveryPackage } }
    """

    def __init__(self):
        # Primary index: package_id → version → DeliveryPackage
        self._store: Dict[str, Dict[int, DeliveryPackage]] = {}
        # Secondary index: task_id → list of package_ids
        self._task_index: Dict[str, List[str]] = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Write operations
    # ─────────────────────────────────────────────────────────────────────────

    async def create(
        self, package: DeliveryPackage
    ) -> Tuple[DeliveryPackage, Optional[str]]:
        """Create a new DeliveryPackage. Errors if version already exists."""
        if package.package_id not in self._store:
            self._store[package.package_id] = {}

        versions = self._store[package.package_id]
        if package.version in versions:
            return package, (
                f"DeliveryPackage '{package.package_id}' "
                f"version {package.version} already exists."
            )

        versions[package.version] = package
        self._task_index.setdefault(package.task_id, [])
        if package.package_id not in self._task_index[package.task_id]:
            self._task_index[package.task_id].append(package.package_id)

        return package, None

    async def update(
        self, package: DeliveryPackage
    ) -> Tuple[DeliveryPackage, Optional[str]]:
        """Upsert a DeliveryPackage version."""
        if package.package_id not in self._store:
            return await self.create(package)

        package.updated_at = datetime.now(timezone.utc)
        self._store[package.package_id][package.version] = package
        return package, None

    # ─────────────────────────────────────────────────────────────────────────
    # Read operations
    # ─────────────────────────────────────────────────────────────────────────

    async def get_by_id(
        self,
        package_id: str,
        version: Optional[int] = None,
    ) -> Optional[DeliveryPackage]:
        """Retrieve a package by ID. Returns the latest version if version is None."""
        if package_id not in self._store:
            return None
        versions = self._store[package_id]
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        return versions[max(versions.keys())]

    async def get_by_task_id(
        self,
        task_id: str,
        status: Optional[DeliveryStatus] = None,
    ) -> List[DeliveryPackage]:
        """Return all latest-version packages for a task, optionally filtered by status."""
        package_ids = self._task_index.get(task_id, [])
        results = []
        for pid in package_ids:
            pkg = await self.get_by_id(pid)
            if pkg and (status is None or pkg.status == status):
                results.append(pkg)
        return results

    async def mark_delivered(self, package_id: str) -> Optional[DeliveryPackage]:
        """Increment delivery_count and set delivered_at."""
        pkg = await self.get_by_id(package_id)
        if not pkg:
            return None
        pkg.delivery_count += 1
        pkg.delivered_at = datetime.now(timezone.utc)
        pkg.status = DeliveryStatus.DELIVERED
        await self.update(pkg)
        return pkg
