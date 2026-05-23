from __future__ import annotations

import logging
import sys
import types
import threading
from dataclasses import dataclass
from typing import Any

import pytest

pytest.skip(
    "Legacy OCR worker executor/tracer hooks changed in v0.2; requires rewrite for current outbox-driven worker.",
    allow_module_level=True,
)

for _module_name in ("cv2", "fitz", "numpy", "pytesseract"):
    if _module_name not in sys.modules:
        sys.modules[_module_name] = types.ModuleType(_module_name)

from fhirbridge.workers import ocr_worker


class _DummySpan:
    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def is_recording(self) -> bool:
        return True

    def set_status(self, status: Any) -> None:
        return None

    def add_event(self, name: str, attributes: dict[str, Any]) -> None:
        return None


class _DummySpanContext:
    def __enter__(self) -> _DummySpan:
        return _DummySpan()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


class _DummyTracer:
    def start_as_current_span(self, _name: str, context: Any = None) -> _DummySpanContext:
        return _DummySpanContext()


class _FailingS3Client:
    async def __aenter__(self) -> "_FailingS3Client":
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False

    async def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:
        raise RuntimeError("synthetic s3 failure")


class _FailingS3Session:
    def client(self, *args: Any, **kwargs: Any) -> _FailingS3Client:
        return _FailingS3Client()


class _FakeExchange:
    async def publish(self, message: Any, routing_key: str) -> None:
        return None


class _MessageProcessContext:
    def __init__(self, message: "_FakeIncomingMessage") -> None:
        self._message = message

    async def __aenter__(self) -> "_FakeIncomingMessage":
        return self._message

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        return False


@dataclass
class _FakeIncomingMessage:
    body: bytes
    headers: dict[str, Any] | None = None
    acked: bool = False
    rejected: bool = False

    def process(self, requeue: bool = False, ignore_processed: bool = True) -> _MessageProcessContext:
        return _MessageProcessContext(self)

    async def ack(self) -> None:
        self.acked = True

    async def reject(self, requeue: bool = False) -> None:
        self.rejected = True


class _FakeChannel:
    def __init__(self) -> None:
        self.default_exchange = _FakeExchange()


@pytest.fixture(autouse=True)
def run_to_thread_in_dedicated_test_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid asyncio default-executor shutdown hangs while preserving off-loop execution."""

    async def _dedicated_to_thread(func: Any, *args: Any, **kwargs: Any) -> Any:
        outcome: dict[str, Any] = {}

        def _target() -> None:
            try:
                outcome["value"] = func(*args, **kwargs)
            except BaseException as exc:
                outcome["error"] = exc

        worker = threading.Thread(target=_target, name="ocr-test-to-thread")
        worker.start()
        worker.join()

        if "error" in outcome:
            raise outcome["error"]
        return outcome.get("value")

    monkeypatch.setattr(ocr_worker.asyncio, "to_thread", _dedicated_to_thread)


@pytest.mark.asyncio
async def test_ocr_db_writes_are_offloaded_from_event_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    loop_thread_id = threading.get_ident()
    db_call_threads: list[int] = []

    monkeypatch.setattr(ocr_worker, "tracer", _DummyTracer())
    monkeypatch.setattr(ocr_worker.aioboto3, "Session", lambda: _FailingS3Session())

    # Guardrail: direct sync SessionFactory usage in async hot path must fail this test.
    def _forbid_direct_session_factory() -> Any:
        raise AssertionError("Direct SessionFactory access in async path is forbidden")

    monkeypatch.setattr(ocr_worker, "SessionFactory", _forbid_direct_session_factory)

    def _fake_update_job_status_sync(
        job_id: int,
        *,
        status: Any,
        ocr_text: str | None = None,
        error_trace: str | None = None,
    ) -> None:
        db_call_threads.append(threading.get_ident())

    monkeypatch.setattr(ocr_worker, "_update_job_status_sync", _fake_update_job_status_sync)

    body = b'{"job_id":1,"filepath":"C:/input/job_1.pdf","s3_object_key":"job_1_payload.pdf"}'
    message = _FakeIncomingMessage(body=body, headers={})

    await ocr_worker.process_ocr_message(message=message, channel=_FakeChannel())

    assert message.rejected is True
    assert db_call_threads
    assert all(tid != loop_thread_id for tid in db_call_threads)


@pytest.mark.asyncio
async def test_ocr_anonymizer_init_is_singleton_and_offloaded(monkeypatch: pytest.MonkeyPatch) -> None:
    loop_thread_id = threading.get_ident()
    init_threads: list[int] = []

    class _FakeAnonymizer:
        def __init__(self) -> None:
            init_threads.append(threading.get_ident())

    monkeypatch.setattr(ocr_worker, "LocalAnonymizer", _FakeAnonymizer)
    monkeypatch.setattr(ocr_worker, "_WORKER_ANONYMIZER", None)
    monkeypatch.setattr(ocr_worker, "_WORKER_ANONYMIZER_LOCK", None)

    first = await ocr_worker._get_worker_anonymizer()
    second = await ocr_worker._get_worker_anonymizer()

    assert first is second
    assert len(init_threads) == 1
    assert init_threads[0] != loop_thread_id


# ---------------------------------------------------------------------------
# P1 Tests: Executor Lifecycle & PHI-Safe Error Handling
# ---------------------------------------------------------------------------


def test_executor_not_created_per_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    ProcessPoolExecutor MUST be instantiated exactly once per worker lifetime.

    Regression guard: each call to _get_ocr_executor() (one per consumed message)
    must return the SAME pool instance without forking new OS processes.
    Anti-pattern guarded: creating a new ProcessPoolExecutor per message
    causes ~300 ms fork+import overhead per job under load.
    """
    init_count = 0
    atexit_calls: list[Any] = []

    class _SpyExecutor:
        """Lightweight spy — does not fork real OS processes."""

        def __init__(self, max_workers: int | None = None) -> None:
            nonlocal init_count
            init_count += 1
            self.max_workers = max_workers

        def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
            pass  # No real processes to clean up in tests.

    # Isolate: reset module state and inject spy.
    monkeypatch.setattr(ocr_worker, "_OCR_EXECUTOR", None)
    monkeypatch.setattr(ocr_worker, "ProcessPoolExecutor", _SpyExecutor)
    # Suppress atexit registration to avoid test-suite side-effects.
    monkeypatch.setattr("atexit.register", lambda fn, *a, **kw: atexit_calls.append(fn))

    e1 = ocr_worker._get_ocr_executor()
    e2 = ocr_worker._get_ocr_executor()
    e3 = ocr_worker._get_ocr_executor()

    assert init_count == 1, (
        f"ProcessPoolExecutor was instantiated {init_count} time(s); "
        "expected exactly 1 — executor must be a module-level singleton."
    )
    assert e1 is e2 is e3, "All calls must return the same executor instance."

    # atexit handler must have been registered (once, on first init).
    assert len(atexit_calls) == 1
    assert atexit_calls[0] is ocr_worker._shutdown_ocr_executor

    # Cleanup: restore module state for subsequent tests.
    monkeypatch.setattr(ocr_worker, "_OCR_EXECUTOR", None)


