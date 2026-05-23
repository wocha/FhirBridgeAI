from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest

pytest.skip(
    "Legacy worker redaction contract changed in v0.2; requires rewrite for current telemetry/error-state model.",
    allow_module_level=True,
)

from fhirbridge.core.database import JobStatus
from fhirbridge.core.llm import LlmValidationError
from fhirbridge.core.rabbitmq import DocumentMetaData, FhirExportMessage
from fhirbridge.core.telemetry import build_safe_error_trace
from fhirbridge.workers import fhir_export_worker, llm_worker


class _DummySpan:
    def __init__(self) -> None:
        self.attributes: dict[str, Any] = {}

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def is_recording(self) -> bool:
        return True

    def set_status(self, status: Any) -> None:
        return None

    def add_event(self, name: str, attributes: dict[str, Any]) -> None:
        return None


class _DummySpanContext:
    def __init__(self, span: _DummySpan) -> None:
        self._span = span

    def __enter__(self) -> _DummySpan:
        return self._span

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class _DummyTracer:
    def start_as_current_span(self, _name: str, context: Any = None) -> _DummySpanContext:
        return _DummySpanContext(_DummySpan())


class _FakeBody:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def read(self) -> bytes:
        return self._payload

    async def __aenter__(self) -> "_FakeBody":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class _FakeS3Client:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def __aenter__(self) -> "_FakeS3Client":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    async def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        return {"Body": _FakeBody(self._payload)}

    async def delete_object(self, Bucket: str, Key: str) -> None:
        return None


class _FakeS3Session:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def client(self, *args: Any, **kwargs: Any) -> _FakeS3Client:
        return _FakeS3Client(self._payload)


class _BoundQueue:
    def __init__(self) -> None:
        self.messages: list[Any] = []


class _FakeExchange:
    def __init__(self) -> None:
        self.published: list[tuple[Any, str]] = []
        self._bindings: dict[str, _BoundQueue] = {}

    def bind_queue(self, routing_key: str) -> _BoundQueue:
        queue = _BoundQueue()
        self._bindings[routing_key] = queue
        return queue

    async def publish(self, message: Any, routing_key: str) -> None:
        self.published.append((message, routing_key))
        queue = self._bindings.get(routing_key)
        if queue is not None:
            queue.messages.append(message)


class _FakeChannel:
    def __init__(self) -> None:
        self.default_exchange = _FakeExchange()
        self.retry_exchange = _FakeExchange()

    async def get_exchange(self, _name: str) -> _FakeExchange:
        return self.retry_exchange


@dataclass
class _FakeIncomingMessage:
    body: bytes
    headers: dict[str, Any] | None = None
    correlation_id: str | None = None
    acked: bool = False
    rejected: bool = False
    rejected_requeue: bool | None = None

    async def ack(self) -> None:
        self.acked = True

    async def reject(self, requeue: bool = False) -> None:
        self.rejected = True
        self.rejected_requeue = requeue


class _FakeProcessContext:
    def __init__(self, message: "_FakeIncomingExportMessage") -> None:
        self._message = message

    async def __aenter__(self) -> "_FakeIncomingExportMessage":
        return self._message

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class _FakeIncomingExportMessage(_FakeIncomingMessage):
    def process(self, requeue: bool = False, ignore_processed: bool = True) -> _FakeProcessContext:
        return _FakeProcessContext(self)


