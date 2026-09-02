import asyncio
from typing import List, Dict, Any

from .team_members.ethan.agent import EthanAgent
from .team_members.priya.agent import PriyaAgent
from .team_members.rohan.agent import RohanAgent
from .team_members.atlas.agent import AtlasAgent
from core.logger import logger
from core.events import event_publisher

class ArchitectureTeam:
    """
    Orchestrates the Architecture Team.
    Phase 1: Ethan, Priya, and Rohan run in parallel.
    Phase 2: Atlas synthesizes their outputs into a final executive blueprint.
    """
    
    def __init__(self, session_id: str = None):
        self.ethan = EthanAgent(session_id=session_id)
        self.priya = PriyaAgent(session_id=session_id)
        self.rohan = RohanAgent(session_id=session_id)
        self.atlas = AtlasAgent(session_id=session_id)
        self.members = [self.ethan, self.priya, self.rohan, self.atlas]
        
    async def run_architecture_review(self, task_description: str, hired_agent_ids: List[str] = None) -> Dict[str, Any]:
        """
        Executes a parallel architecture review session followed by executive synthesis.
        Only runs agents present in hired_agent_ids if provided.
        """
        logger.info("📐 [PHASE 1] Initiating Architecture Team Analysis (Parallel)...")
        
        run_ethan = hired_agent_ids is None or "architecture_ethan" in hired_agent_ids
        run_priya = hired_agent_ids is None or "architecture_priya" in hired_agent_ids
        run_rohan = hired_agent_ids is None or "architecture_rohan" in hired_agent_ids
        
        tasks = []
        if run_ethan:
            await event_publisher.publish(self.ethan.session_id, "start", {"agent": "Ethan", "task": "Validating operational constraints"})
            tasks.append(self.ethan.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Ethan was not hired for this project."))
        
        if run_priya:
            await event_publisher.publish(self.priya.session_id, "start", {"agent": "Priya", "task": "Planning implementation sprints"})
            tasks.append(self.priya.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Priya was not hired for this project."))
        
        if run_rohan:
            await event_publisher.publish(self.rohan.session_id, "start", {"agent": "Rohan", "task": "Designing supply-chain routing"})
            tasks.append(self.rohan.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Rohan was not hired for this project."))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        if run_ethan: await event_publisher.publish(self.ethan.session_id, "finish", {"agent": "Ethan"})
        if run_priya: await event_publisher.publish(self.priya.session_id, "finish", {"agent": "Priya"})
        if run_rohan: await event_publisher.publish(self.rohan.session_id, "finish", {"agent": "Rohan"})
        
        ethan_out = results[0] if not isinstance(results[0], Exception) else str(results[0])
        priya_out = results[1] if not isinstance(results[1], Exception) else str(results[1])
        rohan_out = results[2] if not isinstance(results[2], Exception) else str(results[2])
        
        logger.info("📐 [PHASE 2] Atlas synthesizing reports...")
        
        atlas_prompt = f"""
The Architecture Team has completed Phase 1 for: {task_description}

Here are the verbatim reports:

ETHAN (Validator / Chaos):
{ethan_out}

PRIYA (Planner / Sprints):
{priya_out}

ROHAN (Supply Chain / Geo):
{rohan_out}

Synthesize these reports. Resolve conflicts. 
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
        
        run_atlas = hired_agent_ids is None or "architecture_atlas" in hired_agent_ids
        if run_atlas:
            await event_publisher.publish(self.atlas.session_id, "start", {"agent": "Atlas", "task": "Synthesizing executive blueprint"})
            try:
                atlas_out = await self.atlas.run_task(atlas_prompt)
            except Exception as e:
                atlas_out = f"Atlas failed: {str(e)}"
            await event_publisher.publish(self.atlas.session_id, "finish", {"agent": "Atlas"})
        else:
            atlas_out = "[SKIPPED] Atlas was not hired for this project."
            
        import json
        try:
            atlas_json = json.loads(atlas_out)
        except Exception:
            atlas_json = {"error": "Atlas did not return valid JSON", "raw": atlas_out}
            
        report = {
            "ethan_systems": ethan_out,
            "priya_data": priya_out,
            "rohan_security": rohan_out,
            "atlas_executive": atlas_json
        }
        
        return report

# Singleton
architecture_team = ArchitectureTeam()
