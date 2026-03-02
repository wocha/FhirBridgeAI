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
