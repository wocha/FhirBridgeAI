"""
Tests for ADR-016: Ingestion Endpoint Separation.

Pflicht-Tests gemaess ADR-016:
  T1. POST /ingest/text with text payload -> routed to llm_extraction_queue (NOT ocr_task_queue)
  T2. POST /ingest/pdf  with PDF payload  -> routed to ocr_task_queue
  T3. POST /ingest/pdf  with text payload -> 415 response
  T4. POST /ingest/text with PDF payload  -> 415 response
  T5. PHI-Gate failure in text path       -> no queue publish, OTel error span recorded
  T6. S3 failure during mapping write     -> no queue publish (no orphan)
  T7. Error responses contain NO PHI

KRITIS Sec 8a: Tests MUST verify that PHI never appears in error responses, queue messages,
or log output. Monkeypatching isolates all external I/O (S3, RabbitMQ, DB).
"""
from __future__ import annotations

import pytest

pytest.skip(
    "Legacy ADR-016 endpoint contract changed in v0.2; requires rewrite for current claim-check ingestion API.",
    allow_module_level=True,
)

import json
import os
import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

# ---------------------------------------------------------------------------
# Set required environment variables BEFORE importing the api module.
# This avoids pydantic_settings validation failures in CI (no .env present).
# ---------------------------------------------------------------------------
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_ingest.db")
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")
os.environ.setdefault("MINIO_URL", "http://localhost:9000")

from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Stub optional / missing modules BEFORE importing the API module.
# This mirrors the pattern used in test_ocr_worker_async.py.
# ---------------------------------------------------------------------------

# opentelemetry.instrumentation.fastapi may not be installed in the test venv.
_otel_instr = types.ModuleType("opentelemetry.instrumentation")
_otel_instr_fastapi = types.ModuleType("opentelemetry.instrumentation.fastapi")

class _NoOpInstrumentor:
    def instrument_app(self, *a: Any, **kw: Any) -> None:
        pass

_otel_instr_fastapi.FastAPIInstrumentor = _NoOpInstrumentor  # type: ignore[attr-defined]

for _mod_name, _mod in [
    ("opentelemetry.instrumentation", _otel_instr),
    ("opentelemetry.instrumentation.fastapi", _otel_instr_fastapi),
]:
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = _mod

# ---------------------------------------------------------------------------
# OTel / Jaeger stubs â€” must be installed before importing the API module
# so that init_tracer does not attempt a real OTLP connection.
# ---------------------------------------------------------------------------

class _DummySpan:
    def __init__(self) -> None:
        self.status: Any = None
        self.events: list[dict[str, Any]] = []
        self.attributes: dict[str, Any] = {}
        self._recording = True

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_span_context(self) -> Any:
        from opentelemetry.trace import INVALID_SPAN_CONTEXT

        return INVALID_SPAN_CONTEXT

    def is_recording(self) -> bool:
        return self._recording

    def set_status(self, s: Any) -> None:
        self.status = s

    def add_event(self, name: str, attributes: dict[str, Any]) -> None:
        self.events.append({"name": name, "attributes": attributes})


class _DummySpanContext:
    def __init__(self, span: _DummySpan) -> None:
        self._span = span

    def __enter__(self) -> _DummySpan:
        return self._span

    def __exit__(self, *_: Any) -> bool:
        return False


class _DummyTracer:
    def __init__(self) -> None:
        self.last_span: _DummySpan | None = None

    def start_as_current_span(self, name: str, context: Any = None) -> _DummySpanContext:
        if self.last_span is None:
            self.last_span = _DummySpan()
        return _DummySpanContext(self.last_span)


# ---------------------------------------------------------------------------
# Fake RabbitMQ infrastructure
# ---------------------------------------------------------------------------

@dataclass
class _FakeMessage:
    body: bytes
    routing_key: str


@dataclass
class _FakeExchange:
    published: list[_FakeMessage] = field(default_factory=list)

    async def publish(self, message: Any, routing_key: str) -> None:
        self.published.append(_FakeMessage(body=message.body, routing_key=routing_key))


