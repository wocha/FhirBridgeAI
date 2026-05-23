import logging
import os
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import StatusCode

logger = logging.getLogger(__name__)


def init_tracer(service_name: str) -> trace.Tracer:
    """
    Initializes and returns an OpenTelemetry Tracer.
    Uses BatchSpanProcessor to avoid blocking the asyncio event loop.
    Exports to Jaeger via OTLP gRPC.
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # Use BatchSpanProcessor for async/non-blocking export
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)


def mark_span_error(
    span: Any,
    exc: Exception,
    *,
    error_code: str = "",
    component: str = "",
) -> None:
    """Mark an OTel span as errored WITHOUT leaking PHI.

    Zero-Trust Rule:
        - NEVER call ``span.record_exception(exc)`` — exception payloads may
          contain Protected Health Information (names, dates, IDs).
        - Only the *type name* of the exception is recorded as a safe
          ``error.type`` attribute. An optional ``error_code`` (e.g.
          ``"DEANONYMIZE_VALUE_ERROR"``) is added for structured alerting.

    This function is the single authorised way to flag span errors across the
    entire FhirBridgeAI codebase.
    """
    exc_type_name = type(exc).__name__
    description = error_code if error_code else exc_type_name

    span.set_status(StatusCode.ERROR, description)
    span.set_attribute("error.type", exc_type_name)

    if error_code:
        span.set_attribute("error.code", error_code)
    if component:
        span.set_attribute("error.component", component)


def set_outcome_attributes(
    span: Any,
    *,
    category: str,
    action: str,
    retry_count: int | None = None,
) -> None:
    span.set_attribute("failure.category", category)
    span.set_attribute("failure.action", action)
    if retry_count is not None:
        span.set_attribute("messaging.retry_count", retry_count)
