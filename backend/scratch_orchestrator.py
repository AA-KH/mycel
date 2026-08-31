import sys
import os

# Add the current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO)

from tasks.orchestrator import TaskOrchestrator
from tasks.analyzer import TaskAnalyzer
from tasks.resolver import CapabilityRequirementResolver, TeamResolver
from tasks.decomposer import TaskDecomposer
from tasks.planner import TaskPlanner
from tasks.validator import TaskPlanValidator
from tasks.models import TaskRequest, TaskContext, TaskConstraints
from teams.registry import TeamRegistry
from execution.pipelines.registry import PipelineRegistry
from execution.contracts.registry import ExecutionContractRegistry
from execution.collaboration.registry import TeamCollaborationContractRegistry
from teams.resolver import TeamCapabilityResolver

def main():
    print("--- 1. TASK ANALYSIS & NORMALIZATION ---")
    analyzer = TaskAnalyzer()
    
    prompt = "Build a scalable healthcare AI startup for diagnosing X-rays"
    request = TaskRequest(
        request_id="test_1",
        task_id="test_task_1",
        user_input=prompt,
        context=TaskContext(),
        constraints=TaskConstraints()
    )
    
    normalized = analyzer.normalize_request(prompt)
    print(f"Normalized Prompt: {normalized}\n")
    
    outcome, clarifications = analyzer.analyze_task(request)
    print("Outcome (Goes to Output Resolver):")
    print(outcome.model_dump_json(indent=2))
    
    print("\n--- 2. CAPABILITY RESOLUTION ---")
    cap_resolver = CapabilityRequirementResolver()
    cap_reqs = cap_resolver.resolve_requirements(outcome)
    print("Capabilities Required (Goes to Decomposer/Team Resolver):")
    for req in cap_reqs:
        print(f" - {req}")
        
    print("\n--- 3. TASK DECOMPOSITION ---")
    decomposer = TaskDecomposer()
    work_units = decomposer.decompose("test_task_1", outcome)
    print("Work Units (Goes to Planner):")
    for wu in work_units:
        print(f" - ID: {wu.unit_id} | Objective: {wu.objective}")
        print(f"   Required Capabilities: {wu.required_capabilities}")
        
    print("\n--- 4 & 5. PLANNING & VALIDATION ---")
    try:
        team_reg = TeamRegistry()
        pipe_reg = PipelineRegistry()
        exec_contracts = ExecutionContractRegistry()
        collab_contracts = TeamCollaborationContractRegistry()
        
        team_cap_resolver = TeamCapabilityResolver(team_reg, pipe_reg)
        team_resolver = TeamResolver(team_cap_resolver, exec_contracts, pipe_reg)
        
        validator = TaskPlanValidator(team_reg, pipe_reg, exec_contracts, collab_contracts)
        planner = TaskPlanner(team_resolver, validator)
        
        from tasks.models import Task, TaskStatus
        task = Task(
            task_id="test_task_1",
            organization_id="test",
            title=outcome.objective,
            description=outcome.intent,
            original_request=prompt,
            normalized_request=normalized,
            status=TaskStatus.ANALYZING,
            requested_outputs=outcome.required_outputs
        )
        
        plan = planner.build_plan(task, outcome, work_units, version=1)
        print("\nTask Plan Built:")
        print(plan.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error building plan: {e}")

if __name__ == "__main__":
    main()
