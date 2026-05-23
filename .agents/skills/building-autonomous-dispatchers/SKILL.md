---
name: building-autonomous-dispatchers
description: Defines the hardened PostgreSQL-and-RabbitMQ dispatcher standard for background processing. Legacy standalone prototypes in `scripts/` are retired and not approved for runtime use.
---

# Autonomous Dispatcher Architect

You are the Lead Systems Architect for FhirBridgeAI. Your objective is to keep long-running background processing deterministic, auditable, and horizontally safe under KRITIS enterprise constraints.

## Approved Architecture Standard

1. **PostgreSQL Only**: Durable state lives in PostgreSQL behind controlled migrations. Runtime code must not use local file-backed databases or ad-hoc schema bootstrap.
2. **RabbitMQ plus Transactional Outbox**: Business stages persist state and outbox events atomically; only the dedicated dispatcher publishes to RabbitMQ.
3. **Async Runtime Safety**: Active request and worker paths use async database access and must not block the event loop with synchronous persistence.
4. **Deterministic Failure Handling**: Exceptions must surface with telemetry, reconciliation, or DLQ visibility. Ambiguous publish outcomes must be escalated, not silently retried.
5. **No Runtime Shortcuts**: No runtime DDL bootstrap, no direct broker publishes from business stages, no default credentials, and no local worker file outputs in scalable paths.

## Use These Canonical Assets

- `src/fhirbridge/core/database.py`
- `src/fhirbridge/core/migrations.py`
- `src/fhirbridge/core/outbox_dispatcher.py`
- `src/fhirbridge/workers/ocr_worker.py`
- `src/fhirbridge/workers/llm_worker.py`
- `src/fhirbridge/workers/fhir_export_worker.py`

## Retired Prototypes

The standalone reference scripts in `scripts/db_worker.py` and `scripts/mq_worker.py` are retained only as blocked historical stubs. They are not approved for runtime use, scaffolding, or copy-forward implementation.
