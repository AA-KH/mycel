import logging
from typing import Optional
from execution.collaboration.models import (
    TeamCollaborationContract,
    CollaborationStatus,
    CollaborationReadiness,
    CollaborationValidationIssue,
    TeamCollaborationValidationResult,
    CollaborationValidationSummary,
)
from execution.collaboration.registry import TeamCollaborationContractRegistry
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from execution.contracts.registry import ExecutionContractRegistry
from teams.resolver import TeamCapabilityResolver

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Stable validation error codes
# ─────────────────────────────────────────────────────────────────────────────
#
# COLLABORATION_ID_REQUIRED         – contract_id is empty
# REQUESTING_TEAM_NOT_FOUND         – requesting_team_id not in TeamRegistry
# PROVIDING_TEAM_NOT_FOUND          – providing_team_id not in TeamRegistry
# SELF_COLLABORATION_NOT_ALLOWED    – requesting == providing team
# EXECUTION_CONTRACT_NOT_FOUND      – execution_contract_id not in ExecutionContractRegistry
# EXECUTION_CONTRACT_TEAM_MISMATCH  – execution contract belongs to different team
# PIPELINE_NOT_FOUND                – pipeline_id not in PipelineRegistry
# PIPELINE_TEAM_MISMATCH            – pipeline belongs to different team
# PROVIDER_CAPABILITY_MISSING       – providing team missing a required capability
# REQUEST_TYPE_INVALID              – accepted_request_types is empty
# COMPLETION_CRITERIA_MISSING       – completion_criteria is empty
# FAILURE_CONDITION_MISSING         – failure_conditions is empty
# COLLABORATION_DRAFT_NOT_USABLE    – DRAFT contract is not usable by future systems (WARNING)
# COLLABORATION_NO_INPUTS           – no inputs declared (WARNING)
#
# ─────────────────────────────────────────────────────────────────────────────


