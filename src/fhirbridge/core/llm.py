"""
Canonical LLM Retry Client for FhirBridgeAI.

Provides a robust, Pydantic-configured client for interacting with local
Ollama/Mistral instances. Implements exponential backoff, structured output
validation, and self-correction loops.

Usage:
    from integrating_local_llms.scripts.llm_retry_client import (
        LlmRetryClient, LlmConfig, LlmValidationError, LlmConnectionError,
    )

    client = LlmRetryClient()
    result = client.generate_structured(
        prompt="Extrahiere die Diagnosen aus folgendem Text: ...",
        schema=MyPydanticModel,
    )
"""

from __future__ import annotations

import json
import logging
import os
from typing import TypeVar

import httpx
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, ValidationError
from tenacity import (
    AsyncRetrying,
    before_sleep_log,
    retry_if_exception_type,
    stop_after_attempt,
    wait_none,
)

LLM_GENERATION_DURATION = Histogram(
    "llm_generation_duration_seconds", "Time spent generating a response from the LLM endpoint"
)

LLM_VALIDATION_ERRORS = Counter(
    "llm_validation_errors_total",
    "Number of Pydantic validation errors during structured generation",
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Custom Error Classes
# ---------------------------------------------------------------------------


class LlmValidationError(Exception):
    """Raised when the LLM output cannot be validated against the target
    Pydantic schema after all retries are exhausted.

    Attributes:
        last_raw_output: The raw string the LLM returned on its final attempt.
        validation_errors: The Pydantic ``ValidationError`` from the last attempt.
    """

    def __init__(
        self,
        message: str,
        last_raw_output: str = "",
        validation_errors: ValidationError | None = None,
    ) -> None:
        super().__init__(message)
        self.last_raw_output = last_raw_output
        self.validation_errors = validation_errors


class LlmConnectionError(Exception):
    """Raised when the Ollama endpoint is unreachable after all retries.

    Attributes:
        attempts: Number of connection attempts made before giving up.
    """

    def __init__(self, message: str, attempts: int = 0) -> None:
        super().__init__(message)
        self.attempts = attempts


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


class LlmConfig(BaseModel):
    """Typed, documented configuration for the LLM client.

    All defaults are explicit — no magic numbers. Override via constructor
    kwargs or environment variables (``OLLAMA_URL``, ``LLM_MODEL``).
    """

    base_url: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        description="Base URL of the Ollama REST API (without trailing path).",
    )
    model: str = Field(
        default_factory=lambda: os.getenv("LLM_MODEL", "mistral-nemo"),
        description="Ollama model tag to use for generation.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description=(
            "Sampling temperature. Low values (0.1) for deterministic extraction, "
            "higher values (0.7+) for creative text generation."
        ),
    )
    max_tokens: int = Field(
        default=2048,
        gt=0,
        description="Maximum number of tokens the model should predict per request.",
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of retry attempts for validation or connection errors.",
    )
    initial_backoff_seconds: float = Field(
        default=1.0,
        gt=0.0,
        description="Initial delay (in seconds) before the first retry. Doubles on each subsequent attempt.",
    )
    request_timeout_seconds: float = Field(
        default=180.0,
        gt=0.0,
        description="HTTP request timeout (in seconds) for a single Ollama call.",
    )
    inference_engine: str = Field(
        default_factory=lambda: os.getenv("INFERENCE_ENGINE", "ollama"),
        description="Engine to use: 'ollama' or 'vllm'. 'vllm' uses OpenAI compatible endpoints.",
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class LlmRetryClient:
    """Enterprise-grade client for local LLM structured generation.

    Wraps the Ollama ``/api/generate`` and ``/api/chat`` endpoints with:
    - **Pydantic validation loop**: on schema mismatch the error is fed back
      to the model for self-correction.
    - **Exponential backoff**: ``initial_backoff * 2^attempt`` on connection
      or timeout errors.
    """

    def __init__(self, config: LlmConfig | None = None) -> None:
        self.config = config or LlmConfig()
        base_url = self.config.base_url.rstrip("/")
        if self.config.inference_engine == "vllm":
            if "/v1" not in base_url:
                base_url += "/v1"
            self._generate_url = base_url + "/completions"
            self._chat_url = base_url + "/chat/completions"
        else:
            self._generate_url = base_url + "/api/generate"
            self._chat_url = base_url + "/api/chat"

        logger.debug(
            "LlmRetryClient initialised — engine=%s, model=%s, max_retries=%d",
            self.config.inference_engine,
            self.config.model,
            self.config.max_retries,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @LLM_GENERATION_DURATION.time()
    async def generate_text(self, prompt: str, system_context: str = "") -> str:
        """Generate basic free-form text output (no Pydantic validation).

        Uses ``/api/generate`` and applies exponential backoff for HTTP errors.
        """
        prompt_text = prompt
        if system_context:
            prompt_text = f"{system_context}\n\n{prompt}"

        if self.config.inference_engine == "vllm":
            payload = {
                "model": self.config.model,
                "prompt": prompt_text,
                "stream": False,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }
        else:
            payload = {
                "model": self.config.model,
                "prompt": prompt_text,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            }
        return await self._execute_http_with_backoff(self._generate_url, payload)

    @LLM_GENERATION_DURATION.time()
    async def generate_structured(
        self, prompt: str, schema: type[T], system_context: str = ""
    ) -> T:
        """Generate a structured response matching ``schema`` using ``/api/generate``.

        Raises:
            LlmValidationError: If output fails schema validation after retries.
            LlmConnectionError: If Ollama is unreachable.
        """
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        prompt_text = self._build_initial_prompt(prompt, schema_json, system_context)

        last_validation_error: ValidationError | None = None

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_none(),
            retry=retry_if_exception_type(LlmValidationError),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.WARNING),
        ):
            with attempt:
                if self.config.inference_engine == "vllm":
                    payload = {
                        "model": self.config.model,
                        "prompt": prompt_text,
                        "stream": False,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "response_format": {"type": "json_object"},
                    }
                else:
                    payload = {
                        "model": self.config.model,
                        "prompt": prompt_text,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens,
                        },
                    }

                raw_output = await self._execute_http_with_backoff(self._generate_url, payload)

                try:
                    result = schema.model_validate_json(raw_output)
                    return result
                except (ValidationError, json.JSONDecodeError) as exc:
                    LLM_VALIDATION_ERRORS.inc()
                    last_validation_error = exc if isinstance(exc, ValidationError) else None
                    logger.warning("Validation failed on attempt %s", str(exc)[:200])
                    prompt_text += (
                        f"\n\nFEHLER: Dein letztes JSON verletzte das Schema:\n{str(exc)}\n\n"
                        f"Inkorrektes JSON:\n{raw_output}\n\n"
                        "Fix this JSON error."
                    )
                    raise LlmValidationError(
                        f"LLM output failed schema validation for {schema.__name__} after retries.",
                        last_raw_output=raw_output,
                        validation_errors=last_validation_error,
                    ) from exc

    @LLM_GENERATION_DURATION.time()
    async def chat_structured(self, messages: list[dict[str, str]], schema: type[T]) -> T:
        """Generate a structured response across a stateful conversation using ``/api/chat``.

        The schema constraint is expected to be part of the initial messages array by the caller.
        """
        chat_messages = list(messages)  # Clone list
        last_validation_error: ValidationError | None = None

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_none(),
            retry=retry_if_exception_type(LlmValidationError),
            reraise=True,
            before_sleep=before_sleep_log(logger, logging.WARNING),
        ):
            with attempt:
                if self.config.inference_engine == "vllm":
                    payload = {
                        "model": self.config.model,
                        "messages": chat_messages,
                        "stream": False,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "response_format": {"type": "json_object"},
                    }
                else:
                    payload = {
                        "model": self.config.model,
                        "messages": chat_messages,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": self.config.temperature,
                            "num_predict": self.config.max_tokens,
                        },
                    }
                raw_output = await self._execute_http_with_backoff(self._chat_url, payload)

                if not raw_output:
                    chat_messages.append(
                        {
                            "role": "user",
                            "content": "Fehler: Leere Antwort erhalten. Bitte JSON generieren.",
                        }
                    )
                    raise LlmValidationError("Empty response from LLM")

                try:
                    result = schema.model_validate_json(raw_output)
                    return result
                except (ValidationError, json.JSONDecodeError) as exc:
                    LLM_VALIDATION_ERRORS.inc()
                    last_validation_error = exc if isinstance(exc, ValidationError) else None
                    logger.warning("Validation failed on attempt %s", str(exc)[:200])
                    chat_messages.append({"role": "assistant", "content": raw_output})
                    chat_messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"FEHLER: Dein letztes JSON verletzte das Schema:\n{str(exc)}\n\n"
                                f"Inkorrektes JSON:\n{raw_output}\n\n"
                                "Fix this JSON error."
                            ),
                        }
                    )
                    raise LlmValidationError(
                        f"LLM output failed schema validation for {schema.__name__} after retries.",
                        last_raw_output=raw_output,
                        validation_errors=last_validation_error,
                    ) from exc

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _execute_http_with_backoff(self, url: str, payload: dict) -> str:
        """Executes a POST request without in-process sleep; broker handles retries."""
        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            try:
                result = await client.post(url, json=payload)
                result.raise_for_status()
                data = result.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                raise LlmConnectionError(
                    message=f"Ollama request to {url} failed without broker retry handoff: {exc}",
                    attempts=1,
                ) from exc

            if "response" in data:
                return str(data.get("response", "")).strip()
            if "message" in data:
                msg = data.get("message", {})
                if isinstance(msg, dict):
                    return str(msg.get("content", "")).strip()
                return ""
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice:
                    msg = choice["message"]
                    if isinstance(msg, dict):
                        return str(msg.get("content", "")).strip()
                    return ""
                if "text" in choice:
                    return str(choice.get("text", "")).strip()
            return ""

    def _build_initial_prompt(
        self,
        user_prompt: str,
        schema_json: str,
        system_context: str,
    ) -> str:
        parts: list[str] = [
            "System: Du bist ein medizinischer Dokumentations-Assistent. "
            "Schreibe fachlich korrekte Texte für deutsche Krankenhausakten.",
            f"Du musst zwingend ein gültiges JSON-Objekt generieren, "
            f"das folgendem Schema entspricht:\n{schema_json}",
        ]
        if system_context:
            parts.append(f"Kontext: {system_context}")
        parts.append(f"Aufgabe: {user_prompt}")
        parts.append(
            "Antworte AUSSCHLIESSLICH mit dem JSON-Objekt. "
            "Keine Markdown-Block-Syntax (kein ```json). Nur das reine JSON."
        )
        return "\n\n".join(parts)
