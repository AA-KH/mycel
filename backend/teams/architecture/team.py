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
    
    def __init__(self):
        self.ethan = EthanAgent()
        self.priya = PriyaAgent()
        self.rohan = RohanAgent()
        self.atlas = AtlasAgent()
        self.members = [self.ethan, self.priya, self.rohan, self.atlas]
        
    async def run_architecture_review(self, task_description: str) -> Dict[str, Any]:
        """
        Executes a parallel architecture review session followed by executive synthesis.
        """
        logger.info("📐 [PHASE 1] Initiating Architecture Team Analysis (Parallel)...")
        
        results = await asyncio.gather(
            self.ethan.run_task(task_description),
            self.priya.run_task(task_description),
            self.rohan.run_task(task_description),
            return_exceptions=True
        )
        
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
