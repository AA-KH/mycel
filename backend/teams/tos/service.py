"""
Team Operating System Service (TOS 20)

A READ-ONLY integration facade that provides a unified view over all
Team Operating System subsystems (TOS 0–19).

Responsibilities:
    - get_team_snapshot        → TOSTeamSnapshot
    - get_operating_profile    → TOSTeamOperatingProfile
    - get_team_health          → TOSTeamHealthReport
    - get_validation_report    → TOSTeamValidationReport
    - get_capability_view      → TOSTeamCapabilityView
    - get_execution_contracts  → List[str]  (contract IDs)
    - get_collaboration_contracts → TOSContractMap
    - make_execution_context   → TeamExecutionContext

Boundaries (MUST NOT):
    ✗ Execute pipelines
    ✗ Call LLMs
    ✗ Invoke tools
    ✗ Create agents
    ✗ Generate artifacts
    ✗ Hire members
    ✗ Route tasks
    ✗ Mutate any subsystem
    ✗ Expose secrets, credentials, or raw knowledge

Every subsystem continues to own its own data.
This service is an aggregation point — not a second source of truth.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path

from teams.tos.models import (
    TOSTeamReadiness,
    TOSValidationComponent,
    TOSTeamValidationReport,
    TOSTeamCapabilityView,
    TOSContractMap,
    TOSComponentHealth,
    TOSTeamHealthReport,
    TOSTeamOperatingProfile,
    TOSTeamSnapshot,
)
from teams.tos.context import TeamExecutionContext
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from teams.resolver import TeamCapabilityResolver
from teams.validator import TeamValidator
from execution.contracts.registry import ExecutionContractRegistry
from execution.collaboration.registry import TeamCollaborationContractRegistry

logger = logging.getLogger(__name__)


class TeamOperatingSystemService:
    """
    Read-only integration facade for the Team Operating System.

    Accepts injected registries so that the service can be used
    in tests with lightweight fixtures as well as in production with
    fully-seeded registries.
    """

    def __init__(
        self,
        team_registry: TeamRegistry,
        pipeline_registry: PipelineRegistry,
        capability_resolver: TeamCapabilityResolver,
        team_validator: TeamValidator,
        execution_contract_registry: ExecutionContractRegistry,
        collaboration_registry: TeamCollaborationContractRegistry,
    ):
        self._teams = team_registry
        self._pipelines = pipeline_registry
        self._resolver = capability_resolver
        self._validator = team_validator
        self._exec_contracts = execution_contract_registry
        self._collab_contracts = collaboration_registry

    # ─────────────────────────────────────────────────────────────────────
    # Primary façade methods
    # ─────────────────────────────────────────────────────────────────────

    def get_team_snapshot(self, team_id: str) -> TOSTeamSnapshot:
        """
        Generate a lightweight, stable snapshot of a team's operational state.
        Contains only IDs and safe summaries. Never exposes secrets.
        """
        team = self._teams.get_team(team_id)
        if not team:
            return TOSTeamSnapshot(
                team_id=team_id,
                readiness=TOSTeamReadiness.NOT_READY,
                metadata={"error": f"Team '{team_id}' not found in TeamRegistry"},
            )

        # Capability resolution
        capability_view = self.get_capability_view(team_id)

        # Validation
        validation = self.get_validation_report(team_id)

        # Contracts
        contract_map = self.get_collaboration_contracts(team_id)
        exec_ids = self.get_execution_contracts(team_id)

        # Members from seed
        member_ids = self._get_member_ids(team_id)
        position_ids = capability_view.positions

        return TOSTeamSnapshot(
            team_id=team_id,
            team_name=team.name,
            company_id=team.company_id,
            slug=getattr(team, "slug", team_id),
            status=getattr(team, "status", "ACTIVE"),
            version=getattr(team, "version", "1.0.0"),

            readiness=validation.readiness,
            validation_valid=validation.overall_valid,
            validation_error_count=validation.total_errors,
            validation_warning_count=validation.total_warnings,

            skill_ids=capability_view.skills,
            tool_ids=capability_view.tools,
            knowledge_ids=capability_view.knowledge,
            reasoning_ids=capability_view.reasoning,
            capability_resolved=capability_view.resolved,

            pipeline_ids=capability_view.pipelines,
            stage_ids=capability_view.pipelines,   # stages stored as pipeline IDs in profile

            quality_gate_ids=capability_view.quality_requirements,
            output_contract_ids=capability_view.outputs,

            position_ids=position_ids,
            member_ids=member_ids,
            member_count=len(member_ids),

            execution_contract_ids=exec_ids,
            outgoing_collaboration_ids=contract_map.outgoing_collaboration_ids,
            incoming_collaboration_ids=contract_map.incoming_collaboration_ids,
        )

    def get_operating_profile(self, team_id: str) -> TOSTeamOperatingProfile:
        """
        Generate a human-readable operational profile for a team.
        Derived on-demand; not stored separately.
        """
        snapshot = self.get_team_snapshot(team_id)
        contract_map = self.get_collaboration_contracts(team_id)

        # Derive team IDs this team collaborates with
        collaborates_with = self._collaborating_team_ids(team_id)

        return TOSTeamOperatingProfile(
            team_id=team_id,
            team_name=snapshot.team_name,
            company_id=snapshot.company_id,
            slug=snapshot.slug,
            status=snapshot.status,
            readiness=snapshot.readiness,

            common_skills=snapshot.skill_ids,
            common_tools=snapshot.tool_ids,
            knowledge_spaces=snapshot.knowledge_ids,
            reasoning_profiles=snapshot.reasoning_ids,

            pipeline_ids=snapshot.pipeline_ids,
            output_contract_ids=snapshot.output_contract_ids,
            quality_gate_ids=snapshot.quality_gate_ids,
            position_ids=snapshot.position_ids,
            member_count=snapshot.member_count,

            execution_contract_ids=snapshot.execution_contract_ids,
            outgoing_collaboration_ids=contract_map.outgoing_collaboration_ids,
            incoming_collaboration_ids=contract_map.incoming_collaboration_ids,
            collaborates_with=collaborates_with,
        )

    def get_team_health(self, team_id: str) -> TOSTeamHealthReport:
        """
        Produce a lightweight health report for a team.
        Derived from validation and capability resolution — nothing executes.
        """
        validation = self.get_validation_report(team_id)
        capability_view = self.get_capability_view(team_id)

        components: List[TOSComponentHealth] = []
        all_errors: List[str] = []
        all_warnings: List[str] = []

        for comp in validation.components:
            healthy = comp.status in ("VALID", "WARNING")
            components.append(TOSComponentHealth(
                component=comp.component,
                healthy=healthy,
                issues=comp.errors + comp.warnings,
            ))
            all_errors.extend(comp.errors)
            all_warnings.extend(comp.warnings)

        if not capability_view.resolved:
            components.append(TOSComponentHealth(
                component="capability_resolution",
                healthy=False,
                issues=capability_view.resolution_errors or ["Capability resolution failed"],
            ))
            all_errors.extend(capability_view.resolution_errors or ["Capability resolution failed"])

        # Status
        if all_errors:
            status = "UNHEALTHY"
        elif all_warnings:
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        return TOSTeamHealthReport(
            team_id=team_id,
            status=status,
            readiness=validation.readiness,
            components=components,
            warnings=all_warnings,
            errors=all_errors,
        )

    def get_validation_report(self, team_id: str) -> TOSTeamValidationReport:
        """
        Aggregate validation results from all TOS subsystems for a team.
        Calls existing validators — does NOT duplicate their logic.
        """
        report = TOSTeamValidationReport(team_id=team_id)

        # ── 1. Identity ───────────────────────────────────────────────────
        identity_comp = self._validate_identity(team_id)
        report.add_component(identity_comp)

        # ── 2. Capabilities ───────────────────────────────────────────────
        capability_comp = self._validate_capabilities(team_id)
        report.add_component(capability_comp)

        # ── 3. Pipelines ──────────────────────────────────────────────────
        pipeline_comp = self._validate_pipelines(team_id)
        report.add_component(pipeline_comp)

        # ── 4. Execution contracts ────────────────────────────────────────
        exec_comp = self._validate_execution_contracts(team_id)
        report.add_component(exec_comp)

        # ── 5. Collaboration contracts ────────────────────────────────────
        collab_comp = self._validate_collaboration_contracts(team_id)
        report.add_component(collab_comp)

        # ── 6. Full team validation via existing TeamValidator ────────────
        team_val_comp = self._validate_via_team_validator(team_id)
        report.add_component(team_val_comp)

        # ── Compute overall readiness ─────────────────────────────────────
        report.overall_valid = report.total_errors == 0
        report.readiness = self._compute_readiness(report)
        return report

    def get_capability_view(self, team_id: str) -> TOSTeamCapabilityView:
        """
        Derived capability view sourced entirely from TeamCapabilityResolver.
        No new data store.
        """
        view = TOSTeamCapabilityView(team_id=team_id)
        resolution = self._resolver.resolve(team_id)
        if not resolution.resolved or not resolution.profile:
            view.resolved = False
            view.resolution_errors = list(resolution.errors)
            return view

        profile = resolution.profile
        view.skills = list(profile.skills)
        view.tools = list(profile.tools)
        view.knowledge = list(profile.knowledge)
        view.reasoning = list(profile.reasoning)
        view.pipelines = list(profile.pipelines)
        view.outputs = list(profile.outputs)
        view.quality_requirements = list(profile.quality_requirements)
        view.positions = list(profile.positions)
        view.resolved = True
        return view

    def get_execution_contracts(self, team_id: str) -> List[str]:
        """IDs of all ACTIVE execution contracts for a team."""
        return [
            c.contract_id
            for c in self._exec_contracts.get_active_by_team(team_id)
        ]

    def get_collaboration_contracts(self, team_id: str) -> TOSContractMap:
        """
        IDs of collaboration contracts where this team is provider or requester.
        Outgoing = this team is the PROVIDER (does the work).
        Incoming = this team is the REQUESTER (asks for the work).
        """
        outgoing = [
            c.contract_id
            for c in self._collab_contracts.get_active_by_providing_team(team_id)
        ]
        incoming = [
            c.contract_id
            for c in self._collab_contracts.get_active_by_requesting_team(team_id)
        ]
        return TOSContractMap(
            team_id=team_id,
            execution_contract_ids=self.get_execution_contracts(team_id),
            outgoing_collaboration_ids=outgoing,
            incoming_collaboration_ids=incoming,
        )

    def make_execution_context(
        self,
        team_id: str,
        task_id: Optional[str] = None,
        execution_contract_id: Optional[str] = None,
        collaboration_contract_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        position_id: Optional[str] = None,
        member_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        initiated_by_team_id: Optional[str] = None,
        notes: str = "",
    ) -> TeamExecutionContext:
        """
        Create an immutable execution identity context.
        Does NOT execute anything. Does NOT hire. Does NOT create agents.
        """
        return TeamExecutionContext(
            context_id=str(uuid.uuid4()),
            team_id=team_id,
            task_id=task_id,
            execution_contract_id=execution_contract_id,
            collaboration_contract_id=collaboration_contract_id,
            pipeline_id=pipeline_id,
            position_id=position_id,
            member_id=member_id,
            agent_id=agent_id,
            initiated_by_team_id=initiated_by_team_id,
            notes=notes,
        )

    # ─────────────────────────────────────────────────────────────────────
    # Private helpers — subsystem validation slices
    # ─────────────────────────────────────────────────────────────────────

    def _validate_identity(self, team_id: str) -> TOSValidationComponent:
        comp = TOSValidationComponent(component="identity")
        if not self._teams.exists(team_id):
            comp.errors.append(f"TOS_TEAM_NOT_FOUND: Team '{team_id}' not in TeamRegistry")
            comp.status = "INVALID"
            return comp
        team = self._teams.get_team(team_id)
        if not team or not team.name:
            comp.errors.append(f"TOS_IDENTITY_INVALID: Team '{team_id}' has no name")
            comp.status = "INVALID"
            return comp
        comp.status = "VALID"
        return comp

    def _validate_capabilities(self, team_id: str) -> TOSValidationComponent:
        comp = TOSValidationComponent(component="capabilities")
        resolution = self._resolver.resolve(team_id)
        if not resolution.resolved:
            comp.errors.append(f"TOS_CAPABILITY_INVALID: Capability resolution failed for '{team_id}'")
            comp.status = "INVALID"
        else:
            comp.warnings.extend(resolution.warnings)
            comp.status = "WARNING" if resolution.warnings else "VALID"
        return comp

    def _validate_pipelines(self, team_id: str) -> TOSValidationComponent:
        comp = TOSValidationComponent(component="pipelines")
        try:
            pipelines = self._pipelines.get_team_pipelines(team_id)
        except AttributeError:
            pipelines = []

        if not pipelines:
            comp.errors.append(f"TOS_PIPELINE_INVALID: No pipelines registered for team '{team_id}'")
            comp.status = "INVALID"
        else:
            # Cross-team leakage check
            for p in pipelines:
                if p.team_id != team_id:
                    comp.errors.append(
                        f"TOS_PIPELINE_INVALID: Pipeline '{p.pipeline_id}' has team_id='{p.team_id}' "
                        f"but is registered under team '{team_id}'"
                    )
            comp.status = "INVALID" if comp.errors else "VALID"
        return comp

    def _validate_execution_contracts(self, team_id: str) -> TOSValidationComponent:
        comp = TOSValidationComponent(component="execution_contracts")
        contracts = self._exec_contracts.get_by_team(team_id)
        if not contracts:
            comp.warnings.append(
                f"TOS_EXECUTION_CONTRACT_INVALID: No execution contracts for team '{team_id}'"
            )
            comp.status = "WARNING"
        else:
            for c in contracts:
                if c.team_id != team_id:
                    comp.errors.append(
                        f"TOS_EXECUTION_CONTRACT_INVALID: Contract '{c.contract_id}' "
                        f"has team_id='{c.team_id}', expected '{team_id}'"
                    )
            comp.status = "INVALID" if comp.errors else "VALID"
        return comp

    def _validate_collaboration_contracts(self, team_id: str) -> TOSValidationComponent:
        comp = TOSValidationComponent(component="collaboration_contracts")
        outgoing = self._collab_contracts.get_by_providing_team(team_id)
        incoming = self._collab_contracts.get_by_requesting_team(team_id)
        total = len(outgoing) + len(incoming)

        if total == 0:
            comp.warnings.append(
                f"Team '{team_id}' has no collaboration contracts (outgoing or incoming)."
            )
            comp.status = "WARNING"
        else:
            for c in outgoing:
                if c.providing_team_id != team_id:
                    comp.errors.append(
                        f"TOS_COLLABORATION_CONTRACT_INVALID: Outgoing collaboration "
                        f"'{c.contract_id}' has providing_team_id='{c.providing_team_id}'"
                    )
            for c in incoming:
                if c.requesting_team_id != team_id:
                    comp.errors.append(
                        f"TOS_COLLABORATION_CONTRACT_INVALID: Incoming collaboration "
                        f"'{c.contract_id}' has requesting_team_id='{c.requesting_team_id}'"
                    )
            comp.status = "INVALID" if comp.errors else "VALID"
        return comp

    def _validate_via_team_validator(self, team_id: str) -> TOSValidationComponent:
        """
        Call the existing TeamValidator (TOS 17) for identity/pipeline/member validation.
        Maps its errors and warnings into a TOSValidationComponent.
        Does NOT duplicate validator logic.
        """
        comp = TOSValidationComponent(component="team_validator")
        try:
            result = self._validator.validate_team(team_id)
            for issue in result.errors:
                comp.errors.append(f"{issue.code}: {issue.message}")
            for issue in result.warnings:
                comp.warnings.append(f"{issue.code}: {issue.message}")
            comp.status = "INVALID" if result.errors else (
                "WARNING" if result.warnings else "VALID"
            )
            comp.metadata["checks"] = result.checks
        except Exception as e:
            comp.warnings.append(f"TeamValidator unavailable: {e}")
            comp.status = "WARNING"
        return comp

    # ─────────────────────────────────────────────────────────────────────
    # Private helpers — readiness & misc
    # ─────────────────────────────────────────────────────────────────────

    def _compute_readiness(self, report: TOSTeamValidationReport) -> TOSTeamReadiness:
        """
        Derives TOS 20 readiness from the aggregated validation report.

        Mapping:
            errors exist              → NOT_READY
            only warnings (identity
              valid, non-critical
              cap missing)            → PARTIALLY_READY
            no errors, no warnings    → READY
        """
        if report.total_errors > 0:
            # Check if identity component itself is broken (fundamental)
            identity = next(
                (c for c in report.components if c.component == "identity"), None
            )
            if identity and identity.status == "INVALID":
                return TOSTeamReadiness.NOT_READY
            return TOSTeamReadiness.NOT_READY
        if report.total_warnings > 0:
            return TOSTeamReadiness.PARTIALLY_READY
        return TOSTeamReadiness.READY

    def _get_member_ids(self, team_id: str) -> List[str]:
        """
        Retrieve member IDs for a team from the TeamRegistry.
        Returns empty list if not available — does not crash.
        """
        try:
            members = self._teams.get_members(team_id)
            if members:
                return [
                    getattr(m, "employee_id", getattr(m, "id", str(m)))
                    for m in members
                ]
        except Exception:
            pass
        # Fall back to validator seed data
        try:
            seed_data = self._validator.seed_data
            return [
                m.employee_id
                for m in seed_data.get("members", [])
                if m.team_id == team_id
            ]
        except Exception:
            return []

    def _collaborating_team_ids(self, team_id: str) -> List[str]:
        """All distinct team IDs this team collaborates with (provides to or requests from)."""
        ids = set()
        for c in self._collab_contracts.get_by_providing_team(team_id):
            ids.add(c.requesting_team_id)
        for c in self._collab_contracts.get_by_requesting_team(team_id):
            ids.add(c.providing_team_id)
        return sorted(ids)

    def list_all_team_ids(self) -> List[str]:
        """All team IDs currently registered."""
        return [t.id for t in self._teams.list_teams()]
