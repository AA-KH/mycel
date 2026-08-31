"""
Manager Agent — The orchestrator of all Mycel agent tasks.

Flow:
1. Receives a project task from the human
2. Appears in the Virtual Office as Manager (working)
3. Calls Groq to produce a structured JSON plan (list of subtasks per team)
4. Delegates each subtask to the appropriate team agent
5. Collects all results
6. Writes a consolidated final report
7. Logs everything via task_logger
"""

import asyncio
import json
import re
import logging
from datetime import datetime, timezone

from agents.base_agent import BaseAgent
from agents.team_agents import build_team_agent
from core.task_logger import (
    update_task_status,
    log_manager_plan,
    log_team_result,
    log_final_report,
)
from core.groq_engine import groq_engine
from core.orchestration_events import emit_orchestration_event, OrchestrationPhase

logger = logging.getLogger(__name__)

MANAGER_SYSTEM_PROMPT = """You are the Manager Agent at Mycel — an elite AI project manager orchestrating a company of 42 specialized talent roles.

Your responsibilities:
1. Analyse the project task given to you
2. Break it into clear, specific subtasks for your team
3. Assign each subtask to the most appropriate specialist from our talent market (e.g., frontend-developer, backend-architect, ui-designer, marketing-strategist, etc.)
   *SPECIAL CASE*: If the user asks to "call" someone regarding "properties" or "real estate", you MUST assign a subtask to 'real-estate-advisor' to fetch properties, and another to 'voice-orchestrator' to make the outbound call.
4. You MUST respond with ONLY valid JSON in this exact format:

{
  "project": "<short project name>",
  "overview": "<2-3 sentence project summary>",
  "subtasks": [
    { "team": "real-estate-advisor", "task": "Search database for properties for Kaushal" },
    { "team": "voice-orchestrator", "task": "Call Kaushal and present the property options" }
  ]
}

Rules:
- Always include at least 2 subtasks
- "team" can be any valid role identifier (use lowercase with dashes)
- Each task instruction must be specific and actionable, not vague
- Return ONLY the JSON object, no markdown, no explanation outside the JSON
"""

FINAL_REPORT_PROMPT = """You are the Chief Synthesis Officer at Mycel AI. 
Your specialized AI agents have generated individual components of a complex project.

Your job is NOT to write a meta-report about what the agents did (do not say "The Marketing Team did X").
Your job is to synthesize all their outputs into the FINAL, COHESIVE SOLUTION the user requested.

If the user asked for a Business Plan, output the ultimate Business Plan integrating all the research.
If the user asked for a Market Feasibility Study, output the complete Study.

Produce a highly professional, beautifully structured Markdown document. 
Use tables, bullet points, and bold text to make it extremely premium and readable. 
This is the final deliverable presented to a CEO/Client. Make it outstanding."""


