"""
Talent Candidate Matcher (Phase 15)

Computes a CandidateMatchBreakdown for an eligible candidate.
Each dimension produces:
  - score       : 0.0–1.0 or None (NOT_EVALUATED when data is absent)
  - status      : MATCH | PARTIAL_MATCH | NO_MATCH | NOT_EVALUATED
  - matched     : list of IDs that satisfied the requirement
  - missing     : list of IDs that were required but absent / below threshold
  - detail      : human-readable explanation

Rules:
- Missing data → NOT_EVALUATED, not 0.
- No LLM calls — purely deterministic structured matching.
- Preferred (soft) skills contribute to skill score but cannot fail eligibility.
- Tool matching checks authorized_tools (authorization already verified by filter).
"""

import logging
from typing import List, Optional

from talent.models import (
    TalentCapabilitySnapshot, TalentSearchRequest,
    CandidateMatchBreakdown, DimensionResult, MatchStatus, TalentAvailability
)

logger = logging.getLogger(__name__)

_AVAILABILITY_SCORE = {
    TalentAvailability.AVAILABLE:   1.0,
    TalentAvailability.LIMITED:     0.6,
    TalentAvailability.BUSY:        0.2,
    TalentAvailability.OFFLINE:     0.0,
    TalentAvailability.UNAVAILABLE: 0.0,
}


