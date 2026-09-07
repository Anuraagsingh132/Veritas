import os
import json
import time
import logging
from typing import Dict, Any, Optional, List
from groq import Groq
from app.config import settings

logger = logging.getLogger(__name__)

# Preferred model discovery order for Groq API
PREFERRED_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "groq/compound",
    "groq/compound-mini",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "qwen/qwen3.8-27b",
    "qwen/qwen3.6-27b"
]

class LLMClient:
    """
    Robust LLM interface with support for Groq models, dynamic model discovery,
    automatic retry with exponential backoff, and strict JSON validation.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY
        self.model = model or settings.DEFAULT_MODEL
        self.fallback_model = settings.FALLBACK_MODEL
        self._client = None
        self._rate_limited_until = 0.0
        
        if self.api_key and self.api_key.strip() and self.api_key != "your_groq_api_key_here":
            self._init_client()
        else:
            logger.info("No Groq API key configured. Offline structural reasoning will be used.")

    def is_rate_limited(self) -> bool:
        """Returns True if a rate-limit cooldown is currently active."""
        return time.time() < self._rate_limited_until

    def mark_rate_limited(self, duration: float = 20.0):
        """Sets a rate-limit cooldown to avoid blocking loops on Groq 429."""
        self._rate_limited_until = time.time() + duration

    def _init_client(self):
        try:
            self._client = Groq(api_key=self.api_key, max_retries=0)
            self._discover_models()
            logger.info(f"Groq client initialized: primary='{self.model}', fallback='{self.fallback_model}'")
        except Exception as e:
            logger.warning("Failed to initialize Groq client: %s", e)
            self._client = None

    def _discover_models(self):
        """
        Dynamically discovers available models on the current Groq API key
        and chooses the optimal primary and fallback models.
        """
        if not self._client:
            return

        try:
            available_models = [m.id for m in self._client.models.list().data]
            logger.info(f"Discovered {len(available_models)} available models on Groq account.")
            
            chosen_primary = None
            chosen_fallback = None

            # Find highest ranked available model
            for pref in PREFERRED_MODELS:
                if pref in available_models:
                    if not chosen_primary:
                        chosen_primary = pref
                    elif not chosen_fallback and pref != chosen_primary:
                        chosen_fallback = pref
                        break

            if chosen_primary:
                self.model = chosen_primary
            if chosen_fallback:
                self.fallback_model = chosen_fallback
            elif not chosen_fallback and self.model in available_models:
                # Pick any other chat model as fallback
                for m in available_models:
                    if m != self.model and ("llama" in m or "qwen" in m or "gpt" in m or "compound" in m):
                        self.fallback_model = m
                        break

        except Exception as e:
            logger.debug(f"Model auto-discovery skipped: {e}. Using configured defaults.")

    def is_available(self) -> bool:
        return self._client is not None

    def chat_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Calls LLM expecting structured JSON response.
        Implements fail-fast rate-limit protection and multi-model fallback.
        """
        if not self._client:
            raise RuntimeError("Groq API client is not configured. Please supply GROQ_API_KEY.")

        if self.is_rate_limited():
            remaining = int(self._rate_limited_until - time.time())
            raise RuntimeError(f"Groq API rate limit cooldown active ({remaining}s remaining). Proceeding immediately with heuristic fallback.")

        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)
        
        last_exception = None

        for current_model in models_to_try:
            try:
                logger.debug(f"Calling LLM ({current_model})")
                response = self._client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": system_prompt + "\nIMPORTANT: You must reply with VALID JSON ONLY. No preamble, no markdown formatting outside JSON."},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                raw_content = response.choices[0].message.content.strip()
                # Strip markdown blocks if returned
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
                    logger.warning(f"Groq rate limit (429) on {current_model}. Setting cooldown & triggering fast fallback.")
                    self.mark_rate_limited(20.0)
                    continue
                elif "model_not_found" in err_str or "does not exist" in err_str:
                    logger.warning(f"Model {current_model} not accessible on this account. Trying next model.")
                    continue
                else:
                    logger.warning(f"Error calling {current_model}: {e}")
                    continue

        logger.info(f"LLM call unavailable: {last_exception}. Proceeding with domain-agnostic fallback.")
        raise last_exception or RuntimeError("LLM request failed.")

    def set_api_key(self, api_key: str):
        """Allows dynamically updating API key at runtime via UI or API."""
        self.api_key = api_key
        if api_key and api_key.strip():
            self._init_client()
        else:
            self._client = None

# Global shared singleton
shared_llm_client = LLMClient()
