from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime

from core.mongodb import mongodb_connection
from core.logger import logger
from core.events import event_publisher

router = APIRouter()

class AlertPayload(BaseModel):
    alert_id: str
    severity: str
    title: str
    description: str
    affected_entities: Optional[List[str]] = []
    project_id: Optional[str] = None # Added for demo to target a specific project if needed

class TariffAlertPayload(BaseModel):
    imposingCountry: str
    imposingCountryName: str
    targetCountry: str
    targetCountryName: str
    sector: str
    previousRatePercent: Optional[float] = None
    newRatePercent: float
    delta: float
    unit: str
    effectiveDate: Optional[str] = None
    legalBasis: Optional[str] = None
    notes: Optional[str] = None
    project_id: Optional[str] = None

async def run_crisis_rearchitecture_in_background(project_id: str, alert: AlertPayload):
    from core.orchestrator import MasterOrchestrator
    try:
        logger.info(f"Starting CRISIS re-architecture for project {project_id}")
        
        # We need the existing project to get the original prompt
        db = mongodb_connection.db
        project = await db.projects.find_one({"project_id": project_id})
        
        if not project:
            logger.error(f"Project {project_id} not found for crisis rearchitecture.")
            return
            
        original_prompt = project.get("master_prompt", "")
        
        crisis_prompt = f"""
CRITICAL CRISIS ALERT RECEIVED:
Title: {alert.title}
Severity: {alert.severity}
Description: {alert.description}

You must COMPLETELY REDESIGN the architecture to avoid this risk. 
Your new architecture must mitigate the impact of this crisis.
Furthermore, Helena MUST calculate the estimated PROFIT LOSS caused by this crisis.

CRITICAL INSTRUCTION FOR ATLAS:
In your final JSON output, you MUST include a new block called `crisis_impact` at the same level as `stages` and `rollout`.
The `crisis_impact` block MUST have this exact schema:
"crisis_impact": {{
    "profit_loss_estimate": "String (e.g. $1.2M Loss)",
    "risk_mitigated": "String (Description of what disaster was avoided)",
    "architectural_changes": ["Array of Strings (e.g. Shifted 40% volume from China to Vietnam)"]
}}

Original Request Context:
{original_prompt}
"""
        
        # We summon only the critical team for re-architecture
        hired_personnel = [
            {"agent_id": "architecture_rohan", "name": "Rohan", "role": "Master Supply-Chain Architect", "team": "ARCHITECTURE", "badge": "MYC-018-ROH", "status": "GREEN"},
            {"agent_id": "council_helena", "name": "Helena", "role": "Cost Strategist", "team": "COUNCIL", "badge": "MYC-005-HEL", "status": "GREEN"},
            {"agent_id": "architecture_atlas", "name": "Atlas", "role": "Executive Orchestrator", "team": "ARCHITECTURE", "badge": "MYC-017-ATL", "status": "GREEN"}
        ]
        
        # Let the frontend know agents are working on the crisis
        await event_publisher.publish(project_id, "log", {"level": "action", "text": "CRISIS MODE: Rohan and Helena have been summoned to re-architect and calculate profit loss."})
        
        orchestrator = MasterOrchestrator(session_id=project_id)
        report = await orchestrator.run_project_analysis(crisis_prompt, hired_personnel)
        
        # Save the new architecture report
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "COMPLETED",
                "architecture_report": report,
                "crisis_resolved_at": datetime.datetime.utcnow()
            }}
        )
        
        # Notify frontend that the crisis has been resolved and new architecture is ready
        await event_publisher.publish(project_id, "crisis_resolved", {"report": report})
        logger.info(f"Crisis re-architecture completed for {project_id}")
        
    except Exception as e:
        logger.error(f"Failed crisis re-architecture for {project_id}: {str(e)}")


@router.post("/alert")
async def receive_monitor_alert(
    payload: AlertPayload,
    background_tasks: BackgroundTasks
):
    """
    Receives an alert from the Monitor subsystem (or a fake website).
    Broadcasts it to the frontend and triggers a crisis re-architecture.
    """
    logger.info(f"Received MONITOR ALERT: {payload.title}")
    
    # In a real scenario, the monitor might not know the exact project ID, 
    # but it might know the network_id which maps to a project_id.
    # For this demo, we'll assume the payload provides it, or we'll grab the most recent active project.
    
    db = mongodb_connection.db
    project_id = payload.project_id
    
    if not project_id:
        # Get the most recently created project for the demo
        latest_project = await db.projects.find_one({}, sort=[("created_at", -1)])
        if latest_project:
            project_id = latest_project["project_id"]
        else:
            raise HTTPException(status_code=404, detail="No active project found to apply alert to.")
            
    # 1. Broadcast the CRITICAL_ALERT to the frontend via WebSockets
    await event_publisher.publish(project_id, "crisis_alert", {
        "title": payload.title,
        "description": payload.description,
        "severity": payload.severity,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    
    # 2. Trigger Autonomous Re-architecture
    background_tasks.add_task(run_crisis_rearchitecture_in_background, project_id, payload)
    
    return {"status": "success", "message": "Alert received, crisis re-architecture initiated."}

@router.post("/tariff-alert")
async def receive_tariff_alert(
    payload: TariffAlertPayload,
    background_tasks: BackgroundTasks
):
    """
    Receives a specific tariff increase payload from the demo site.
    Translates it into an AlertPayload and triggers the crisis flow.
    """
    logger.info(f"Received TARIFF ALERT: {payload.imposingCountryName} -> {payload.targetCountryName}")
    
    title = f"URGENT: Tariff Increase by {payload.imposingCountryName} on {payload.targetCountryName} ({payload.sector})"
    description = f"A new tariff has been imposed by {payload.imposingCountryName} on {payload.targetCountryName} for sector {payload.sector}. The rate has increased from {payload.previousRatePercent}% to {payload.newRatePercent}% (a {payload.delta}% increase). Effective Date: {payload.effectiveDate}. Legal Basis: {payload.legalBasis}."
    
    alert = AlertPayload(
        alert_id=f"tariff-{datetime.datetime.utcnow().timestamp()}",
        severity="CRITICAL",
        title=title,
        description=description,
        affected_entities=[payload.targetCountry, payload.sector],
        project_id=payload.project_id
    )
    
    # Delegate to the main alert processor
    return await receive_monitor_alert(alert, background_tasks)

