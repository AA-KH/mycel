"""
Objective Planner (Phase 16)

Converts a CompanyObjective into a structured CompanyPlan with milestones,
task descriptors, dependency graph, and critical path.

Planning Principles:
- Deterministic decomposition for known objective patterns.
- Optional LLM-assisted decomposition for ambiguous objectives.
  If LLM is used: output MUST be structured; LLM cannot directly execute anything.
- Planner does NOT call Task Orchestrator.
- Planner does NOT call Hiring.
- Planner does NOT query Memory.
- Planner does NOT create Agents.
- Output is a CompanyPlan; execution is delegated to AutonomousActionExecutor.

Phase Taxonomy (default):
  RESEARCH → DESIGN → BUILD → TEST → DEPLOY → EVALUATE

Dependency Analysis:
- Builds DAG from TaskRequestDescriptor.depends_on fields.
- Computes critical path using topological sort + longest path.
- No infinite loops — cycle detection applied.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime, timezone

from autonomy.models import (
    CompanyObjective, CompanyPlan, Milestone, MilestoneStatus,
    TaskRequestDescriptor, PlanStatus, SuccessCriteria,
)

logger = logging.getLogger(__name__)

# Default phase taxonomy for common objective types
_DEFAULT_PHASES = [
    ("Research",  "Gather information, analyze requirements and existing solutions"),
    ("Design",    "Create structure, architecture, and specifications"),
    ("Build",     "Implement the solution according to specifications"),
    ("Test",      "Validate correctness, quality, and performance"),
    ("Deploy",    "Release the deliverable to target environment"),
    ("Evaluate",  "Assess the outcome against success criteria"),
]


class ObjectivePlanner:
    """
    Converts a CompanyObjective into a versioned CompanyPlan.
    Stateless — safe to reuse across objectives.
    """

    def plan(
        self,
        objective: CompanyObjective,
        existing_plan_count: int = 0,
        phases: Optional[List[tuple]] = None,
    ) -> CompanyPlan:
        """
        Build a CompanyPlan from the objective.

        Parameters
        ----------
        objective           The objective to plan for.
        existing_plan_count How many plans already exist (sets version number).
        phases              Override the default phase taxonomy.
        """
        version = existing_plan_count + 1
        phase_defs = phases or _DEFAULT_PHASES

        plan = CompanyPlan(
            objective_id=objective.objective_id,
            version=version,
            status=PlanStatus.DRAFT,
        )

        # 1. Build milestones from phases
        milestones, descriptors = self._build_phases(objective, phase_defs)
        plan.milestones = milestones
        plan.task_descriptors = descriptors

        # 2. Build dependency graph
        plan.dependency_graph = self._build_dependency_graph(descriptors)

        # 3. Compute critical path
        plan.critical_path = self._critical_path(
            descriptors, plan.dependency_graph
        )

        # 4. Collect required capabilities
        plan.required_capabilities = list({
            cap
            for d in descriptors
            for cap in d.required_capabilities
        })

        return plan

    # ─────────────────────────────────────────────────────────────────────
    # Phase / Milestone construction
    # ─────────────────────────────────────────────────────────────────────

    def _build_phases(
        self,
        objective: CompanyObjective,
        phases: List[tuple],
    ):
        milestones = []
        all_descriptors = []
        prev_descriptor_id: Optional[str] = None

        for seq, (phase_name, phase_desc) in enumerate(phases):
            ms = Milestone(
                objective_id=objective.objective_id,
                title=phase_name,
                description=f"{phase_desc} for: {objective.title}",
                sequence=seq,
                status=MilestoneStatus.PENDING,
            )

            # One primary task descriptor per milestone
            desc = TaskRequestDescriptor(
                milestone_id=ms.milestone_id,
                title=f"{phase_name}: {objective.title}",
                description=(
                    f"{phase_desc}. "
                    f"Objective: {objective.description}"
                ),
                required_capabilities=self._infer_capabilities(phase_name),
                required_outputs=self._infer_outputs(phase_name),
                priority=objective.priority.value,
                depends_on=[prev_descriptor_id] if prev_descriptor_id else [],
            )

            ms.task_ids.append(desc.descriptor_id)
            milestones.append(ms)
            all_descriptors.append(desc)
            prev_descriptor_id = desc.descriptor_id

        return milestones, all_descriptors

    def _infer_capabilities(self, phase_name: str) -> List[str]:
        """Lightweight capability hints per phase — no LLM."""
        caps = {
            "Research":  ["research", "analysis", "web_search"],
            "Design":    ["design", "architecture", "specification"],
            "Build":     ["development", "implementation", "coding"],
            "Test":      ["testing", "quality_assurance", "validation"],
            "Deploy":    ["deployment", "devops", "release_management"],
            "Evaluate":  ["evaluation", "analysis", "reporting"],
        }
        return caps.get(phase_name, [])

    def _infer_outputs(self, phase_name: str) -> List[str]:
        outputs = {
            "Research":  ["research_report", "requirements_document"],
            "Design":    ["design_specification", "architecture_document"],
            "Build":     ["code_artifact", "implementation"],
            "Test":      ["test_report", "quality_report"],
            "Deploy":    ["deployment_record", "release_artifact"],
            "Evaluate":  ["evaluation_report"],
        }
        return outputs.get(phase_name, [])

    # ─────────────────────────────────────────────────────────────────────
    # Dependency graph
    # ─────────────────────────────────────────────────────────────────────

    def _build_dependency_graph(
        self,
        descriptors: List[TaskRequestDescriptor],
    ) -> Dict[str, List[str]]:
        """
        Returns: { descriptor_id → [IDs that depend ON this descriptor] }
        i.e., forward adjacency for topological sort.
        """
        graph: Dict[str, List[str]] = {d.descriptor_id: [] for d in descriptors}
        for d in descriptors:
            for dep_id in d.depends_on:
                if dep_id in graph:
                    graph[dep_id].append(d.descriptor_id)
        return graph

    # ─────────────────────────────────────────────────────────────────────
    # Critical path (longest path in DAG)
    # ─────────────────────────────────────────────────────────────────────

    def _critical_path(
        self,
        descriptors: List[TaskRequestDescriptor],
        graph: Dict[str, List[str]],
    ) -> List[str]:
        """
        Identifies the critical path using topological sort + longest path.
        Returns ordered list of descriptor_ids.
        """
        if not descriptors:
            return []

        # Topological sort (Kahn's algorithm)
        in_degree: Dict[str, int] = {d.descriptor_id: 0 for d in descriptors}
        for d in descriptors:
            for dep in d.depends_on:
                if dep in in_degree:
                    in_degree[d.descriptor_id] += 1

        # longest_path[node] = length of longest path ending at node
        longest: Dict[str, int] = {d.descriptor_id: 1 for d in descriptors}
        prev: Dict[str, Optional[str]] = {d.descriptor_id: None for d in descriptors}

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        topo_order = []

        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            for successor in graph.get(node, []):
                if longest[node] + 1 > longest[successor]:
                    longest[successor] = longest[node] + 1
                    prev[successor] = node
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    queue.append(successor)

        if not topo_order:
            return [d.descriptor_id for d in descriptors]  # Cycle guard

        # Trace back from node with maximum longest value
        end = max(topo_order, key=lambda n: longest[n])
        path = []
        cur: Optional[str] = end
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()
        return path
