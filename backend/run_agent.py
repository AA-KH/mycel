import asyncio
import os
import sys

# Add the backend directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.mongodb import mongodb_connection
from agents.base_agent import BaseAgent
from core.logger import logger

async def main():
    # 1. Connect to MongoDB required for status reporting
    logger.info("Connecting to MongoDB...")
    await mongodb_connection.connect()

    try:
        # 2. Create the Agent
        agent = BaseAgent(
            name="Groq Researcher",
            role="Researcher",
            system_prompt="You are a brilliant researcher. Always provide the best possible output, well structured and deeply analytical."
        )

        logger.info(f"Agent {agent.name} initialized. Session ID: {agent.session_id}")
        
        # 3. Run a test task
        task = "Explain the architecture of a robust multi-agent system with failover mechanisms."
        logger.info(f"Assigning task: {task}")
        
        # This will use the robust Groq Engine with failover
        result = await agent.run_task(task_description=task)
        
        logger.info("Task completed successfully!")
        print("\n=== AGENT OUTPUT ===\n")
        print(result)
        print("\n====================\n")
        
    finally:
        # 4. Clean up
        await mongodb_connection.close()

if __name__ == "__main__":
    asyncio.run(main())
