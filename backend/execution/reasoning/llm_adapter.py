from typing import Type, TypeVar, Any, Dict, Optional
import json
from pydantic import BaseModel, ValidationError
from execution.llm.provider import LLMProvider
from core.logger import logger

T = TypeVar('T', bound=BaseModel)


class LLMReasoner:
    """
    Adapter that ensures LLM reasoning outputs conform to structured Pydantic models.
    Passes team_id through to LLMProvider for team-level API key routing.
    Supports bounded retry if the LLM generates invalid schemas.
    """

    def __init__(self, max_retries: int = 3, team_id: Optional[str] = None):
        self.max_retries = max_retries
        self.team_id = team_id

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generates reasoning and validates it against the response_model.
        Routes the LLM call to the team-specific key pool.
        """
        schema_json = response_model.schema_json()
        augmented_system = (
            f"{system_prompt}\n\n"
            f"You MUST respond with a valid JSON object containing the ACTUAL DATA that matches the schema below.\n"
            f"CRITICAL: DO NOT output the schema itself. ONLY output a JSON instance that satisfies it.\n"
            f"Schema:\n{schema_json}"
        )

        last_error = None
        for attempt in range(self.max_retries):
            try:
                raw_dict = await LLMProvider.generate_json(
                    augmented_system,
                    user_prompt,
                    team_id=self.team_id,
                )

                validated_obj = response_model(**raw_dict)
                return validated_obj

            except ValidationError as e:
                logger.warning(
                    f"[LLMReasoner|team={self.team_id}] "
                    f"Attempt {attempt + 1}: schema validation failed. {e}"
                )
                last_error = e
                user_prompt += (
                    f"\n\nYour last response failed schema validation:\n{e}\n"
                    f"Please fix it and return valid JSON."
                )
            except Exception as e:
                logger.warning(
                    f"[LLMReasoner|team={self.team_id}] "
                    f"Attempt {attempt + 1}: generation failed. {e}"
                )
                last_error = e

        raise ValueError(
            f"Failed to generate valid structured reasoning after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )
