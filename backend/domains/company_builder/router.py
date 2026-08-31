from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from domains.company_builder.pipeline import CompanyBuilderPipeline
from domains.company_builder.models import CompanyBuilderState, BuilderStage
from memory.service import MemoryService
from domains.company_builder.memory_bridge import CompanyMemoryBridge
from domains.company_builder.delegation_engine import build_delegation_graph
from domains.company_builder.document_generator import generate_html_document
from tasks.orchestrator import TaskOrchestrator
from teams.registry import TeamRegistry
from teams.seed import TeamCatalogueSeed
from pathlib import Path
from execution.pipelines.registry import PipelineRegistry
from execution.contracts.registry import ExecutionContractRegistry
from execution.collaboration.registry import TeamCollaborationContractRegistry

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/company-builder", tags=["Company Builder Demo"])

# ── In-memory singletons for the demo ────────────────────────────────────────
_memory_service = MemoryService()
_memory_bridge = CompanyMemoryBridge(_memory_service)
_team_registry = TeamRegistry()

try:
    _seed = TeamCatalogueSeed(base_dir=Path(__file__).parent.parent.parent / "teams")
    for team in _seed.load_teams():
        try:
            _team_registry.register(team)
        except Exception:
            pass  # already registered or invalid
except Exception as e:
    logger.warning(f"Could not seed teams into registry: {e}")

_pipeline_registry = PipelineRegistry()
_exec_contracts = ExecutionContractRegistry()
_collab_contracts = TeamCollaborationContractRegistry()

_orchestrator = TaskOrchestrator(
    team_registry=_team_registry,
    pipeline_registry=_pipeline_registry,
    execution_contracts=_exec_contracts,
    collaboration_contracts=_collab_contracts
)

_pipeline = CompanyBuilderPipeline(
    memory_bridge=_memory_bridge,
    orchestrator=_orchestrator
)

# In-memory store for delegation graphs and documents
_delegation_store: Dict[str, Any] = {}
_document_store: Dict[str, Any] = {}


# ── Request/Response models ───────────────────────────────────────────────────

class InitRequest(BaseModel):
    company_id: Optional[str] = None
    workspace_id: Optional[str] = None
    company_name: Optional[str] = "New Company"


class PromptRequest(BaseModel):
    workflow_id: str
    prompt: str
    company_name: Optional[str] = "Your Company"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/init")
async def init_company_builder(req: InitRequest):
    """Initialize a new company building workflow."""
    company_id = req.company_id or f"company_{uuid.uuid4().hex[:8]}"
    workspace_id = req.workspace_id or f"ws_{uuid.uuid4().hex[:8]}"

    state = await _pipeline.initialize_company(company_id, workspace_id)
    # Store company_name in metadata
    state.metadata["company_name"] = req.company_name or "New Company"
    return {"workflow_id": state.workflow_id, "state": state.model_dump()}


@router.post("/prompt")
async def submit_prompt(req: PromptRequest):
    """
    Submit a user prompt for the current stage.
    Returns:
      - orchestration_result: TaskOrchestrator plan
      - delegation_graph: Manager → Member task transparency
      - document: HTML document for this stage (browser-printable as PDF)
    """
    try:
        state = _pipeline.get_state(req.workflow_id)
        if not state:
            raise HTTPException(status_code=404, detail="Workflow not found")

        current_stage = state.current_stage.value
        company_name = state.metadata.get("company_name", req.company_name or "Your Company")

        # 1. Run orchestration pipeline
        orchestration_result = await _pipeline.process_prompt(req.workflow_id, req.prompt)
        
        # Try to extract the final result string from the orchestration result
        # process_prompt returns a dict with "orchestration_result" key which is the OrchestrationResult dump.
        orch_dump = orchestration_result.get("orchestration_result", {})
        
        # It's usually found in `final_report` or we can fallback to something else if needed
        agent_output = orch_dump.get("final_report")
        if not agent_output and "team_results" in orch_dump:
            team_results = orch_dump.get("team_results", [])
            if team_results:
                agent_output = team_results[-1].get("result", "")
        if not agent_output:
            agent_output = "No output could be extracted for this stage."

        # 2. Build delegation graph (transparency layer)
        delegation_graph = build_delegation_graph(
            workflow_id=req.workflow_id,
            stage=current_stage,
            prompt=req.prompt,
        )
        _delegation_store[req.workflow_id] = _delegation_store.get(req.workflow_id, [])
        _delegation_store[req.workflow_id].append(delegation_graph.model_dump())

        # 3. Generate HTML document
        doc = generate_html_document(
            workflow_id=req.workflow_id,
            stage=current_stage,
            prompt=req.prompt,
            delegation_graph=delegation_graph,
            company_name=company_name,
            agent_output=agent_output,
        )
        _document_store[f"{req.workflow_id}_{current_stage}"] = doc.model_dump()

        return {
            "workflow_id": req.workflow_id,
            "stage": current_stage,
            "orchestration_result": orchestration_result.get("orchestration_result"),
            "delegation_graph": delegation_graph.model_dump(),
            "document_id": doc.doc_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/state/{workflow_id}")
def get_state(workflow_id: str):
    """Get the current workflow state."""
    state = _pipeline.get_state(workflow_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return state.model_dump()


@router.get("/delegation/{workflow_id}")
def get_delegation_history(workflow_id: str):
    """Get all delegation graphs for a workflow (transparency history)."""
    graphs = _delegation_store.get(workflow_id, [])
    return {"workflow_id": workflow_id, "delegation_history": graphs}


@router.get("/document/{workflow_id}/{stage}", response_class=HTMLResponse)
def get_document(workflow_id: str, stage: str):
    """Serve the HTML document for a stage — browser can print to PDF."""
    key = f"{workflow_id}_{stage}"
    doc = _document_store.get(key)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not generated yet for this stage")
    return HTMLResponse(content=doc["content_html"])


@router.get("/documents/{workflow_id}")
def list_documents(workflow_id: str):
    """List all generated documents for a workflow."""
    docs = []
    for key, doc in _document_store.items():
        if doc["workflow_id"] == workflow_id:
            docs.append({
                "doc_id": doc["doc_id"],
                "stage": doc["stage"],
                "title": doc["title"],
                "format": doc["format"],
                "url": f"/api/company-builder/document/{workflow_id}/{doc['stage']}",
            })
    return {"workflow_id": workflow_id, "documents": docs}


@router.post("/advance/{workflow_id}")
async def advance_stage(workflow_id: str, stage: BuilderStage):
    """Manually advance the workflow to a specific stage."""
    try:
        await _pipeline.advance_stage(workflow_id, stage)
        return {"status": "success", "current_stage": stage}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
