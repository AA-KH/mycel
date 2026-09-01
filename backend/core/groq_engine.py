"""
Groq LLM Engine — Team-Level API Key Routing

Architecture:
- RobustGroqClient: wraps a specific pool of API keys with failover rotation.
- GroqEngineManager: constructs and manages one RobustGroqClient per team.
- Teams that do not have dedicated keys fall back to the global key pool.
- get_engine(team_id) is the primary entry point for all callers.
"""

import asyncio
import logging
from typing import Dict, List, Optional

from groq import AsyncGroq, APIStatusError, RateLimitError

from core.config import settings

logger = logging.getLogger(__name__)


class RobustGroqClient:
    """
    A failover-capable Groq client wrapping a pool of API keys.
    On rate-limit (429) or quota errors, it rotates to the next key
    in its pool automatically.
    """

    def __init__(self, keys: List[str], team_id: str = "default"):
        self.team_id = team_id
        self.keys = [k.strip() for k in keys if k.strip()]

        if not self.keys:
            logger.warning(f"[GroqEngine:{team_id}] No API keys configured. Calls will fail.")
            self.clients: List[AsyncGroq] = []
        else:
            self.clients = [AsyncGroq(api_key=key) for key in self.keys]
            logger.info(f"[GroqEngine:{team_id}] Initialized with {len(self.clients)} key(s).")

        self._current_idx = 0

    def _get_client(self) -> AsyncGroq:
        if not self.clients:
            raise ValueError(f"No Groq API keys available for team '{self.team_id}'.")
        return self.clients[self._current_idx]

    def _rotate_client(self) -> bool:
        if len(self.clients) > 1:
            self._current_idx = (self._current_idx + 1) % len(self.clients)
            logger.info(f"[GroqEngine:{self.team_id}] Rotated to key index {self._current_idx}.")
            return True
        return False

    async def chat_completion(self, model: str, messages: list, **kwargs):
        """
        Execute a chat completion with automatic key-rotation on rate limits.
        Tries every key in the pool before giving up.
        """
        import re
        attempts = 0
        max_attempts = 10  # Increased to guarantee output by waiting out limits

        while attempts < max_attempts:
            client = self._get_client()
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                return response

            except (RateLimitError, APIStatusError) as e:
                status_code = getattr(e, "status_code", None)
                if status_code == 429:
                    error_msg = str(e)
                    # Try to parse "Please try again in 8.879s"
                    wait_match = re.search(r"try again in (\d+\.?\d*)s", error_msg)
                    if wait_match:
                        wait_time = float(wait_match.group(1)) + 1.0  # 1s buffer
                    else:
                        wait_time = 10.0 # Default fallback
                        
                    logger.warning(
                        f"[GroqEngine:{self.team_id}] Rate Limit 429 hit. Waiting {wait_time:.1f}s before retry... (Attempt {attempts+1}/{max_attempts})"
                    )
                    
                    # Try to rotate key if we have multiple, otherwise just sleep on current key
                    if len(self.clients) > 1:
                        self._rotate_client()
                        
                    await asyncio.sleep(wait_time)
                elif status_code in (401, 403):
                    logger.warning(
                        f"[GroqEngine:{self.team_id}] Key {self._current_idx} Auth error ({status_code}): {e}"
                    )
                    can_rotate = self._rotate_client()
                    if not can_rotate:
                        raise e # No other keys to try
                else:
                    raise
            except Exception as e:
                logger.error(f"[GroqEngine:{self.team_id}] Unexpected error: {e}")
                raise

            attempts += 1

        raise RuntimeError(
            f"[GroqEngine:{self.team_id}] All {len(self.clients)} key(s) exhausted after {attempts} attempts."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Team → Env-var Key Mapping
# ─────────────────────────────────────────────────────────────────────────────

_TEAM_KEY_MAP: Dict[str, str] = {
    "creative":    "groq_creative_keys",
    "engineering": "groq_engineering_keys",
    "operations":  "groq_operations_keys",
    "sales":       "groq_sales_keys",
    "hr":          "groq_hr_keys",
    "research":    "groq_research_keys",
    "marketing":   "groq_marketing_keys",
    
    # Intelligence Agents
    "mira":        "groq_api_key_mira",
    "ravi":        "groq_api_key_ravi",
    "anika":       "groq_api_key_anika",
    "noor":        "groq_api_key_noor",
    
    # Network Agents
    "aanya":       "groq_api_key_aanya",
    "dev":         "groq_api_key_dev",
    "kabir":       "groq_api_key_kabir",
    "tara":        "groq_api_key_tara",
}


def _parse_keys(raw: str) -> List[str]:
    """Split a comma-separated key string into a clean list."""
    return [k.strip() for k in raw.split(",") if k.strip()]


class GroqEngineManager:
    """
    Manages a pool of RobustGroqClient instances, one per team.

    Lookup order for a given team_id:
      1. Team-specific keys from the team's env-var key pool.
      2. Global fallback keys (groq_api_key_1 / groq_api_key_2).

    All clients are initialized once at startup; no per-request allocation.
    """

    def __init__(self):
        # Build the default / global client
        global_keys = [k for k in [settings.groq_api_key_1, settings.groq_api_key_2, settings.groq_api_key] if k]
        self._default = RobustGroqClient(keys=global_keys, team_id="default")

        # Build per-team clients, falling back to the global pool if no keys are set
        self._team_engines: Dict[str, RobustGroqClient] = {}
        for team_id, attr_name in _TEAM_KEY_MAP.items():
            raw_keys = getattr(settings, attr_name, "")
            team_keys = _parse_keys(raw_keys)
            if team_keys:
                self._team_engines[team_id] = RobustGroqClient(keys=team_keys, team_id=team_id)
                logger.info(f"[GroqEngineManager] Team '{team_id}' → {len(team_keys)} dedicated key(s).")
            else:
                logger.info(f"[GroqEngineManager] Team '{team_id}' → using global fallback pool.")

    def get_engine(self, team_id: Optional[str] = None) -> RobustGroqClient:
        """
        Returns the most specific RobustGroqClient for the given team_id.

        Falls back to the default global engine if no team-specific keys exist.
        """
        if team_id and team_id in self._team_engines:
            return self._team_engines[team_id]
        return self._default

    async def chat_completion(
        self,
        model: str,
        messages: list,
        team_id: Optional[str] = None,
        **kwargs,
    ):
        """Convenience passthrough that resolves the engine by team_id."""
        engine = self.get_engine(team_id)
        return await engine.chat_completion(model=model, messages=messages, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

engine_manager = GroqEngineManager()

# Backward-compat alias — existing code that imported `groq_engine` will still work
groq_engine = engine_manager.get_engine("default")
