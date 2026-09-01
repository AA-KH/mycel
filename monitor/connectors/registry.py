"""
Source connector registry.

Activates and deactivates source connectors based on the monitoring profile.
Each profile may require different sources. The registry manages the lifecycle.
"""

from __future__ import annotations

from loguru import logger

from ..config import MonitorConfig
from ..models.signals import SignalType
from .base import SourceConnector
from .changedetection import ChangeDetectionConnector
from .gdacs import GDACSConnector
from .gdelt import GDELTConnector
from .gta import GTAConnector
from .openmeteo import OpenMeteoConnector
from .usgs import USGSConnector
from .wits import WITSConnector
from .wto import WTOConnector


class ConnectorRegistry:
    """Manages the lifecycle of source connectors.

    Only activates connectors needed by the current monitoring profile.
    """

    def __init__(self, config: MonitorConfig):
        self.config = config
        self._connectors: dict[str, SourceConnector] = {}
        self._available: dict[str, type[SourceConnector]] = {
            "gdelt": GDELTConnector,
            "gdacs": GDACSConnector,
            "usgs": USGSConnector,
            "openmeteo": OpenMeteoConnector,
            "changedetection": ChangeDetectionConnector,
            "wto": WTOConnector,
            "global_trade_alert": GTAConnector,
            "wits": WITSConnector,
        }

    def activate(self, source_names: list[str]) -> None:
        """Activate the specified source connectors."""
        for name in source_names:
            if name in self._connectors:
                continue  # Already active

            if name not in self._available:
                logger.warning(f"Unknown source connector: {name}")
                continue

            # Check if source is enabled in config
            enabled_flag = getattr(self.config, f"{name}_enabled", True)
            if not enabled_flag:
                logger.info(f"Source {name} is disabled in configuration")
                continue

            # Special check for sources requiring configuration
            if name == "changedetection":
                connector = ChangeDetectionConnector(self.config)
                if not connector.is_configured:
                    logger.info("changedetection.io not configured — skipping")
                    continue
            elif name == "wto":
                connector = WTOConnector(self.config)
                if not connector.is_configured:
                    logger.info("WTO API key not configured — skipping")
                    continue
            elif name == "global_trade_alert":
                connector = GTAConnector(self.config)
                if not connector.is_configured:
                    logger.info("Global Trade Alert not configured — skipping")
                    continue

            connector = self._available[name](self.config)
            self._connectors[name] = connector
            logger.info(f"Activated source connector: {name}")

    def deactivate(self, source_name: str) -> None:
        """Deactivate a source connector."""
        if source_name in self._connectors:
            del self._connectors[source_name]
            logger.info(f"Deactivated source connector: {source_name}")

    def get(self, source_name: str) -> SourceConnector | None:
        """Get an active connector by name."""
        return self._connectors.get(source_name)

    def active_connectors(self) -> dict[str, SourceConnector]:
        """Return all active connectors."""
        return dict(self._connectors)

    def connectors_for_signal(self, signal_type: SignalType) -> list[SourceConnector]:
        """Return active connectors that produce the given signal type."""
        return [
            c for c in self._connectors.values()
            if signal_type in c.signal_types
        ]

    async def health_check_all(self) -> dict[str, bool]:
        """Run health checks on all active connectors."""
        results = {}
        for name, connector in self._connectors.items():
            try:
                results[name] = await connector.health_check()
            except Exception:
                results[name] = False
        return results

    async def close_all(self) -> None:
        """Close all active connectors."""
        for connector in self._connectors.values():
            if hasattr(connector, "close"):
                await connector.close()
        self._connectors.clear()
