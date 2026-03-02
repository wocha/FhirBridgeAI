"""
Unit tests for the canonical LLM Retry Client.

All Ollama HTTP calls are mocked — no running Ollama instance required.

Run:
    cd c:\\Projects\\FhirBridgeAi
    .venv\\Scripts\\python.exe -m pytest tests/test_llm_retry_client.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, Field

# Ensure the skill scripts directory is importable
_skill_scripts = str(
    Path(__file__).resolve().parent.parent
    / ".agents"
    / "skills"
    / "integrating-local-llms"
    / "scripts"
)
if _skill_scripts not in sys.path:
    sys.path.insert(0, _skill_scripts)

from llm_retry_client import (  # noqa: E402
    LlmConfig,
    LlmConnectionError,
    LlmRetryClient,
    LlmValidationError,
)

# ---------------------------------------------------------------------------
# Test Schema
# ---------------------------------------------------------------------------


class SimpleReport(BaseModel):
    """Minimal schema for testing structured generation."""

    title: str = Field(description="Document title")
    content: str = Field(description="Document body text")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_ollama_response(data: dict) -> MagicMock:
    """Create a mock ``httpx.Response`` that returns ``data`` as JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": json.dumps(data)}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


def _mock_ollama_raw(raw_string: str) -> MagicMock:
    """Create a mock response returning a raw (potentially invalid) string."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": raw_string}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLlmConfig:
    """Tests for LlmConfig defaults and validation."""

    def test_defaults(self) -> None:
        config = LlmConfig()
        assert config.model == "mistral-nemo"
        assert config.temperature == 0.1
        assert config.max_retries == 3
        assert config.initial_backoff_seconds == 1.0
        assert config.max_tokens == 2048
        assert config.request_timeout_seconds == 180.0

    def test_custom_values(self) -> None:
        config = LlmConfig(temperature=0.7, max_retries=5, max_tokens=4096)
        assert config.temperature == 0.7
        assert config.max_retries == 5
        assert config.max_tokens == 4096

    def test_temperature_bounds(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LlmConfig(temperature=3.0)


class TestLlmRetryClient:
    """Tests for the core retry/validation loop."""

    @pytest.mark.asyncio
    @patch("llm_retry_client.httpx.AsyncClient")
    async def test_successful_generation(self, mock_client_cls: MagicMock) -> None:
        """Valid JSON on first attempt — no retries needed."""
        valid_data = {"title": "OP-Bericht", "content": "Laparoskopische Appendektomie"}

        mock_client = AsyncMock()
        mock_client.post.return_value = _mock_ollama_response(valid_data)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        client = LlmRetryClient(LlmConfig(max_retries=3))
        result = await client.generate_structured(
            prompt="Erstelle einen OP-Bericht",
            schema=SimpleReport,
        )

        assert isinstance(result, SimpleReport)
        assert result.title == "OP-Bericht"
        assert result.content == "Laparoskopische Appendektomie"
        assert mock_client.post.call_count == 1

    @pytest.mark.asyncio
    @patch("llm_retry_client.asyncio.sleep")  # Skip actual backoff
    @patch("llm_retry_client.httpx.AsyncClient")
    async def test_retry_on_validation_error(
        self, mock_client_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """First response is invalid JSON, second is valid — expects 2 calls."""
        invalid_resp = _mock_ollama_raw('{"title": "Test"}')  # missing 'content'
        valid_resp = _mock_ollama_response({"title": "Test", "content": "Corrected output"})

        mock_client = AsyncMock()
        mock_client.post.side_effect = [invalid_resp, valid_resp]
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        client = LlmRetryClient(LlmConfig(max_retries=3))
        result = await client.generate_structured(
            prompt="Generate report",
            schema=SimpleReport,
        )

        assert result.content == "Corrected output"
        assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    @patch("llm_retry_client.asyncio.sleep")
    @patch("llm_retry_client.httpx.AsyncClient")
    async def test_max_retries_exhausted_raises_validation_error(
        self, mock_client_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """All 3 responses invalid — LlmValidationError must be raised."""
        bad_response = _mock_ollama_raw('{"wrong_field": "value"}')

        mock_client = AsyncMock()
        mock_client.post.return_value = bad_response
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        client = LlmRetryClient(LlmConfig(max_retries=3))

        with pytest.raises(LlmValidationError) as exc_info:
            await client.generate_structured(prompt="Generate", schema=SimpleReport)

        assert "SimpleReport" in str(exc_info.value)
        assert exc_info.value.last_raw_output == '{"wrong_field": "value"}'
        assert mock_client.post.call_count == 3

    @pytest.mark.asyncio
    @patch("llm_retry_client.asyncio.sleep")
    @patch("llm_retry_client.httpx.AsyncClient")
    async def test_connection_error_with_backoff(
        self, mock_client_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """ConnectionError on first attempt — LlmConnectionError raised immediately."""
        import httpx

        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.RequestError("Connection refused")
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        client = LlmRetryClient(LlmConfig(max_retries=3))

        with pytest.raises(LlmConnectionError) as exc_info:
            await client.generate_structured(prompt="Test", schema=SimpleReport)

        assert exc_info.value.attempts == 3
        assert "Connection refused" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("llm_retry_client.httpx.AsyncClient")
    async def test_system_context_included_in_prompt(self, mock_client_cls: MagicMock) -> None:
        """Verify system_context is passed through to the Ollama request."""
        valid_data = {"title": "Befund", "content": "Normalbefund"}

        mock_client = AsyncMock()
        mock_client.post.return_value = _mock_ollama_response(valid_data)
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        client = LlmRetryClient()
        await client.generate_structured(
            prompt="Erstelle einen Befund",
            schema=SimpleReport,
            system_context="Patient: Max Mustermann",
        )

        call_args = mock_client.post.call_args
        sent_prompt = call_args.kwargs.get("json", call_args[1].get("json", {}))["prompt"]
        assert "Max Mustermann" in sent_prompt
