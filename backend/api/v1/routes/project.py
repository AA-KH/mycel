from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime

from api.v1.schemas.project import ProjectPayload
from core.mongodb import mongodb_connection
from core.logger import logger
from teams.architecture.team import architecture_team
from teams.executive.team_members.maya.agent import MayaHRAgent

router = APIRouter()

def construct_master_prompt(payload: ProjectPayload) -> str:
    """
    Converts the UI JSON payload into a natural language prompt for the AI agents.
    """
    prompt = f"Design a highly resilient and scalable supply-chain architecture for a {payload.business_type} business.\n"
    
    prompt += f"Product: {payload.product.name}\n"
    if payload.product.description:
        prompt += f"Description: {payload.product.description}\n"
        
    prompt += "\nOperational Regions:\n"
    prompt += f"- Sourcing/Supply: {payload.regions.supply or 'Unknown'}\n"
    prompt += f"- Manufacturing/Operations: {payload.regions.operations or 'Unknown'}\n"
    prompt += f"- Customers/Distribution: {payload.regions.customers or 'Unknown'}\n"
    
    if payload.priorities:
        prompt += f"\nOptimization Priorities (in order of importance): {', '.join(payload.priorities)}\n"
        
    if payload.existing_knowledge:
        prompt += "\nExisting Constraints & Knowledge:\n"
        if payload.existing_knowledge.suppliers:
            prompt += f"- Suppliers: {', '.join(payload.existing_knowledge.suppliers)}\n"
        if payload.existing_knowledge.hard_constraints:
            prompt += f"- Hard Constraints: {', '.join(payload.existing_knowledge.hard_constraints)}\n"
            
    prompt += "\nPlease provide a full technical and geographical architecture review, including sprint planning, chaos testing, and an executive blueprint."
    return prompt

async def run_agents_in_background(project_id: str, master_prompt: str):
    """
    Runs the HR agent to hire a team, then runs the architecture team analysis.
    """
    try:
        logger.info(f"Starting background HR review for project {project_id}")
        
        # 1. Maya (HR) Phase
        maya = MayaHRAgent(session_id=project_id)
        maya_prompt = f"Review the following project and hire a team:\n\n{master_prompt}"
        maya_response = await maya.run_task(maya_prompt)
        
        # Parse Maya's output to find hired_personnel (assuming she returned JSON)
        import json
        import re
        
        # Default fallback
        hired_personnel = [
            {"agent_id": "architecture_ethan", "name": "Ethan", "role": "Independent Validator", "team": "ARCHITECTURE", "badge": "MYC-020-ETH", "mandate": "Default validation", "status": "GREEN"},
            {"agent_id": "architecture_priya", "name": "Priya", "role": "Implementation Planner", "team": "ARCHITECTURE", "badge": "MYC-019-PRI", "mandate": "Default planning", "status": "GREEN"},
            {"agent_id": "architecture_rohan", "name": "Rohan", "role": "Master Supply-Chain Architect", "team": "ARCHITECTURE", "badge": "MYC-018-ROH", "mandate": "Default routing", "status": "GREEN"},
            {"agent_id": "architecture_atlas", "name": "Atlas", "role": "Executive Orchestrator", "team": "ARCHITECTURE", "badge": "MYC-017-ATL", "mandate": "Default orchestration", "status": "GREEN"}
        ]
        
        hired_agent_ids = ["architecture_ethan", "architecture_priya", "architecture_rohan", "architecture_atlas"]
        
        try:
            # Try to extract the JSON payload she generated via tool
            match = re.search(r'\{.*"hired_personnel":\s*\[.*?\]\}', maya_response, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                hired_personnel = parsed.get("hired_personnel", hired_personnel)
                hired_agent_ids = [p["agent_id"] for p in hired_personnel if "agent_id" in p]
        except Exception as e:
            logger.warning(f"Failed to parse Maya's output for hired personnel, defaulting to core team. Error: {e}")

        logger.info(f"Maya hired the following team: {hired_agent_ids}")

        db = mongodb_connection.client.get_database("mycel")
        # Save hired team to DB immediately so frontend can show them
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"hired_team": hired_personnel}}
        )

        # 2. Architecture Phase
        # Instantiate a dedicated ArchitectureTeam for this project to maintain isolated logs/session_id
        from teams.architecture.team import ArchitectureTeam
        project_architecture_team = ArchitectureTeam(session_id=project_id)
        
        report = await project_architecture_team.run_architecture_review(master_prompt, hired_agent_ids)
        
        # Save final report to MongoDB
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "COMPLETED",
                "architecture_report": report,
                "updated_at": datetime.utcnow()
            }}
        )
        logger.info(f"Successfully completed architecture review for project {project_id}")
    except Exception as e:
        logger.error(f"Failed background architecture review for {project_id}: {str(e)}")
        db = mongodb_connection.client.get_database("mycel")
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "FAILED",
                "error": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

@router.post("/create", status_code=201)
async def create_project(payload: ProjectPayload, background_tasks: BackgroundTasks):
    try:
        db = mongodb_connection.client.get_database("mycel")
        
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        master_prompt = construct_master_prompt(payload)
        
        # 1. Save to MongoDB
        project_data = payload.dict()
        project_data["project_id"] = project_id
        project_data["status"] = "RUNNING"
        project_data["created_at"] = datetime.utcnow()
        project_data["master_prompt"] = master_prompt
        
        await db.projects.insert_one(project_data)
        
        # 2. Trigger Agents in Background
        background_tasks.add_task(run_agents_in_background, project_id, master_prompt)
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": "Project created. Architecture team has been deployed in the background.",
            "websocket_url": "ws://localhost:8000/api/realtime/sessions"
        }
        
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