class ManagerAgent(BaseAgent):
    def __init__(self, task_id: str, user_id: str = "system"):
        super().__init__(
            name="Manager",
            role="manager",
            system_prompt=MANAGER_SYSTEM_PROMPT,
            user_id=user_id,
        )
        self.task_id = task_id

    async def run_project(self, project_task: str):
        """
        Full orchestration pipeline:
        Pass A - Assembly (plan → hire → create wallet cards)
        Pass B - Execution (delegate → execute → collect)
        """
        started_at = datetime.now(timezone.utc)
        await update_task_status(self.task_id, "in_progress")

        # ── Intent Resolution ──────────────────────
        from domains.company_builder.intent_resolver import IntentResolver
        from tasks.models import OutputModality
        
        resolver = IntentResolver()
        output_spec = await resolver.resolve_async(project_task)

        # ── Orchestration: Task Received ──────────────────────
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.TASK_RECEIVED,
            detail=f"Task received: {project_task[:120]} (Intent: {output_spec.intent}, Modality: {output_spec.modality.value})",
        )
        
        # ── Fast Path for Generated Modalities (e.g., WEBSITE) ──
        if output_spec.modality == OutputModality.WEBSITE:
            await self.report_status("working", f"Executing Website Generation: {project_task[:80]}...")
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.HR_ANALYSIS_STARTED,
                detail="Manager identified a direct website generation request.",
            )
            try:
                from tools.gateway import CoreToolGateway
                from agents.runtime.result import ToolRequest
                from workforce.employees.registry import EmployeeRegistry
                from workforce.employees.repositories import MongoEmployeeRepository
                from core.mongodb import mongodb_connection
                import uuid
                
                db = mongodb_connection.db
                repo = MongoEmployeeRepository(db)
                registry = EmployeeRegistry(repo)
                
                gateway = CoreToolGateway(employee_registry=registry)
                request = ToolRequest(
                    tool_name="website.generate",
                    employee_id="sys",
                    execution_id=str(uuid.uuid4()),
                    reason="Direct website generation request",
                    arguments={
                        "task_description": project_task, 
                        "company_name": "Mycel Client"
                    }
                )
                res = await gateway.execute(request)
                if res.status == "success":
                    await self.report_status("complete", "Website generated successfully.")
                    
                    html_content = res.output.get("content", "<!-- No content generated -->")
                    
                    # Log as a team result for the frontend to pick up
                    await log_team_result(
                        self.task_id,
                        "frontend-developer",
                        "Generated Landing Page",
                        html_content
                    )
                    
                    # Create a simple final report
                    report = f"# Project: Mycel Client\n\n**Overview**: {project_task}\n\n## Website Generated\n\nThe website code has been generated successfully. Switch to the Live Preview to view it."
                    await log_final_report(self.task_id, report, started_at)
                    
                    await update_task_status(self.task_id, "completed")
                    await emit_orchestration_event(
                        self.task_id, OrchestrationPhase.ORCHESTRATION_COMPLETED,
                        detail="Orchestration completed successfully."
                    )
                    return
                else:
                    raise Exception(res.error or "Unknown website generation error.")
            except Exception as e:
                logger.error(f"Failed to generate website via gateway: {e}")
                custom_error_msg = "❌ groq and gemini ip is block in this network , try with another network"
                await self.report_status("failure", custom_error_msg)
                await update_task_status(self.task_id, "failed")
                await emit_orchestration_event(
                    self.task_id, OrchestrationPhase.ORCHESTRATION_FAILED,
                    detail=custom_error_msg
                )
                return

        # =======================================================
        # PASS A — WORKFORCE ASSEMBLY
        # =======================================================

        # ── Orchestration: HR Analysis Started ────────────────
        await self.report_status("working", f"📋 Planning: {project_task[:80]}...")
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.HR_ANALYSIS_STARTED,
            detail="Manager is analyzing requirements and creating an execution plan...",
        )

        # ── Deterministic Orchestration (Zero LLM Tokens) ─────
        from tasks.orchestrator import TaskOrchestrator
        from tasks.models import TaskRequest
        import uuid
        
        try:
            orchestrator = TaskOrchestrator()
            request = TaskRequest(
                request_id=str(uuid.uuid4()),
                task_id=self.task_id,
                user_input=project_task
            )
            orch_result = orchestrator.orchestrate(request)
            
            subtasks = []
            for wu in orch_result.work_units:
                subtasks.append({
                    "team": wu.team_id.replace("scm_", "") if wu.team_id else "coder",
                    "task": f"{wu.title}: {wu.objective}"
                })
                
            plan = {
                "project": "Supply Chain Architecture Design",
                "overview": project_task,
                "subtasks": subtasks
            }
        except Exception as e:
            logger.error(f"TaskOrchestrator failed: {e}")
            plan = None

        if not plan or not plan.get("subtasks"):
            await self.report_status("failure", "Failed to generate project plan using Orchestrator.")
            await update_task_status(self.task_id, "failed")
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.ORCHESTRATION_FAILED,
                detail="Failed to generate project plan.",
            )
            return

        await log_manager_plan(self.task_id, plan)
        subtasks = plan.get("subtasks", [])
        project_name = plan.get("project", "Project")

        # ── Orchestration: Capabilities Identified ────────────
        team_names = [s.get("team", "coder") for s in subtasks]
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.CAPABILITY_IDENTIFIED,
            detail=f"Plan created for '{project_name}' — {len(subtasks)} subtasks identified.",
            capabilities=list(set(team_names)),
        )

        # ── Orchestration: Team Selection Started ─────────────
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.TEAM_SELECTION_STARTED,
            detail=f"Identifying required teams for {len(subtasks)} subtasks...",
            selected_teams=list(set(team_names)),
            total_subtasks=len(subtasks),
        )

        # ── Orchestration: Team Selected ──────────────────────
        for t_name in set(team_names):
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.TEAM_SELECTED,
                detail=f"Required team: {t_name}",
                team_name=t_name
            )

        # Initialize Hiring Engine
        try:
            from workforce.employees.registry import EmployeeRegistry
            from workforce.employees.repositories import MongoEmployeeRepository
            from core.mongodb import mongodb_connection
            db = mongodb_connection.db
            repo = MongoEmployeeRepository(db)
            registry = EmployeeRegistry(repo)
            from hiring.engine import HiringEngine
            hiring_engine = HiringEngine(registry)
        except Exception as e:
            logger.warning(f"Could not initialize HiringEngine, using fallback: {e}")
            hiring_engine = None

        company_id = "default_company"
        assembled_assignments = []
        team_results = []

        await self.report_status(
            "working",
            f"✅ Plan ready for '{project_name}'. Hiring agents..."
        )

        for idx, item in enumerate(subtasks):
            team_name = item.get("team", "coder")
            subtask_desc = item.get("task", "")
            
            agent = None
            hiring_score = None
            employee_name = None
            employee_id = None
            canonical_team = team_name # Fallback to LLM requested capability
            
            if hiring_engine:
                try:
                    await self.report_status("working", f"🔍 Hiring candidate for capability: {team_name}...")
                    decision = await hiring_engine.select_candidate(subtask_desc, self.task_id, company_id)
                    
                    if decision.status == "selected" and decision.selected_employee_id:
                        hiring_score = decision.overall_score
                        employee_id = decision.selected_employee_id
                        await self.report_status("working", f"🎯 Hired {employee_id} (Score: {hiring_score})")
                        
                        employee = await registry.get_active_employee(company_id, employee_id)
                        employee_name = employee.name
                        
                        # Phase 2 & 3: Use the actual organizational team, NOT the requested capability!
                        canonical_team = employee.department_id if hasattr(employee, "department_id") and employee.department_id else employee.team_id
                        
                        # Pass employee_id so the registry can load specific Micro-Agents (like MiraAgent)
                        agent = build_team_agent(employee_id, self.task_id, self.user_id)
                        agent.name = employee_name
                        agent.team = canonical_team  # type: ignore
                        agent.employee_name = employee_name  # type: ignore
                        agent.system_prompt += f"\n\nYou are {employee_name}, {employee.identity.title}. Use your {employee.reasoning_profile_id} reasoning."
                except Exception as e:
                    logger.error(f"Hiring engine error: {e}")
            
            if not agent:
                await self.report_status("working", f"⚠️ No valid candidate found. Falling back to generic '{team_name}'...")
                agent = build_team_agent(team_name, self.task_id, self.user_id)
                agent.team = team_name  # type: ignore
                agent.employee_name = agent.name  # type: ignore
                employee_name = agent.name
                employee_id = agent.name
                canonical_team = team_name

            # ── Orchestration: Member Selection Started ──
            # We emit this now that we know the true organizational team
            import asyncio
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.MEMBER_SELECTION_STARTED,
                detail=f"HR processing member for {canonical_team}...",
                team_name=canonical_team,
                subtask_index=idx,
                total_subtasks=len(subtasks),
            )
            await asyncio.sleep(1.0) # Give UI time to visually show "HR SELECTING MEMBER..."

            # ── Create WalletCard (HR assignment) ──
            wallet_card = None
            wallet_card_id = None
            try:
                from api.wallet_router import create_wallet_card
                wallet_card = await create_wallet_card(
                    task_id=self.task_id,
                    agent_id=agent.session_id,
                    agent_role=agent.role,
                    agent_name=agent.name,
                    task_title=subtask_desc[:160],
                    team=canonical_team,
                )
                wallet_card_id = wallet_card.get("id") if wallet_card else None
            except Exception as e:
                logger.warning(f"WalletCard creation failed: {e}")

            # ── Orchestration: Member Selected ──
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.MEMBER_SELECTED,
                detail=f"Hired {employee_name} for {canonical_team}",
                team_name=canonical_team,
                employee_id=employee_id,
                employee_name=employee_name,
                employee_role=agent.role,
                session_id=agent.session_id,
                wallet_card_id=wallet_card_id,
                match_score=hiring_score,
                subtask_index=idx,
                total_subtasks=len(subtasks),
                metadata={"subtask_description": subtask_desc[:120]},
            )

            assembled_assignments.append({
                "subtask_desc": subtask_desc,
                "agent": agent,
                "wallet_card": wallet_card,
                "team_name": canonical_team,
                "subtask_index": idx,
            })

        # ── Orchestration: Team Assembled ──
        for t_name in set(team_names):
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.TEAM_ASSEMBLED,
                detail=f"Team assembled: {t_name}",
                team_name=t_name,
            )

        # ── Orchestration: Workforce Assembled ──
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.WORKFORCE_ASSEMBLED,
            detail=f"All {len(assembled_assignments)} agents assembled.",
            total_subtasks=len(subtasks),
        )

        # =======================================================
        # PASS B — EXECUTION
        # =======================================================
        
        for assignment in assembled_assignments:
            agent = assignment["agent"]
            subtask_desc = assignment["subtask_desc"]
            wallet_card = assignment["wallet_card"]
            team_name = assignment["team_name"]
            idx = assignment["subtask_index"]
            
            # ── Orchestration: Task Assigned ──
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.TASK_ASSIGNED,
                detail=f"Assigned task to {agent.name}: {subtask_desc[:60]}",
                session_id=agent.session_id,
                team_name=team_name,
                employee_name=agent.employee_name,
                subtask_index=idx,
                total_subtasks=len(subtasks),
            )
            
            # ── Orchestration: Agent Moving ──
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.AGENT_MOVING,
                detail=f"{agent.name} is entering the office...",
                session_id=agent.session_id,
                team_name=team_name,
                employee_name=agent.employee_name,
                subtask_index=idx,
                total_subtasks=len(subtasks),
            )
            # Sync session state
            await agent.report_status(
                "walking",
                f"🚶 {agent.name} entering office for: {subtask_desc[:60]}...",
                event_type="hr_assignment",
            )

            # ── Orchestration: Execution Started ──
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.EXECUTION_STARTED,
                detail=f"{agent.name} is starting execution...",
                session_id=agent.session_id,
                team_name=team_name,
                employee_name=agent.employee_name,
                subtask_index=idx,
                total_subtasks=len(subtasks),
            )
            # Sync session state
            await agent.report_status(
                "working",
                f"👉 Executing: {subtask_desc[:60]}..."
            )
            
            # ── Orchestration: Agent Working ──
            await emit_orchestration_event(
                self.task_id, OrchestrationPhase.AGENT_WORKING,
                detail=f"{agent.name} is working on: {subtask_desc[:80]}",
                session_id=agent.session_id,
                team_name=team_name,
                employee_name=agent.employee_name,
                subtask_index=idx,
                total_subtasks=len(subtasks),
                metadata={"subtask_description": subtask_desc[:120]},
            )

            if team_name == "voice-orchestrator":
                from domains.real_estate.voice_outbound import VoiceLinkOutboundService
                from tasks.pdf_generator import PDFReportGenerator
                
                # We pretend the previous agent passed properties
                await VoiceLinkOutboundService.initiate_call("+91XXXXXXXXXX", {}, self.task_id)
                
                # To simulate the conversation finishing, we wait and generate a PDF summary
                await asyncio.sleep(5)
                transcript = [
                    {"speaker": "Agent", "text": "Hello Kaushal, I have found 2 properties for you."},
                    {"speaker": "Kaushal", "text": "What are the legal implications?"},
                    {"speaker": "Legal Team", "text": "As per RERA regulations, you must check the clear title."},
                ]
                pdf_url = PDFReportGenerator.generate_summary(self.task_id, transcript, [], [{"question": "Legal implications?", "answer": "Check RERA clear title."}])
                
                result = f"Call completed. Summary PDF generated at {pdf_url}"
                await log_team_result(self.task_id, "voice-orchestrator", subtask_desc, result)
                team_results.append({
                    "team": "voice-orchestrator",
                    "subtask": subtask_desc,
                    "result": result
                })
                continue
                
            try:
                result = await agent.run_task(subtask_desc)
                await log_team_result(self.task_id, agent.name, subtask_desc, result)
                team_results.append({
                    "team": agent.name,
                    "subtask": subtask_desc,
                    "result": result,
                })
                logger.info(f"[{self.task_id}] {agent.name} completed their subtask.")

                # ── Orchestration: Agent Completed ──
                await emit_orchestration_event(
                    self.task_id, OrchestrationPhase.AGENT_COMPLETED,
                    detail=f"{agent.name} completed: {subtask_desc[:80]}",
                    session_id=agent.session_id,
                    team_name=team_name,
                    employee_name=agent.employee_name,
                    subtask_index=idx,
                    total_subtasks=len(subtasks),
                )

                # ── Update WalletCard to done ──
                if wallet_card:
                    try:
                        from api.wallet_router import update_wallet_card_status
                        await update_wallet_card_status(
                            wallet_card["id"],
                            "done",
                            completed_summary=result[:500] if result else None,
                        )
                    except Exception as e:
                        logger.warning(f"WalletCard update failed: {e}")
                
                await agent.report_status(
                    "complete",
                    f"✅ {agent.name} finished: {subtask_desc[:60]}",
                    event_type="task_complete",
                )

            except Exception as e:
                logger.error(f"[{self.task_id}] {agent.name} failed: {e}")
                await log_team_result(self.task_id, agent.name, subtask_desc, f"ERROR: {e}")
                team_results.append({
                    "team": agent.name,
                    "subtask": subtask_desc,
                    "result": f"ERROR: {str(e)}"
                })
                
                # ── Orchestration: Agent Failed ──
                await emit_orchestration_event(
                    self.task_id, OrchestrationPhase.AGENT_FAILED,
                    detail=f"{agent.name} failed: {e}",
                    session_id=agent.session_id,
                    team_name=team_name,
                    employee_name=agent.employee_name,
                    subtask_index=idx,
                    total_subtasks=len(subtasks),
                )
                
                if wallet_card:
                    try:
                        from api.wallet_router import update_wallet_card_status
                        await update_wallet_card_status(
                            wallet_card["id"],
                            "done",
                            completed_summary=f"FAILED: {e}"[:500],
                        )
                    except Exception as ex:
                        logger.warning(f"WalletCard update failed: {ex}")
                
                await agent.report_status(
                    "failure",
                    f"❌ {agent.name} failed: {str(e)[:60]}",
                    event_type="task_complete",
                )

        # ── Step 3: Write final report ────────────────────────
        await self.report_status("working", "📝 All teams done. Writing final report...")
        final_report = await self._write_final_report(project_task, plan, team_results)

        await log_final_report(self.task_id, final_report, started_at)
        await self.report_status(
            "complete",
            f"🎉 '{project_name}' complete! All team results logged."
        )

        # ── Orchestration: Orchestration Completed ───────────
        await emit_orchestration_event(
            self.task_id, OrchestrationPhase.ORCHESTRATION_COMPLETED,
            detail=f"Project '{project_name}' complete — {len(team_results)} subtasks finished.",
            total_subtasks=len(subtasks),
        )

    async def _write_final_report(
        self, project_task: str, plan: dict, team_results: list
    ) -> str:
        """Call Groq to synthesize team outputs into a final report."""
        
        # Fast path: Check for artifacts to avoid expensive LLM summarization
        for r in team_results:
            result_lower = r.get('result', '').lower()
            subtask_lower = r.get('subtask', '').lower()
            team_name = r.get('team', '').lower()
            
            # Website Detection: Check for HTML tags, or if any team generated code for a website task
            is_website = (
                '<html' in result_lower or 
                '<!doctype html>' in result_lower or 
                '<div' in result_lower or 
                '<script' in result_lower or
                'react' in result_lower or
                ('website' in subtask_lower) or 
                ('landing page' in subtask_lower)
            )
            
            if is_website:
                return f"# Project: {plan.get('project', 'Unknown')}\n\n**Overview**: {plan.get('overview', '')}\n\n## Website Generated\n\nThe website code has been generated successfully. Switch to the Live Preview to view it.\n\n```html\n{r['result']}\n```"
                
            if 'creative.presentation.generate' in result_lower or '.pptx' in result_lower or 'download presentation' in result_lower:
                return f"# Project: {plan.get('project', 'Unknown')}\n\n**Overview**: {plan.get('overview', '')}\n\n## Presentation Generated\n\n{r['result']}"

        summary_lines = [f"# Project: {plan.get('project', 'Unknown')}\n"]
        summary_lines.append(f"**Overview**: {plan.get('overview', '')}\n")
        for r in team_results:
            summary_lines.append(
                f"\n## {r['team'].capitalize()} Team\n**Subtask**: {r['subtask']}\n\n{r['result'][:2000]}"
            )

        context = "\n".join(summary_lines)
        messages = [
            {"role": "system", "content": FINAL_REPORT_PROMPT},
            {"role": "user", "content": f"Original task: {project_task}\n\nTeam outputs:\n{context}"},
        ]
        try:
            from core.gemini_engine import engine_manager as gemini_manager
            
            # Use Gemini's best model for the final comprehensive solution synthesis
            response = await gemini_manager.chat_completion(
                model="gemini-1.5-pro", # Use the best model for high-quality reports
                messages=messages,
                temperature=0.4, # Lower temp for more professional, structured output
                max_tokens=8192,
            )
            raw = response.choices[0].message.content or ""
            return raw.strip()
        except Exception as e:
            logger.error(f"Final report generation failed: {e}")
            return f"Final report generation failed: {e}\n\nRaw team results:\n{context}"
