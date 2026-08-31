"""
Memory Validator (Phase 12 Memory System)

Responsibilities:
- Validates MemoryItem schema integrity, title/content non-emptiness, and scope bounds.
- Enforces security & privacy boundaries:
    - Strips/blocks secret keys (credentials, tokens, API keys).
    - Strips/blocks hidden chain-of-thought traces.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
from memory.models import MemoryItem

logger = logging.getLogger(__name__)

PROHIBITED_KEYS = {
    "api_key", "secret", "password", "token", "credentials",
    "chain_of_thought", "reasoning_trace", "think", "hidden_prompt",
    "private_tools", "private_knowledge", "internal_logs",
}


class MemoryValidator:
    """
    Deterministic validator for MemoryItem objects.
    """

    def validate_memory(self, item: MemoryItem) -> Tuple[bool, List[str]]:
        """
        Validates MemoryItem integrity and security invariants.
        Returns (valid, errors).
        """
        errors: List[str] = []

        # ── 1. Mandatory Fields Check ──────────────────────────────────────
        if not item.title or len(item.title.strip()) < 3:
            errors.append("MemoryItem 'title' must be non-empty (at least 3 characters).")

        if not item.content or len(item.content.strip()) < 3:
            errors.append("MemoryItem 'content' must be non-empty (at least 3 characters).")

        if not item.scope_id or not item.scope_id.strip():
            errors.append("MemoryItem 'scope_id' must be specified.")

        # ── 2. Security & Privacy Invariants Check ────────────────────────
        if self._contains_secrets(item.content):
            errors.append("MemoryItem 'content' contains prohibited secret keys or reasoning traces.")

        if self._contains_secrets_dict(item.metadata):
            errors.append("MemoryItem 'metadata' contains prohibited secret keys or reasoning traces.")

        # ── 3. ArtifactReference Integrity Check ──────────────────────────
        for ref in item.artifact_references:
            if not ref.artifact_id or not ref.artifact_type:
                errors.append("ArtifactReference in MemoryItem must declare artifact_id and artifact_type.")

        valid = len(errors) == 0
        return valid, errors

    def _contains_secrets(self, text: str) -> bool:
        """Checks if text contains secret key patterns or CoT blocks."""
        lower = text.lower()
        return any(p_key in lower for p_key in PROHIBITED_KEYS)

    def _contains_secrets_dict(self, data: Dict[str, Any]) -> bool:
        """Checks if dictionary contains prohibited secret keys."""
        for k, v in data.items():
            if any(p_key in k.lower() for p_key in PROHIBITED_KEYS):
                return True
            if isinstance(v, dict) and self._contains_secrets_dict(v):
                return True
            if isinstance(v, str) and self._contains_secrets(v):
                return True
        return False
