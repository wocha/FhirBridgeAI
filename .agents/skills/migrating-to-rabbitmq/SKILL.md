---
name: migrating-to-rabbitmq
description: Guides the agent to migrate from SQLite-backed queues to a horizontally scalable RabbitMQ architecture, utilizing At-Least-Once Delivery and Dead-Letter-Exchange (DLX).
---

# Migrating to RabbitMQ (Tier 8 Enterprise Architecture)

## Context

Our project originally utilized SQLite for the job queue (`background_jobs` table) in `db_worker.py`. However, SQLite cannot handle high-throughput concurrent writes and locks gracefully when scaling horizontally across multiple worker nodes. Therefore, we migrated the messaging layer to RabbitMQ.

## Canonical Implementations

The production workers live in the main package and are the source of truth:

| Component | File | Role |
|-----------|------|------|
| Connection & DLX Setup | `src/fhirbridge/core/rabbitmq.py` | `init_rabbitmq()`, Pydantic message models, DLX binding |
| Database (results only) | `src/fhirbridge/core/database.py` | `Job` model, `init_db()`, WAL mode for concurrent reads |
| OCR Consumer | `src/fhirbridge/workers/ocr_worker.py` | Ingests PDFs → OCR → publishes to `llm_task_queue` |
| LLM Consumer | `src/fhirbridge/workers/llm_worker.py` | Consumes OCR text → LLM extraction → stores FHIR JSON |

The prototype in `scripts/mq_worker.py` is a simplified, standalone reference implementation for learning purposes.

## Architecture Principles

1. **At-Least-Once Delivery**: Workers must never `basic_ack` a message until the full processing lifecycle completes and the result is safely committed to the database. See `process_llm_message()` and `process_ocr_message()` for the canonical ACK-after-commit pattern.

2. **Dead-Letter Exchange (DLX)**: Any message that fails decisively is rejected (`message.reject(requeue=False)`). The queue is configured with `x-dead-letter-exchange` and `x-dead-letter-routing-key` so that unprocessable messages are safely parked in `dead_letter_queue` for manual review.

3. **No Database Queue Locks**: The `fhirbridge` database stores *results* (FHIR JSON, OCR text, audit logs) and status updates, but is **never** used for queue distribution. RabbitMQ handles all message routing and fair dispatch via `prefetch_count`.

4. **Async-First**: All workers use `aio-pika` with `asyncio.to_thread()` for CPU-heavy work (OCR, LLM calls) to avoid blocking the AMQP heartbeat.

## Queue Topology

```
      ┌──────────────────┐
      │  ocr_task_queue   │──→ OCR Worker ──→ llm_task_queue
      └──────────────────┘
      ┌──────────────────┐
      │  llm_task_queue   │──→ LLM Worker ──→ DB (FHIR_GENERATED)
      └──────────────────┘
              │ (on reject)
              ▼
      ┌──────────────────┐
      │ dead_letter_queue │  ← fhirbridge.dlx exchange
      └──────────────────┘
```

## Docker Compose

RabbitMQ is defined in the project root `docker-compose.yml` as `rabbitmq:3.13-management-alpine` with ports `5672` (AMQP) and `15672` (Management UI). Workers depend on the `rabbitmq` service with `condition: service_healthy`.
