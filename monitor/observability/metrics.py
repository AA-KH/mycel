"""
Pipeline metrics — first-class feature.

The monitor answers: "Of everything observed, how much actually mattered?"
This is powerful evidence that the deterministic architecture is working.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


class PipelineMetrics:
    """Tracks all pipeline metrics as a first-class feature.

    Every stage of the pipeline increments counters. The metrics
    tell the story of deterministic filtering effectiveness.
    """

    def __init__(self):
        self.started_at: datetime = datetime.now(timezone.utc)

        # Ingestion
        self.events_received: int = 0
        self.events_unchanged: int = 0  # Same content, not re-processed

        # Deduplication
        self.events_deduplicated: int = 0
        self.events_exact_dedup: int = 0
        self.events_near_dedup: int = 0

        # Relevance
        self.events_rejected: int = 0
        self.events_network_matched: int = 0
        self.events_entity_matched: int = 0
        self.events_geo_matched: int = 0
        self.events_commodity_matched: int = 0
        self.events_route_matched: int = 0
        self.events_country_matched: int = 0

        # Analysis
        self.events_semantically_reviewed: int = 0
        self.semantic_confirms: int = 0
        self.semantic_rejects: int = 0

        # Correlation
        self.situations_created: int = 0
        self.situations_updated: int = 0
        self.situations_active: int = 0
        self.situations_resolved: int = 0

        # Alerting
        self.alerts_generated: int = 0
        self.alerts_suppressed: int = 0
        self.alerts_dispatched: int = 0
        self.alerts_dispatch_failed: int = 0

        # State transitions
        self.state_transitions: int = 0
        self.state_escalations: int = 0
        self.state_recoveries: int = 0

        # Source health
        self.source_requests: int = 0
        self.source_successes: int = 0
        self.source_failures: int = 0
        self.source_timeouts: int = 0

        # LLM resources
        self.llm_calls: int = 0
        self.llm_failures: int = 0
        self.estimated_prompt_tokens: int = 0
        self.estimated_completion_tokens: int = 0

    @property
    def estimated_tokens(self) -> int:
        return self.estimated_prompt_tokens + self.estimated_completion_tokens

    @property
    def uptime_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    @property
    def filtering_effectiveness(self) -> Optional[float]:
        """Percentage of events that were correctly filtered out."""
        if self.events_received == 0:
            return None
        filtered = self.events_deduplicated + self.events_rejected + self.events_unchanged
        return filtered / self.events_received

    def to_dict(self) -> dict:
        """Export all metrics as a dictionary."""
        return {
            "uptime_seconds": round(self.uptime_seconds, 1),
            "events_received": self.events_received,
            "events_unchanged": self.events_unchanged,
            "events_deduplicated": self.events_deduplicated,
            "events_rejected": self.events_rejected,
            "events_network_matched": self.events_network_matched,
            "events_entity_matched": self.events_entity_matched,
            "events_geo_matched": self.events_geo_matched,
            "events_commodity_matched": self.events_commodity_matched,
            "events_route_matched": self.events_route_matched,
            "events_country_matched": self.events_country_matched,
            "events_semantically_reviewed": self.events_semantically_reviewed,
            "semantic_confirms": self.semantic_confirms,
            "semantic_rejects": self.semantic_rejects,
            "situations_created": self.situations_created,
            "situations_updated": self.situations_updated,
            "situations_active": self.situations_active,
            "situations_resolved": self.situations_resolved,
            "alerts_generated": self.alerts_generated,
            "alerts_suppressed": self.alerts_suppressed,
            "alerts_dispatched": self.alerts_dispatched,
            "alerts_dispatch_failed": self.alerts_dispatch_failed,
            "state_transitions": self.state_transitions,
            "state_escalations": self.state_escalations,
            "state_recoveries": self.state_recoveries,
            "source_requests": self.source_requests,
            "source_successes": self.source_successes,
            "source_failures": self.source_failures,
            "source_timeouts": self.source_timeouts,
            "llm_calls": self.llm_calls,
            "llm_failures": self.llm_failures,
            "estimated_tokens": self.estimated_tokens,
            "filtering_effectiveness": round(self.filtering_effectiveness, 4) if self.filtering_effectiveness is not None else None,
        }

    def summary(self) -> str:
        """Human-readable pipeline summary."""
        eff = self.filtering_effectiveness
        eff_str = f"{eff:.1%}" if eff is not None else "N/A"

        return (
            f"Pipeline: {self.events_received} received → "
            f"{self.events_unchanged} unchanged → "
            f"{self.events_deduplicated} dedup → "
            f"{self.events_rejected} rejected → "
            f"{self.events_network_matched} matched → "
            f"{self.events_semantically_reviewed} reviewed → "
            f"{self.situations_active} situations → "
            f"{self.alerts_generated} alerts | "
            f"LLM: {self.llm_calls} calls, {self.estimated_tokens} tokens | "
            f"Filtering: {eff_str}"
        )
