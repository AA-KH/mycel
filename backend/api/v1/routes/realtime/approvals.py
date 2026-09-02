"""
api/v1/routes/realtime/approvals.py

HTTP endpoint for the frontend to submit human approval/denial
decisions for ArmorIQ-gated tool calls.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.approval_gate import resolve_approval
from core.logger import logger

router = APIRouter()


class ApprovalResponse(BaseModel):
    approved: bool


@router.post("/approvals/{approval_id}/respond")
async def respond_to_approval(approval_id: str, body: ApprovalResponse):
    """
    Called by the frontend when the user clicks Allow or Deny on the
    ArmorIQ approval modal.
    """
    success = resolve_approval(approval_id, body.approved)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Approval request {approval_id!r} not found or already expired.",
        )

    action = "approved" if body.approved else "denied"
    logger.info(f"[ArmorIQ] Human {action} approval_id={approval_id}")
    return {"status": "ok", "approval_id": approval_id, "approved": body.approved}
