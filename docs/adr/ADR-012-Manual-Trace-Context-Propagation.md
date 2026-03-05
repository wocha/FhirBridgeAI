# ADR-012: Manual Trace Context Propagation in RabbitMQ

## Status

Accepted

## Context

During the implementation of distributed tracing via OpenTelemetry and Jaeger, we experienced "Context Loss" across asynchronous microservice boundaries. The automated `AioPikaInstrumentor` proved unreliable when context was passed through `aio_pika` consumers, down to background thread pools (e.g., OCR ProcessPoolExecutor), and back to `aio_pika` exchanges.
This resulted in severed traces; the full DAG from ingestion to FHIR export was broken, displaying fragmented, isolated traces for each worker.

## Decision

We enforce **strikte, manuelle Context-Propagation** (Manual Context Propagation Pattern) across all our asyncio message-consuming workers.

1. **Extraction:** Incoming trace contexts must be explicitly extracted from RabbitMQ headers (`opentelemetry.propagate.extract`).
2. **Activation:** The extracted context must be attached to the current runtime context using `token = opentelemetry.context.attach(ctx)` *before* starting the new span.
3. **Injection:** When publishing subsequent messages to the next queue, the context must be explicitly injected back into the outgoing headers using `opentelemetry.propagate.inject(outgoing_headers)`.
4. **Cleanup:** Context leakage between different incoming messages must be prevented by strictly calling `opentelemetry.context.detach(token)` within a `finally` block enclosing the entire message processing logic.

## Consequences

- **Positive:** Guaranteed end-to-end tracing spanning the entire distributed architecture. No more fragmented DAGs in Jaeger.
- **Negative:** Increased boilerplate code. Every worker requires a carefully structured `try...finally` block to manage the `otel_context` token, which adds slight complexity to the worker codebase.
- **Rules:** Engineers must NOT rely solely on auto-instrumentation for message brokers in our async stack. Manual injection/extraction becomes our Tier-1 KRITIS Standard for tracing.