def test_executor_shutdown_called_on_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    _shutdown_ocr_executor() must call executor.shutdown(wait=True) and clear
    the module reference so no further work is submitted after shutdown begins.

    Tests both:
    - Correct shutdown kwargs (wait=True, cancel_futures=True for Python ≥ 3.9)
    - Module reference set to None (prevents post-shutdown job submission)
    """
    shutdown_calls: list[dict[str, Any]] = []

    class _MockExecutor:
        def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
            shutdown_calls.append({"wait": wait, "cancel_futures": cancel_futures})

    monkeypatch.setattr(ocr_worker, "_OCR_EXECUTOR", _MockExecutor())

    ocr_worker._shutdown_ocr_executor()

    assert len(shutdown_calls) == 1, "executor.shutdown() must be called exactly once."
    assert shutdown_calls[0]["wait"] is True, "shutdown must use wait=True for graceful drain."
    assert shutdown_calls[0]["cancel_futures"] is True, (
        "shutdown must cancel pending futures to avoid blocking indefinitely."
    )
    assert ocr_worker._OCR_EXECUTOR is None, (
        "_OCR_EXECUTOR must be cleared so no new work is submitted after shutdown."
    )


def test_extract_raw_ocr_phi_safe_error_log(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    When Tesseract raises an exception, the exception MESSAGE must NOT appear in logs.
    Tesseract error messages can include OCR fragment output (partial patient names,
    file paths with patient IDs) — logging str(exc) would constitute a PHI leak.

    Compliance: BSI 200-1 §6.2, ADR-011 Zero-Trust PHI.
    """
    import cv2 as _cv2
    import fitz as _fitz
    import numpy as _np
    import pytesseract as _pytess

    # A string that looks like PHI — must NEVER appear in log output.
    PHI_SENTINEL = "Patient:Mustermann,Heinrich,DOB:1959-03-07,ID:0815"

    # --- Minimal OpenCV/PyMuPDF pipeline mocks ---
    class _FakeArr:
        """Mimics numpy ndarray: supports reshape() and passes cv2 functions."""

        def reshape(self, *args: Any) -> "_FakeArr":
            return self

    class _FakePixmap:
        n = 3  # RGB path (skips RGBA branch)
        height = 2
        width = 2
        samples = bytes(12)  # 2×2×3 bytes

    class _FakePage:
        def get_pixmap(self, dpi: int) -> _FakePixmap:
            return _FakePixmap()

    class _FakeDoc:
        def __len__(self) -> int:
            return 1

        def load_page(self, i: int) -> _FakePage:
            return _FakePage()

    fake_arr = _FakeArr()
    # raising=False is required for stub modules that don't pre-define these attributes.
    monkeypatch.setattr(_fitz, "open", lambda **kwargs: _FakeDoc(), raising=False)
    monkeypatch.setattr(_np, "uint8", None, raising=False)  # dtype attribute access only
    monkeypatch.setattr(_np, "frombuffer", lambda data, dtype=None: fake_arr, raising=False)
    for attr in (
        "COLOR_RGB2BGR",
        "COLOR_RGBA2BGR",
        "COLOR_GRAY2BGR",
        "COLOR_BGR2GRAY",
        "THRESH_BINARY",
        "THRESH_OTSU",
    ):
        monkeypatch.setattr(_cv2, attr, 0, raising=False)
    monkeypatch.setattr(_cv2, "cvtColor", lambda img, code: img, raising=False)
    monkeypatch.setattr(_cv2, "GaussianBlur", lambda img, ksize, sigma: img, raising=False)
    monkeypatch.setattr(_cv2, "threshold", lambda img, thresh, maxval, flags: (None, img), raising=False)

    # Tesseract raises with PHI-carrying message (real-world scenario).
    def _raise_with_phi(*args: Any, **kwargs: Any) -> str:
        raise RuntimeError(PHI_SENTINEL)

    monkeypatch.setattr(_pytess, "image_to_string", _raise_with_phi, raising=False)

    with caplog.at_level(logging.ERROR, logger="OCRWorker"):
        result = ocr_worker.extract_raw_ocr_sync(b"fake-pdf-bytes")

    assert result == "", "Expected empty string when all pages fail OCR."
    assert PHI_SENTINEL not in caplog.text, (
        "PHI (exception message) must NOT appear in logs — "
        "Tesseract may include OCR fragments in error messages."
    )
    assert "RuntimeError" in caplog.text, (
        "Exception type must be logged for auditability (non-PHI metadata)."
    )


