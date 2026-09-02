from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import Dict, Any
import uuid
import hashlib
import json
from datetime import datetime, timedelta

from api.v1.schemas.project import ProjectPayload
from core.mongodb import mongodb_connection
from core.logger import logger
from core.dependencies import CurrentOperatorDep
from teams.architecture.team import architecture_team
from teams.executive.team_members.maya.agent import MayaHRAgent
from core.events import event_publisher

router = APIRouter()

def construct_master_prompt(payload: ProjectPayload) -> str:
    """
    Converts the UI JSON payload into a natural language prompt for the AI agents.
    """
    prompt = f"Design a highly resilient and scalable supply-chain architecture for a {payload.businessType} business.\n"
    
    if payload.productName:
        prompt += f"Product: {payload.productName}\n"
    elif payload.categories:
        prompt += f"Categories: {payload.categories}\n"
        
    if payload.productDescription:
        prompt += f"Description: {payload.productDescription}\n"
    elif payload.businessDescription:
        prompt += f"Description: {payload.businessDescription}\n"
        
    prompt += "\nOperational Regions:\n"
    prompt += f"- Sourcing/Supply: {payload.supplySource or 'Unknown'} ({payload.supplyCountries})\n"
    prompt += f"- Manufacturing/Operations: {payload.operations or 'Unknown'} ({payload.operationsDetails})\n"
    prompt += f"- Customers/Distribution: {payload.customerScope or 'Unknown'} ({payload.customerAreas})\n"
    
    prompt += f"\nScale & Timeline:\n"
    prompt += f"- Volume: {payload.volume}\n"
    prompt += f"- Demand Pattern: {payload.demandPattern} (Peak: {payload.peakSurge})\n"
    prompt += f"- Timeline: {payload.timeline} ({payload.targetDate})\n"
    
    if payload.priorities:
        prompt += f"\nOptimization Priorities (in order of importance): {', '.join(payload.priorities)}\n"
        
    if payload.constraints:
        prompt += "\nExisting Constraints & Knowledge:\n"
        for constraint in payload.constraints:
            prompt += f"- {constraint.category}: {constraint.text}\n"
            
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
        
        # Default fallback (ensuring representation from all phases and teams)
        hired_personnel = [
            # Phase 1: Research
            {"agent_id": "intelligence_ravi", "name": "Ravi", "role": "Supplier Intelligence", "team": "INTELLIGENCE", "badge": "MYC-010-RAV", "mandate": "Default supplier data", "status": "GREEN"},
            {"agent_id": "network_aanya", "name": "Aanya", "role": "Network Design", "team": "NETWORK", "badge": "MYC-014-AAN", "mandate": "Default routing", "status": "GREEN"},
            {"agent_id": "council_sofia", "name": "Sofia", "role": "Council Chair", "team": "COUNCIL", "badge": "MYC-005-SOF", "mandate": "Default strategy", "status": "GREEN"},
            
            # Phase 2: Drafting
            {"agent_id": "architecture_priya", "name": "Priya", "role": "Implementation Planner", "team": "ARCHITECTURE", "badge": "MYC-019-PRI", "mandate": "Default planning", "status": "GREEN"},
            {"agent_id": "architecture_rohan", "name": "Rohan", "role": "Master Supply-Chain Architect", "team": "ARCHITECTURE", "badge": "MYC-018-ROH", "mandate": "Default routing", "status": "GREEN"},
            
            # Phase 3: Validation
            {"agent_id": "resilience_leena", "name": "Leena", "role": "Stress Tester", "team": "RESILIENCE", "badge": "MYC-021-LEE", "mandate": "Default stress testing", "status": "GREEN"},
            {"agent_id": "architecture_ethan", "name": "Ethan", "role": "Independent Validator", "team": "ARCHITECTURE", "badge": "MYC-020-ETH", "mandate": "Default validation", "status": "GREEN"},
            
            # Phase 4: Synthesis
            {"agent_id": "architecture_atlas", "name": "Atlas", "role": "Executive Orchestrator", "team": "ARCHITECTURE", "badge": "MYC-017-ATL", "mandate": "Default orchestration", "status": "GREEN"}
        ]
        
        hired_agent_ids = [p["agent_id"] for p in hired_personnel]
        
        try:
            # Safest method: Extract directly from Maya's tool call execution
            if hasattr(maya, "hired_team") and maya.hired_team:
                hired_personnel = maya.hired_team
                logger.info(f"Successfully extracted {len(hired_personnel)} agents directly from Maya's hire_team tool call.")
            else:
                # Legacy fallback: Try to extract the JSON payload she generated via tool
                match = re.search(r'\{.*"hired_personnel":\s*\[.*?\]\}', maya_response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    hired_personnel = parsed.get("hired_personnel", hired_personnel)
                    logger.info("Successfully extracted hired agents via regex fallback.")
        except Exception as e:
            logger.warning(f"Failed to parse Maya's output for hired personnel, defaulting to core team. Error: {e}")
            
        # GUARANTEE FULL TEAM PARTICIPATION
        # If Maya missed any core teams, forcefully inject the fallback representative
        represented_teams = {p.get("team", "").upper() for p in hired_personnel}
        
        fallback_representatives = {
            "INTELLIGENCE": {"agent_id": "intelligence_ravi", "name": "Ravi", "role": "Supplier Intelligence", "team": "INTELLIGENCE", "badge": "MYC-010-RAV", "status": "GREEN"},
            "NETWORK": {"agent_id": "network_aanya", "name": "Aanya", "role": "Network Design", "team": "NETWORK", "badge": "MYC-014-AAN", "status": "GREEN"},
            "COUNCIL": {"agent_id": "council_sofia", "name": "Sofia", "role": "Council Chair", "team": "COUNCIL", "badge": "MYC-005-SOF", "status": "GREEN"},
            "RESILIENCE": {"agent_id": "resilience_leena", "name": "Leena", "role": "Stress Tester", "team": "RESILIENCE", "badge": "MYC-021-LEE", "status": "GREEN"},
            "ARCHITECTURE": {"agent_id": "architecture_atlas", "name": "Atlas", "role": "Executive Orchestrator", "team": "ARCHITECTURE", "badge": "MYC-017-ATL", "status": "GREEN"}
        }
        
        for required_team, fallback_agent in fallback_representatives.items():
            if required_team not in represented_teams:
                logger.info(f"Team {required_team} was missing from Maya's hires. Forcefully injecting representative {fallback_agent['name']}.")
                hired_personnel.append(fallback_agent)
                
        hired_agent_ids = [p["agent_id"] for p in hired_personnel]

        logger.info(f"Maya hired the following team: {hired_agent_ids}")
        
        await event_publisher.publish(project_id, "log", {"level": "action", "text": "Maya assembling task force. Only load-bearing specialists will be hired."})

        db = mongodb_connection.db
        # Save hired team to DB immediately so frontend can show them
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {"hired_team": hired_personnel}}
        )
        
        # Publish 'hire' events
        for p in hired_personnel:
            await event_publisher.publish(project_id, "hire", {
                "agent": p["name"],
                "team": p["team"].capitalize() if isinstance(p.get("team"), str) else "Architecture",
                "role": p["role"],
                "badge": p.get("badge", ""),
                "clearance": p.get("status", "GREEN"),
                "mandate": p.get("mandate", "Task assignment pending")
            })

        # 2. Global Execution Phase
        from core.orchestrator import MasterOrchestrator
        orchestrator = MasterOrchestrator(session_id=project_id)
        
        report = await orchestrator.run_project_analysis(master_prompt, hired_personnel)
        
        # ─────────────────────────────────────────────────────────────
        # GUARANTEED PITCH DEMO HOOK (ArmorIQ AMBER Trigger)
        # ─────────────────────────────────────────────────────────────
        # Force Helena to check with ArmorIQ before the final report is sent.
        # This ensures the "Human-in-the-Loop" popup always fires at the climax of the demo,
        # regardless of whether the LLM hallucinates or skips the tool call.
        from core.approval_gate import gate_tool_call
        await event_publisher.publish(project_id, "log", {"level": "action", "text": "Helena is preparing to email the final strategic blueprint to external stakeholders..."})
        
        await gate_tool_call(
            session_id=project_id,
            agent_name="Helena",
            tool_name="email_stakeholders",
            arguments={"subject": "Final Mycel Architecture Blueprint", "report_body": "Confidential Strategic Plan."}
        )
        # ─────────────────────────────────────────────────────────────

        # Save final report to MongoDB
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "COMPLETED",
                "architecture_report": report,
                "updated_at": datetime.utcnow()
            }}
        )
        await event_publisher.publish(project_id, "complete", {})
        logger.info(f"Successfully completed global architecture review for project {project_id}")
    except Exception as e:
        logger.error(f"Failed background architecture review for {project_id}: {str(e)}")
        db = mongodb_connection.db
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "status": "FAILED",
                "error": str(e),
                "updated_at": datetime.utcnow()
            }}
        )

