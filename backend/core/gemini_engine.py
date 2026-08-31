import logging
from typing import List, Dict, Any

import google.generativeai as genai
from core.config import settings

logger = logging.getLogger(__name__)

# Configure the API key once on load
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
else:
    logger.warning("[GeminiEngine] GEMINI_API_KEY is not set. Calls will fail.")

class MockMessage:
    def __init__(self, content: str):
        self.content = content

class MockChoice:
    def __init__(self, message: MockMessage):
        self.message = message

class MockResponse:
    def __init__(self, choices: List[MockChoice]):
        self.choices = choices

class GeminiEngineManager:
    """Drop-in replacement for GroqEngineManager using Gemini."""

    def __init__(self):
        # Use smallest available model to avoid quota exhaustion
        self.default_model = "gemini-flash-lite-latest"

    async def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 512,
        **kwargs
    ) -> MockResponse:
        
        system_instruction = None
        history = []
        
        # Parse OpenAI-style messages into Gemini format
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                # If there are multiple system messages, append them
                if system_instruction:
                    system_instruction += "\n" + content
                else:
                    system_instruction = content
            elif role == "user":
                history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                history.append({"role": "model", "parts": [content]})

        # If it's a multimodal request (STT) passed directly via a custom param, handle it
        multimodal_contents = kwargs.get("gemini_contents", None)

        # Build model configuration
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        keys_to_try = [k for k in [settings.gemini_api_key, settings.gemini_api_key_2] if k]
        if not keys_to_try:
            logger.warning("[GeminiEngine] No API keys configured. Calls will fail.")
            keys_to_try = [""]

        # Always prefer smallest/cheapest models first to avoid quota exhaustion
        # gemini-flash-lite-latest -> gemini-flash-latest -> gemini-3.5-flash-lite -> gemini-3.6-flash
        models_to_try = []
        if model and model != self.default_model:
            # Map any large model references to lite equivalents
            if "pro" in model:
                model = "gemini-flash-lite-latest"  # downgrade pro -> lite
            elif "3.6" in model or "3.5" in model or "3.1" in model:
                model = "gemini-flash-lite-latest"
            elif "1.5" in model or "2.5" in model:
                model = "gemini-flash-lite-latest"
            models_to_try.append(model)
            
        # Fallback chain: smallest -> slightly bigger -> biggest
        models_to_try.append("gemini-flash-lite-latest")
        models_to_try.append("gemini-flash-latest")
        models_to_try.append("gemini-3.5-flash-lite")
        models_to_try.append("gemini-3.6-flash")
        
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = None
        for key in keys_to_try:
            if key:
                genai.configure(api_key=key)
                
            for current_model in models_to_try:
                try:
                    logger.info(f"[GeminiEngine] Attempting generation with key ending in ...{key[-4:] if len(key)>4 else key} and model {current_model}")
                    gemini_model = genai.GenerativeModel(
                        model_name=current_model,
                        system_instruction=system_instruction
                    )
                    
                    if multimodal_contents:
                        response = await gemini_model.generate_content_async(
                            multimodal_contents,
                            generation_config=generation_config
                        )
                    else:
                        chat = gemini_model.start_chat(history=history[:-1] if len(history) > 0 else [])
                        last_msg = history[-1]["parts"][0] if len(history) > 0 else ""
                        response = await chat.send_message_async(
                            last_msg,
                            generation_config=generation_config
                        )
                        
                    result_text = response.text
                    
                    # Mock the Groq/OpenAI response structure
                    return MockResponse([
                        MockChoice(MockMessage(result_text))
                    ])
                    
                except Exception as e:
                    logger.warning(f"[GeminiEngine] API call failed with model {current_model} and key ...{key[-4:] if len(key)>4 else key}: {e}")
                    last_error = e
                    # If it's a rate limit, maybe we should break model loop and try next key
                    if "429" in str(e) or "quota" in str(e).lower():
                        break # Go to next key
                    
        # If we exhausted everything
        logger.error(f"[GeminiEngine] All fallback models and keys failed. Last error: {last_error}")
        raise last_error or Exception("Gemini API completely failed.")

# Singleton instance
engine_manager = GeminiEngineManager()
