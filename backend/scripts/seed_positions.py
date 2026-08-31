"""
Seed script for positions from team definitions.
Loads position definitions from teams/ directories and seeds them into the database.
"""

import asyncio
import os
import sys
import importlib.util
from pathlib import Path

# Ensure backend directory is in PYTHONPATH for direct execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.mongodb import mongodb_connection
from workforce.positions.models import Position, PositionStatus
from workforce.positions.repository import PositionRepository
from workforce.positions.validator import PositionValidator

async def seed_positions():
    print("Connecting to MongoDB...")
    await mongodb_connection.connect()
    
    try:
        db = mongodb_connection.db
        position_repo = PositionRepository(db)
        validator = PositionValidator()
        
        # Create indexes
        await db.positions.create_index("position_id", unique=True)
        await db.positions.create_index("team_id")
        
        # Load positions from team directories
        base_dir = Path(__file__).parent.parent / "teams"
        
        for team_dir in base_dir.iterdir():
            if not team_dir.is_dir():
                continue
                
            positions_dir = team_dir / "positions"
            if not positions_dir.exists():
                continue
                
            print(f"Loading positions from team: {team_dir.name}")
            
            for position_file in positions_dir.glob("*.py"):
                if position_file.name == "__init__.py":
                    continue
                    
                try:
                    # Load the position module
                    mod_path = f"teams.{team_dir.name}.positions.{position_file.stem}"
                    spec = importlib.util.spec_from_file_location(mod_path, str(position_file))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    
                    # Find position instances in the module
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, Position):
                            position = attr
                            
                            # Check if position already exists
                            existing = await position_repo.get_by_position_id(position.position_id, position.version)
                            
                            if existing:
                                print(f"  Position already exists: {position.position_id}")
                            else:
                                # Validate and create position
                                await validator.validate_position(position)
                                created = await position_repo.create(position)
                                print(f"  Created position: {position.position_id} - {position.display_name}")
                                
                except Exception as e:
                    print(f"  Error loading position from {position_file.name}: {e}")
                    
        print("Position seeding complete.")
        
    finally:
        await mongodb_connection.close()

if __name__ == "__main__":
    asyncio.run(seed_positions())