@router.post("/create", status_code=201)
async def create_project(
    payload: ProjectPayload, 
    background_tasks: BackgroundTasks,
    current_operator: CurrentOperatorDep
):
    try:
        db = mongodb_connection.db
        
        # Implement Idempotency: Check if the exact same payload was submitted recently
        payload_str = payload.json()
        payload_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
        
        recent_project = await db.projects.find_one({
            "user_id": current_operator.user_id,
            "payload_hash": payload_hash,
            "created_at": {"$gte": datetime.utcnow() - timedelta(minutes=5)}
        })
        
        if recent_project:
            logger.info(f"Idempotency hit: Returning existing project {recent_project['project_id']}")
            return {
                "status": "success",
                "project_id": recent_project["project_id"],
                "message": "Project already created (idempotent request).",
                "websocket_url": "ws://localhost:8000/api/realtime/sessions"
            }
        
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        master_prompt = construct_master_prompt(payload)
        
        # 1. Save to MongoDB
        project_data = payload.dict()
        project_data["project_id"] = project_id
        project_data["user_id"] = current_operator.user_id
        project_data["company_id"] = current_operator.company_id
        project_data["status"] = "RUNNING"
        project_data["created_at"] = datetime.utcnow()
        project_data["master_prompt"] = master_prompt
        project_data["payload_hash"] = payload_hash
        
        await db.projects.insert_one(project_data)
        
        # Link uploaded draft documents to this project
        if payload.files:
            await db.knowledge.update_many(
                {"project_id": "draft", "cloudinary_url": {"$in": payload.files}},
                {"$set": {"project_id": project_id}}
            )
        
        # 2. Trigger Agents in Background
        background_tasks.add_task(run_agents_in_background, project_id, master_prompt)
        
        return {
            "status": "success",
            "project_id": project_id,
            "message": "Project created. Architecture team has been deployed in the background.",
            "websocket_url": f"ws://localhost:8000/api/v1/realtime/sessions/{project_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{project_id}")
async def get_project(project_id: str, operator: CurrentOperatorDep):
    db = mongodb_connection.db
    project = await db.projects.find_one({"project_id": project_id, "user_id": operator.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
