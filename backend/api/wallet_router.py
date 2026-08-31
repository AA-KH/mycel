"""
Wallet Router — REST endpoints for HR-issued WalletCards.

Each WalletCard represents an assignment of an agent to a subtask.
Cards are created during the ManagerAgent pipeline and stored in MongoDB.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.mongodb import mongodb_connection

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ────────────────────────────────────────────────────────

class WalletCardSchema(BaseModel):
    id: str
    task_id: str
    agent_id: str
    agent_role: str
    agent_name: str
    task_title: str
    team: str
    issued_by: str = "hr_agent"
    issued_at: str
    status: str  # "assigned" | "in_progress" | "done"
    completed_summary: Optional[str] = None


class WalletCardCreateRequest(BaseModel):
    task_id: str = Field(..., description="Parent task ID")
    agent_id: str = Field(..., description="Agent session ID or employee ID")
    agent_role: str = Field(..., description="Agent role label")
    agent_name: str = Field(..., description="Agent display name")
    task_title: str = Field(..., description="Subtask description")
    team: str = Field(..., description="Team assignment")


# ── Helper: Create a WalletCard ────────────────────────────────────

async def create_wallet_card(
    task_id: str,
    agent_id: str,
    agent_role: str,
    agent_name: str,
    task_title: str,
    team: str,
) -> dict:
    """Create a WalletCard document in MongoDB and return it."""
    import uuid
    db = mongodb_connection.db
    now = datetime.now(timezone.utc)

    card = {
        "id": str(uuid.uuid4()),
        "task_id": task_id,
        "agent_id": agent_id,
        "agent_role": agent_role,
        "agent_name": agent_name,
        "task_title": task_title[:160],
        "team": team,
        "issued_by": "hr_agent",
        "issued_at": now.isoformat(),
        "status": "assigned",
        "completed_summary": None,
    }

    await db.wallet_cards.insert_one(card)
    logger.info(f"WalletCard created: {card['id']} for {agent_name} ({team})")
    return card


async def update_wallet_card_status(
    card_id: str,
    status: str,
    completed_summary: Optional[str] = None,
) -> Optional[dict]:
    """Update a WalletCard status and return the updated doc."""
    db = mongodb_connection.db
    update_fields = {"status": status}
    if completed_summary:
        update_fields["completed_summary"] = completed_summary[:500]

    result = await db.wallet_cards.find_one_and_update(
        {"id": card_id},
        {"$set": update_fields},
        return_document=True,
    )
    if result:
        result["_id"] = str(result["_id"])
        logger.info(f"WalletCard {card_id} updated to {status}")
    return result


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("/cards", summary="List wallet cards")
async def get_wallet_cards(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """Return WalletCard documents, optionally filtered."""
    db = mongodb_connection.db
    query = {}
    if status:
        query["status"] = status
    if task_id:
        query["task_id"] = task_id

    cursor = db.wallet_cards.find(query).sort("issued_at", -1).limit(limit)
    cards = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        cards.append(doc)

    return {"cards": cards, "count": len(cards)}


@router.get("/cards/{card_id}", summary="Get single wallet card")
async def get_wallet_card(card_id: str):
    """Return a single WalletCard by ID."""
    db = mongodb_connection.db
    doc = await db.wallet_cards.find_one({"id": card_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"WalletCard '{card_id}' not found")
    doc["_id"] = str(doc["_id"])
    return doc


@router.delete("/cards", summary="Clear all wallet cards (dev only)")
async def clear_wallet_cards():
    """Delete all wallet cards. For development use."""
    db = mongodb_connection.db
    result = await db.wallet_cards.delete_many({})
    return {"deleted": result.deleted_count}
