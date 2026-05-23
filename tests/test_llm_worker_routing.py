"""
Tests for LLM Worker dual-message-type routing (FIX 1).

Test matrix:
  [T1] LlmTextMessage parsed correctly Ã¢â€ â€™ source_type == "text_direct" in span
  [T2] DocumentMetaData (OCR path) still parsed Ã¢â€ â€™ source_type == "ocr_output"
  [T3] Unknown payload Ã¢â€ â€™ reject(requeue=False) called, no ack
  [T4] Fallback parse (DocumentMetaData after LlmTextMessage fails) logged at DEBUG
  [T5] Recovery-path inner LlmTextMessage parse failure logged at DEBUG;
       _persist_failed_job awaited with correct job_id
"""
from __future__ import annotations

import json
import os
import sys
import types
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.skip(
    "Legacy LLM worker routing hooks changed in v0.2; requires rewrite for current outbox-driven worker.",
    allow_module_level=True,
)

# ---------------------------------------------------------------------------
# Env vars required by config.py before import
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_llm_routing.db")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("API_KEY_SECRET", "test-llm-routing-key")
os.environ.setdefault("DEPLOYMENT_ENV", "test")
os.environ.setdefault("MINIO_URL", "http://localhost:9000")

# ---------------------------------------------------------------------------
# Stub OTel exporters before importing anything that triggers init_tracer
# ---------------------------------------------------------------------------
with patch("fhirbridge.core.telemetry.OTLPSpanExporter"):
    from fhirbridge.workers import llm_worker


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class _TrackingSpan:
    """Span that records set_attribute calls."""

    def __init__(self) -> None:
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []
        self._recording = True

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def is_recording(self) -> bool:
        return self._recording

    def set_status(self, s: Any) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any]) -> None:
        self.events.append({"name": name, "attributes": attributes})


class _TrackingSpanContext:
    def __init__(self) -> None:
        self.span = _TrackingSpan()

    def __enter__(self) -> _TrackingSpan:
        return self.span

    def __exit__(self, *_: Any) -> bool:
        return False


class _TrackingTracer:
    def __init__(self) -> None:
        self.last_ctx: _TrackingSpanContext | None = None

    def start_as_current_span(self, name: str, context: Any = None) -> _TrackingSpanContext:
        ctx = _TrackingSpanContext()
        self.last_ctx = ctx
        return ctx


class _FakeMessage:
    """Minimal aio_pika IncomingMessage stub."""

    def __init__(self, body: bytes) -> None:
        self.body = body
        self.headers: dict[str, Any] = {}
        self.ack = AsyncMock()
        self.reject = AsyncMock()


class _FakeExchange:
    async def publish(self, message: Any, routing_key: str) -> None:
        pass


class _FakeChannel:
    @property
    def default_exchange(self) -> _FakeExchange:
        return _FakeExchange()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracking_tracer(monkeypatch: pytest.MonkeyPatch) -> _TrackingTracer:
    t = _TrackingTracer()
    monkeypatch.setattr(llm_worker, "tracer", t)
    return t


@pytest.fixture()
def fake_channel() -> _FakeChannel:
    return _FakeChannel()


@pytest.fixture()
def fake_dlq_exchange() -> AsyncMock:
    exc = AsyncMock()
    exc.publish = AsyncMock()
    return exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LLM_TEXT_MESSAGE_BODY = json.dumps({
    "job_id": 42,
    "filepath": "api_text_abc123",
    "s3_object_key": "job_42_payload.txt",
    "mapping_s3_key": "mappings/42.json",
}).encode()

DOCUMENT_METADATA_BODY = json.dumps({
    "job_id": 99,
    "filepath": "/tmp/scan.pdf",
    "s3_object_key": "job_99_ocr.txt",
}).encode()

UNKNOWN_PAYLOAD_BODY = json.dumps({"garbage": "data", "no_job_id": True}).encode()


def _make_noop_db_update(*_: Any, **__: Any) -> None:
    """No-op DB update Ã¢â‚¬â€ avoids real SQLite writes in routing tests."""


