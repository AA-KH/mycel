from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
from datetime import datetime

from api.v1.schemas.project import ProjectPayload
from core.mongodb import mongodb_connection
from core.logger import logger
from teams.architecture.team import architecture_team

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
    Runs the architecture team analysis in the background and updates the database with the final report.
    """
    try:
        logger.info(f"Starting background architecture review for project {project_id}")
        report = await architecture_team.run_architecture_review(master_prompt)
        
        # Save final report to MongoDB
        db = mongodb_connection.client.get_database("mycel")
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
