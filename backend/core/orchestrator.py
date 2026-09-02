import asyncio
import importlib
import json
from typing import List, Dict, Any
from core.logger import logger
from core.events import event_publisher
from teams.architecture.team_members.atlas.agent import AtlasAgent

class MasterOrchestrator:
    """
    Dynamically executes any hired agents across all teams in parallel,
    then feeds their output into the Master Orchestrator (Atlas) for synthesis.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id

    async def run_project_analysis(self, master_prompt: str, hired_personnel: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"🚀 [GLOBAL ORCHESTRATOR] Initiating 4-Phase Execution Pipeline for {self.session_id}")
        
        # Categorize agents into phases
        phase1_agents = [] # Research (Intelligence, Council, Network)
        phase2_agents = [] # Drafting (Architecture planners)
        phase3_agents = [] # Validation (Resilience, Chaos)
        atlas_person = None # Synthesis
        
        for person in hired_personnel:
            agent_id = person.get("agent_id", "")
            team = person.get("team", "").upper()
            name = person.get("name", "")
            
            if agent_id == "architecture_atlas":
                atlas_person = person
            elif team in ["INTELLIGENCE", "COUNCIL", "NETWORK"]:
                phase1_agents.append(person)
            elif team == "RESILIENCE" or name.lower() == "ethan":
                phase3_agents.append(person)
            else:
                # Default to Phase 2 (Architecture planners)
                phase2_agents.append(person)
                
        # To accumulate contextual history for the next phase
        accumulated_context = f"INITIAL PROJECT PROMPT:\n{master_prompt}\n"
        raw_reports = {}
        
        def truncate_report(report: str, max_chars=800) -> str:
            if not isinstance(report, str):
                report = str(report)
            if len(report) > max_chars:
                return report[:max_chars] + "...[TRUNCATED to save context]"
            return report
        
        # --- PHASE 1: Research & Discovery ---
        if phase1_agents:
            logger.info("🟢 [PHASE 1] Running Research & Discovery (Intelligence, Council, Network)...")
            p1_results = await self._run_phase(phase1_agents, accumulated_context)
            accumulated_context += "\n--- PHASE 1 (RESEARCH) REPORTS ---\n"
            for name, report in p1_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] REPORT:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 2: Drafting ---
        if phase2_agents:
            logger.info("🟡 [PHASE 2] Running Architecture Drafting (Planners)...")
            p2_prompt = accumulated_context + "\nBased on the above intelligence and requirements, draft the optimal supply chain architecture."
            p2_results = await self._run_phase(phase2_agents, p2_prompt)
            accumulated_context += "\n--- PHASE 2 (DRAFTING) REPORTS ---\n"
            for name, report in p2_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] DRAFT:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 3: Validation & Red-Teaming ---
        if phase3_agents:
            logger.info("🔴 [PHASE 3] Running Validation & Resilience (Chaos, Stress Testers)...")
            p3_prompt = accumulated_context + "\nCritique, attack, and validate the drafted architecture above. Identify single points of failure."
            p3_results = await self._run_phase(phase3_agents, p3_prompt)
            accumulated_context += "\n--- PHASE 3 (VALIDATION) REPORTS ---\n"
            for name, report in p3_results.items():
                condensed = truncate_report(report)
                accumulated_context += f"[{name.upper()}] CRITIQUE:\n{condensed}\n\n"
                raw_reports[name.lower()] = report
                
        # --- PHASE 4: Master Synthesis (Atlas) ---
        logger.info("🔵 [PHASE 4] Atlas synthesizing global reports...")
        
        atlas_prompt = f"""
The Global Task Force has completed its multi-phase analysis. Here is the entire contextual history:
{accumulated_context}

Synthesize these reports. Resolve conflicts. You MUST factor in ALL Intelligence, Network, Resilience, and Architectural constraints provided above.
You MUST output your final synthesis as a strict JSON object matching this schema exactly:

CRITICAL RULES:
1. Every node's "stage" field MUST exactly equal the "id" of its parent stage.
2. Every node "id" must be unique across ALL stages (e.g., "sup-a", "mfg-main", "wh-central").
3. "risk" must be one of: "low", "medium", or "high" — nothing else.
4. Include as many real nodes per stage as the analysis warrants (1 to 6 per stage). Be dynamic.
5. Output ONLY the raw JSON — no markdown fences, no commentary.

