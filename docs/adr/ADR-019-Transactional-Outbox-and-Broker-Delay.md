# ADR-019: Transactional Outbox and Broker-Side Delay

## Status

Accepted

## Context

The pipeline spans Postgres, RabbitMQ, MinIO, and a downstream FHIR server. Direct multi-write paths create orphan data, silent divergence, and duplicate publish risk under parallel dispatcher instances.

## Decision

1. Persist business state and outbox event in one database transaction.
2. Dispatch outbox events with a dedicated dispatcher process that claims events before publish.
3. Use a claim token plus lease on each outbox row so only claimed rows are publishable.
4. Allow restart recovery only by reclaiming expired leases; consumers remain idempotent via `consumed_messages`.
5. Route transient failures through broker-side retry queues with TTL.
6. Route permanent data failures to DLQ.
7. Route policy failures to a security alert queue.
8. Route downstream consistency failures to reconciliation.

## Consequences

- Success-path broker publishes move out of business workers.
- Retry delays no longer live in worker memory.
- Multiple dispatcher instances do not publish the same unclaimed `PENDING` row.
- Restart recovery may re-publish only after lease expiry; worker-side duplicate suppression remains mandatory.
- Reconciliation is explicit instead of buried in logs.

## Technical Evidence

- `src/fhirbridge/core/database.py`
- `src/fhirbridge/core/outbox_dispatcher.py`
- `tests/test_outbox_dispatcher.py`
