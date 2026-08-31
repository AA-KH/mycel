"""
Seed script for knowledge spaces from team definitions.
Loads knowledge definitions from teams/ directories and seeds them into the database.
"""

import asyncio
import os
import sys
import importlib.util
from pathlib import Path

# Ensure backend directory is in PYTHONPATH for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mongodb import mongodb_connection
from knowledge.repository import KnowledgeRepository
from knowledge.models import KnowledgeSpace, KnowledgeStatus

async def seed_knowledge():
    print("Connecting to MongoDB...")
    await mongodb_connection.connect()
    
    try:
        db = mongodb_connection.db
        knowledge_repo = KnowledgeRepository(db)
        
        # Create indexes
        await db.knowledge_spaces.create_index("knowledge_space_id", unique=True)
        await db.knowledge_spaces.create_index("domain")
        
        # Load knowledge from team directories
        base_dir = Path(__file__).parent.parent / "teams"
        
        for team_dir in base_dir.iterdir():
            if not team_dir.is_dir():
                continue
                
            knowledge_dir = team_dir / "common" / "knowledge"
            if not knowledge_dir.exists():
                continue
                
            print(f"Loading knowledge from team: {team_dir.name}")
            
            # Load from individual knowledge files
            individual_dir = knowledge_dir / "individual"
            if individual_dir.exists():
                for knowledge_file in individual_dir.glob("*.py"):
                    if knowledge_file.name == "__init__.py":
                        continue
                        
                    try:
                        # Load the knowledge module
                        mod_path = f"teams.{team_dir.name}.common.knowledge.individual.{knowledge_file.stem}"
                        spec = importlib.util.spec_from_file_location(mod_path, str(knowledge_file))
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        
                        # Find knowledge instances in the module
                        for attr_name in dir(mod):
                            attr = getattr(mod, attr_name)
                            if isinstance(attr, dict) and "knowledge_space_id" in attr:
                                knowledge_data = attr
                                
                                # Check if knowledge already exists
                                existing = await knowledge_repo.get_by_knowledge_space_id(knowledge_data["knowledge_space_id"])
                                
                                if existing:
                                    print(f"  Knowledge already exists: {knowledge_data['knowledge_space_id']}")
                                else:
                                    # Create knowledge space
                                    knowledge_space = KnowledgeSpace(
                                        knowledge_space_id=knowledge_data["knowledge_space_id"],
                                        name=knowledge_data["name"],
                                        display_name=knowledge_data["display_name"],
                                        description=knowledge_data["description"],
                                        domain=knowledge_data["domain"],
                                        category=knowledge_data["category"],
                                        status=KnowledgeStatus.ACTIVE
                                    )
                                    created = await knowledge_repo.create(knowledge_space)
                                    print(f"  Created knowledge: {knowledge_data['knowledge_space_id']} - {knowledge_data['display_name']}")
                                    
                    except Exception as e:
                        print(f"  Error loading knowledge from {knowledge_file.name}: {e}")
                        
        print("Knowledge seeding complete.")
        
    finally:
        await mongodb_connection.close()

if __name__ == "__main__":
    asyncio.run(seed_knowledge())
