---
name: migrating-to-rabbitmq
description: Guides the agent to migrate from legacy local queue patterns to a horizontally scalable RabbitMQ architecture, utilizing At-Least-Once Delivery and Dead-Letter-Exchange (DLX).
---

# Migrating to RabbitMQ (Tier 8 Enterprise Architecture)

## Context

Our project originally utilized a legacy local job queue (`background_jobs` table) in `db_worker.py`. That pattern cannot satisfy the horizontal-scaling and recovery requirements of the hardened runtime, so the messaging layer is migrated to RabbitMQ.

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

5. **Tier 1 Retry Pattern (Zero-Code Delay)**:
   For operations that can fail due to transient network issues (e.g., HTTP POST to external servers), use the "Zero-Code Delay" pattern to implement Dead-Lettering with Exponential Backoff. **Never** use `asyncio.sleep()` or similar blocking calls in a consumer, as this creates a "Stateful Sinner" that blocks the event loop and holds unacknowledged messages in RAM.
   - **No Consumer on Retry Queue**: The retry queue (`*_retry_queue`) must not have an active consumer.
   - **DLX Routing**: Configure the retry queue with `x-dead-letter-exchange` pointing back to the main exchange (or `""` for default) and `x-dead-letter-routing-key` pointing back to the main queue.
   - **Manual Publish to DLX**: When a transient error occurs in the main consumer, calculate the next delay (e.g., `delay = BASE_DELAY * (2 ** retry_count)`) and manually publish a new message to the dedicated retry exchange (`*_retry.dlx`) with the `expiration` property set to the delay in milliseconds.
   - **Ack Original**: Acknowledge (`ack()`) the original message in the main consumer.
   - **Passive Waiting**: The message waits passively on disk in the retry queue until the TTL expires, at which point RabbitMQ automatically pushes it back to the main queue for another attempt.

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
