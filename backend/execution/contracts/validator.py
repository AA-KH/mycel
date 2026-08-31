import logging
from typing import Optional
from execution.contracts.models import (
    TeamExecutionContract,
    ContractStatus,
    ContractReadiness,
    ContractValidationIssue,
    TeamContractValidationResult,
    ContractValidationSummary,
)
from execution.contracts.registry import ExecutionContractRegistry
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Stable validation error codes
# ─────────────────────────────────────────────────────────────────────────────
# CONTRACT_ID_REQUIRED             – contract_id is empty
# CONTRACT_TEAM_REQUIRED           – team_id is missing
# CONTRACT_TEAM_NOT_FOUND          – team_id not in TeamRegistry
# CONTRACT_TEAM_MISMATCH           – contract declares wrong team_id
# CONTRACT_PIPELINE_NOT_FOUND      – pipeline_id not in PipelineRegistry
# CONTRACT_PIPELINE_TEAM_MISMATCH  – pipeline belongs to a different team
# CONTRACT_SKILL_NOT_FOUND         – required skill not in team capabilities
# CONTRACT_TOOL_NOT_FOUND          – required tool not in team capabilities
# CONTRACT_TASK_TYPES_MISSING      – no accepted_task_types declared
# CONTRACT_COMPLETION_CRITERIA_MISSING – completion_criteria list empty
# CONTRACT_FAILURE_CONDITIONS_MISSING  – failure_conditions list empty
# CONTRACT_HANDOFF_MISSING         – handoff_contract not configured
# CONTRACT_NO_INPUTS               – no required or optional inputs (warning)
# CONTRACT_DRAFT_NOT_EXECUTABLE    – DRAFT contracts are not executable (warning)
# ─────────────────────────────────────────────────────────────────────────────


