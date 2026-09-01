"""
LLM client abstraction.

Model provider/name as configuration. Tracks token usage. Graceful failure:
if LLM unavailable, deterministic result preserved, event stays in WATCH.
Never invents results.
"""

from __future__ import annotations

from typing import Optional

from loguru import logger

from ..config import MonitorConfig

# Try to import Groq; it's the default but not hard-required
try:
    from groq import AsyncGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logger.info("groq package not installed — LLM analysis disabled")


class LLMClient:
    """Abstracted LLM client. Provider/model configurable via env vars."""

    def __init__(self, config: MonitorConfig):
        self.config = config
        self.provider = config.llm_provider
        self.model = config.llm_model
        self.max_tokens = config.llm_max_tokens
        self.temperature = config.llm_temperature
        self._client: object | None = None

        # Token tracking
        self.total_calls: int = 0
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_failures: int = 0

    @property
    def is_available(self) -> bool:
        """Check if LLM is configured and usable."""
        if self.provider == "groq":
            return HAS_GROQ and bool(self.config.llm_api_key)
        return False

    async def complete(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Send a completion request to the LLM.

        Returns the response text, or None on failure.
        Never raises — all errors are caught and logged.
        """
        if not self.is_available:
            logger.debug("LLM not available — skipping analysis")
            return None

        try:
            if self.provider == "groq":
                return await self._complete_groq(system_prompt, user_prompt)
            else:
                logger.warning(f"Unsupported LLM provider: {self.provider}")
                return None

        except Exception as e:
            self.total_failures += 1
            logger.warning(f"LLM call failed: {e}")
            return None

    async def _complete_groq(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Make a completion request to Groq."""
        if not HAS_GROQ:
            return None

        api_key = self.config.llm_api_key
        if not api_key:
            return None

        client = AsyncGroq(api_key=api_key)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            self.total_calls += 1

            # Track tokens
            usage = response.usage
            if usage:
                self.total_prompt_tokens += usage.prompt_tokens or 0
                self.total_completion_tokens += usage.completion_tokens or 0

            choice = response.choices[0] if response.choices else None
            return choice.message.content if choice and choice.message else None

        except Exception as e:
            self.total_failures += 1
            logger.warning(f"Groq API error: {e}")

            # Try fallback key
            fallback_key = self.config.llm_api_key_fallback
            if fallback_key and fallback_key != api_key:
                try:
                    fallback_client = AsyncGroq(api_key=fallback_key)
                    response = await fallback_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                    )
                    self.total_calls += 1
                    choice = response.choices[0] if response.choices else None
                    return choice.message.content if choice and choice.message else None
                except Exception as e2:
                    logger.warning(f"Groq fallback also failed: {e2}")

            return None

    @property
    def estimated_total_tokens(self) -> int:
        """Total estimated tokens consumed."""
        return self.total_prompt_tokens + self.total_completion_tokens
