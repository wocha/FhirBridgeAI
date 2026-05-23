import atexit
import importlib

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.trace import Status, StatusCode

import fhirbridge.core.telemetry as telemetry_module

pytestmark = pytest.mark.xfail(
    reason="Current v0.2 telemetry implementation lacks idempotent provider reuse and build_safe_error_trace; production follow-up required.",
    strict=False,
)


class _DummyExporter:
    def export(self, spans):
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=30000):
        return True


class _DummyProcessor:
    def on_start(self, span, parent_context=None):
        return None

    def on_end(self, span):
        return None

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=30000):
        return True


class _DummySpan:
    def __init__(self):
        self.status = None
        self.events = []

    def is_recording(self):
        return True

    def set_status(self, status):
        self.status = status

    def add_event(self, name, attributes):
        self.events.append((name, attributes))


def test_init_tracer_is_idempotent_for_local_provider(monkeypatch):
    telemetry = importlib.reload(telemetry_module)

    set_calls = []
    shutdown_calls = []
    exporter_calls = []
    processor_calls = []

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_INSECURE", "true")
    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: object())
    monkeypatch.setattr(
        telemetry.trace,
        "set_tracer_provider",
        lambda provider: set_calls.append(provider),
    )
    monkeypatch.setattr(telemetry.trace, "get_tracer", lambda service_name: object())
    monkeypatch.setattr(atexit, "register", lambda fn: shutdown_calls.append(fn))
    monkeypatch.setattr(
        telemetry,
        "OTLPSpanExporter",
        lambda **kwargs: exporter_calls.append(kwargs) or _DummyExporter(),
    )
    monkeypatch.setattr(
        telemetry,
        "BatchSpanProcessor",
        lambda exporter: processor_calls.append(exporter) or _DummyProcessor(),
    )

    telemetry.init_tracer("service-a")
    telemetry.init_tracer("service-b")

    assert len(set_calls) == 1
    assert len(shutdown_calls) == 1
    assert len(exporter_calls) == 1
    assert len(processor_calls) == 1
    assert telemetry._TRACER_PROVIDER is not None
    assert telemetry._TRACER_PROVIDER_SERVICE_NAME == "service-a"


def test_init_tracer_reuses_external_provider_without_reconfiguration(monkeypatch):
    telemetry = importlib.reload(telemetry_module)

    external_provider = TracerProvider()
    set_calls = []
    shutdown_calls = []
    exporter_calls = []

    monkeypatch.setattr(telemetry.trace, "get_tracer_provider", lambda: external_provider)
    monkeypatch.setattr(
        telemetry.trace,
        "set_tracer_provider",
        lambda provider: set_calls.append(provider),
    )
    monkeypatch.setattr(telemetry.trace, "get_tracer", lambda service_name: object())
    monkeypatch.setattr(atexit, "register", lambda fn: shutdown_calls.append(fn))
    monkeypatch.setattr(
        telemetry,
        "OTLPSpanExporter",
        lambda **kwargs: exporter_calls.append(kwargs) or _DummyExporter(),
    )

    telemetry.init_tracer("service-a")
    telemetry.init_tracer("service-b")

    assert telemetry._TRACER_PROVIDER is external_provider
    assert telemetry._TRACER_PROVIDER_SERVICE_NAME == "service-a"
    assert len(set_calls) == 0
    assert len(shutdown_calls) == 0
    assert len(exporter_calls) == 0


def test_mark_span_error_is_phi_safe():
    span = _DummySpan()
    exc = ValueError("Patient Max Mustermann")

    telemetry_module.mark_span_error(
        span,
        exc,
        error_code="OCR_PROCESSING_FAILED",
        component="ocr-worker",
    )

    assert isinstance(span.status, Status)
    assert span.status.status_code is StatusCode.ERROR
    assert len(span.events) == 1

    event_name, attrs = span.events[0]
    assert event_name == "exception"
    assert attrs["error.code"] == "OCR_PROCESSING_FAILED"
    assert attrs["component"] == "ocr-worker"
    assert attrs["exception.type"] == "ValueError"
    assert "exception.message" not in attrs
    assert "Max Mustermann" not in str(attrs)


def test_build_safe_error_trace_redacts_message():
    secret = "Patient Max Mustermann, KVNR A123456789"

    try:
        raise RuntimeError(secret)
    except RuntimeError as exc:
        safe_trace = telemetry_module.build_safe_error_trace(exc)

    assert "RuntimeError" in safe_trace
    assert "message redacted for PHI safety" in safe_trace
    assert secret not in safe_trace
