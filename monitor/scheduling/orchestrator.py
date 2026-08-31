"""
Pipeline orchestrator.

Manages the full monitoring lifecycle:
profile load → watch plan compile → source activate → fetch → normalize
→ dedup → match → gate → correlate → (optional semantic) → severity → alert.

Uses asyncio for concurrent source fetching. One failing source never blocks others.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from ..alerting.adaptive_state import AdaptiveStateManager
from ..alerting.alert_dispatcher import AlertDispatcher
from ..alerting.alert_manager import AlertManager
from ..alerting.severity_policy import SeverityPolicy
from ..analysis.llm_client import LLMClient
from ..analysis.semantic_analyst import SemanticAnalyst
from ..compiler.profile_compiler import compile_profile
from ..config import MonitorConfig
from ..connectors.registry import ConnectorRegistry
from ..graph.network_graph import NetworkGraph
from ..models.events import CanonicalEvent
from ..models.network import NetworkArchitecture
from ..models.profile import MonitoringProfile
from ..models.situations import Situation
from ..observability.metrics import PipelineMetrics
from ..pipeline.correlation_engine import CorrelationEngine
from ..pipeline.deduplicator import DeduplicationEngine
from ..pipeline.entity_resolver import EntityResolver
from ..pipeline.geo_matcher import GeoMatcher
from ..pipeline.relevance_engine import RelevanceEngine
from ..storage.store import MonitorStore


class Orchestrator:
    """Central pipeline orchestrator.

    Ties together all monitoring subsystem components. Manages lifecycle,
    processes events through the full pipeline.
    """

    def __init__(self, config: MonitorConfig):
        self.config = config

        # Core state
        self.profile: Optional[MonitoringProfile] = None
        self.graph: Optional[NetworkGraph] = None
        self.architecture: Optional[NetworkArchitecture] = None

        # Components (initialized when profile is loaded)
        self.connectors = ConnectorRegistry(config)
        self.deduplicator = DeduplicationEngine(
            time_window_hours=config.dedup_time_window_hours,
            simhash_threshold=config.dedup_simhash_threshold,
        )
        self.state_manager = AdaptiveStateManager()
        self.alert_manager = AlertManager(
            cooldown_minutes=config.alert_cooldown_minutes,
            max_per_situation_per_hour=config.max_alerts_per_situation_per_hour,
        )
        self.severity_policy = SeverityPolicy(config)
        self.dispatcher = AlertDispatcher(config)
        self.store = MonitorStore(config.db_path)
        self.metrics = PipelineMetrics()

        # LLM components
        self.llm = LLMClient(config)
        self.analyst = SemanticAnalyst(self.llm)

        # Pipeline components (require profile)
        self.entity_resolver: Optional[EntityResolver] = None
        self.geo_matcher: Optional[GeoMatcher] = None
        self.relevance_engine: Optional[RelevanceEngine] = None
        self.correlation_engine: Optional[CorrelationEngine] = None

        self._initialized = False

    def initialize(self) -> None:
        """Initialize storage and prepare for operation."""
        self.store.initialize()
        self._initialized = True
        logger.info("Orchestrator initialized")

    async def load_profile_from_architecture(self, architecture_data: dict) -> MonitoringProfile:
        """Load a network architecture and compile it into a monitoring profile.

        This is the primary entry point for configuring monitoring.
        """
        if not self._initialized:
            self.initialize()

        # Parse architecture
        self.architecture = NetworkArchitecture(**architecture_data)
        logger.info(f"Loaded network: {self.architecture.network_id} ({len(self.architecture.nodes)} nodes, {len(self.architecture.edges)} edges)")

        # Build graph
        self.graph = NetworkGraph(self.architecture)

        # Compile profile
        self.profile = compile_profile(self.architecture)
        logger.info(
            f"Compiled profile: {self.profile.profile_id} | "
            f"{self.profile.total_entities} entities, "
            f"{self.profile.total_locations} locations, "
            f"{self.profile.total_commodities} commodities, "
            f"{len(self.profile.watch_targets)} watch targets, "
            f"{len(self.profile.active_sources)} sources"
        )

        # Initialize pipeline components
        self.entity_resolver = EntityResolver(self.profile.entity_aliases)
        self.geo_matcher = GeoMatcher(self.profile)
        self.relevance_engine = RelevanceEngine(
            self.profile, self.graph, self.entity_resolver, self.geo_matcher,
        )
        self.correlation_engine = CorrelationEngine(
            network_id=self.architecture.network_id,
        )

        # Initialize entity states
        for target in self.profile.watch_targets:
            if target.entity_id and target.entity_name:
                self.state_manager.initialize_entity(target.entity_id, target.entity_name)

        # Activate source connectors
        self.connectors.activate(self.profile.active_sources)

        # Persist profile
        self.store.save_profile(
            self.profile.profile_id,
            self.profile.network_id,
            self.profile.architecture_version,
            self.profile.model_dump_json(),
        )

        logger.info(f"Monitor ready for network: {self.architecture.network_id}")
        return self.profile

    async def load_profile_from_file(self, path: str) -> MonitoringProfile:
        """Load architecture from a JSON file."""
        data = json.loads(Path(path).read_text())
        return await self.load_profile_from_architecture(data)

    async def process_event(self, event: CanonicalEvent) -> Optional[Situation]:
        """Process a single event through the full pipeline.

        Returns the situation if the event is relevant and creates/updates
        a situation, None otherwise.

        Pipeline: dedup → entity/geo match → hard gate → correlate →
                  (optional semantic) → severity → alert
        """
        if not self.profile or not self.relevance_engine:
            logger.warning("No profile loaded — cannot process events")
            return None

        self.metrics.events_received += 1

        # ── 1. Deduplication ──
        duplicate_of = self.deduplicator.check_and_register(event)
        if duplicate_of:
            self.metrics.events_deduplicated += 1
            event.dedup_of = duplicate_of
            return None

        # ── 2. Entity/Geo Match + Hard Relevance Gate ──
        result = self.relevance_engine.evaluate(event)

        if not result.passed_gate:
            self.metrics.events_rejected += 1
            return None

        # Track match types
        self.metrics.events_network_matched += 1
        if result.breakdown.entity_match:
            self.metrics.events_entity_matched += 1
        if result.breakdown.location_match:
            self.metrics.events_geo_matched += 1
        if result.breakdown.commodity_match:
            self.metrics.events_commodity_matched += 1
        if result.breakdown.route_match:
            self.metrics.events_route_matched += 1
        if result.breakdown.country_match:
            self.metrics.events_country_matched += 1

        # ── 3. Correlation (deterministic-first) ──
        situation = self.correlation_engine.correlate(result)

        if len(situation.event_ids) == 1:
            self.metrics.situations_created += 1
        else:
            self.metrics.situations_updated += 1

        self.metrics.situations_active = len(self.correlation_engine.active_situations())

        # ── 4. Semantic Analysis (on-demand, selective) ──
        if result.needs_semantic_analysis and self.analyst.is_available:
            self.metrics.events_semantically_reviewed += 1
            self.metrics.llm_calls += 1

            analysis = await self.analyst.analyze_event(
                event, result.breakdown, situation,
            )

            if analysis:
                if analysis.confirms_disruption:
                    self.metrics.semantic_confirms += 1
                    situation.confidence = max(situation.confidence, analysis.confidence)
                    if analysis.why_it_matters:
                        situation.why_it_matters = [analysis.why_it_matters]
                    situation.ai_interpretation = analysis.actual_impact
                else:
                    self.metrics.semantic_rejects += 1
                    # Don't suppress — the deterministic match was real,
                    # semantic just says the article doesn't confirm disruption.
                    # Lower confidence instead.
                    situation.confidence *= 0.5
            else:
                self.metrics.llm_failures += 1

            # Track token usage
            self.metrics.estimated_prompt_tokens = self.llm.total_prompt_tokens
            self.metrics.estimated_completion_tokens = self.llm.total_completion_tokens

        # ── 5. Severity Classification ──
        severity = self.severity_policy.classify(situation)
        situation.severity = severity

        # ── 6. State Transition ──
        for entity_id in situation.affected_entity_ids:
            new_state = self.state_manager.escalate(
                entity_id, severity, situation.situation_id,
                reason=f"{event.signal_type.value}: {event.title[:80]}",
            )
            if new_state:
                self.metrics.state_transitions += 1
                self.metrics.state_escalations += 1

        # ── 7. Alert Generation ──
        if self.severity_policy.should_alert(severity):
            alert = self.alert_manager.create_or_update_alert(
                situation, severity,
                evidence_path=result.evidence_path,
                why_it_matters=situation.why_it_matters,
            )
            if alert:
                self.metrics.alerts_generated += 1
                self.store.save_alert(alert)

                # Dispatch asynchronously
                dispatched = await self.dispatcher.dispatch(alert)
                if dispatched:
                    self.metrics.alerts_dispatched += 1
                else:
                    self.metrics.alerts_dispatch_failed += 1
            else:
                self.metrics.alerts_suppressed += 1

        # ── 8. Persist ──
        self.store.save_event(event, situation.situation_id)
        self.store.save_situation(situation)

        return situation

    async def process_events(self, events: list[CanonicalEvent]) -> list[Situation]:
        """Process multiple events through the pipeline."""
        situations = []
        for event in events:
            situation = await self.process_event(event)
            if situation:
                situations.append(situation)
        return situations

    async def fetch_from_source(self, source_name: str, **kwargs) -> list[CanonicalEvent]:
        """Fetch events from a specific source connector."""
        connector = self.connectors.get(source_name)
        if not connector:
            logger.warning(f"Source {source_name} not active")
            return []

        self.metrics.source_requests += 1

        try:
            events = await connector.fetch(**kwargs)
            self.metrics.source_successes += 1
            return events
        except Exception as e:
            self.metrics.source_failures += 1
            logger.error(f"Source {source_name} fetch error: {e}")
            return []

    async def run_poll_cycle(self) -> dict:
        """Run a complete polling cycle across all active sources.

        Fetches from each active source, processes all events through
        the pipeline. Returns summary of what happened.
        """
        if not self.profile:
            return {"error": "No profile loaded"}

        results = {
            "events_fetched": 0,
            "events_matched": 0,
            "situations_created": 0,
            "alerts_generated": 0,
            "sources_polled": 0,
        }

        # Fetch from each active source
        all_events: list[CanonicalEvent] = []

        for source_name, connector in self.connectors.active_connectors().items():
            try:
                events: list[CanonicalEvent] = []

                if source_name == "openmeteo" and self.profile.watched_coordinates:
                    events = await connector.fetch(
                        coordinates=self.profile.watched_coordinates
                    )
                elif source_name in ("gdelt",):
                    # Use compiled query groups
                    for qg in self.profile.query_groups:
                        if qg.source == source_name:
                            batch_events = await connector.fetch(query=qg.query)
                            events.extend(batch_events)
                elif source_name in ("gdacs", "usgs"):
                    events = await connector.fetch()
                elif source_name == "changedetection":
                    events = await connector.fetch()

                all_events.extend(events)
                results["sources_polled"] += 1

            except Exception as e:
                logger.error(f"Poll cycle error for {source_name}: {e}")
                self.metrics.source_failures += 1

        results["events_fetched"] = len(all_events)

        # Process all events
        situations = await self.process_events(all_events)
        results["events_matched"] = len(situations)
        results["situations_created"] = self.metrics.situations_created
        results["alerts_generated"] = self.metrics.alerts_generated

        logger.info(f"Poll cycle complete: {self.metrics.summary()}")

        return results

    def get_status(self) -> dict:
        """Get current monitor and network status."""
        source_health = {}
        for name, connector in self.connectors.active_connectors().items():
            source_health[name] = {
                "state": connector.health.state.value,
                "last_success": connector.health.last_success.isoformat() if connector.health.last_success else None,
                "consecutive_failures": connector.health.consecutive_failures,
            }

        sources_healthy = sum(1 for s in source_health.values() if s["state"] == "healthy")
        sources_degraded = sum(1 for s in source_health.values() if s["state"] != "healthy")

        return {
            "monitor": {
                "status": "healthy" if sources_healthy > 0 else "degraded",
                "uptime_seconds": round(self.metrics.uptime_seconds, 1),
                "profile_loaded": self.profile is not None,
                "sources_healthy": sources_healthy,
                "sources_degraded": sources_degraded,
                "source_details": source_health,
            },
            "network": {
                "network_id": self.profile.network_id if self.profile else None,
                "state": self.state_manager.get_network_condition(),
                "active_situations": len(self.correlation_engine.active_situations()) if self.correlation_engine else 0,
                "entities_watched": len(self.state_manager.all_states()),
                "entities_elevated": len(self.state_manager.get_elevated_entities()),
            },
        }

    async def shutdown(self) -> None:
        """Clean shutdown."""
        await self.connectors.close_all()
        await self.dispatcher.close()
        self.store.close()
        logger.info("Orchestrator shutdown complete")
