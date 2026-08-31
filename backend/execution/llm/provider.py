import json
import re
from typing import Dict, Any, Optional
from core.groq_engine import engine_manager
from core.logger import logger


class LLMProvider:
    """
    Abstraction layer over the Groq engine manager.
    Routes LLM calls to the team-specific API key pool when team_id is provided,
    ensuring that no single team can exhaust the entire organization's rate limits.
    """

    @staticmethod
    async def generate_json(
        system_prompt: str,
        user_prompt: str,
        model: str = "openai/gpt-oss-120b",
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calls the LLM via the team-aware engine manager and parses the response as JSON.

        Args:
            system_prompt: The agent's system instructions.
            user_prompt:   The user/task input.
            model:         The Groq model to use.
            team_id:       Optional team identifier for dedicated API key pool routing.
                           Falls back to the global key pool if None or unknown.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Enforce JSON output requirement in the system prompt if not explicitly present
        if "json" not in system_prompt.lower():
            messages[0]["content"] += "\n\nYou MUST respond with ONLY valid JSON."
            
        messages[0]["content"] += (
            "\n\nCRITICAL: DO NOT use tool calls or function calling syntax. "
            "DO NOT wrap your JSON in `{\"name\": \"answer\", \"arguments\": {...}}`. "
            "Output the required JSON schema directly at the root level."
        )

        logger.debug(
            f"LLMProvider.generate_json | team={team_id or 'default'} | model={model}"
        )

        try:
            response = await engine_manager.chat_completion(
                model=model,
                messages=messages,
                temperature=0.4,
                max_tokens=1500,
                response_format={"type": "json_object"},
                team_id=team_id,
            )
            raw_original = response.choices[0].message.content or ""
            
            # Remove any thinking blocks if the model supports it
            raw = re.sub(r"<think>.*?</think>", "", raw_original, flags=re.DOTALL).strip()
            
            if not raw:
                logger.warning(f"Raw response became empty after stripping <think> tags. Original: {raw_original}")

            # Extract JSON
            json_match = re.search(r"\{.*\}", raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(raw)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON. Raw response: {raw}")
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"LLM Provider execution failed: {e}")
            raise
