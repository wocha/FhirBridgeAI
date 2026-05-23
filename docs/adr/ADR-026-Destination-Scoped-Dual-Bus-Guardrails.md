# ADR-026: Destination-Scoped Dual-Bus Guardrails for Kafka Preparation

## Status

Accepted (guardrail-only, runtime inactive)

## Date

2026-03-15

## Context

The ingestion slice continues to use RabbitMQ as the operational command bus under ADR-019 and ADR-025. Kafka may be prepared for future evidence replication or research fan-out, but a naive "one outbox row, two best-effort publishes" pattern would break the existing claim, fencing, and reconciliation guarantees.

## Decision

1. RabbitMQ remains the only active command bus in the runtime compose for this alignment track.
2. Kafka preparation is limited to ADRs, threat-model text, control mappings, and architecture guardrails. No Kafka broker, compose service, producer, consumer, runtime library, or hidden feature-flag shortcut is introduced into the active runtime.
3. If Kafka shadow pipelines are introduced later, each destination must have its own outbox record, dedupe key, claim token, lease lifecycle, publish-attempt fence, reconciliation workflow, and repair evidence.
4. A single outbox record must never publish to RabbitMQ and Kafka, and RabbitMQ/Kafka must never share claim state, lease renewal, publish fencing, escalation, or reconciliation state.
5. Shared claim, shared lease, shared publish fence, or shared repair bookkeeping across RabbitMQ and Kafka is forbidden even for "shadow-only" or "best-effort" fan-out.
6. RabbitMQ command semantics remain authoritative. Failure, lag, replay, repair, or outage in any future Kafka shadow pipeline must never delay, block, reorder, reinterpret, or auto-retry operational RabbitMQ command dispatch.
7. Any future Kafka activation requires explicit ADR approval, destination-specific schema and migration work, dedicated credentials, destination-scoped reconciliation, and fresh runtime evidence. A config-only or compose-only shortcut is not approved.

## Consequences

- Positive: Kafka readiness can be designed without weakening the proven RabbitMQ outbox contract.
- Positive: Ambiguous publish handling stays destination-scoped and auditable instead of being buried in a mixed publish path.
- Positive: RabbitMQ command delivery remains isolated from future audit-ledger and research-bridge shadow failures.
- Negative: Future dual-bus rollout will require explicit schema, dispatcher, reconciliation, and incident-model work instead of a shortcut toggle.

## Verification Hooks

- `docs/adr/ADR-028-Research-Isolation-and-Advisory-Only-Retrieval.md`
- `docs/adr/ADR-029-BSI-Audit-Ledger-Shadow-Pipeline-Anchoring.md`
- `docs/security/threat-model.md`
- `tests/test_outbox_dispatcher.py`
- `tests/test_architecture_guards.py`
- `scripts/security/check_security_posture.py`
- `docs/security/control-mapping.md`