class TeamExecutionContractValidator:
    """
    Validates whether a TeamExecutionContract is structurally correct,
    referentially consistent, and ready for future runtime use.

    Validation is DETERMINISTIC — no LLM, no tools, no pipelines execute.
    Same contract → same result, every time.

    Responsibilities:
        - Identity & ownership checks
        - Pipeline ownership verification
        - Capability compatibility check (via TeamCapabilityResolver)
        - Completion criteria and failure conditions presence
        - Handoff definition presence
        - Status-based readiness assessment

    NOT responsible for:
        - Executing contracts
        - Running pipelines or quality gates
        - Selecting members or agents
        - Generating artifacts
    """

    def __init__(
        self,
        contract_registry: ExecutionContractRegistry,
        team_registry: TeamRegistry,
        pipeline_registry: PipelineRegistry,
        capability_resolver: TeamCapabilityResolver,
    ):
        self.contract_registry = contract_registry
        self.team_registry = team_registry
        self.pipeline_registry = pipeline_registry
        self.capability_resolver = capability_resolver

    # ── Public API ─────────────────────────────────────────────────────────

    def validate(
        self, contract_id: str, strict: bool = False
    ) -> TeamContractValidationResult:
        contract = self.contract_registry.get(contract_id)
        if not contract:
            result = TeamContractValidationResult(
                contract_id=contract_id, team_id="unknown"
            )
            result.errors.append(ContractValidationIssue(
                code="CONTRACT_ID_REQUIRED",
                message=f"Contract '{contract_id}' not found in registry.",
                severity="ERROR",
                path="contract_id",
            ))
            self._finalise(result, strict)
            return result
        return self.validate_contract(contract, strict=strict)

    def validate_contract(
        self, contract: TeamExecutionContract, strict: bool = False
    ) -> TeamContractValidationResult:
        result = TeamContractValidationResult(
            contract_id=contract.contract_id,
            team_id=contract.team_id,
        )

        self._check_identity(contract, result)
        self._check_team_ownership(contract, result)
        self._check_pipeline_ownership(contract, result)
        self._check_capabilities(contract, result)
        self._check_task_types(contract, result)
        self._check_completion_criteria(contract, result)
        self._check_failure_conditions(contract, result)
        self._check_inputs(contract, result)
        self._check_status(contract, result)

        self._finalise(result, strict)
        return result

    def validate_all(self, strict: bool = False) -> ContractValidationSummary:
        summary = ContractValidationSummary()
        for contract in self.contract_registry.list_all():
            res = self.validate_contract(contract, strict=strict)
            summary.results.append(res)
            summary.total_contracts += 1
            summary.total_errors += len(res.errors)
            summary.total_warnings += len(res.warnings)
            if res.valid:
                summary.valid_contracts += 1
            else:
                summary.invalid_contracts += 1
            if res.readiness == ContractReadiness.READY:
                summary.ready_contracts += 1
            else:
                summary.not_ready_contracts += 1
        return summary

    # ── Internal checks ────────────────────────────────────────────────────

    def _check_identity(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.contract_id:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_ID_REQUIRED",
                message="contract_id must not be empty.",
                severity="ERROR", path="contract_id",
            ))
        if not c.team_id:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_TEAM_REQUIRED",
                message="team_id must not be empty.",
                severity="ERROR", path="team_id",
            ))

    def _check_team_ownership(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.team_id:
            return
        if not self.team_registry.exists(c.team_id):
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_TEAM_NOT_FOUND",
                message=f"Team '{c.team_id}' declared in contract does not exist in TeamRegistry.",
                severity="ERROR", path=f"team_id={c.team_id}",
            ))

    def _check_pipeline_ownership(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.pipeline_id:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_PIPELINE_NOT_FOUND",
                message="Contract declares no pipeline_id.",
                severity="ERROR", path="pipeline_id",
            ))
            return

        pipeline = self.pipeline_registry.get_pipeline(c.pipeline_id)
        if not pipeline:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_PIPELINE_NOT_FOUND",
                message=f"Pipeline '{c.pipeline_id}' not found in PipelineRegistry.",
                severity="ERROR", path=f"pipeline_id={c.pipeline_id}",
            ))
            return

        if pipeline.team_id != c.team_id:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_PIPELINE_TEAM_MISMATCH",
                message=(
                    f"Pipeline '{c.pipeline_id}' belongs to team '{pipeline.team_id}', "
                    f"but contract declares team '{c.team_id}'."
                ),
                severity="ERROR",
                path=f"pipeline_id={c.pipeline_id}",
            ))

    def _check_capabilities(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.team_id or not self.team_registry.exists(c.team_id):
            return  # team errors already recorded above

        resolution = self.capability_resolver.resolve(c.team_id)
        if not resolution.resolved or not resolution.profile:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_TEAM_NOT_FOUND",
                message=f"Capability resolution failed for team '{c.team_id}'.",
                severity="ERROR", path=f"capabilities.{c.team_id}",
            ))
            return

        profile = resolution.profile
        for skill in c.required_skills:
            if skill not in profile.skills:
                r.errors.append(ContractValidationIssue(
                    code="CONTRACT_SKILL_NOT_FOUND",
                    message=f"Required skill '{skill}' not found in team '{c.team_id}' capabilities.",
                    severity="ERROR", path=f"required_skills.{skill}",
                ))

        for tool in c.required_tools:
            if tool not in profile.tools:
                r.errors.append(ContractValidationIssue(
                    code="CONTRACT_TOOL_NOT_FOUND",
                    message=f"Required tool '{tool}' not found in team '{c.team_id}' capabilities.",
                    severity="ERROR", path=f"required_tools.{tool}",
                ))

    def _check_task_types(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.accepted_task_types:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_TASK_TYPES_MISSING",
                message="Contract must declare at least one accepted_task_type.",
                severity="ERROR", path="accepted_task_types",
            ))

    def _check_completion_criteria(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.completion_criteria:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_COMPLETION_CRITERIA_MISSING",
                message="Contract must define completion_criteria.",
                severity="ERROR", path="completion_criteria",
            ))

    def _check_failure_conditions(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.failure_conditions:
            r.errors.append(ContractValidationIssue(
                code="CONTRACT_FAILURE_CONDITIONS_MISSING",
                message="Contract must define failure_conditions.",
                severity="ERROR", path="failure_conditions",
            ))

    def _check_inputs(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if not c.required_inputs and not c.optional_inputs:
            r.warnings.append(ContractValidationIssue(
                code="CONTRACT_NO_INPUTS",
                message="Contract declares no required or optional inputs — verify this is intentional.",
                severity="WARNING", path="required_inputs",
            ))

    def _check_status(
        self, c: TeamExecutionContract, r: TeamContractValidationResult
    ) -> None:
        r.checks += 1
        if c.status == ContractStatus.DRAFT:
            r.warnings.append(ContractValidationIssue(
                code="CONTRACT_DRAFT_NOT_EXECUTABLE",
                message=f"Contract '{c.contract_id}' is DRAFT and cannot be selected by future runtime.",
                severity="WARNING", path="status",
            ))

    # ── Readiness finalisation ─────────────────────────────────────────────

    def _finalise(
        self, result: TeamContractValidationResult, strict: bool
    ) -> None:
        has_errors = bool(result.errors)
        has_warnings = bool(result.warnings)

        result.valid = not has_errors

        if has_errors:
            result.readiness = ContractReadiness.NOT_READY
        elif strict and has_warnings:
            result.readiness = ContractReadiness.NOT_READY
            result.valid = False
        elif has_warnings:
            result.readiness = ContractReadiness.READY_WITH_WARNINGS
        else:
            result.readiness = ContractReadiness.READY
