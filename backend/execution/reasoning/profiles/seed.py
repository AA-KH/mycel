import asyncio
import logging
from core.mongodb import mongodb_connection
from organization.teams.repository import TeamRepository
from organization.registry import TeamRegistry

from execution.reasoning.profiles.repository import (
    TeamReasoningProfileRepository, 
    TeamReasoningStrategyAssignmentRepository
)
from execution.reasoning.profiles.registry import TeamReasoningRegistry
from execution.reasoning.profiles.models import (
    ReasoningPolicies, VerificationPolicy, EvidencePolicy, OutputPolicy
)

logger = logging.getLogger(__name__)

async def seed_reasoning_profiles():
    """Idempotent seed for Team Reasoning Philosophy."""
    logger.info("Starting Team Reasoning Philosophy seed...")
    
    db = mongodb_connection.db
    
    team_repo = TeamRepository(db)
    team_registry = TeamRegistry(team_repo)
    
    profile_repo = TeamReasoningProfileRepository(db)
    assignment_repo = TeamReasoningStrategyAssignmentRepository(db)
    reasoning_registry = TeamReasoningRegistry(profile_repo, assignment_repo, team_registry)

    # 1. Setup Backend Engineering Team
    backend_team = await team_repo.get_by_id("team-backend")
    if backend_team:
        existing_profile = await reasoning_registry.get_active_profile(backend_team.id)
        if not existing_profile:
            policies = ReasoningPolicies(
                verification=VerificationPolicy(verify_important_claims=True, code_execution_required=True),
                output=OutputPolicy(structured_summary=True)
            )
            profile = await reasoning_registry.create_profile(
                team_id=backend_team.id,
                name="engineering_philosophy",
                display_name="Engineering Philosophy",
                description="Plan, implement, test and verify.",
                principles=[
                    "understand_before_modify",
                    "prefer_simple_design",
                    "test_before_completion",
                    "validate_edge_cases"
                ],
                policies=policies.model_dump()
            )
            logger.info(f"Created TeamReasoningProfile for {backend_team.id}")
            
            # Map to global code_test strategy
            await reasoning_registry.assign_strategy(profile.id, "code_test", priority=1)
        else:
            logger.info(f"TeamReasoningProfile already exists for {backend_team.id}")

    # 2. Setup Research Team (assuming team-research exists)
    research_team = await team_repo.get_by_id("team-research")
    if research_team:
        existing_profile = await reasoning_registry.get_active_profile(research_team.id)
        if not existing_profile:
            policies = ReasoningPolicies(
                evidence=EvidencePolicy(prefer_primary_sources=True, citation_required=True),
                output=OutputPolicy(structured_summary=True, include_confidence_notes=True)
            )
            profile = await reasoning_registry.create_profile(
                team_id=research_team.id,
                name="research_philosophy",
                display_name="Research Philosophy",
                description="Research before synthesis.",
                principles=[
                    "verify_before_conclude",
                    "prefer_primary_sources",
                    "cross_check_important_claims",
                    "separate_fact_from_inference"
                ],
                policies=policies.model_dump()
            )
            logger.info(f"Created TeamReasoningProfile for {research_team.id}")
            
            # Map to global research_verify strategy
            await reasoning_registry.assign_strategy(profile.id, "research_verify", priority=1)
        else:
            logger.info(f"TeamReasoningProfile already exists for {research_team.id}")

    logger.info("Team Reasoning Philosophy seed complete.")

if __name__ == "__main__":
    asyncio.run(seed_reasoning_profiles())