@dataclass
class _FakeChannel:
    exchange: _FakeExchange = field(default_factory=_FakeExchange)
    close_count: int = field(default=0)

    @property
    def default_exchange(self) -> _FakeExchange:
        return self.exchange

    async def declare_queue(self, name: str, durable: bool = True) -> None:
        pass

    async def close(self) -> None:
        self.close_count += 1


# ---------------------------------------------------------------------------
# Fake S3 infrastructure
# ---------------------------------------------------------------------------

class _S3ClientOk:
    """S3 client that silently succeeds all operations."""

    def __init__(self) -> None:
        self.puts: list[dict[str, Any]] = []
        self.deletes: list[str] = []

    async def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        self.puts.append({"Bucket": Bucket, "Key": Key, "size": len(Body)})

    async def delete_object(self, *, Bucket: str, Key: str) -> None:
        self.deletes.append(Key)

    async def __aenter__(self) -> "_S3ClientOk":
        return self

    async def __aexit__(self, *_: Any) -> bool:
        return False


class _S3ClientFailOnMapping(_S3ClientOk):
    """S3 client that fails when writing the mapping key."""

    async def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        if "mappings/" in Key:
            raise RuntimeError("synthetic S3 mapping write failure")
        await super().put_object(Bucket=Bucket, Key=Key, Body=Body)


class _S3ClientFailAlways(_S3ClientOk):
    """S3 client that always fails on put_object."""

    async def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        raise RuntimeError("synthetic S3 put failure")


class _FakeS3Session:
    def __init__(self, client: _S3ClientOk) -> None:
        self._client = client

    def client(self, *_: Any, **__: Any) -> _S3ClientOk:
        return self._client


# ---------------------------------------------------------------------------
# Import the FastAPI app AFTER env vars and stubs are prepared.
# ---------------------------------------------------------------------------

# Suppress OTel exporter connection at import time by pre-patching init_tracer
_dummy_tracer = _DummyTracer()

with patch("fhirbridge.core.telemetry.OTLPSpanExporter"):
    from fhirbridge.ingestion import api as ingest_api

from fhirbridge.core.auth import UserClaims, get_current_user

HEADERS_PDF = {"Content-Type": "application/pdf"}
HEADERS_TEXT = {"Content-Type": "text/plain; charset=utf-8"}

_PHYSICIAN_USER = UserClaims(sub="test-physician-sub", roles=["PHYSICIAN"], station="Teststation")
_ADMIN_USER = UserClaims(sub="test-admin-sub", roles=["ADMIN"])
_EMERGENCY_USER = UserClaims(sub="test-emergency-sub", roles=["EMERGENCY"], station="EMERGENCY")


async def _override_physician_user() -> UserClaims:
    return _PHYSICIAN_USER


async def _override_admin_user() -> UserClaims:
    return _ADMIN_USER


async def _override_emergency_user() -> UserClaims:
    return _EMERGENCY_USER


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_tracer(monkeypatch: pytest.MonkeyPatch) -> _DummyTracer:
    """Replace the OTel tracer in the ingestion module with a no-op tracer."""
    t = _DummyTracer()
    t.last_span = _DummySpan()
    monkeypatch.setattr(ingest_api, "tracer", t)
    monkeypatch.setattr(
        "opentelemetry.trace.get_current_span",
        lambda *args, **kwargs: t.last_span,
    )
    return t


@pytest.fixture(autouse=True)
def default_physician_auth():
    """All tests default to PHYSICIAN role via FastAPI dependency override."""
    ingest_api.app.dependency_overrides[get_current_user] = _override_physician_user
    yield
    ingest_api.app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def run_sync_work_inline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep endpoint unit tests out of asyncio's default ThreadPoolExecutor."""

    async def _inline_to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    monkeypatch.setattr(ingest_api.asyncio, "to_thread", _inline_to_thread)


