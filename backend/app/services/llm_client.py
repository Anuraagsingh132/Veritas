import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Robust LLM interface with support for Groq (Llama 3.3 70B & 8B),
    automatic retry, rate limit backoff, and JSON validation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.model = model or settings.DEFAULT_MODEL
        self.fallback_model = settings.FALLBACK_MODEL
        self._client = None
        
        if self.api_key and self.api_key.strip() and self.api_key != "your_groq_api_key_here":
            try:
                self._client = Groq(api_key=self.api_key)
                logger.info("Groq client initialized with model: %s", self.model)
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s", e)
                self._client = None
        else:
            logger.info("No Groq API key configured. Offline/curated reasoning engine will be used.")

    def is_available(self) -> bool:
        return self._client is not None

    def chat_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Calls LLM expecting structured JSON response.
        Implements exponential backoff on rate limits.
        """
        if not self._client:
            raise RuntimeError("Groq API client is not configured. Please supply GROQ_API_KEY.")

        models_to_try = [self.model, self.fallback_model]
        last_exception = None

        for current_model in models_to_try:
            for attempt in range(3):
                try:
                    logger.info(f"Calling LLM ({current_model}), attempt {attempt + 1}")
                    response = self._client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": system_prompt + "\nIMPORTANT: You must reply with VALID JSON ONLY. No preamble, no markdown backticks outside json."},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    raw_content = response.choices[0].message.content.strip()
                    
                    # Clean up backticks if any were included
                    if raw_content.startswith("```json"):
                        raw_content = raw_content[7:]
                    if raw_content.startswith("```"):
                        raw_content = raw_content[3:]
                    if raw_content.endswith("```"):
                        raw_content = raw_content[:-3]
                    raw_content = raw_content.strip()

                    parsed = json.loads(raw_content)
                    return parsed

                except Exception as e:
                    last_exception = e
                    err_str = str(e).lower()
                    if "rate limit" in err_str or "429" in err_str:
                        wait_time = (attempt + 1) * 3
                        logger.warning(f"Rate limit hit on {current_model}. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.warning(f"Error calling {current_model}: {e}")
                        break  # Try fallback model

        logger.error(f"LLM call failed after retries: {last_exception}")
        raise last_exception or RuntimeError("LLM request failed.")

    def set_api_key(self, api_key: str):
        """Allows dynamically updating API key at runtime via UI or API."""
        self.api_key = api_key
        if api_key and api_key.strip():
            self._client = Groq(api_key=api_key)
            logger.info("Groq client re-initialized with new key.")
        else:
            self._client = None

# Global shared singleton
shared_llm_client = LLMClient()
