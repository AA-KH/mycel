import asyncio
from typing import List, Dict, Any

from .team_members.ethan.agent import EthanAgent
from .team_members.priya.agent import PriyaAgent
from .team_members.rohan.agent import RohanAgent
from core.logger import logger

class ArchitectureTeam:
    """
    Orchestrates the Architecture Team (Ethan, Priya, Rohan).
    These agents work in parallel to evaluate or design complex system architectures.
    """
    
    def __init__(self):
        self.ethan = EthanAgent()
        self.priya = PriyaAgent()
        self.rohan = RohanAgent()
        self.members = [self.ethan, self.priya, self.rohan]
        
    async def run_architecture_review(self, task_description: str) -> Dict[str, Any]:
        """
        Executes a parallel architecture review session.
        """
        logger.info("📐 Initiating Architecture Team Analysis...")
        
        # Run all three architects in parallel
        results = await asyncio.gather(
            self.ethan.run_task(task_description),
            self.priya.run_task(task_description),
            self.rohan.run_task(task_description),
            return_exceptions=True
        )
        
        report = {
            "ethan_systems": results[0] if not isinstance(results[0], Exception) else str(results[0]),
            "priya_data": results[1] if not isinstance(results[1], Exception) else str(results[1]),
            "rohan_security": results[2] if not isinstance(results[2], Exception) else str(results[2])
        }
        
        return report

# Singleton
architecture_team = ArchitectureTeam()