@pytest.mark.asyncio
async def test_ocr_otel_span_phi_safe_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    OTel error spans must contain exception type and error code but NOT the
    exception message — which may carry PHI from S3 responses, Tesseract output,
    or DB error strings.

    Verifies: mark_span_error() contract holds end-to-end in process_ocr_message().
    Compliance: ADR-011, OWASP Sensitive Data Exposure.
    """
    span_events: list[dict[str, Any]] = []

    class _RecordingSpan:
        def set_attribute(self, key: str, value: Any) -> None:
            pass

        def is_recording(self) -> bool:
            return True

        def set_status(self, status: Any) -> None:
            pass

        def add_event(self, name: str, attributes: dict[str, Any]) -> None:
            span_events.append({"name": name, "attributes": dict(attributes)})

    class _RecordingSpanContext:
        def __enter__(self) -> _RecordingSpan:
            return _RecordingSpan()

        def __exit__(self, *args: Any) -> bool:
            return False

    class _RecordingTracer:
        def start_as_current_span(self, name: str, context: Any = None) -> _RecordingSpanContext:
            return _RecordingSpanContext()

    # PHI_SENTINEL is the RuntimeError message raised by _FailingS3Client.get_object.
    # This string must NOT appear in any OTel span attribute.
    PHI_SENTINEL = "synthetic s3 failure"

    monkeypatch.setattr(ocr_worker, "tracer", _RecordingTracer())
    monkeypatch.setattr(ocr_worker.aioboto3, "Session", lambda: _FailingS3Session())
    monkeypatch.setattr(ocr_worker, "_update_job_status_sync", lambda *a, **kw: None)

    body = b'{"job_id":42,"filepath":"test.pdf","s3_object_key":"test.pdf"}'
    message = _FakeIncomingMessage(body=body, headers={})

    await ocr_worker.process_ocr_message(message=message, channel=_FakeChannel())

    assert message.rejected is True, "Message must be rejected after unrecoverable OCR failure."

    # Check that no span attribute value contains the exception message.
    all_attr_values = str([e["attributes"] for e in span_events])
    assert PHI_SENTINEL not in all_attr_values, (
        "Exception message (potential PHI) must NOT appear in OTel span attributes."
    )

    # At least one error event must exist with the correct minimal structure.
    error_events = [e for e in span_events if e.get("name") == "exception"]
    assert error_events, "Expected at least one OTel 'exception' event on OCR failure."
    for event in error_events:
        attrs = event["attributes"]
        assert "exception.type" in attrs, "exception.type must be present for error classification."
        assert "exception.message" not in attrs, (
            "exception.message must NOT be in span attributes — PHI risk."
        )
        assert "error.code" in attrs, "error.code must be present for auditability."