class TeamCollaborationContractValidator:
    """
    Validates whether a TeamCollaborationContract is structurally correct,
    referentially consistent, and ready for future runtime use.

    Validation is DETERMINISTIC — no LLM, no tools, no pipelines execute.

    Check layers:
        1.  Identity
        2.  Requesting team ownership
        3.  Providing team ownership
        4.  Self-collaboration guard
        5.  Execution contract reference (if set)
        6.  Pipeline ownership (if set)
        7.  Provider capability compatibility
        8.  Request types
        9.  Completion criteria
        10. Failure conditions
        11. Inputs / Status warnings
    """

    def __init__(
        self,
        collaboration_registry: TeamCollaborationContractRegistry,
        team_registry: TeamRegistry,
        pipeline_registry: PipelineRegistry,
        execution_contract_registry: ExecutionContractRegistry,
        capability_resolver: TeamCapabilityResolver,
    ):
        self.collaboration_registry = collaboration_registry
        self.team_registry = team_registry
        self.pipeline_registry = pipeline_registry
        self.execution_contract_registry = execution_contract_registry
        self.capability_resolver = capability_resolver

    # ── Public API ─────────────────────────────────────────────────────────

    def validate(
        self, contract_id: str, strict: bool = False
    ) -> TeamCollaborationValidationResult:
        contract = self.collaboration_registry.get(contract_id)
        if not contract:
            result = TeamCollaborationValidationResult(
                contract_id=contract_id,
                requesting_team_id="unknown",
                providing_team_id="unknown",
            )
            result.errors.append(CollaborationValidationIssue(
                code="COLLABORATION_ID_REQUIRED",
                message=f"Collaboration contract '{contract_id}' not found in registry.",
                severity="ERROR",
                path="contract_id",
            ))
            self._finalise(result, strict)
            return result
        return self.validate_contract(contract, strict=strict)

    def validate_contract(
        self,
        contract: TeamCollaborationContract,
        strict: bool = False,
    ) -> TeamCollaborationValidationResult:
        result = TeamCollaborationValidationResult(
            contract_id=contract.contract_id,
            requesting_team_id=contract.requesting_team_id,
            providing_team_id=contract.providing_team_id,
        )

        self._check_identity(contract, result)
        self._check_requesting_team(contract, result)
        self._check_providing_team(contract, result)
        self._check_self_collaboration(contract, result)
        self._check_execution_contract(contract, result)
        self._check_pipeline(contract, result)
        self._check_provider_capabilities(contract, result)
        self._check_request_types(contract, result)
        self._check_completion_criteria(contract, result)
        self._check_failure_conditions(contract, result)
        self._check_inputs_and_status(contract, result)

        self._finalise(result, strict)
        return result

    def validate_all(self, strict: bool = False) -> CollaborationValidationSummary:
        summary = CollaborationValidationSummary()
        for contract in self.collaboration_registry.list_all():
            res = self.validate_contract(contract, strict=strict)
            summary.results.append(res)
            summary.total_contracts += 1
            summary.total_errors += len(res.errors)
            summary.total_warnings += len(res.warnings)
            if res.valid:
                summary.valid_contracts += 1
            else:
                summary.invalid_contracts += 1
            if res.readiness == CollaborationReadiness.READY:
                summary.ready_contracts += 1
            else:
                summary.not_ready_contracts += 1
        return summary

    # ── Internal checks ────────────────────────────────────────────────────

    def _err(
        self,
        result: TeamCollaborationValidationResult,
        code: str,
        message: str,
        path: str,
    ) -> None:
        result.checks += 1
        result.errors.append(CollaborationValidationIssue(
            code=code, message=message, severity="ERROR", path=path,
        ))

    def _warn(
        self,
        result: TeamCollaborationValidationResult,
        code: str,
        message: str,
        path: str,
    ) -> None:
        result.checks += 1
        result.warnings.append(CollaborationValidationIssue(
            code=code, message=message, severity="WARNING", path=path,
        ))

    def _check_identity(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.contract_id:
            self._err(r, "COLLABORATION_ID_REQUIRED",
                      "contract_id must not be empty.", "contract_id")
        if not c.requesting_team_id:
            self._err(r, "REQUESTING_TEAM_NOT_FOUND",
                      "requesting_team_id must not be empty.", "requesting_team_id")
        if not c.providing_team_id:
            self._err(r, "PROVIDING_TEAM_NOT_FOUND",
                      "providing_team_id must not be empty.", "providing_team_id")

    def _check_requesting_team(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if c.requesting_team_id and not self.team_registry.exists(c.requesting_team_id):
            self._err(
                r, "REQUESTING_TEAM_NOT_FOUND",
                f"Requesting team '{c.requesting_team_id}' not found in TeamRegistry.",
                f"requesting_team_id={c.requesting_team_id}",
            )

    def _check_providing_team(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if c.providing_team_id and not self.team_registry.exists(c.providing_team_id):
            self._err(
                r, "PROVIDING_TEAM_NOT_FOUND",
                f"Providing team '{c.providing_team_id}' not found in TeamRegistry.",
                f"providing_team_id={c.providing_team_id}",
            )

    def _check_self_collaboration(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if c.requesting_team_id and c.providing_team_id:
            if c.requesting_team_id == c.providing_team_id:
                self._err(
                    r, "SELF_COLLABORATION_NOT_ALLOWED",
                    f"Team '{c.requesting_team_id}' cannot collaborate with itself. "
                    "Use a Team Execution Contract for internal work.",
                    "requesting_team_id",
                )

    def _check_execution_contract(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.execution_contract_id:
            return  # optional — no error

        exec_contract = self.execution_contract_registry.get(c.execution_contract_id)
        if not exec_contract:
            self._err(
                r, "EXECUTION_CONTRACT_NOT_FOUND",
                f"Execution contract '{c.execution_contract_id}' not found "
                "in ExecutionContractRegistry.",
                f"execution_contract_id={c.execution_contract_id}",
            )
            return

        if exec_contract.team_id != c.providing_team_id:
            self._err(
                r, "EXECUTION_CONTRACT_TEAM_MISMATCH",
                f"Execution contract '{c.execution_contract_id}' belongs to team "
                f"'{exec_contract.team_id}', but collaboration declares providing team "
                f"'{c.providing_team_id}'.",
                f"execution_contract_id={c.execution_contract_id}",
            )

    def _check_pipeline(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.pipeline_id:
            return  # optional — no error

        pipeline = self.pipeline_registry.get_pipeline(c.pipeline_id)
        if not pipeline:
            self._err(
                r, "PIPELINE_NOT_FOUND",
                f"Pipeline '{c.pipeline_id}' not found in PipelineRegistry.",
                f"pipeline_id={c.pipeline_id}",
            )
            return

        if pipeline.team_id != c.providing_team_id:
            self._err(
                r, "PIPELINE_TEAM_MISMATCH",
                f"Pipeline '{c.pipeline_id}' belongs to team '{pipeline.team_id}', "
                f"but collaboration declares providing team '{c.providing_team_id}'.",
                f"pipeline_id={c.pipeline_id}",
            )

    def _check_provider_capabilities(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.providing_team_id or not self.team_registry.exists(c.providing_team_id):
            return  # already flagged above

        if not c.required_capabilities and not c.required_tools:
            return  # nothing to check

        resolution = self.capability_resolver.resolve(c.providing_team_id)
        if not resolution.resolved or not resolution.profile:
            self._err(
                r, "PROVIDING_TEAM_NOT_FOUND",
                f"Capability resolution failed for providing team '{c.providing_team_id}'.",
                f"capabilities.{c.providing_team_id}",
            )
            return

        profile = resolution.profile
        for cap in c.required_capabilities:
            if cap not in profile.skills and cap not in profile.tools:
                self._err(
                    r, "PROVIDER_CAPABILITY_MISSING",
                    f"Providing team '{c.providing_team_id}' is missing required "
                    f"capability '{cap}'.",
                    f"required_capabilities.{cap}",
                )

        for tool in c.required_tools:
            if tool not in profile.tools:
                self._err(
                    r, "PROVIDER_CAPABILITY_MISSING",
                    f"Providing team '{c.providing_team_id}' is missing required "
                    f"tool '{tool}'.",
                    f"required_tools.{tool}",
                )

    def _check_request_types(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.accepted_request_types:
            self._err(
                r, "REQUEST_TYPE_INVALID",
                "accepted_request_types must not be empty.",
                "accepted_request_types",
            )

    def _check_completion_criteria(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.completion_criteria:
            self._err(
                r, "COMPLETION_CRITERIA_MISSING",
                "Collaboration contract must define completion_criteria.",
                "completion_criteria",
            )

    def _check_failure_conditions(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.failure_conditions:
            self._err(
                r, "FAILURE_CONDITION_MISSING",
                "Collaboration contract must define failure_conditions.",
                "failure_conditions",
            )

    def _check_inputs_and_status(
        self, c: TeamCollaborationContract, r: TeamCollaborationValidationResult
    ) -> None:
        r.checks += 1
        if not c.required_inputs and not c.optional_inputs:
            self._warn(
                r, "COLLABORATION_NO_INPUTS",
                "Collaboration declares no inputs — verify this is intentional.",
                "required_inputs",
            )
        if c.status == CollaborationStatus.DRAFT:
            self._warn(
                r, "COLLABORATION_DRAFT_NOT_USABLE",
                f"Contract '{c.contract_id}' is DRAFT and cannot be used by future systems.",
                "status",
            )

    # ── Readiness finalisation ─────────────────────────────────────────────

    def _finalise(
        self,
        result: TeamCollaborationValidationResult,
        strict: bool,
    ) -> None:
        has_errors = bool(result.errors)
        has_warnings = bool(result.warnings)

        result.valid = not has_errors

        if has_errors:
            result.readiness = CollaborationReadiness.NOT_READY
        elif strict and has_warnings:
            result.readiness = CollaborationReadiness.NOT_READY
            result.valid = False
        elif has_warnings:
            result.readiness = CollaborationReadiness.READY_WITH_WARNINGS
        else:
            result.readiness = CollaborationReadiness.READY
