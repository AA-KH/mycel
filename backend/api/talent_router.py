"""
Talent Market API Router (Phase 15)

Exposes discovery endpoints. All endpoints are READ-ONLY.
No endpoint performs hiring, assignment, or state mutation.

Endpoints:
  POST /api/talent/match
      Structured search via TalentSearchRequest body.

  GET  /api/talent/search
      Lightweight query-param search (skill, tool, capability, team, etc.).

  GET  /api/talent/candidates/{employee_id}
      Fetch single TalentProfile for a specific employee.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from talent.models import (
    TalentSearchRequest, TalentSearchResult, TalentProfile,
    SkillRequirement, ToolRequirement, CapabilityRequirement, TalentAvailability,
)
from talent.registry import TalentRegistry
from talent.service import TalentMarketService
from talent.filter import TalentCandidateFilter
from talent.matcher import TalentCandidateMatcher
from talent.ranker import TalentCandidateRanker

logger = logging.getLogger(__name__)
router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Singleton dependencies (Phase 15 — no DI framework yet)
# ─────────────────────────────────────────────────────────────────────────────
_registry = TalentRegistry()
_service = TalentMarketService(
    registry=_registry,
    candidate_filter=TalentCandidateFilter(),
    matcher=TalentCandidateMatcher(),
    ranker=TalentCandidateRanker(),
)


def get_service() -> TalentMarketService:
    return _service


def get_registry() -> TalentRegistry:
    return _registry


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/match",
    response_model=TalentSearchResult,
    summary="Structured talent search via request body",
)
async def match_talent(request: TalentSearchRequest):
    """
    Perform a structured capability-based talent search.
    Returns ranked CandidateReferences. Does NOT make hiring decisions.
    """
    service = get_service()
    return service.search(request)


@router.get(
    "/search",
    response_model=TalentSearchResult,
    summary="Query-param talent search",
)
async def search_talent(
    skill: Optional[str] = Query(default=None, description="Skill ID to require"),
    min_proficiency: int = Query(default=0, ge=0, le=100),
    capability: Optional[str] = Query(default=None, description="Capability ID to require"),
    tool: Optional[str] = Query(default=None, description="Tool ID to require (authorized only)"),
    team_id: Optional[str] = Query(default=None),
    position_id: Optional[str] = Query(default=None),
    availability: Optional[TalentAvailability] = Query(default=None),
    max_workload: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Lightweight query-param-based talent search. Internally builds a
    TalentSearchRequest and delegates to the structured search pipeline.
    """
    request = TalentSearchRequest(
        required_skills=(
            [SkillRequirement(skill_id=skill, minimum_proficiency=min_proficiency)]
            if skill else []
        ),
        required_capabilities=(
            [CapabilityRequirement(capability_id=capability)]
            if capability else []
        ),
        required_tools=(
            [ToolRequirement(tool_id=tool)]
            if tool else []
        ),
        team_id=team_id,
        position_id=position_id,
        availability_required=availability,
        max_workload=max_workload,
        limit=limit,
        offset=offset,
    )
    service = get_service()
    return service.search(request)


@router.get(
    "/candidates/{employee_id}",
    response_model=TalentProfile,
    summary="Get TalentProfile for a specific employee",
)
async def get_candidate_profile(employee_id: str):
    """
    Returns the TalentProfile projection for the given employee.
    404 if no snapshot exists for this employee.
    """
    service = get_service()
    profile = service.get_profile(employee_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"No talent snapshot found for employee '{employee_id}'."
        )
    return profile
