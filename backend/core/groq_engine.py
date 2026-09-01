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
    On rate-limit (429), it instantly routes to the next healthy key in the pool,
    tracking cooldowns per key to avoid blocking.
    """

    def __init__(self, keys: List[str], team_id: str = "default"):
        import time
        self.team_id = team_id
        self.keys = [k.strip() for k in keys if k.strip()]

        if not self.keys:
            logger.warning(f"[GroqEngine:{team_id}] No API keys configured. Calls will fail.")
            self.clients: List[dict] = []
        else:
            self.clients = [
                {
                    "client": AsyncGroq(api_key=key),
                    "cooldown_until": 0.0,
                    "key_preview": f"{key[:8]}..."
                }
                for key in self.keys
            ]
            logger.info(f"[GroqEngine:{team_id}] Initialized with {len(self.clients)} key(s).")

    async def _get_healthy_client(self) -> dict:
        import time
        import random
        if not self.clients:
            raise ValueError(f"No Groq API keys available for team '{self.team_id}'.")
            
        now = time.time()
        
        # 1. Find all healthy clients (cooldown expired)
        healthy = [c for c in self.clients if c["cooldown_until"] <= now]
        if healthy:
            # SCATTER TRAFFIC: Pick a random healthy key to avoid hammering the same key concurrently
            return random.choice(healthy)
            
        # 2. If ALL clients are on cooldown, find the one that expires soonest
        soonest = min(self.clients, key=lambda c: c["cooldown_until"])
        wait_time = soonest["cooldown_until"] - now
        if wait_time > 0:
            logger.warning(f"[GroqEngine:{self.team_id}] EXTREME LOAD: All {len(self.clients)} keys on cooldown. Sleeping {wait_time:.1f}s.")
            await asyncio.sleep(wait_time)
            
        return soonest

    async def chat_completion(self, model: str, messages: list, **kwargs):
        """
        Execute a chat completion with instant zero-block key rotation on rate limits.
        """
        import re
        import time
        attempts = 0
        max_attempts = 100 # Extremely high so we can cycle through 25+ keys multiple times if needed

        while attempts < max_attempts:
            client_dict = await self._get_healthy_client()
            client = client_dict["client"]
            
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
                        wait_time = float(wait_match.group(1)) + 1.0
                    else:
                        wait_time = 10.0
                        
                    # Mark THIS specific key on cooldown
                    client_dict["cooldown_until"] = time.time() + wait_time
                    logger.warning(
                        f"[GroqEngine:{self.team_id}] Key {client_dict['key_preview']} Rate Limited (429). Benched for {wait_time:.1f}s. (Attempt {attempts+1})"
                    )
                    
                    # IMMEDIATELY continue to next iteration which will pick the next healthy key!
                    attempts += 1
                    continue
                    
                elif status_code in (401, 403):
                    logger.warning(f"[GroqEngine:{self.team_id}] Key {client_dict['key_preview']} Auth error ({status_code}): {e}")
                    # Bench it for a very long time so we don't keep trying dead keys
                    client_dict["cooldown_until"] = time.time() + 86400 
                    attempts += 1
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"[GroqEngine:{self.team_id}] Unexpected error: {e}")
                raise

        raise RuntimeError(
            f"[GroqEngine:{self.team_id}] Exhausted {max_attempts} attempts across {len(self.clients)} key(s)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Team → Env-var Key Mapping
# ─────────────────────────────────────────────────────────────────────────────

_TEAM_KEY_MAP: Dict[str, str] = {
    # Executive Team
    "atlas":       "groq_api_key_atlas",
    "maya":        "groq_api_key_maya",
    
    # Architecture Team
    "ethan":       "groq_api_key_ethan",
    "priya":       "groq_api_key_priya",
    "rohan":       "groq_api_key_rohan",
    
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
    
    # Resilience Agents
    "arjun":       "groq_api_key_arjun",
    "ishaan":      "groq_api_key_ishaan",
    "leena":       "groq_api_key_leena",
    "zoya":        "groq_api_key_zoya",
    # Council Agents
    "helena":      "groq_api_key_helena",
    "vikram":      "groq_api_key_vikram",
    "nisha":       "groq_api_key_nisha",
    "omar":        "groq_api_key_omar",
    "sofia":       "groq_api_key_sofia",
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
        global_keys = []
        if getattr(settings, "groq_extreme_pool", None):
            global_keys.extend(_parse_keys(settings.groq_extreme_pool))
        else:
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
                
        # Global Concurrency Queue (Semaphore)
        self._async_semaphore: Optional[asyncio.Semaphore] = None

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
        """Convenience passthrough that resolves the engine by team_id and applies global rate limiting."""
        if self._async_semaphore is None:
            self._async_semaphore = asyncio.Semaphore(settings.groq_max_concurrency)
            
        engine = self.get_engine(team_id)
        
        async with self._async_semaphore:
            return await engine.chat_completion(model=model, messages=messages, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

engine_manager = GroqEngineManager()

# Backward-compat alias — existing code that imported `groq_engine` will still work
groq_engine = engine_manager.get_engine("default")