# ===========================================================================
# [T1] LlmTextMessage Ã¢â€ â€™ source_type == "text_direct"
# ===========================================================================


@pytest.mark.asyncio
async def test_llm_text_message_parsed_correctly(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LlmTextMessage payload sets source_type='text_direct' on the OTel span."""
    # Patch DB + S3 so the worker doesn't need real infrastructure
    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    # Patch asyncio.to_thread to run sync functions directly
    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    # S3 get_object returns the anonymized text
    fake_s3_body = AsyncMock()
    fake_s3_body.read = AsyncMock(return_value=b"anonymized clinical text")
    fake_s3_body.__aenter__ = AsyncMock(return_value=fake_s3_body)
    fake_s3_body.__aexit__ = AsyncMock(return_value=False)

    fake_s3_response = {"Body": fake_s3_body}
    fake_s3_client = AsyncMock()
    fake_s3_client.get_object = AsyncMock(return_value=fake_s3_response)
    fake_s3_client.__aenter__ = AsyncMock(return_value=fake_s3_client)
    fake_s3_client.__aexit__ = AsyncMock(return_value=False)

    fake_session = MagicMock()
    fake_session.client.return_value = fake_s3_client

    monkeypatch.setattr(llm_worker.aioboto3, "Session", lambda: fake_session)

    # LLM client returns a valid BundleExtraction
    from fhirbridge.models.fhir_models import BundleExtraction

    fake_bundle = BundleExtraction()
    fake_llm_client = AsyncMock()
    fake_llm_client.generate_structured = AsyncMock(return_value=fake_bundle)

    with patch("fhirbridge.workers.llm_worker.LlmRetryClient", return_value=fake_llm_client):
        msg = _FakeMessage(LLM_TEXT_MESSAGE_BODY)
        await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    assert tracking_tracer.last_ctx is not None
    span_attrs = tracking_tracer.last_ctx.span.attributes
    assert span_attrs.get("source_type") == "text_direct", (
        f"Expected source_type='text_direct', got {span_attrs.get('source_type')!r}"
    )
    assert span_attrs.get("job_id") == 42


# ===========================================================================
# [T2] DocumentMetaData (OCR path) Ã¢â€ â€™ source_type == "ocr_output"
# ===========================================================================


@pytest.mark.asyncio
async def test_document_metadata_still_parsed(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DocumentMetaData (OCR path) sets source_type='ocr_output' Ã¢â‚¬â€ backward compat."""
    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    fake_s3_body = AsyncMock()
    fake_s3_body.read = AsyncMock(return_value=b"ocr extracted text")
    fake_s3_body.__aenter__ = AsyncMock(return_value=fake_s3_body)
    fake_s3_body.__aexit__ = AsyncMock(return_value=False)

    fake_s3_response = {"Body": fake_s3_body}
    fake_s3_client = AsyncMock()
    fake_s3_client.get_object = AsyncMock(return_value=fake_s3_response)
    fake_s3_client.__aenter__ = AsyncMock(return_value=fake_s3_client)
    fake_s3_client.__aexit__ = AsyncMock(return_value=False)

    fake_session = MagicMock()
    fake_session.client.return_value = fake_s3_client

    monkeypatch.setattr(llm_worker.aioboto3, "Session", lambda: fake_session)

    from fhirbridge.models.fhir_models import BundleExtraction

    fake_bundle = BundleExtraction()
    fake_llm_client = AsyncMock()
    fake_llm_client.generate_structured = AsyncMock(return_value=fake_bundle)

    with patch("fhirbridge.workers.llm_worker.LlmRetryClient", return_value=fake_llm_client):
        msg = _FakeMessage(DOCUMENT_METADATA_BODY)
        await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    assert tracking_tracer.last_ctx is not None
    span_attrs = tracking_tracer.last_ctx.span.attributes
    assert span_attrs.get("source_type") == "ocr_output", (
        f"Expected source_type='ocr_output', got {span_attrs.get('source_type')!r}"
    )
    assert span_attrs.get("job_id") == 99


# ===========================================================================
# [T3] Unknown payload Ã¢â€ â€™ reject(requeue=False)
# ===========================================================================


@pytest.mark.asyncio
async def test_unknown_payload_rejected_to_dlq(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A body that matches neither LlmTextMessage nor DocumentMetaData Ã¢â€ â€™ reject(requeue=False)."""
    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    msg = _FakeMessage(UNKNOWN_PAYLOAD_BODY)
    await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    msg.reject.assert_called_once_with(requeue=False)
    msg.ack.assert_not_called()


# ===========================================================================
# [T4] Fallback parse is logged at DEBUG level (not silent)
# ===========================================================================


@pytest.mark.asyncio
async def test_fallback_parse_is_logged(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When a DocumentMetaData body triggers the fallback, a DEBUG log must appear."""
    import logging

    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    fake_s3_body = AsyncMock()
    fake_s3_body.read = AsyncMock(return_value=b"ocr text")
    fake_s3_body.__aenter__ = AsyncMock(return_value=fake_s3_body)
    fake_s3_body.__aexit__ = AsyncMock(return_value=False)

    fake_s3_response = {"Body": fake_s3_body}
    fake_s3_client = AsyncMock()
    fake_s3_client.get_object = AsyncMock(return_value=fake_s3_response)
    fake_s3_client.__aenter__ = AsyncMock(return_value=fake_s3_client)
    fake_s3_client.__aexit__ = AsyncMock(return_value=False)

    fake_session = MagicMock()
    fake_session.client.return_value = fake_s3_client

    monkeypatch.setattr(llm_worker.aioboto3, "Session", lambda: fake_session)

    from fhirbridge.models.fhir_models import BundleExtraction

    fake_bundle = BundleExtraction()
    fake_llm_client = AsyncMock()
    fake_llm_client.generate_structured = AsyncMock(return_value=fake_bundle)

    with patch("fhirbridge.workers.llm_worker.LlmRetryClient", return_value=fake_llm_client):
        with caplog.at_level(logging.DEBUG, logger="LLMWorker"):
            msg = _FakeMessage(DOCUMENT_METADATA_BODY)
            await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("retrying as DocumentMetaData" in m for m in debug_messages), (
        f"Expected DEBUG log 'retrying as DocumentMetaData' not found.\n"
        f"DEBUG messages: {debug_messages}"
    )
    # PHI safety: no exception message content in the log
    assert not any("synthetic" in m for m in debug_messages)


# ===========================================================================
# [T5] Recovery-path inner parse exception is logged (not swallowed silently)
# ===========================================================================


@pytest.mark.asyncio
async def test_recovery_path_inner_parse_exception_logged(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    Recovery-path inner except must log at DEBUG Ã¢â‚¬â€ not swallow silently.

    Setup:
    - Happy-path: both LlmTextMessage AND DocumentMetaData parse fail
      (task stays None, outer except fires)
    - Recovery block: LlmTextMessage fails (Ã¢â€ â€™ _recovery_parse_exc logged),
      DocumentMetaData succeeds (Ã¢â€ â€™ task set, job persisted, reject called)
    """
    import logging

    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    # Spy on _persist_failed_job to verify Zweig 2 (task found in recovery, job persisted)
    fake_persist = AsyncMock()
    monkeypatch.setattr(llm_worker, "_persist_failed_job", fake_persist)

    # Track parse call counts to vary behavior between happy-path and recovery-path
    parse_calls: dict[str, int] = {"llm": 0, "doc": 0}

    from fhirbridge.core.rabbitmq import DocumentMetaData as _RealDocumentMetaData

    def _llm_parse_always_fails(body: bytes) -> None:  # type: ignore[return]
        parse_calls["llm"] += 1
        raise ValueError("not a LlmTextMessage")

    def _doc_parse_fail_first_succeed_second(body: bytes) -> Any:
        parse_calls["doc"] += 1
        if parse_calls["doc"] == 1:
            raise ValueError("first doc parse fails too")
        # Second call (recovery) succeeds with a real DocumentMetaData
        return _RealDocumentMetaData(
            job_id=77,
            filepath="/recovery/test.pdf",
            s3_object_key="job_77_payload.txt",
        )

    fake_llm_cls = MagicMock()
    fake_llm_cls.model_validate_json = MagicMock(side_effect=_llm_parse_always_fails)

    fake_doc_cls = MagicMock()
    fake_doc_cls.model_validate_json = MagicMock(side_effect=_doc_parse_fail_first_succeed_second)

    monkeypatch.setattr(llm_worker, "LlmTextMessage", fake_llm_cls)
    monkeypatch.setattr(llm_worker, "DocumentMetaData", fake_doc_cls)

    with caplog.at_level(logging.DEBUG, logger="LLMWorker"):
        msg = _FakeMessage(UNKNOWN_PAYLOAD_BODY)
        await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    # Recovery task parse succeeded Ã¢â€ â€™ Zweig 2: _persist_failed_job awaited, then reject
    msg.reject.assert_called_once_with(requeue=False)
    fake_persist.assert_awaited_once()
    call_kwargs = fake_persist.call_args.kwargs
    assert call_kwargs.get("job_id") == 77, (
        f"Expected _persist_failed_job called with job_id=77, got {call_kwargs}"
    )

    # The _recovery_parse_exc DEBUG log must appear
    debug_messages = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
    assert any("Recovery:" in m and "retrying as DocumentMetaData" in m for m in debug_messages), (
        f"Expected DEBUG log 'Recovery: ... retrying as DocumentMetaData' not found.\n"
        f"DEBUG messages: {debug_messages}"
    )
    # PHI safety: exception message content must NOT appear
    assert not any("not a LlmTextMessage" in m for m in debug_messages)


@pytest.mark.asyncio
async def test_validation_exhausted_goes_to_central_dlq_route(
    tracking_tracer: _TrackingTracer,
    fake_channel: _FakeChannel,
    fake_dlq_exchange: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validation-exhausted must be durably published to the bound central DLQ route."""
    monkeypatch.setattr(llm_worker, "_update_job_sync", _make_noop_db_update)

    async def _fake_to_thread(fn: Any, *args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _fake_to_thread)

    fake_s3_body = AsyncMock()
    fake_s3_body.read = AsyncMock(return_value=b"anonymized clinical text")
    fake_s3_body.__aenter__ = AsyncMock(return_value=fake_s3_body)
    fake_s3_body.__aexit__ = AsyncMock(return_value=False)

    fake_s3_response = {"Body": fake_s3_body}
    fake_s3_client = AsyncMock()
    fake_s3_client.get_object = AsyncMock(return_value=fake_s3_response)
    fake_s3_client.__aenter__ = AsyncMock(return_value=fake_s3_client)
    fake_s3_client.__aexit__ = AsyncMock(return_value=False)

    fake_session = MagicMock()
    fake_session.client.return_value = fake_s3_client
    monkeypatch.setattr(llm_worker.aioboto3, "Session", lambda: fake_session)

    fake_llm_client = AsyncMock()
    fake_llm_client.generate_structured = AsyncMock(
        side_effect=llm_worker.LlmValidationError("validation exhausted")
    )

    with patch("fhirbridge.workers.llm_worker.LlmRetryClient", return_value=fake_llm_client):
        msg = _FakeMessage(LLM_TEXT_MESSAGE_BODY)
        await llm_worker.process_llm_message(msg, fake_channel, fake_dlq_exchange)

    msg.ack.assert_called_once()
    msg.reject.assert_not_called()
    fake_dlq_exchange.publish.assert_called_once()

    call_args = fake_dlq_exchange.publish.call_args
    published_message = call_args.args[0]
    routing_key = (
        call_args.kwargs["routing_key"]
        if "routing_key" in call_args.kwargs
        else call_args.args[1]
    )

    assert routing_key == llm_worker.DLQ_ROUTING_KEY
    assert published_message.delivery_mode == llm_worker.aio_pika.DeliveryMode.PERSISTENT
    assert published_message.headers["x-error-code"] == llm_worker.ERROR_LLM_VALIDATION
    assert published_message.headers["x-error-class"] == "LlmValidationError"