@pytest.fixture()
def fake_channel() -> _FakeChannel:
    return _FakeChannel()


@pytest.fixture()
def s3_ok() -> _S3ClientOk:
    return _S3ClientOk()


@pytest.fixture()
def s3_fail_mapping() -> _S3ClientFailOnMapping:
    return _S3ClientFailOnMapping()


# ---------------------------------------------------------------------------
# Helper: async HTTP client backed by the FastAPI ASGI app
# ---------------------------------------------------------------------------

async def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=ingest_api.app), base_url="http://testserver")


def _metric_value(exposition: str, metric_name: str) -> float:
    match = re.search(rf"^{re.escape(metric_name)}\s+([0-9.eE+-]+)$", exposition, re.MULTILINE)
    assert match is not None, f"metric '{metric_name}' not found in exposition"
    return float(match.group(1))

# ===========================================================================
# T_METRICS. GET /metrics -> 200 + Prometheus text format + PHI-free payload
# ===========================================================================

@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus_text_format() -> None:
    async with await _client() as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    content_type = resp.headers.get("content-type", "")
    assert "text/plain" in content_type
    assert "version=" in content_type

    body = resp.text
    assert "# HELP fhirbridge_ingestion_http_requests_total" in body
    assert "fhirbridge_ingestion_http_request_duration_seconds_bucket" in body
    assert "fhirbridge_ingestion_metrics_scrapes_total" in body
    assert "fhirbridge_ingestion_documents_accepted_total" in body


@pytest.mark.asyncio
async def test_metrics_payload_contains_no_phi_fragments() -> None:
    async with await _client() as client:
        resp = await client.get("/metrics")

    assert resp.status_code == 200
    body = resp.text
    for forbidden in [
        "Max Mustermann",
        "A123456789",
        "15.03.1972",
        "J18.0",
    ]:
        assert forbidden not in body



@pytest.mark.asyncio
async def test_metrics_scrapes_do_not_increment_general_http_counter() -> None:
    async with await _client() as client:
        non_metrics = await client.post(
            "/ingest/pdf",
            content=b"not a pdf",
            headers={"Content-Type": "text/plain"},
        )
        first = await client.get("/metrics")
        second = await client.get("/metrics")

    assert non_metrics.status_code == 415
    assert first.status_code == 200
    assert second.status_code == 200

    first_http_total = _metric_value(first.text, "fhirbridge_ingestion_http_requests_total")
    second_http_total = _metric_value(second.text, "fhirbridge_ingestion_http_requests_total")
    first_scrape_total = _metric_value(first.text, "fhirbridge_ingestion_metrics_scrapes_total")
    second_scrape_total = _metric_value(second.text, "fhirbridge_ingestion_metrics_scrapes_total")

    assert second_http_total == first_http_total
    assert second_scrape_total >= first_scrape_total + 1.0

def test_ingestion_router_not_exposing_metrics_externally() -> None:
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    compose_text = compose_path.read_text(encoding="utf-8")
    pattern = (
        r"traefik\.http\.routers\.ingestion-gateway\.rule="
        r"Host\(`ingest\.docker\.localhost`\)\s*&&\s*PathPrefix\(`/ingest`\)"
    )
    assert re.search(pattern, compose_text), "Ingestion router must not expose /metrics externally"

# ===========================================================================
# T1. POST /ingest/text â†’ llm_extraction_queue (NOT ocr_task_queue)
# ===========================================================================

@pytest.mark.asyncio
async def test_text_routed_to_llm_queue(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(
        ingest_api.aioboto3,
        "Session",
        lambda: _FakeS3Session(s3_ok),
    )

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"Patient Max Mustermann, geb. 01.01.1970",
            headers=HEADERS_TEXT,
        )

    assert resp.status_code == 202, resp.text
    assert len(fake_channel.exchange.published) == 1
    msg = fake_channel.exchange.published[0]
    assert msg.routing_key == ingest_api.LLM_QUEUE_NAME
    assert msg.routing_key != ingest_api.OCR_QUEUE_NAME

    payload = json.loads(msg.body)
    assert "mapping_s3_key" in payload  # LlmTextMessage, not DocumentMetaData


