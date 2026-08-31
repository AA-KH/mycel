"""
Real Estate Domain — FastAPI Router

Endpoints:
  POST /api/v1/real-estate/conversations/{id}/message  — main chat endpoint
  POST /api/v1/real-estate/data/upload                 — Excel upload
  GET  /api/v1/real-estate/data/status                 — ingestion job status
  GET  /api/v1/real-estate/properties                  — paginated property listing
  GET  /api/v1/real-estate/customers/{id}              — customer context
  POST /api/v1/real-estate/conversations               — create new conversation
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from domains.real_estate.models import (
    ConversationState, CustomerContext, CustomerRequirements,
    get_or_create_conversation,
)
from domains.real_estate.ingestion import (
    get_all_ingestion_jobs, get_ingestion_job,
    process_property_excel, search_properties,
    process_knowledge_document
)
from domains.real_estate.router import RealEstateRouter
from domains.real_estate.voice import voice_gateway

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/real-estate", tags=["Real Estate Demo"])

_re_router = RealEstateRouter()

# ─────────────────────────────────────────────────────────────────────────────
# Demo customer store — seeded with Kaushal as a normal data entry
# ─────────────────────────────────────────────────────────────────────────────
_customers: Dict[str, CustomerContext] = {
    "kaushal": CustomerContext(
        customer_id="kaushal",
        name="Kaushal",
        email="kaushal@demo.mycel",
        phone="+91-98765-43210",
        lead_status="hot",
        previous_interactions=3,
        requirements=CustomerRequirements(
            budget_max=8_000_000,  # 80 lakhs
            bhk=2,
            location="Chandigarh",
            purpose="family",
            investment_interest=True,
        ),
        notes="Interested in Tricity region (Chandigarh, Mohali, Panchkula). Prefers gated communities.",
    )
}


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────────────────────────────────────

class MessageRequest(BaseModel):
    customer_id: str
    text: str


class MessageResponse(BaseModel):
    conversation_id: str
    intent: str
    language: str
    team: str
    member: str
    source: str
    response: str
    tool_output: Optional[Any] = None


class NewConversationRequest(BaseModel):
    customer_id: str


class NewConversationResponse(BaseModel):
    conversation_id: str
    customer_id: str


# ─────────────────────────────────────────────────────────────────────────────
# Conversation Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/conversations", response_model=NewConversationResponse)
async def create_conversation(req: NewConversationRequest):
    """Create a new conversation for a customer."""
    conversation_id = str(uuid.uuid4())
    state = get_or_create_conversation(conversation_id, req.customer_id)
    # Pre-load customer requirements if customer exists
    customer = _customers.get(req.customer_id)
    if customer:
        r = customer.requirements
        state.requirements = {
            k: v for k, v in {
                "budget_max": r.budget_max,
                "bhk": r.bhk,
                "location": r.location,
                "purpose": r.purpose,
                "investment_interest": r.investment_interest,
            }.items() if v is not None
        }
    return NewConversationResponse(conversation_id=conversation_id, customer_id=req.customer_id)


@router.post("/conversations/{conversation_id}/message", response_model=MessageResponse)
async def send_message(conversation_id: str, req: MessageRequest):
    """
    Primary chat endpoint. Routes user query through the full pipeline:
    Intent → Capability → Security → Tool → Response.
    Emits WebSocket events at every stage.
    """
    try:
        result = await _re_router.route_and_execute(
            user_query=req.text,
            conversation_id=conversation_id,
            customer_id=req.customer_id,
        )
        return MessageResponse(
            conversation_id=result["conversation_id"],
            intent=result["intent"],
            language=result.get("language", "en"),
            team=result["team"],
            member=result["member"],
            source=result["source"],
            response=result["response"],
            tool_output=result.get("tool_output"),
        )
    except Exception as e:
        logger.error(f"Message routing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# VoiceLink Telephony Integration
# Register this WS URL in VoiceLink portal → Voice Services → WebSocket Bots:
#   ws://<your-server>/ws/voicelink/stream
#
# VoiceLink sends: connected → start → media (audio/alaw 8kHz) → stop
# We send back:    media (audio/alaw TTS) → mark → clear (barge-in)
# ─────────────────────────────────────────────────────────────────────────────

# VoiceLink WS is mounted on the root FastAPI app (not the sub-router)
# because WebSocket routers require different mounting.
# The endpoint is registered in main.py via:
#   app.add_api_websocket_route("/ws/voicelink/stream", voicelink_stream_handler)

async def voicelink_stream_handler(websocket: WebSocket):
    """
    VoiceLink WebSocket stream handler.
    URL: ws://<host>/ws/voicelink/stream

    Configure in VoiceLink portal:
        Voice Services → WebSocket Bots → Add Bot
        WebSocket URL: ws://<your-public-host>/ws/voicelink/stream

    Custom parameters (set in VoiceLink campaign/flow):
        customer_id: maps inbound caller to a customer profile
        language: "en" | "hi" | "pa" — defaults to auto-detect
    """
    await websocket.accept()
    logger.info("[VoiceLink] Inbound WebSocket connection accepted")
    try:
        handler = voice_gateway.create_voicelink_handler()
        await handler.handle_websocket(websocket)
    except RuntimeError as e:
        # Not in voicelink mode
        logger.warning(f"[VoiceLink] Gateway not in voicelink mode: {e}")
        import json
        await websocket.send_text(json.dumps({"error": "VoiceLink mode not enabled"}))
        await websocket.close()
    except Exception as e:
        logger.error(f"[VoiceLink] Stream handler error: {e}", exc_info=True)
        try:
            await websocket.close()
        except Exception:
            pass


@router.post("/voicelink/call-event")
async def voicelink_call_event(request: dict):
    """
    VoiceLink Call Event Webhook.
    Configure in VoiceLink portal → Call Event API.

    Receives call lifecycle events: call_initiated, call_answered,
    call_ended, call_failed, recording_ready.

    Used to update conversation state and trigger post-call analytics.
    """
    event_type = request.get("event_type", "unknown")
    call_sid = request.get("call_sid", "")
    caller = request.get("from", "")
    duration = request.get("duration", 0)

    logger.info(
        f"[VoiceLink Webhook] event={event_type} | call_sid={call_sid} | "
        f"from={caller} | duration={duration}s"
    )

    if event_type == "call_ended":
        # Optionally update conversation state with call metadata
        pass

    return {"status": "received", "event_type": event_type}


# ─────────────────────────────────────────────────────────────────────────────
# Property Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/properties")
async def list_properties(
    budget_max: Optional[float] = Query(None),
    bhk: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    skip: int = Query(0),
):
    """Paginated, server-side property search with structured filters."""
    results = await search_properties(
        budget_max=budget_max,
        bhk=bhk,
        location=location,
        limit=limit,
        skip=skip,
    )
    return {"properties": results, "count": len(results)}


# ─────────────────────────────────────────────────────────────────────────────
# Data Upload Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/data/upload")
async def upload_property_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload property Excel file.
    Validation and ingestion run as a background task.
    Returns dataset_id immediately for status polling.
    """
    if not file.filename or not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only .xlsx or .xls files are accepted.")

    try:
        content = await file.read()
        # Return immediately — ingestion is a background task
        background_tasks.add_task(process_property_excel, content, file.filename)
        return {
            "status": "accepted",
            "message": f"File '{file.filename}' accepted for ingestion. Check /data/status for progress.",
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data/status")
async def get_ingestion_status():
    """List all ingestion jobs with their versioning and status."""
    jobs = get_all_ingestion_jobs()
    return {"jobs": jobs, "total": len(jobs)}


@router.post("/knowledge/upload")
async def upload_knowledge_data(
    file: UploadFile = File(...),
):
    """
    Upload knowledge document (PDF/TXT) for fast vector retrieval.
    Processed immediately and stored in memory.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
        
    try:
        content = await file.read()
        chunks_added = await process_knowledge_document(content, file.filename)
        return {
            "status": "success",
            "message": f"File '{file.filename}' processed. Added {chunks_added} vector chunks.",
            "chunks_added": chunks_added
        }
    except Exception as e:
        logger.error(f"Knowledge upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Customer Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    """Retrieve customer context and requirements."""
    customer = _customers.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found.")
    return customer.model_dump()


@router.get("/customers")
async def list_customers():
    """List all customers (demo endpoint)."""
    return {"customers": [c.model_dump() for c in _customers.values()]}


# ─────────────────────────────────────────────────────────────────────────────
# Legacy endpoint — backward compat with previous /real_estate/ prefix
# ─────────────────────────────────────────────────────────────────────────────

legacy_router = APIRouter(prefix="/real_estate", tags=["Real Estate Demo (Legacy)"])


class _LegacyChatRequest(BaseModel):
    customer_id: str
    conversation_id: Optional[str] = None
    query: str


@legacy_router.post("/chat")
async def legacy_chat(req: _LegacyChatRequest):
    """Legacy endpoint for backward compatibility with the frontend hook."""
    conversation_id = req.conversation_id or str(uuid.uuid4())
    try:
        result = await _re_router.route_and_execute(
            user_query=req.query,
            conversation_id=conversation_id,
            customer_id=req.customer_id,
        )
        return {
            "conversation_id": result["conversation_id"],
            "status": "routed",
            "routing": {
                "intent": result["intent"],
                "team": result["team"],
                "member": result["member"],
                "capabilities": result.get("capabilities", []),
                "data_source": result.get("source", ""),
            },
            "response": result.get("response", ""),
            "tool_output": result.get("tool_output"),
        }
    except Exception as e:
        logger.error(f"Legacy chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@legacy_router.post("/upload")
async def legacy_upload(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Legacy upload endpoint — delegates to new handler."""
    if not file.filename or not file.filename.endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    content = await file.read()
    background_tasks.add_task(process_property_excel, content, file.filename)
    return {"status": "accepted", "message": "File upload accepted. Ingestion running in background."}
