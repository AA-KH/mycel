"""
Memory Extractor (Phase 12 Memory System)

Responsibilities:
- Extracts structured MemoryItem objects from execution experiences, task results, and handoffs.
- Enforces Memory is NOT Chat History (extracts insights/summaries, NOT raw transcript loops).
- Automatically prunes prohibited secrets and reasoning traces.
- Assigns canonical MemoryScope (TEAM, EMPLOYEE, TASK, ORGANIZATION).
"""

import uuid
import re
import logging
from typing import Optional, List, Dict, Any

from memory.models import (
    MemoryItem,
    MemoryScope,
    MemoryType,
    MemoryImportance,
    MemoryExtractRequest,
)

logger = logging.getLogger(__name__)

PROHIBITED_PATTERNS = [
    r'(?i)api[-_]?key\s*[:=]\s*\S+',
    r'(?i)secret\s*[:=]\s*\S+',
    r'(?i)password\s*[:=]\s*\S+',
    r'<think>.*?</think>',
]


class MemoryExtractor:
    """
    Extracts and sanitizes structured MemoryItems from raw execution experiences.
    """

    def extract_memory(self, request: MemoryExtractRequest) -> MemoryItem:
        """
        Extracts structured MemoryItem from MemoryExtractRequest payload.
        """
        raw = request.raw_text_or_data.strip()

        # ── 1. Clean Secrets and Chain-of-Thought ──────────────────────────
        cleaned = raw
        for pattern in PROHIBITED_PATTERNS:
            cleaned = re.sub(pattern, '[REDACTED]', cleaned, flags=re.DOTALL)

        # ── 2. Derive Title & Content Summary ──────────────────────────────
        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        title = lines[0][:80] if lines else f"{request.experience_type.value.title()} Memory"
        content = " ".join(lines[:10]) if lines else "No execution summary available."

        # ── 3. Resolve Scope ───────────────────────────────────────────────
        scope = MemoryScope.ORGANIZATION
        scope_id = "mycel_global"

        if request.employee_id:
            scope = MemoryScope.EMPLOYEE
            scope_id = request.employee_id
        elif request.team_id:
            scope = MemoryScope.TEAM
            scope_id = request.team_id
        elif request.task_id:
            scope = MemoryScope.TASK
            scope_id = request.task_id

        # ── 4. Build MemoryItem ────────────────────────────────────────────
        memory_id = f"mem_{uuid.uuid4().hex[:8]}"

        return MemoryItem(
            memory_id=memory_id,
            organization_id="mycel_global",
            scope=scope,
            scope_id=scope_id,
            memory_type=request.experience_type,
            importance=request.importance,
            title=title,
            content=content,
            summary=content[:150],
            tags=list(request.tags),
            source_task_id=request.task_id,
            source_work_unit_id=request.work_unit_id,
            source_employee_id=request.employee_id,
            source_team_id=request.team_id,
            metadata=request.metadata,
        )
