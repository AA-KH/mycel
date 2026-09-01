import asyncio
from typing import List, Dict, Any

from .team_members.ethan.agent import EthanAgent
from .team_members.priya.agent import PriyaAgent
from .team_members.rohan.agent import RohanAgent
from .team_members.atlas.agent import AtlasAgent
from core.logger import logger

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
        if run_ethan: tasks.append(self.ethan.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Ethan was not hired for this project."))
        
        if run_priya: tasks.append(self.priya.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Priya was not hired for this project."))
        
        if run_rohan: tasks.append(self.rohan.run_task(task_description))
        else: tasks.append(asyncio.sleep(0, result="[SKIPPED] Rohan was not hired for this project."))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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

Synthesize these reports. Resolve conflicts. Use your tools to calculate the final health score and compile the executive blueprint.
"""
        
        try:
            atlas_out = await self.atlas.run_task(atlas_prompt)
        except Exception as e:
            atlas_out = f"Atlas failed: {str(e)}"
            
        report = {
            "ethan_systems": ethan_out,
            "priya_data": priya_out,
            "rohan_security": rohan_out,
            "atlas_executive": atlas_out
        }
        
        return report

# Singleton
architecture_team = ArchitectureTeam()
