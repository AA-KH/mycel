import logging
import uuid
from typing import List, Optional, Dict, Any

from memory.service import MemoryService
from memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryType,
    MemoryImportance,
    MemoryStatus
)
from tasks.models import TaskContext

logger = logging.getLogger(__name__)

class CompanyMemoryBridge:
    """
    Hooks the CompanyBuilder pipeline into the core MemorySystem.
    Ensures that as the user provides prompts across stages, the system retains
    context without forcing the user to repeat previous constraints.
    """
    def __init__(self, memory_service: MemoryService):
        self._memory = memory_service

    def build_task_context(self, company_id: str, prompt: str, current_artifacts: List[str]) -> TaskContext:
        """
        Synthesizes a TaskContext by querying previous memories and constraints 
        related to this company based on the current prompt semantics.
        """
        # Fetch relevant context from Memory
        context_memories = self._memory.get_context_memories(
            scope=MemoryScope.ORGANIZATION,
            scope_id=company_id,
            keywords=prompt.split(), # Simple keyword extraction for now
            limit=10
        )
        
        # Parse memories into constraints and references
        user_constraints = []
        brand_context = ""
        product_context = ""
        target_audience = ""
        industry = ""
        
        for mem in context_memories:
            tags = mem.get("tags", [])
            content = mem.get("content", "")
            
            if "constraint" in tags:
                user_constraints.append(content)
            if "brand" in tags:
                brand_context += f"{content} "
            if "product" in tags:
                product_context += f"{content} "
            if "audience" in tags:
                target_audience += f"{content} "
            if "industry" in tags:
                industry = content
                
        # Build TaskContext
        return TaskContext(
            product_context=product_context.strip() or None,
            brand_context=brand_context.strip() or None,
            target_audience=target_audience.strip() or None,
            industry=industry.strip() or None,
            user_constraints=user_constraints,
            existing_artifacts=current_artifacts
        )
        
    def record_decision(self, company_id: str, title: str, decision: str, tags: List[str] = None):
        """Records a permanent decision made during company generation."""
        _tags = ["decision"] + (tags or [])
        item = MemoryItem(
            memory_id=f"mem_{uuid.uuid4().hex[:10]}",
            organization_id="mycel_global",
            scope=MemoryScope.ORGANIZATION,
            scope_id=company_id,
            memory_type=MemoryType.DECISION,
            importance=MemoryImportance.HIGH,
            title=title,
            content=decision,
            tags=_tags
        )
        self._memory.record_memory(item)
        logger.info(f"Recorded decision for company {company_id}: {title}")

    def record_constraint(self, company_id: str, title: str, constraint: str, tags: List[str] = None):
        """Records a user-imposed constraint."""
        _tags = ["constraint"] + (tags or [])
        item = MemoryItem(
            memory_id=f"mem_{uuid.uuid4().hex[:10]}",
            organization_id="mycel_global",
            scope=MemoryScope.ORGANIZATION,
            scope_id=company_id,
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.HIGH,
            title=title,
            content=constraint,
            tags=_tags
        )
        self._memory.record_memory(item)
        logger.info(f"Recorded constraint for company {company_id}: {title}")
