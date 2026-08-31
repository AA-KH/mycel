"""
Evaluation API Router (Phase 13 Evaluation System)

Exposes REST endpoints for the Evaluation System.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from evaluation.models import Evaluation, EvaluationType, EvaluationStatus
from evaluation.repository import EvaluationRepository


router = APIRouter()

# Simple global dependency for phase 13 (mocked persistence)
_eval_repo = EvaluationRepository()

def get_eval_repo() -> EvaluationRepository:
    return _eval_repo


class SearchEvaluationsRequest(BaseModel):
    task_id: str = None
    evaluation_type: str = None
    status: str = None
    limit: int = 50


@router.get("/{evaluation_id}", summary="Get Evaluation by ID")
async def get_evaluation(evaluation_id: str):
    """
    Retrieves a specific evaluation record by ID.
    """
    repo = get_eval_repo()
    evaluation = await repo.get_by_id(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    return evaluation.model_dump()


@router.post("/search", summary="Search Evaluations")
async def search_evaluations(body: SearchEvaluationsRequest):
    """
    Queries evaluations by task_id, type, and status.
    """
    repo = get_eval_repo()
    
    eval_type = EvaluationType(body.evaluation_type) if body.evaluation_type else None
    eval_status = EvaluationStatus(body.status) if body.status else None
    
    results = await repo.search(
        task_id=body.task_id,
        evaluation_type=eval_type,
        status=eval_status,
        limit=body.limit
    )
    
    return [r.model_dump() for r in results]
