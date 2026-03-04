---
name: building-kritis-dashboards
description: Guides the agent to build secure, locally-hosted Streamlit dashboards for monitoring batch processes and auditing KI decisions, compliant with KRITIS environments (no external dependencies, safe database reads).
---

# KRITIS Dashboard Builder

You are a Frontend Security Engineer for FhirBridgeAI. Your objective is to build a modern, intuitive, and highly secure `Streamlit` dashboard that visualizes the progress of the RabbitMQ-driven extraction pipeline and provides an audit log for all LLM decisions.

## Core Architecture Principles

1. **Air-Gapped & Secure**: The UI must run 100% locally. Do NOT include ANY external CDN links, Google Fonts, or external tracking analytics in the Streamlit config or custom HTML components.
2. **Read-Only Database Access**: The dashboard is primarily an observer. When querying the Postgres database, ensure queries use a read-only connection (via `DATABASE_URL`) and proper SQLAlchemy session management to avoid interfering with worker writes.
3. **Auditability (KRITIS Focus)**: Every LLM transformation (from OCR Text -> FHIR JSON) must be traceable. The UI needs dedicated views allowing users to click a processed file and see:
   - The raw input (OCR text / HL7 message)
   - The intermediate LLM reasoning (if captured)
   - The final FHIR Resource

## Data Sources

The dashboard aggregates data from three distinct sources:

### a) Postgres (Read-Only) – Job Status Projection

- **Connection**: Via `DATABASE_URL` environment variable.
- **Purpose**: Read-only projection for job status, audit trail, and historical throughput metrics.
- **Pattern**: Use SQLAlchemy `sessionmaker` with `autocommit=False, autoflush=False`. All queries are SELECT-only.
- **Example metrics**: Total Jobs, Pending, Processing, Completed, Failed.

### b) RabbitMQ Management HTTP API – Queue Health

- **Connection**: Via `RABBITMQ_MANAGEMENT_URL` (e.g., `http://rabbitmq:15672`), authenticated with `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS`.
- **Purpose**: Live queue lengths, consumer counts, and Dead-Letter Queue (DLQ) counts.
- **Pattern**: Use `httpx` to call the RabbitMQ Management REST API endpoints (e.g., `/api/queues/%2f/<queue_name>`).
- **Example metrics**: Messages ready, Messages unacknowledged, DLQ depth per queue.

### c) Prometheus Metrics (Future) – via Grafana Datasource

- **Connection**: Via Grafana datasource configuration pointing to the `prometheus` service.
- **Purpose**: Long-term time-series metrics for latency percentiles, throughput rates, and error rates.
- **Note**: This datasource is planned for future integration. For now, the Streamlit dashboard covers operational monitoring; Grafana handles SRE-level observability.

## Workflow: Scaffolding a KRITIS Dashboard

1. **Setup the Framework**:
   - Create a structured Streamlit app entry point at `dashboard/app.py` with a multi-page setup or a sidebar for navigation (e.g., `Dashboard`, `Audit Log`, `Queue Health`, `Settings`).
2. **Database Integration (Postgres)**:
   - Write safe reading functions that connect to the Postgres database via `DATABASE_URL`.
   - Import the `Job` model and `JobStatus` enum from `src.fhirbridge.core.database`.
   - Example: Implement metrics for "Total Files", "Processing", "Success", and "Failed".
3. **Queue Health Integration (RabbitMQ)**:
   - Use `httpx` to query the RabbitMQ Management API for real-time queue statistics.
   - Display queue lengths, consumer counts, and DLQ depths as KPI cards.
4. **Visualization**:
   - Use built-in Streamlit charts (e.g., `st.bar_chart`, `st.metric`) or local Plotly/Altair visualizations to show throughput over time without relying on cloud rendering.
5. **Error Handling & Resilience**:
   - Wrap DB and HTTP calls in `try/except` and use `st.error` to gracefully handle connection failures or missing tables without crashing the UI.
