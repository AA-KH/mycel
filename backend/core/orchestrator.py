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
        logger.info(f"🚀 [PHASE 1] Initiating Global Team Analysis for {self.session_id} (Parallel)...")
        
        tasks = []
        agent_names = []
        
        for person in hired_personnel:
            agent_id = person.get("agent_id")
            if not agent_id or agent_id == "architecture_atlas":
                continue # Skip Atlas, he runs in Phase 2
                
            try:
                # agent_id is formatted like "intelligence_ravi"
                parts = agent_id.split("_")
                team_name = parts[0].lower()
                member_name = parts[1].lower()
                class_name = f"{member_name.capitalize()}Agent"
                module_path = f"teams.{team_name}.team_members.{member_name}.agent"
                
                module = importlib.import_module(module_path)
                AgentClass = getattr(module, class_name)
                
                # Instantiate the agent
                agent_instance = AgentClass(session_id=self.session_id)
                agent_name = person.get("name", member_name.capitalize())
                agent_role = person.get("role", "Specialist")
                
                agent_names.append({"name": agent_name, "role": agent_role})
                
                # Create the wrapped async task to include event broadcasting
                tasks.append(self._run_agent_task(agent_instance, agent_name, agent_role, master_prompt))
                
            except Exception as e:
                logger.error(f"Failed to load or execute agent {agent_id}: {e}")
                
        # Execute all Domain Experts in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format the combined reports
        combined_reports_text = ""
        raw_reports = {}
        
        for i, res in enumerate(results):
            agent_meta = agent_names[i]
            name = agent_meta["name"]
            role = agent_meta["role"]
            
            output = res if not isinstance(res, Exception) else f"FAILED: {str(res)}"
            raw_reports[name.lower()] = output
            
            combined_reports_text += f"\n\n{name.upper()} ({role}):\n{output}"
            
        logger.info(f"🚀 [PHASE 2] Atlas synthesizing global reports...")
        
        # If Atlas is in the hired_personnel, or we just force him to run as the final synthesizer
        atlas = AtlasAgent(session_id=self.session_id)
        
        atlas_prompt = f"""
The Global Task Force has completed Phase 1 for: {master_prompt}

Here are the verbatim reports from all Domain Experts:
{combined_reports_text}

Synthesize these reports. Resolve conflicts. Factor in all intelligence, network, resilience, and architectural constraints provided above.
You MUST output your final synthesis as a strict JSON object matching this schema exactly:
```json
{{
  "stages": [
    {{
      "id": "stage-id",
      "label": "Stage Label (e.g. Suppliers)",
      "owner": "Agent Name",
      "question": "Stage question?",
      "nodes": [
        {{
          "id": "node-id",
          "stage": "stage-id",
          "name": "Node Name",
          "share": "100%",
          "risk": "low", 
          "location": "Location",
          "function": "Node function summary",
          "flowLabel": "Flow label",
          "meta": ["meta1", "meta2"],
          "detail": [{{ "label": "Detail label", "value": "Detail value" }}],
          "fallback": "Fallback plan"
        }}
      ]
    }}
  ],
  "decision": {{
    "verdict": "Overall verdict",
    "allocation": "Allocation strategy",
    "reason": "Why this topology",
    "tradeoff": "Cost vs Resilience tradeoff",
    "resilience": "Resilience summary"
  }},
  "rollout": [
    {{ "phase": "Phase 1", "action": "Action", "status": "Ready now" }}
  ]
}}
```
Output ONLY the JSON. No markdown backticks, no commentary.
"""
        
        await event_publisher.publish(self.session_id, "start", {"agent": "Atlas", "task": "Synthesizing executive blueprint from all teams"})
        try:
            atlas_out = await atlas.run_task(atlas_prompt)
        except Exception as e:
            atlas_out = f'{{"error": "Atlas failed: {str(e)}"}}'
        await event_publisher.publish(self.session_id, "finish", {"agent": "Atlas"})
        
        try:
            atlas_json = json.loads(atlas_out)
        except Exception:
            atlas_json = {"error": "Atlas did not return valid JSON", "raw": atlas_out}
            
        # Final combined report
        final_report = {
            "expert_reports": raw_reports,
            "atlas_executive": atlas_json
        }
        
        return final_report

    async def _run_agent_task(self, agent_instance, name, role, prompt):
        await event_publisher.publish(self.session_id, "start", {"agent": name, "task": f"Analyzing {role} constraints"})
        try:
            # Some base agents expect (task_description), some (task) - mostly task_description
            res = await agent_instance.run_task(prompt)
        except Exception as e:
            res = str(e)
        await event_publisher.publish(self.session_id, "finish", {"agent": name})
        return res
