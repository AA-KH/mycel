"""
Talent Registry (Phase 15)

In-memory store for TalentCapabilitySnapshots.
Supports:
- Build + register a new snapshot.
- Retrieve a snapshot by employee_id.
- Invalidate (mark stale) when Employee data changes.
- Iterate all snapshots for search.
- Idempotent re-registration (no duplicate records).

In production this would be backed by MongoDB + a secondary
indexed collection. The interface is designed for drop-in replacement.

The registry does NOT:
- Maintain the Employee source of truth.
- Call LLM.
- Hire or assign employees.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from talent.models import TalentCapabilitySnapshot
from talent.snapshot import TalentSnapshotBuilder
from workforce.employees.models import Employee

logger = logging.getLogger(__name__)


class TalentRegistry:
    """
    In-memory snapshot store with build, get, invalidate, and search support.
    """

    def __init__(self):
        # Primary index: employee_id → TalentCapabilitySnapshot
        self._store: Dict[str, TalentCapabilitySnapshot] = {}
        self._builder = TalentSnapshotBuilder()
        self._version_counter: Dict[str, int] = {}

    # ─────────────────────────────────────────────────────────────────────
    # Build / Register
    # ─────────────────────────────────────────────────────────────────────

    def build_snapshot(
        self,
        employee: Employee,
        upskill_capabilities: Optional[List[str]] = None,
        workload: Optional[float] = None,
        team_capabilities: Optional[List[str]] = None,
    ) -> TalentCapabilitySnapshot:
        """Build and store a snapshot for the given Employee. Idempotent."""
        eid = employee.employee_id
        version = self._version_counter.get(eid, 0) + 1

        snapshot = self._builder.build(
            employee=employee,
            upskill_capabilities=upskill_capabilities,
            workload=workload,
            team_capabilities=team_capabilities,
            version=version,
        )

        self._store[eid] = snapshot
        self._version_counter[eid] = version
        logger.debug(
            f"[TalentRegistry] Built snapshot v{version} for employee='{eid}'."
        )
        return snapshot

    def register(self, snapshot: TalentCapabilitySnapshot) -> None:
        """Register a pre-built snapshot (e.g., from tests or batch import)."""
        self._store[snapshot.employee_id] = snapshot
        self._version_counter[snapshot.employee_id] = snapshot.snapshot_version

    # ─────────────────────────────────────────────────────────────────────
    # Read
    # ─────────────────────────────────────────────────────────────────────

    def get_snapshot(self, employee_id: str) -> Optional[TalentCapabilitySnapshot]:
        return self._store.get(employee_id)

    def all_snapshots(self) -> List[TalentCapabilitySnapshot]:
        return list(self._store.values())

    def count(self) -> int:
        return len(self._store)

    # ─────────────────────────────────────────────────────────────────────
    # Invalidation
    # ─────────────────────────────────────────────────────────────────────

    def invalidate(self, employee_id: str) -> bool:
        """
        Mark a snapshot as stale. Returns True if the snapshot existed.
        Stale snapshots remain retrievable but are flagged for refresh.
        """
        snap = self._store.get(employee_id)
        if not snap:
            return False
        snap.is_stale = True
        return True

    def remove(self, employee_id: str) -> bool:
        """Remove a snapshot entirely."""
        existed = employee_id in self._store
        self._store.pop(employee_id, None)
        self._version_counter.pop(employee_id, None)
        return existed

    def is_stale(self, employee_id: str) -> bool:
        snap = self._store.get(employee_id)
        return snap.is_stale if snap else True
