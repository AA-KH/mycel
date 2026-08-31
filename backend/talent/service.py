"""
Talent Market Service (Phase 15)

Primary orchestration facade for the Talent Market.

Pipeline:
    TalentSearchRequest
        → TalentRegistry          (load snapshots)
        → TalentCandidateFilter   (hard eligibility gates)
        → TalentCandidateMatcher  (per-dimension breakdowns)
        → TalentCandidateRanker   (weighted score + top-k)
        → TalentSearchResult

Invariants enforced here:
- Talent Market never hires, assigns, creates Agents, grants Tools,
  activates Upskills, or changes Team/Employee membership.
- Snapshots are eventually consistent projections; hiring MUST revalidate.
- No LLM calls for structured search requests.
- Candidate results are bounded by request.limit.
- Missing data is NOT_EVALUATED, not a disqualification.
"""

import logging
from typing import List, Optional

from talent.models import (
    TalentSearchRequest, TalentSearchResult, TalentProfile,
    CandidateReference, TalentCapabilitySnapshot,
)
from talent.registry import TalentRegistry
from talent.filter import TalentCandidateFilter
from talent.matcher import TalentCandidateMatcher
from talent.ranker import TalentCandidateRanker

logger = logging.getLogger(__name__)


class TalentMarketService:
    """
    Orchestrates candidate discovery: filter → match → rank → return.
    This is the ONLY entry point for Talent Market consumers.
    """

    def __init__(
        self,
        registry: TalentRegistry,
        candidate_filter: Optional[TalentCandidateFilter] = None,
        matcher: Optional[TalentCandidateMatcher] = None,
        ranker: Optional[TalentCandidateRanker] = None,
    ):
        self.registry = registry
        self.filter = candidate_filter or TalentCandidateFilter()
        self.matcher = matcher or TalentCandidateMatcher()
        self.ranker = ranker or TalentCandidateRanker()

    # ─────────────────────────────────────────────────────────────────────
    # Primary Search
    # ─────────────────────────────────────────────────────────────────────

    def search(self, request: TalentSearchRequest) -> TalentSearchResult:
        """
        Execute a structured Talent Market search.
        Returns a TalentSearchResult with ranked CandidateReferences.

        This method makes ZERO hiring decisions and ZERO LLM calls.
        """
        logger.info(
            f"[TalentMarket] search: skills={[s.skill_id for s in request.required_skills]}, "
            f"tools={[t.tool_id for t in request.required_tools]}, "
            f"caps={[c.capability_id for c in request.required_capabilities]}, "
            f"team={request.team_id}, limit={request.limit}"
        )

        # 1. Load all snapshots from registry
        all_snapshots = self.registry.all_snapshots()

        # 2. Filter (hard eligibility)
        eligible_snapshots: List[TalentCapabilitySnapshot] = []
        filter_rejections = 0
        for snap in all_snapshots:
            eligible, reasons = self.filter.evaluate(snap, request)
            if eligible:
                eligible_snapshots.append(snap)
            else:
                filter_rejections += 1
                logger.debug(
                    f"[TalentMarket] Employee '{snap.employee_id}' filtered: {reasons}"
                )

        total_eligible = len(eligible_snapshots)

        # 3. Match — compute breakdowns for eligible candidates only
        breakdowns = [
            self.matcher.match(snap, request)
            for snap in eligible_snapshots
        ]

        # 4. Rank all eligible candidates (top_k = total eligible)
        # Pagination slicing happens AFTER ranking so offset works correctly.
        ranked: List[CandidateReference] = self.ranker.rank(
            eligible_snapshots, breakdowns, request, top_k=len(eligible_snapshots)
        )

        # 5. Apply offset + limit for pagination
        total_matched = len(ranked)
        page = ranked[request.offset: request.offset + request.limit]
        has_more = (request.offset + len(page)) < total_matched

        logger.info(
            f"[TalentMarket] search complete: "
            f"total={len(all_snapshots)}, eligible={total_eligible}, "
            f"matched={total_matched}, returned={len(page)}, "
            f"rejected={filter_rejections}"
        )

        return TalentSearchResult(
            items=page,
            total_eligible=total_eligible,
            total_matched=total_matched,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Profile Lookup
    # ─────────────────────────────────────────────────────────────────────

    def get_profile(self, employee_id: str) -> Optional[TalentProfile]:
        """
        Return the TalentProfile for a specific employee.
        Returns None if no snapshot exists.
        """
        snap = self.registry.get_snapshot(employee_id)
        if not snap:
            return None
        return TalentProfile(
            employee_id=snap.employee_id,
            display_name=snap.employee_id,   # Resolved from Employee if needed
            team_id=snap.team_id,
            position_id=snap.position_id,
            specialization="",               # Not in snapshot — can be enriched
            experience_level="",
            skills=snap.skills,
            authorized_tools=snap.authorized_tools,
            capabilities=snap.capabilities,
            upskill_capabilities=snap.upskill_capabilities,
            outputs=snap.outputs,
            availability=snap.availability,
            workload=snap.workload,
            overall_performance=snap.overall_performance,
            tasks_completed=snap.tasks_completed,
            snapshot_version=snap.snapshot_version,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Snapshot Management
    # ─────────────────────────────────────────────────────────────────────

    def invalidate_snapshot(self, employee_id: str) -> bool:
        """
        Mark an employee's snapshot as stale (call on EMPLOYEE_UPDATED events).
        """
        return self.registry.invalidate(employee_id)

    # ─────────────────────────────────────────────────────────────────────
    # Invariant Safety — explicit method absence declarations
    # ─────────────────────────────────────────────────────────────────────
    # The following capabilities do NOT exist on this service.
    # Attempting to add them here violates Phase 15 invariants:
    #   hire()            → belongs to HiringEngine
    #   assign_task()     → belongs to TaskOrchestrator
    #   create_agent()    → belongs to AgentRuntime
    #   grant_tool()      → belongs to ToolGateway
    #   activate_upskill()→ belongs to UpskillSystem
    #   modify_skill()    → belongs to SkillRegistry
    #   change_team()     → belongs to TeamRegistry
