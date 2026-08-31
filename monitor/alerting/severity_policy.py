"""
Severity policy.

Deterministic rules ONLY. LLM NEVER decides alert level.
Multi-dimensional input → INFO / WATCH / WARNING / CRITICAL.
Configurable thresholds.
"""

from __future__ import annotations

from ..config import MonitorConfig
from ..models.situations import RelevanceBreakdown, Situation
from ..models.state import AlertSeverity


class SeverityPolicy:
    """Deterministic severity classification.

    Input: multi-dimensional relevance breakdown + situation confidence
    Output: INFO / WATCH / WARNING / CRITICAL

    The LLM never touches this. Numbers from network data drive severity.
    """

    def __init__(self, config: MonitorConfig):
        self.critical_threshold = config.severity_critical_threshold
        self.warning_threshold = config.severity_warning_threshold
        self.watch_threshold = config.severity_watch_threshold
        self.confidence_high = config.confidence_high
        self.confidence_medium = config.confidence_medium

    def classify(self, situation: Situation) -> AlertSeverity:
        """Classify situation severity from its relevance breakdown.

        Factors:
        - Impact score (from multi-dimensional relevance)
        - Confidence (from source corroboration)
        - Criticality (from network topology)
        - Independent source count
        """
        if not situation.relevance:
            return AlertSeverity.INFO

        breakdown = situation.relevance
        impact = breakdown.impact_score()
        confidence = situation.confidence
        criticality = breakdown.criticality

        # High criticality entities get earlier alerting
        effective_impact = impact
        if criticality >= 0.7:
            effective_impact = impact * 1.2
        elif criticality >= 0.5:
            effective_impact = impact * 1.1

        # Low alternate coverage increases severity
        if breakdown.alternate_coverage < 0.3 and breakdown.dependency_share > 0.3:
            effective_impact *= 1.15

        # Corroboration boosts severity
        if situation.independent_source_count >= 3:
            effective_impact *= 1.1
        elif situation.independent_source_count >= 2:
            effective_impact *= 1.05

        effective_impact = min(1.0, effective_impact)

        # Classification
        if effective_impact >= self.critical_threshold and confidence >= self.confidence_medium:
            return AlertSeverity.CRITICAL
        elif effective_impact >= self.warning_threshold and confidence >= self.confidence_medium:
            return AlertSeverity.WARNING
        elif effective_impact >= self.watch_threshold:
            return AlertSeverity.WATCH
        else:
            return AlertSeverity.INFO

    def should_alert(self, severity: AlertSeverity) -> bool:
        """Determine if a severity level warrants generating an alert."""
        return severity in (AlertSeverity.WATCH, AlertSeverity.WARNING, AlertSeverity.CRITICAL)