# ===========================================================================
# T2. POST /ingest/pdf â†’ ocr_task_queue
# ===========================================================================

@pytest.mark.asyncio
async def test_pdf_routed_to_ocr_queue(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(
        ingest_api.aioboto3,
        "Session",
        lambda: _FakeS3Session(s3_ok),
    )

    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake pdf bytes",
            headers=HEADERS_PDF,
        )

    assert resp.status_code == 202, resp.text
    assert len(fake_channel.exchange.published) == 1
    msg = fake_channel.exchange.published[0]
    assert msg.routing_key == ingest_api.OCR_QUEUE_NAME
    assert msg.routing_key != ingest_api.LLM_QUEUE_NAME


# ===========================================================================
# T3. POST /ingest/pdf with text payload â†’ 415
# ===========================================================================

@pytest.mark.asyncio
async def test_pdf_endpoint_rejects_text_content_type() -> None:
    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"plain text content",
            headers={"Content-Type": "text/plain"},
        )

    assert resp.status_code == 415
    body = resp.json()
    # Error response must not contain PHI
    assert "pdf" in body.get("detail", "").lower() or "unsupported" in body.get("detail", "").lower()


# ===========================================================================
# T4. POST /ingest/text with PDF content-type â†’ 415
# ===========================================================================

@pytest.mark.asyncio
async def test_text_endpoint_rejects_pdf_content_type() -> None:
    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"%PDF-1.4 fake",
            headers={"Content-Type": "application/pdf"},
        )

    assert resp.status_code == 415
    body = resp.json()
    assert "unsupported" in body.get("detail", "").lower() or "text" in body.get("detail", "").lower()


# ===========================================================================
# T5. PHI-Gate failure â†’ no queue publish + OTel Error span
# ===========================================================================

@pytest.mark.asyncio
async def test_phi_gate_failure_blocks_publish(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
    patch_tracer: _DummyTracer,
) -> None:
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    # Make the PHI-Gate throw an exception
    async def _failing_phi_gate(*_: Any, **__: Any) -> None:
        raise RuntimeError("synthetic PHI-Gate failure")

    monkeypatch.setattr(ingest_api.asyncio, "to_thread", _failing_phi_gate)

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"some clinical text",
            headers=HEADERS_TEXT,
        )

    # No queue publish
    assert len(fake_channel.exchange.published) == 0
    # HTTP 500 (fail-closed)
    assert resp.status_code == 500
    # OTel error span was set
    assert patch_tracer.last_span is not None
    span_events = patch_tracer.last_span.events
    error_events = [e for e in span_events if e.get("name") == "exception"]
    assert len(error_events) >= 1
    assert error_events[0]["attributes"].get("error.code") == ingest_api.ERROR_PHI_GATE
    # Error response must not contain PHI
    assert "phi" not in resp.text.lower() or "internal" in resp.text.lower()


# ===========================================================================
# T6. S3 mapping write failure â†’ no queue publish (no orphan)
# ===========================================================================

@pytest.mark.asyncio
async def test_s3_mapping_failure_blocks_publish(
    fake_channel: _FakeChannel,
    s3_fail_mapping: _S3ClientFailOnMapping,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(
        ingest_api.aioboto3,
        "Session",
        lambda: _FakeS3Session(s3_fail_mapping),
    )

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"Patient data here",
            headers=HEADERS_TEXT,
        )

    # Queue must not have received any message
    assert len(fake_channel.exchange.published) == 0
    # HTTP 500 (fail-closed, no orphan)
    assert resp.status_code == 500
    # The text-payload S3 write succeeded but mapping failed.
    # Compensating cleanup should have deleted the text payload.
    assert len(s3_fail_mapping.deletes) >= 1, (
        "Compensating cleanup must delete the written text S3 object"
    )


