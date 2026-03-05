---
name: instrumenting-opentelemetry
description: Sets the standard for enterprise observability using Prometheus and OpenTelemetry.
---

# Enterprise Observability & Telemetry (Tier 7)

In KRITIS environments, strict monitoring and observability of our AI components are mandatory. We need to track how long LLM inferences take, how often Pydantic validation fails (triggering retries), and the total end-to-end processing time of our autonomous background jobs.

## 1. Metrics Framework: `prometheus_client`

We use the official `prometheus_client` for Python to expose lightweight metrics directly via HTTP, which are then scraped by a central Prometheus instance.

### Key Metric Types to Use

- **Histogram**: Used for measuring durations (e.g., `llm_generation_duration_seconds`, `job_processing_duration_seconds`). Useful for calculating percentiles (p95, p99).
- **Counter**: Used for counting discrete events (e.g., `llm_validation_errors_total`, `jobs_processed_total`).
- **Gauge**: Used for current state that goes up and down (e.g., `active_jobs_in_queue`).

## 2. Naming Conventions

All metrics must follow these naming conventions:

- Use snake_case.
- End with a unit suffix if applicable (e.g., `_seconds`, `_total`).
- Prefix with the domain/component (e.g., `llm_`, `job_`).

Examples:

- `llm_generation_duration_seconds`
- `llm_validation_errors_total`
- `job_processing_duration_seconds`

## 3. Scrape Endpoints

Workers should expose a `/metrics` endpoint on port `8000` (or similar).

```python
from prometheus_client import start_http_server

if __name__ == "__main__":
    # Start up the server to expose the metrics.
    start_http_server(8000)
    # Start your worker loop...
```

## 4. Architectural Setup (Docker)

Prometheus runs locally via Docker Compose and scrapes internal container ports or the Docker host network using `host.docker.internal` for locally executed Python scripts.

Grafana is used for visualization, consuming metrics directly from the Prometheus container.

## 5. Distributed Tracing: Jaeger & OpenTelemetry

We use OpenTelemetry (OTel) to enable end-to-end distributed tracing across our asynchronous RabbitMQ components.

### Critical Architecture Rule: Manual Context Propagation

Do **NOT** rely on auto-instrumentation for message queues (like `AioPikaInstrumentor`) to carry context through complex async loops or thread pools. You MUST explicitly handle context propagation in all workers to prevent fragmented Jaeger traces:

1. **Extraction:** Extract trace context from incoming RabbitMQ headers.

   ```python
   from opentelemetry.propagate import extract
   ctx = extract(message.headers or {})
   ```

2. **Activation:** Explicitly attach the context *before* creating your span.

   ```python
   from opentelemetry import context as otel_context
   token = otel_context.attach(ctx)
   try:
       with tracer.start_as_current_span("process_message", context=ctx) as span:
           # Processing logic here...
   ```

3. **Injection:** When publishing to the next queue, explicitly inject the context into the outgoing message headers.

   ```python
   from opentelemetry.propagate import inject
   out_headers = {}
   inject(out_headers) 
   await exchange.publish(aio_pika.Message(body=data, headers=out_headers), routing_key="...")
   ```

4. **Cleanup:** Ensure context detach is called in a `finally` block to prevent leakage between RabbitMQ messages.

   ```python
   finally:
       otel_context.detach(token)
   ```
