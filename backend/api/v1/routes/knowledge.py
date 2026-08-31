import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from organization.schemas import APIResponse
from knowledge.schemas import KnowledgeSpaceCreate, KnowledgeSpaceResponse, KnowledgeSourceCreate, KnowledgeSourceResponse
from knowledge.models import KnowledgeSource, KnowledgeDocument
from knowledge.registry import KnowledgeRegistry
from knowledge.ingestion.service import IngestionService
from knowledge.retrieval.retriever import KnowledgeRetriever
from knowledge.access import KnowledgeAccessPolicy

from api.dependencies.knowledge import (
    get_knowledge_registry, get_ingestion_service, 
    get_knowledge_retriever, get_knowledge_access_policy,
    get_source_repo, get_document_repo
)

router = APIRouter()

# ---------------------------------------------------------
# Space & Source Management
# ---------------------------------------------------------

@router.get("/teams/{team_id}/knowledge", response_model=APIResponse)
async def get_team_knowledge_space(
    team_id: str,
    registry: KnowledgeRegistry = Depends(get_knowledge_registry)
):
    space = await registry.get_knowledge_space_by_team(team_id)
    if not space:
        raise HTTPException(status_code=404, detail="Knowledge Space not found for team")
    return APIResponse(data=KnowledgeSpaceResponse(**space.model_dump()))

@router.post("/teams/{team_id}/knowledge/sources", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def add_knowledge_source(
    team_id: str,
    data: KnowledgeSourceCreate,
    registry: KnowledgeRegistry = Depends(get_knowledge_registry),
    policy: KnowledgeAccessPolicy = Depends(get_knowledge_access_policy),
    source_repo = Depends(get_source_repo),
    doc_repo = Depends(get_document_repo),
    ingestion: IngestionService = Depends(get_ingestion_service)
):
    # 1. Resolve authorized space (Team must own the space)
    space_id = await policy.resolve_authorized_space(team_id)
    
    # 2. Create Source
    source = KnowledgeSource(
        knowledge_space_id=space_id,
        **data.model_dump()
    )
    created_source = await source_repo.create(source)
    
    # 3. Create logical Document mapping to the source
    doc = KnowledgeDocument(
        source_id=created_source.id,
        knowledge_space_id=space_id,
        title=data.name,
        description=data.description,
    )
    created_doc = await doc_repo.create(doc)
    
    # 4. Trigger ingestion (synchronously for TOS 4)
    # In a real app this would be dispatched to a worker queue
    await ingestion.ingest_document(created_doc.id, created_source.uri)
    
    return APIResponse(data=KnowledgeSourceResponse(**created_source.model_dump()))


# ---------------------------------------------------------
# Retrieval (RAG)
# ---------------------------------------------------------

@router.get("/teams/{team_id}/knowledge/search", response_model=APIResponse)
async def search_team_knowledge(
    team_id: str,
    query: str,
    top_k: int = 5,
    retriever: KnowledgeRetriever = Depends(get_knowledge_retriever)
):
    """
    Searches the team's knowledge space securely.
    """
    context = await retriever.retrieve(team_id, query, top_k)
    return APIResponse(data=context.model_dump())