EXAMPLE of correct structure (yours must follow this exact shape with real data):
{{
  "stages": [
    {{
      "id": "suppliers",
      "label": "Tier-1 Suppliers",
      "owner": "Rohan",
      "question": "Who feeds the network?",
      "nodes": [
        {{
          "id": "sup-a",
          "stage": "suppliers",
          "name": "Supplier A",
          "share": "60%",
          "risk": "medium",
          "location": "Germany",
          "function": "Primary source — lowest landed cost, carries the base volume.",
          "flowLabel": "60% · 21d",
          "meta": ["Primary — lowest landed cost", "Lead time 21 days"],
          "detail": [{{"label": "Allocation", "value": "60% of annual volume"}}],
          "fallback": "Supplier B absorbs 40% on outage > 72h."
        }}
      ]
    }},
    {{
      "id": "manufacturing",
      "label": "Manufacturing",
      "owner": "Kabir",
      "question": "Where is value added?",
      "nodes": [
        {{
          "id": "mfg-main",
          "stage": "manufacturing",
          "name": "Primary Plant",
          "share": null,
          "risk": "high",
          "location": "India · West",
          "function": "Core production hub, capacity 140k units/yr.",
          "flowLabel": "140k units/yr",
          "meta": ["Capacity 140k units/yr", "ISO 9001 certified"],
          "detail": [{{"label": "Capacity", "value": "140k units/yr"}}],
          "fallback": "Shift 30% to contract manufacturer within 2 weeks."
        }}
      ]
    }}
  ],
  "decision": {{
    "verdict": "APPROVED — resilient dual-source network",
    "allocation": "Supplier A 60% · Supplier B 25% · Supplier C 15%",
    "reason": "Dual-source mitigates single-country dependency",
    "tradeoff": "Slightly higher cost vs single-source, offset by resilience",
    "resilience": "All critical nodes have documented fallback paths"
  }},
  "rollout": [
    {{"phase": "Phase 1", "action": "Qualify Supplier B to 25% share", "status": "Ready now"}},
    {{"phase": "Phase 2", "action": "Commission Regional Buffer warehouse", "status": "Q2 2025"}}
  ]
}}

Now generate the REAL output based on the actual analysis above. Use real supplier names, locations, percentages, and specifics from the expert reports — not placeholder text.
"""
        
        await event_publisher.publish(self.session_id, "start", {"agent": "Atlas", "task": "Synthesizing executive blueprint from all teams"})
        
        # Bypass Agent loop to avoid tool hallucination and enforce JSON output
        from core.gemini_engine import engine_manager as gemini_manager
        try:
            # We use Gemini for JSON mode to save tokens and avoid 413
            response = await gemini_manager.chat_completion(
                model="gemini-flash-latest", 
                messages=[
                    {"role": "system", "content": "You are Atlas, the Master Orchestrator. Output ONLY valid JSON."},
                    {"role": "user", "content": atlas_prompt}
                ]
            )
            atlas_out = response.choices[0].message.content
            
            # Strip markdown and text to ensure valid JSON extraction
            atlas_out = atlas_out.strip()
            if "```json" in atlas_out:
                atlas_out = atlas_out.split("```json")[1].split("```")[0].strip()
            elif "```" in atlas_out:
                atlas_out = atlas_out.split("```")[1].split("```")[0].strip()
            
            # Ultimate fallback to just grabbing everything between first { and last }
            if atlas_out.find("{") != -1 and atlas_out.rfind("}") != -1:
                atlas_out = atlas_out[atlas_out.find("{"):atlas_out.rfind("}")+1]
                
        except Exception as e:
            logger.error(f"Atlas LLM synthesis failed: {str(e)}")
            atlas_out = f'{{"error": "Atlas LLM synthesis failed: {str(e)}"}}'
            
        await event_publisher.publish(self.session_id, "finish", {"agent": "Atlas"})
        
        try:
            atlas_json = json.loads(atlas_out)
        except Exception:
            atlas_json = {"error": "Atlas did not return valid JSON", "raw": atlas_out}
            
        final_report = {
            "expert_reports": raw_reports,
            "atlas_executive": atlas_json
        }
        
        return final_report

    async def _run_phase(self, personnel: List[Dict[str, Any]], phase_prompt: str) -> Dict[str, str]:
        tasks = []
        agent_names = []
        
        for person in personnel:
            agent_id = person.get("agent_id")
            try:
                parts = agent_id.split("_")
                team_name = parts[0].lower()
                member_name = parts[1].lower()
                class_name = f"{member_name.capitalize()}Agent"
                module_path = f"teams.{team_name}.team_members.{member_name}.agent"
                
                module = importlib.import_module(module_path)
                AgentClass = getattr(module, class_name)
                
                agent_instance = AgentClass(session_id=self.session_id)
                agent_name = person.get("name", member_name.capitalize())
                agent_role = person.get("role", "Specialist")
                
                agent_names.append({"name": agent_name, "role": agent_role})
                tasks.append(self._run_agent_task(agent_instance, agent_name, agent_role, phase_prompt))
                
            except Exception as e:
                logger.error(f"Failed to load agent {agent_id}: {e}")
                
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        phase_reports = {}
        for i, res in enumerate(results):
            name = agent_names[i]["name"]
            phase_reports[name] = res if not isinstance(res, Exception) else f"FAILED: {str(res)}"
            
        return phase_reports

    async def _run_agent_task(self, agent_instance, name, role, prompt):
        await event_publisher.publish(self.session_id, "start", {"agent": name, "task": f"Analyzing {role} constraints"})
        try:
            # Some base agents expect (task_description), some (task) - mostly task_description
            res = await agent_instance.run_task(prompt)
        except Exception as e:
            res = str(e)
        await event_publisher.publish(self.session_id, "finish", {"agent": name})
        return res