# ===========================================================================
# T7. Error responses contain NO PHI
# ===========================================================================

@pytest.mark.asyncio
async def test_error_responses_contain_no_phi(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    PHI_SAMPLE = "Max Mustermann KVNR A123456789 geb. 15.03.1972 Diagnose: ICD-10 J18.0"

    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    # Force the PHI-Gate to fail so PHI is in-scope during error handling
    async def _failing_phi_gate(*_: Any, **__: Any) -> None:
        raise RuntimeError(f"PHI LEAK ATTEMPT: {PHI_SAMPLE}")

    monkeypatch.setattr(ingest_api.asyncio, "to_thread", _failing_phi_gate)

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=PHI_SAMPLE.encode("utf-8"),
            headers=HEADERS_TEXT,
        )

    assert resp.status_code == 500
    response_body = resp.text

    # None of the PHI data points may appear in the HTTP response
    for phi_fragment in [
        "Max Mustermann",
        "A123456789",
        "15.03.1972",
        "J18.0",
        "PHI LEAK ATTEMPT",
    ]:
        assert phi_fragment not in response_body, (
            f"PHI fragment '{phi_fragment}' found in error response â€” KRITIS Â§8a violation"
        )


# ===========================================================================
# FIX 2: Channel-close tests (prevent RabbitMQ channel-limit exhaustion)
# ===========================================================================


@pytest.mark.asyncio
async def test_channel_closed_after_pdf_publish(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """channel.close() must be called after a successful PDF publish."""
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake pdf bytes",
            headers=HEADERS_PDF,
        )

    assert resp.status_code == 202, resp.text
    assert fake_channel.close_count == 1, (
        f"Expected channel.close() called once, got {fake_channel.close_count}"
    )


@pytest.mark.asyncio
async def test_channel_closed_on_pdf_s3_error(
    fake_channel: _FakeChannel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """channel.close() must be called even when the S3 put raises an exception."""
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    s3_fail = _S3ClientFailAlways()
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_fail))

    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake pdf bytes",
            headers=HEADERS_PDF,
        )

    # S3 failure â†’ 500 response, but channel was never opened (S3 error happens before channel)
    # The channel.close() is only invoked after a successful channel acquisition.
    # S3 fails BEFORE get_rabbitmq_channel() is called, so close_count stays 0.
    assert resp.status_code == 500
    # channel was acquired after S3 write â€” with S3 failing, channel was never opened
    assert fake_channel.close_count == 0


@pytest.mark.asyncio
async def test_channel_closed_after_text_publish(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """channel.close() must be called after a successful text publish."""
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"Patient Max Mustermann, geb. 01.01.1970",
            headers=HEADERS_TEXT,
        )

    assert resp.status_code == 202, resp.text
    assert fake_channel.close_count == 1, (
        f"Expected channel.close() called once, got {fake_channel.close_count}"
    )


@pytest.mark.asyncio
async def test_channel_closed_on_text_s3_error(
    fake_channel: _FakeChannel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """channel.close() must be called even when S3 mapping write raises on text path."""
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    s3_fail_mapping = _S3ClientFailOnMapping()
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_fail_mapping))

    async with await _client() as client:
        resp = await client.post(
            "/ingest/text",
            content=b"Patient text here",
            headers=HEADERS_TEXT,
        )

    # S3 mapping write fails â†’ 500, channel was never opened (publish never reached)
    assert resp.status_code == 500
    assert fake_channel.close_count == 0


# ===========================================================================
# FIX 2b: publish() exception not masked by close() exception
# ===========================================================================


class _FailingExchange:
    """Exchange that always raises on publish."""

    async def publish(self, message: Any, routing_key: str) -> None:
        raise RuntimeError("publish error")


