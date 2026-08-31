import os
from pathlib import Path

BACKEND_DIR = Path("d:/Projects/agent-virtual-office/backend")
TEAMS_DIR = BACKEND_DIR / "teams"
VALIDATION_DIR = TEAMS_DIR / "validation"
TESTS_DIR = BACKEND_DIR / "tests" / "teams"
SCRIPTS_DIR = BACKEND_DIR / "scripts"

MODELS_CONTENT = """from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class TeamReadiness(str, Enum):
    READY = "READY"
    READY_WITH_WARNINGS = "READY_WITH_WARNINGS"
    NOT_READY = "NOT_READY"

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str
    path: str
    source: str = "validator"

class TeamValidationResult(BaseModel):
    team_id: str
    valid: bool = False
    readiness: TeamReadiness = TeamReadiness.NOT_READY
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    checks: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamValidationSummary(BaseModel):
    total_teams: int = 0
    valid_teams: int = 0
    invalid_teams: int = 0
    ready_teams: int = 0
    ready_with_warnings_teams: int = 0
    not_ready_teams: int = 0
    warnings: int = 0
    errors: int = 0
    results: List[TeamValidationResult] = Field(default_factory=list)
"""

VALIDATOR_CONTENT = """import logging
from typing import Dict, List, Optional, Any
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline
from workforce.employees.models import Employee
from teams.validation.models import (
    TeamReadiness, ValidationIssue, TeamValidationResult, TeamValidationSummary
)
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
"""

CLI_SCRIPT = """import sys
from pathlib import Path
from teams.validation.models import TeamReadiness
from teams.registry import TeamRegistry, TeamCatalogue
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver
from teams.validator import TeamValidator
from teams.seed import seed

def main():
    print("Initializing Registries...")
    tr = TeamRegistry()
    pr = PipelineRegistry(tr)
    
    # Load all seeds into registries
    print("Loading Team Catalogue...")
    seed_data = seed()
    for team in seed_data["teams"]:
        try:
            tr.register(team)
        except: pass
    for pipe in seed_data["pipelines"]:
        try:
            pr.register(pipe)
        except: pass
        
    resolver = TeamCapabilityResolver(tr, pr)
    validator = TeamValidator(tr, pr, resolver)
    
    print("Validating Teams...")
    summary = validator.validate_all()
    
    print("\\n============================================")
    print("Mycel Team Validation Report")
    print("============================================")
    print(f"Teams checked: {summary.total_teams}")
    print(f"Ready: {summary.ready_teams}")
    print(f"Warnings: {summary.warnings}")
    print(f"Errors: {summary.errors}\\n")
    
    for res in summary.results:
        print(f"{res.team_id.capitalize()}: {res.readiness.value}")
        if res.errors:
            for err in res.errors:
                print(f"  [ERROR] {err.code}: {err.message}")
        if res.warnings:
            for warn in res.warnings:
                print(f"  [WARN] {warn.code}: {warn.message}")
                
    if summary.errors > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

TESTS_CONTENT = """import pytest
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver
from teams.validator import TeamValidator
from teams.validation.models import TeamReadiness
from organization.teams.models import Team
from execution.pipelines.models import TeamPipeline, PipelineInputContract
from workforce.employees.models import (
    Employee, EmployeeIdentity, Personality, Experience
)

@pytest.fixture
def mock_validator():
    tr = TeamRegistry()
    pr = PipelineRegistry(tr)
    resolver = TeamCapabilityResolver(tr, pr)
    
    # Mocking seed data
    dev_team = Team(id="developer", company_id="k", name="Developer")
    tr.register(dev_team)
    
    dev_pipe = TeamPipeline(
        pipeline_id="dev_pipe", team_id="developer", name="pipe",
        input_contract=PipelineInputContract(input_type="task"),
        output_contract_id="code", stages=[]
    )
    pr.register(dev_pipe)
    
    dev_member1 = Employee(
        employee_id="m1", company_id="k", department_id="d", team_id="developer",
        position_id="p1", name="N", display_name="N", reasoning_profile_id="r",
        identity=EmployeeIdentity(title="t", specialization="s", summary="s", personality="p", communication_style="c", experience_level="e"),
        personality=Personality(communication_style="c", decision_style="d"),
        experience=Experience(level="e", years_equivalent=1)
    )
    dev_member2 = dev_member1.model_copy(update={"employee_id": "m2"})
    dev_member3 = dev_member1.model_copy(update={"employee_id": "m3"})
    
    validator = TeamValidator(tr, pr, resolver)
    validator.seed_data = {
        "teams": [dev_team],
        "pipelines": [dev_pipe],
        "members": [dev_member1, dev_member2, dev_member3]
    }
    
    return validator, dev_member1

def test_valid_team(mock_validator):
    validator, _ = mock_validator
    res = validator.validate_team("developer")
    
    assert res.valid is True
    assert res.readiness == TeamReadiness.READY
    assert len(res.errors) == 0

def test_invalid_team_missing(mock_validator):
    validator, _ = mock_validator
    res = validator.validate_team("unknown")
    
    assert res.valid is False
    assert res.readiness == TeamReadiness.NOT_READY
    assert res.errors[0].code == "TEAM_ID_REQUIRED"

def test_member_count_validation(mock_validator):
    validator, _ = mock_validator
    # Remove one member
    validator.seed_data["members"].pop()
    
    res = validator.validate_team("developer")
    
    assert res.valid is False
    assert res.errors[0].code == "MEMBER_COUNT_INVALID"

def test_pipeline_team_mismatch(mock_validator):
    validator, _ = mock_validator
    # Create an invalid pipeline scenario directly modifying the loaded seed data object
    pipe = validator.seed_data["pipelines"][0]
    pipe.team_id = "research"
    
    # We validate "research", it won't be in the team registry.
    # We validate "developer", it will lack pipelines.
    res_dev = validator.validate_team("developer")
    assert res_dev.valid is False
    assert res_dev.errors[0].code == "PIPELINE_NOT_FOUND"

def test_strict_mode(mock_validator):
    validator, _ = mock_validator
    # Add a fake warning to simulate warning failure
    res = validator.validate_team("developer")
    res.warnings.append("Fake warning")
    validator._finalize_readiness(res, strict=True)
    
    assert res.readiness == TeamReadiness.NOT_READY
    assert res.valid is False

def test_architectural_boundaries(mock_validator):
    validator, _ = mock_validator
    assert not hasattr(validator, "call_llm")
    assert not hasattr(validator, "execute_tool")
    assert not hasattr(validator, "create_agent")
"""

def generate_validator():
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    init_file = VALIDATION_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")
    
    models_file = VALIDATION_DIR / "models.py"
    models_file.write_text(MODELS_CONTENT, encoding="utf-8")
    
    validator_file = TEAMS_DIR / "validator.py"
    validator_file.write_text(VALIDATOR_CONTENT, encoding="utf-8")
    
    cli_file = SCRIPTS_DIR / "validate_teams.py"
    cli_file.write_text(CLI_SCRIPT, encoding="utf-8")
    
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    test_file = TESTS_DIR / "test_team_validator.py"
    test_file.write_text(TESTS_CONTENT, encoding="utf-8")

if __name__ == "__main__":
    generate_validator()
    print("Generated TOS 17 Team Validator completed successfully.")