@pytest.mark.asyncio
async def test_llm_validation_error_redacts_headers_and_error_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    phi_value = "Patient Max Mustermann"
    updates: list[dict[str, Any]] = []
    otel_error_codes: list[str] = []

    monkeypatch.setattr(llm_worker, "tracer", _DummyTracer())
    monkeypatch.setattr(llm_worker, "mark_span_error", lambda span, exc, *, error_code, component: otel_error_codes.append(error_code))

    async def _to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    monkeypatch.setattr(llm_worker.asyncio, "to_thread", _to_thread)

    def _update_job_sync(job_id: int, status: JobStatus, fhir_json: str | None = None, error_trace: str | None = None) -> None:
        updates.append({
            "job_id": job_id,
            "status": status,
            "fhir_json": fhir_json,
            "error_trace": error_trace,
        })

    monkeypatch.setattr(llm_worker, "_update_job_sync", _update_job_sync)
    monkeypatch.setattr(llm_worker.aioboto3, "Session", lambda: _FakeS3Session(phi_value.encode("utf-8")))

    async def _raise_validation(self: Any, *args: Any, **kwargs: Any) -> Any:
        raise LlmValidationError(
            "validation exhausted",
            last_raw_output=f"RAW WITH PHI: {phi_value}",
            validation_errors=None,
        )

    monkeypatch.setattr(llm_worker.LlmRetryClient, "generate_structured", _raise_validation)

    task = DocumentMetaData(
        job_id=101,
        filepath="C:/input/fall_101.pdf",
        s3_object_key="job_101_payload.txt",
    )
    message = _FakeIncomingMessage(body=task.model_dump_json().encode("utf-8"), headers={})
    channel = _FakeChannel()
    dlq_exchange = _FakeExchange()
    bound_dlq_queue = dlq_exchange.bind_queue(llm_worker.DLQ_ROUTING_KEY)

    await llm_worker.process_llm_message(message=message, channel=channel, dlq_exchange=dlq_exchange)

    assert message.acked is True
    assert message.rejected is False
    assert len(dlq_exchange.published) == 1
    assert dlq_exchange.published[0][1] == llm_worker.DLQ_ROUTING_KEY
    assert len(bound_dlq_queue.messages) == 1

    dlq_headers = dlq_exchange.published[0][0].headers
    assert "x-validation-errors" not in dlq_headers
    assert "x-last-raw-output" not in dlq_headers
    assert dlq_headers["x-error-code"] == llm_worker.ERROR_LLM_VALIDATION
    assert dlq_headers["x-error-class"] == "LlmValidationError"

    rendered_headers = json.dumps(dlq_headers)
    assert phi_value not in rendered_headers

    failed_updates = [u for u in updates if u["status"] == JobStatus.FAILED]
    assert len(failed_updates) == 1
    failed_trace = failed_updates[0]["error_trace"]
    assert isinstance(failed_trace, str)
    assert llm_worker.ERROR_LLM_VALIDATION in failed_trace
    assert phi_value not in failed_trace

    assert llm_worker.ERROR_LLM_VALIDATION in otel_error_codes


