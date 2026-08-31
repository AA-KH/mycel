"""
Talent Candidate Ranker (Phase 15)

Aggregates per-dimension scores from CandidateMatchBreakdown into a single
weighted match_score, then sorts candidates deterministically.

Design Principles:
- Weights are configurable; defaults are provided.
- Dimensions with score=None (NOT_EVALUATED) are excluded from the
  weighted-sum denominator — they do not penalize candidates.
- Score is bounded 0.0–1.0 rounded to 4 decimal places (no fake precision).
- Sorting is deterministic: primary = match_score DESC, tiebreaker = employee_id ASC.
- Top-K is applied before returning.
- No LLM calls.
- No global leaderboard — ranking is per-query.
"""

import logging
from typing import List, Optional, Dict

from talent.models import (
    TalentCapabilitySnapshot, CandidateMatchBreakdown, CandidateReference, TalentSearchRequest
)

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS: Dict[str, float] = {
    "skills":       0.35,
    "capabilities": 0.25,
    "tools":        0.15,
    "availability": 0.10,
    "workload":     0.10,
    "position":     0.05,
    # evaluation and outputs contribute when present but have no default weight slot;
    # they blend into the capabilities / skills buckets conceptually.
    # Override via TalentSearchRequest.score_weights.
}


class TalentCandidateRanker:
    """
    Computes final match_score and sorts eligible candidates.
    Stateless — safe to reuse across requests.
    """

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or DEFAULT_WEIGHTS

    def rank(
        self,
        snapshots: List[TalentCapabilitySnapshot],
        breakdowns: List[CandidateMatchBreakdown],
        request: TalentSearchRequest,
        top_k: int = 20,
    ) -> List[CandidateReference]:
        """
        Zips snapshots + breakdowns, computes scores, sorts, and applies top-k.
        """
        weights = self._resolve_weights(request)
        references: List[CandidateReference] = []

        for snapshot, breakdown in zip(snapshots, breakdowns):
            score = self._aggregate(breakdown, weights)
            references.append(
                CandidateReference(
                    employee_id=snapshot.employee_id,
                    team_id=snapshot.team_id,
                    position_id=snapshot.position_id,
                    display_name=snapshot.employee_id,  # Resolved later if needed
                    availability=snapshot.availability,
                    match_score=score,
                    match_breakdown=breakdown,
                    snapshot_version=snapshot.snapshot_version,
                    snapshot_built_at=snapshot.built_at,
                )
            )

        # Sort: score DESC, employee_id ASC (deterministic tiebreaker)
        references.sort(key=lambda r: (-r.match_score, r.employee_id))

        return references[:top_k]

    def _aggregate(
        self,
        breakdown: CandidateMatchBreakdown,
        weights: Dict[str, float],
    ) -> float:
        """
        Weighted average of available dimension scores.
        Dimensions with score=None are excluded from both numerator and denominator.
        """
        dimension_map = {
            "skills":       breakdown.skills.score,
            "capabilities": breakdown.capabilities.score,
            "tools":        breakdown.tools.score,
            "availability": breakdown.availability.score,
            "workload":     breakdown.workload.score,
            "position":     breakdown.position.score,
            "outputs":      breakdown.outputs.score,
            "evaluation":   breakdown.evaluation.score,
        }

        weighted_sum = 0.0
        effective_weight = 0.0

        for dim, score in dimension_map.items():
            if score is None:
                continue  # NOT_EVALUATED — exclude from denominator
            w = weights.get(dim, 0.0)
            weighted_sum += score * w
            effective_weight += w

        if effective_weight == 0.0:
            return 0.0

        return round(weighted_sum / effective_weight, 4)

    def _resolve_weights(self, request: TalentSearchRequest) -> Dict[str, float]:
        if request.score_weights:
            # Merge overrides on top of defaults
            merged = dict(self.weights)
            merged.update(request.score_weights)
            return merged
        return self.weights