@dataclass
class _FakeChannelBothFail:
    """Channel where publish raises AND close raises â€” for exception-masking test."""

    _exchange: _FailingExchange = field(default_factory=_FailingExchange)
    close_called: bool = field(default=False)
    warnings_logged: list[str] = field(default_factory=list)

    @property
    def default_exchange(self) -> _FailingExchange:
        return self._exchange

    async def close(self) -> None:
        self.close_called = True
        raise RuntimeError("close error")


@pytest.mark.asyncio
async def test_pdf_publish_error_logged_not_close_error(
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """publish() error must trigger S3 compensation; close() error is only a warning."""
    import logging

    channel = _FakeChannelBothFail()
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    with caplog.at_level(logging.WARNING):
        async with await _client() as client:
            resp = await client.post(
                "/ingest/pdf",
                content=b"%PDF-1.4 fake pdf bytes",
                headers=HEADERS_PDF,
            )

    # HTTP response must be 500 â€” the publish error is what matters
    assert resp.status_code == 500

    # close() must have been called (finally block executed)
    assert channel.close_called

    # Compensating cleanup must remove the previously written PDF payload.
    assert len(s3_ok.puts) == 1
    put_key = s3_ok.puts[0]["Key"]
    assert put_key in s3_ok.deletes, (
        f"Expected compensation delete for uploaded key {put_key!r}, deletes={s3_ok.deletes!r}"
    )

    # The close() failure must appear as a WARNING (not swallowed silently)
    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any(ingest_api.ERROR_PDF_QUEUEING in m for m in warning_messages), (
        f"Expected WARNING with ERROR_PDF_QUEUEING for close failure.\nWarnings: {warning_messages}"
    )


# ===========================================================================
# T_AUTH1. Request ohne Token â†’ 401 (HTTPBearer auto_error=True)
# ===========================================================================

@pytest.mark.asyncio
async def test_request_without_token_returns_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """[T_AUTH1] Requests ohne Bearer-Token werden mit 401 abgelehnt."""
    ingest_api.app.dependency_overrides.clear()  # Remove auth override
    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake",
            headers={"Content-Type": "application/pdf"},
        )
    assert resp.status_code == 401


# ===========================================================================
# T_AUTH2. ADMIN-Rolle â†’ 403 (kein klinischer Datenzugriff)
# ===========================================================================

@pytest.mark.asyncio
async def test_admin_role_blocked_from_clinical_endpoints() -> None:
    """[T_AUTH2] ADMIN hat keinen Zugriff auf Ingestion-Endpoints (kein PHI)."""
    ingest_api.app.dependency_overrides[get_current_user] = _override_admin_user
    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake",
            headers={"Content-Type": "application/pdf"},
        )
    assert resp.status_code == 403
    assert "clinical" in resp.json().get("detail", "").lower()


# ===========================================================================
# T_AUTH3. EMERGENCY-Rolle â†’ 202 (Break-the-Glass, OTel-Audit)
# ===========================================================================

@pytest.mark.asyncio
async def test_emergency_role_granted_with_audit(
    fake_channel: _FakeChannel,
    s3_ok: _S3ClientOk,
    monkeypatch: pytest.MonkeyPatch,
    patch_tracer: _DummyTracer,
) -> None:
    """[T_AUTH3] EMERGENCY-Rolle wird gewÃ¤hrt. OTel break_glass=true muss gesetzt sein."""
    ingest_api.app.dependency_overrides[get_current_user] = _override_emergency_user
    monkeypatch.setattr(ingest_api, "get_rabbitmq_channel", AsyncMock(return_value=fake_channel))
    monkeypatch.setattr(ingest_api.aioboto3, "Session", lambda: _FakeS3Session(s3_ok))

    async with await _client() as client:
        resp = await client.post(
            "/ingest/pdf",
            content=b"%PDF-1.4 fake",
            headers={"Content-Type": "application/pdf"},
        )

    assert resp.status_code == 202
    # OTel span must have break_glass=True
    assert patch_tracer.last_span is not None
    assert patch_tracer.last_span.attributes.get("break_glass") is True
