"""
Source connector protocol.

Every source connector implements this interface. Each connector declares
its signal types, handles its own rate limiting, and normalizes raw data
into CanonicalEvents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..models.events import CanonicalEvent
from ..models.signals import SignalType
from ..models.state import SourceHealth


class SourceConnector(ABC):
    """Abstract base class for all source connectors.

    Each connector:
    - Declares which signal types it produces
    - Fetches data from an external source
    - Normalizes raw data into CanonicalEvents
    - Tracks its own health
    - Manages rate limiting internally
    """

    def __init__(self, name: str, signal_types: list[SignalType]):
        self.name = name
        self.signal_types = signal_types
        self.health = SourceHealth(source_name=name)

    @abstractmethod
    async def fetch(self, query: str | None = None, **kwargs: Any) -> list[CanonicalEvent]:
        """Fetch and normalize events from the source.

        Args:
            query: Optional query string (source-specific format).
            **kwargs: Additional parameters (coordinates, magnitude, etc.)

        Returns:
            List of normalized CanonicalEvent instances.

        Must not raise on transient errors — should log and return empty list,
        updating self.health appropriately.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Quick health check. Returns True if source is reachable."""
        ...

    def record_success(self, response_time_ms: float | None = None) -> None:
        """Record a successful fetch."""
        self.health.record_success(response_time_ms)

    def record_failure(self, error: str) -> None:
        """Record a failed fetch."""
        self.health.record_failure(error)
