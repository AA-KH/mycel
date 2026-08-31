import logging
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline
from workforce.employees.models import Employee

class TeamReadiness(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "ERROR"
    path: str = ""

class TeamValidationResult(BaseModel):
    team_id: str
    valid: bool = False
    readiness: TeamReadiness = TeamReadiness.NOT_READY
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    checks: int = 0

class TeamValidationSummary(BaseModel):
    total_teams: int = 0
    valid_teams: int = 0
    invalid_teams: int = 0
    ready_teams: int = 0
    ready_with_warnings_teams: int = 0
    not_ready_teams: int = 0
    errors: int = 0
    warnings: int = 0
    results: List[TeamValidationResult] = Field(default_factory=list)

from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver
from teams.seed import seed

logger = logging.getLogger(__name__)

class TeamValidator:
    def __init__(self, team_registry: TeamRegistry, pipeline_registry: PipelineRegistry, resolver: TeamCapabilityResolver):
        self.team_registry = team_registry
        self.pipeline_registry = pipeline_registry
        self.resolver = resolver
        
        # We will use the seed output to validate the baseline workforce since registries
        # mock member retrieval currently.
        self.seed_data = seed()

    def validate_all(self, strict: bool = False) -> TeamValidationSummary:
        summary = TeamValidationSummary()
        teams = self.seed_data["teams"]
        summary.total_teams = len(teams)
        
        for team in teams:
            result = self.validate_team(team.id, strict=strict)
            summary.results.append(result)
            summary.errors += len(result.errors)
            summary.warnings += len(result.warnings)
            
            if result.valid:
                summary.valid_teams += 1
            else:
                summary.invalid_teams += 1
                
            if result.readiness == TeamReadiness.READY:
                summary.ready_teams += 1
            elif result.readiness == TeamReadiness.READY_WITH_WARNINGS:
                summary.ready_with_warnings_teams += 1
            elif result.readiness == TeamReadiness.NOT_READY:
                summary.not_ready_teams += 1
                
        return summary

    def validate_team(self, team_id: str, strict: bool = False) -> TeamValidationResult:
        result = TeamValidationResult(team_id=team_id)
        
        # 1. Identity & Structure Validation
        team = self._get_team_from_seed(team_id)
        result.checks += 1
        if not team:
            result.errors.append(ValidationIssue(
                code="TEAM_ID_REQUIRED", message=f"Team {team_id} is missing or empty shell.", severity="ERROR", path="teams"
            ))
            self._finalize_readiness(result, strict)
            return result
            
        if not team.name:
            result.errors.append(ValidationIssue(code="TEAM_NAME_REQUIRED", message="Team requires display_name", severity="ERROR", path=f"teams.{team_id}.name"))
        
        # 2. Registries Consistency
        result.checks += 1
        if not self.team_registry.exists(team_id):
            result.errors.append(ValidationIssue(code="REGISTRY_DISCOVERY_FAILED", message="Team not in TeamRegistry", severity="ERROR", path=f"TeamRegistry.{team_id}"))

        # 3. Pipelines Validation & Ownership
        result.checks += 1
        pipelines = [p for p in self.seed_data["pipelines"] if p.team_id == team_id]
        if len(pipelines) == 0:
            result.errors.append(ValidationIssue(code="PIPELINE_NOT_FOUND", message="Team has no pipelines", severity="ERROR", path=f"teams.{team_id}.pipelines"))
            
        for pipe in pipelines:
            result.checks += 1
            if not self.pipeline_registry.exists(pipe.pipeline_id):
                result.errors.append(ValidationIssue(code="REGISTRY_DISCOVERY_FAILED", message=f"Pipeline {pipe.pipeline_id} not in TeamPipelineRegistry", severity="ERROR", path=f"PipelineRegistry.{pipe.pipeline_id}"))
            
            # Isolation test: does the pipeline declare another team? (Already filtered, but verifying explicit ownership check)
            if pipe.team_id != team_id:
                result.errors.append(ValidationIssue(code="PIPELINE_TEAM_MISMATCH", message=f"Pipeline {pipe.pipeline_id} belongs to {pipe.team_id}, not {team_id}", severity="ERROR", path=f"pipelines.{pipe.pipeline_id}"))

        # 4. Positions and Members
        result.checks += 1
        members = [m for m in self.seed_data["members"] if m.team_id == team_id]
        if len(members) < 3:
            result.errors.append(ValidationIssue(code="MEMBER_COUNT_INVALID", message=f"Team has {len(members)} members, requires at least 3", severity="ERROR", path=f"teams.{team_id}.members"))
            
        for member in members:
            result.checks += 1
            if member.team_id != team_id:
                result.errors.append(ValidationIssue(code="MEMBER_TEAM_MISMATCH", message=f"Member {member.employee_id} incorrectly assigned to {team_id}", severity="ERROR", path=f"members.{member.employee_id}"))
            
            if not member.position_id:
                result.errors.append(ValidationIssue(code="POSITION_NOT_FOUND", message=f"Member {member.employee_id} missing position", severity="ERROR", path=f"members.{member.employee_id}"))

        # 5. Resolver & Inheritance Validation
        result.checks += 1
        res = self.resolver.resolve(team_id, strict=True)
        if not res.resolved:
            result.errors.append(ValidationIssue(code="CAPABILITY_RESOLUTION_FAILED", message=f"Team {team_id} failed capability resolution", severity="ERROR", path=f"resolver.{team_id}"))

        self._finalize_readiness(result, strict)
        return result
        
    def _get_team_from_seed(self, team_id: str) -> Optional[Team]:
        for t in self.seed_data["teams"]:
            if t.id == team_id:
                return t
        return None

    def _finalize_readiness(self, result: TeamValidationResult, strict: bool):
        has_errors = len(result.errors) > 0
        has_warnings = len(result.warnings) > 0
        
        result.valid = not has_errors
        
        if strict and has_warnings:
            result.readiness = TeamReadiness.NOT_READY
            result.valid = False
        elif has_errors:
            result.readiness = TeamReadiness.NOT_READY
        elif has_warnings:
            result.readiness = TeamReadiness.READY_WITH_WARNINGS
        else:
            result.readiness = TeamReadiness.READY
