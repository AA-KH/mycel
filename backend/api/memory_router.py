"""
Memory API Router (Phase 12 Memory System)

Exposes REST endpoints for the Memory System.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from memory.models import (
    MemoryScope,
    MemoryItem,
    MemoryQueryResult,
)
from memory.service import MemoryService
from tasks.schemas import RecordMemoryRequest, QueryMemoryRequest

router = APIRouter()

# Global singleton
_memory_service: MemoryService = None

def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service


@router.post("/record", summary="Record a new MemoryItem")
async def record_memory(body: RecordMemoryRequest):
    """
    Validates and stores a structured memory item.
    """
    service = get_memory_service()
    import uuid
    memory_id = f"mem_{uuid.uuid4().hex[:8]}"

    item = MemoryItem(
        memory_id=memory_id,
        scope=body.scope,
        scope_id=body.scope_id,
        memory_type=body.memory_type,
        importance=body.importance,
        title=body.title,
        content=body.content,
        tags=body.tags,
        metadata=body.metadata,
    )

    saved_item, errors = service.record_memory(item)
    if not saved_item:
        raise HTTPException(status_code=400, detail=errors)

    return saved_item.model_dump()


@router.post("/query", summary="Query active memories")
async def query_memories(body: QueryMemoryRequest):
    """
    Queries memories by scope, tags, and keywords.
    """
    service = get_memory_service()
    results = service.query_memories(
        scope=MemoryScope(body.scope),
        scope_id=body.scope_id,
        keywords=body.keywords,
        tags=body.tags,
        limit=body.limit,
    )

    return [
        {
            "memory_id": r.memory_item.memory_id,
            "title": r.memory_item.title,
            "summary": r.memory_item.summary,
            "score": r.score,
            "reason": r.match_reason,
        }
        for r in results
    ]


@router.get("/context/{scope}/{scope_id}", summary="Get Memory Context Projection")
async def get_memory_context(scope: str, scope_id: str, limit: int = 5):
    """
    Retrieves and projects minimal memory context for execution.
    """
    service = get_memory_service()
    context_list = service.get_context_memories(
        scope=MemoryScope(scope.upper()),
        scope_id=scope_id,
        limit=limit,
    )
    return {"context": context_list}


@router.post("/{memory_id}/supersede", summary="Supersede an existing memory")
async def supersede_memory(memory_id: str, body: RecordMemoryRequest):
    """
    Supersedes an old memory with a new version.
    """
    service = get_memory_service()
    import uuid
    new_memory_id = f"mem_{uuid.uuid4().hex[:8]}"

    new_item = MemoryItem(
        memory_id=new_memory_id,
        scope=body.scope,
        scope_id=body.scope_id,
        memory_type=body.memory_type,
        importance=body.importance,
        title=body.title,
        content=body.content,
        tags=body.tags,
        metadata=body.metadata,
    )

    saved_item, errors = service.supersede_memory(memory_id, new_item)
    if not saved_item:
        raise HTTPException(status_code=400, detail=errors)

    return saved_item.model_dump()


@router.delete("/{memory_id}", summary="Archive a memory")
async def archive_memory(memory_id: str):
    """
    Archives a memory item.
    """
    service = get_memory_service()
    success = service.archive_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="MemoryItem not found or could not be archived.")
    return {"status": "success"}