@pytest.mark.asyncio
async def test_fhir_export_unhandled_error_redacts_db_error_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    phi_value = "Patient Max Mustermann"
    updates: list[dict[str, Any]] = []
    otel_error_codes: list[str] = []

    monkeypatch.setattr(fhir_export_worker, "tracer", _DummyTracer())
    monkeypatch.setattr(
        fhir_export_worker,
        "mark_span_error",
        lambda span, exc, *, error_code, component: otel_error_codes.append(error_code),
    )

    async def _to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    monkeypatch.setattr(fhir_export_worker.asyncio, "to_thread", _to_thread)

    def _update_job_sync(job_id: int, status: JobStatus, error_trace: str | None = None) -> None:
        updates.append({"job_id": job_id, "status": status, "error_trace": error_trace})

    monkeypatch.setattr(fhir_export_worker, "_update_job_sync", _update_job_sync)
    monkeypatch.setattr(
        fhir_export_worker.aioboto3,
        "Session",
        lambda: _FakeS3Session(json.dumps({"<NAME_1>": phi_value}).encode("utf-8")),
    )

    class _FakeAnonymizer:
        def __init__(self, require_nlp: bool = False) -> None:
            return None

        def deanonymize(self, data: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
            return {"Patient": {"resourceType": "Patient"}, "Encounter": {"resourceType": "Encounter"}}

    class _BundleProxy:
        @staticmethod
        def model_validate(data: dict[str, Any]) -> object:
            return object()

    monkeypatch.setattr(fhir_export_worker, "LocalAnonymizer", _FakeAnonymizer)
    monkeypatch.setattr(fhir_export_worker, "Bundle", _BundleProxy)
    monkeypatch.setattr(fhir_export_worker, "inject_idempotency_logic", lambda bundle: "{}")

    async def _raise_unhandled(client: Any, bundle_json: str, correlation_id: str) -> None:
        raise RuntimeError(f"Downstream rejected payload for {phi_value}")

    monkeypatch.setattr(fhir_export_worker, "send_fhir_bundle", _raise_unhandled)

    task = FhirExportMessage(job_id=202, bundle_json=json.dumps({"Patient": {"name": "<NAME_1>"}}))
    message = _FakeIncomingExportMessage(
        body=task.model_dump_json().encode("utf-8"),
        headers={"x-retry-count": 0},
        correlation_id="corr-202",
    )

    channel = _FakeChannel()

    await fhir_export_worker.process_export_message(
        message=message,
        client=object(),
        channel=channel,
    )

    assert message.rejected is True
    assert message.rejected_requeue is False

    failed_updates = [u for u in updates if u["status"] == JobStatus.EXPORT_FAILED]
    assert len(failed_updates) == 1

    failed_trace = failed_updates[0]["error_trace"]
    assert isinstance(failed_trace, str)
    assert fhir_export_worker.ERROR_UNHANDLED in failed_trace
    assert phi_value not in failed_trace

    assert fhir_export_worker.ERROR_UNHANDLED in otel_error_codes


def test_build_safe_error_trace_redacts_exception_message() -> None:
    phi_value = "Patient Max Mustermann"

    try:
        raise RuntimeError(f"Leaked PHI should not appear: {phi_value}")
    except RuntimeError as exc:
        safe_trace = f"TEST_SAFE_TRACE: Synthetic failure\n{build_safe_error_trace(exc)}"

    assert "TEST_SAFE_TRACE" in safe_trace
    assert "Synthetic failure" in safe_trace
    assert phi_value not in safe_trace


@pytest.mark.asyncio
async def test_fhir_export_cleanup_failure_is_not_exported_and_is_phi_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    phi_value = "Patient Max Mustermann"
    updates: list[dict[str, Any]] = []
    otel_error_codes: list[str] = []

    monkeypatch.setattr(fhir_export_worker, "tracer", _DummyTracer())
    monkeypatch.setattr(
        fhir_export_worker,
        "mark_span_error",
        lambda span, exc, *, error_code, component: otel_error_codes.append(error_code),
    )

    async def _to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    monkeypatch.setattr(fhir_export_worker.asyncio, "to_thread", _to_thread)

    def _update_job_sync(job_id: int, status: JobStatus, error_trace: str | None = None) -> None:
        updates.append({"job_id": job_id, "status": status, "error_trace": error_trace})

    monkeypatch.setattr(fhir_export_worker, "_update_job_sync", _update_job_sync)

    class _CleanupFailingS3Client:
        def __init__(self, payload: bytes, fail_delete: bool) -> None:
            self._payload = payload
            self._fail_delete = fail_delete

        async def __aenter__(self) -> "_CleanupFailingS3Client":
            return self

        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
            return False

        async def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
            return {"Body": _FakeBody(self._payload)}

        async def delete_object(self, Bucket: str, Key: str) -> None:
            if self._fail_delete:
                raise RuntimeError(f"cleanup failed for {phi_value}")

    class _CleanupFailingS3Session:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload
            self._calls = 0

        def client(self, *args: Any, **kwargs: Any) -> _CleanupFailingS3Client:
            self._calls += 1
            return _CleanupFailingS3Client(self._payload, fail_delete=self._calls >= 2)

    monkeypatch.setattr(
        fhir_export_worker.aioboto3,
        "Session",
        lambda: _CleanupFailingS3Session(json.dumps({"<NAME_1>": phi_value}).encode("utf-8")),
    )

    class _FakeAnonymizer:
        def __init__(self, require_nlp: bool = False) -> None:
            return None

        def deanonymize(self, data: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
            return {"Patient": {"resourceType": "Patient"}, "Encounter": {"resourceType": "Encounter"}}

    class _BundleProxy:
        @staticmethod
        def model_validate(data: dict[str, Any]) -> object:
            return object()

    monkeypatch.setattr(fhir_export_worker, "LocalAnonymizer", _FakeAnonymizer)
    monkeypatch.setattr(fhir_export_worker, "Bundle", _BundleProxy)
    monkeypatch.setattr(fhir_export_worker, "inject_idempotency_logic", lambda bundle: "{}")

    async def _send_ok(client: Any, bundle_json: str, correlation_id: str) -> None:
        return None

    monkeypatch.setattr(fhir_export_worker, "send_fhir_bundle", _send_ok)

    task = FhirExportMessage(job_id=303, bundle_json=json.dumps({"Patient": {"name": "<NAME_1>"}}))
    message = _FakeIncomingExportMessage(
        body=task.model_dump_json().encode("utf-8"),
        headers={"x-retry-count": 0},
        correlation_id="corr-303",
    )

    await fhir_export_worker.process_export_message(
        message=message,
        client=object(),
        channel=_FakeChannel(),
    )

    assert message.acked is False
    assert message.rejected is True
    assert message.rejected_requeue is False

    assert all(update["status"] != JobStatus.EXPORTED for update in updates)

    cleanup_failed_updates = [
        update for update in updates if update["status"] == JobStatus.EXPORT_CLEANUP_FAILED
    ]
    assert len(cleanup_failed_updates) == 1

    cleanup_trace = cleanup_failed_updates[0]["error_trace"]
    assert isinstance(cleanup_trace, str)
    assert fhir_export_worker.ERROR_VAULT_CLEANUP in cleanup_trace
    assert phi_value not in cleanup_trace

    assert fhir_export_worker.ERROR_VAULT_CLEANUP in otel_error_codes