class TalentCandidateMatcher:
    """
    Produces a CandidateMatchBreakdown for a single candidate.
    Stateless and deterministic — safe to use concurrently.
    """

    def match(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> CandidateMatchBreakdown:
        return CandidateMatchBreakdown(
            skills=self._match_skills(snapshot, request),
            tools=self._match_tools(snapshot, request),
            capabilities=self._match_capabilities(snapshot, request),
            outputs=self._match_outputs(snapshot, request),
            position=self._match_position(snapshot, request),
            availability=self._match_availability(snapshot),
            workload=self._match_workload(snapshot, request),
            evaluation=self._match_evaluation(snapshot),
        )

    # ─────────────────────────────────────────────────────────────────────
    # Skills
    # ─────────────────────────────────────────────────────────────────────

    def _match_skills(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        all_reqs = request.required_skills + request.preferred_skills
        if not all_reqs:
            return DimensionResult(status=MatchStatus.NOT_EVALUATED, detail="No skills required.")

        matched, missing = [], []
        weighted_score, total_weight = 0.0, 0.0

        for s_req in all_reqs:
            actual = snapshot.skills.get(s_req.skill_id, 0)
            # Normalize against required minimum (not 100) to give full credit at threshold
            max_ref = max(s_req.minimum_proficiency, 1)
            dim_score = min(actual / max_ref, 1.0) if actual > 0 else 0.0
            weighted_score += dim_score * s_req.weight
            total_weight += s_req.weight

            if actual >= s_req.minimum_proficiency:
                matched.append(
                    f"{s_req.skill_id}({actual}/{s_req.minimum_proficiency})"
                )
            else:
                missing.append(
                    f"{s_req.skill_id}({actual}<{s_req.minimum_proficiency})"
                )

        score = round(weighted_score / total_weight, 4) if total_weight else 0.0
        status = (
            MatchStatus.MATCH if not missing else
            MatchStatus.PARTIAL_MATCH if matched else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score, status=status, matched=matched, missing=missing,
            detail=f"{len(matched)}/{len(all_reqs)} skills matched."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Tools
    # ─────────────────────────────────────────────────────────────────────

    def _match_tools(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        if not request.required_tools:
            return DimensionResult(status=MatchStatus.NOT_EVALUATED, detail="No tools required.")

        matched, missing = [], []
        for t_req in request.required_tools:
            if t_req.tool_id in snapshot.authorized_tools:
                matched.append(t_req.tool_id)
            else:
                missing.append(t_req.tool_id)

        score = round(len(matched) / len(request.required_tools), 4)
        status = (
            MatchStatus.MATCH if not missing else
            MatchStatus.PARTIAL_MATCH if matched else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score, status=status, matched=matched, missing=missing,
            detail=f"{len(matched)}/{len(request.required_tools)} tools authorized."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Capabilities
    # ─────────────────────────────────────────────────────────────────────

    def _match_capabilities(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        if not request.required_capabilities:
            return DimensionResult(status=MatchStatus.NOT_EVALUATED, detail="No capabilities required.")

        all_caps = set(snapshot.capabilities) | set(snapshot.upskill_capabilities)
        matched, missing = [], []

        for c_req in request.required_capabilities:
            if c_req.capability_id in all_caps:
                src = "upskill" if c_req.capability_id in snapshot.upskill_capabilities else "baseline"
                matched.append(f"{c_req.capability_id}({src})")
            else:
                missing.append(c_req.capability_id)

        score = round(len(matched) / len(request.required_capabilities), 4)
        status = (
            MatchStatus.MATCH if not missing else
            MatchStatus.PARTIAL_MATCH if matched else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score, status=status, matched=matched, missing=missing,
            detail=f"{len(matched)}/{len(request.required_capabilities)} capabilities matched."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Outputs
    # ─────────────────────────────────────────────────────────────────────

    def _match_outputs(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        if not request.required_outputs:
            return DimensionResult(status=MatchStatus.NOT_EVALUATED, detail="No outputs required.")

        matched = [o for o in request.required_outputs if o in snapshot.outputs]
        missing = [o for o in request.required_outputs if o not in snapshot.outputs]
        score = round(len(matched) / len(request.required_outputs), 4)
        status = (
            MatchStatus.MATCH if not missing else
            MatchStatus.PARTIAL_MATCH if matched else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score, status=status, matched=matched, missing=missing,
            detail=f"{len(matched)}/{len(request.required_outputs)} output types supported."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Position
    # ─────────────────────────────────────────────────────────────────────

    def _match_position(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        if not request.position_id:
            return DimensionResult(status=MatchStatus.NOT_EVALUATED, detail="No position required.")

        match = snapshot.position_id == request.position_id
        return DimensionResult(
            score=1.0 if match else 0.0,
            status=MatchStatus.MATCH if match else MatchStatus.NO_MATCH,
            matched=[snapshot.position_id] if match else [],
            missing=[] if match else [request.position_id],
            detail=f"Position {'matches' if match else 'does not match'} '{request.position_id}'."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Availability
    # ─────────────────────────────────────────────────────────────────────

    def _match_availability(self, snapshot: TalentCapabilitySnapshot) -> DimensionResult:
        score = _AVAILABILITY_SCORE.get(snapshot.availability, 0.0)
        status = (
            MatchStatus.MATCH if score >= 0.8 else
            MatchStatus.PARTIAL_MATCH if score > 0.0 else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score,
            status=status,
            matched=[snapshot.availability.value],
            detail=f"Availability: {snapshot.availability.value} → score {score}."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Workload
    # ─────────────────────────────────────────────────────────────────────

    def _match_workload(
        self,
        snapshot: TalentCapabilitySnapshot,
        request: TalentSearchRequest,
    ) -> DimensionResult:
        if snapshot.workload is None:
            return DimensionResult(
                status=MatchStatus.NOT_EVALUATED,
                detail="Workload data unavailable."
            )
        score = round(1.0 - snapshot.workload, 4)
        status = (
            MatchStatus.MATCH if score >= 0.6 else
            MatchStatus.PARTIAL_MATCH if score > 0.2 else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score,
            status=status,
            detail=f"Workload {snapshot.workload:.2f} → availability score {score:.2f}."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Evaluation Signals
    # ─────────────────────────────────────────────────────────────────────

    def _match_evaluation(self, snapshot: TalentCapabilitySnapshot) -> DimensionResult:
        if snapshot.overall_performance is None:
            return DimensionResult(
                status=MatchStatus.NOT_EVALUATED,
                detail="No evaluation history available. Not penalized."
            )
        # Normalize 0–100 → 0.0–1.0
        score = round(min(snapshot.overall_performance / 100.0, 1.0), 4)
        status = (
            MatchStatus.MATCH if score >= 0.7 else
            MatchStatus.PARTIAL_MATCH if score >= 0.4 else
            MatchStatus.NO_MATCH
        )
        return DimensionResult(
            score=score,
            status=status,
            detail=(
                f"Overall performance {snapshot.overall_performance:.1f}/100 "
                f"({snapshot.tasks_completed} tasks)."
            )
        )
