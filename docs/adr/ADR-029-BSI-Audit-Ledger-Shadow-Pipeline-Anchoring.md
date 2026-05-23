# ADR-029: BSI Audit Ledger Shadow Pipeline Anchoring

## Status

Accepted (guardrail-only, runtime inactive)

## Date

2026-03-15

## Context

Future governance work may replicate selected audit or security events into a Kafka-based BSI audit-ledger shadow pipeline. Kafka can offer durable transport and replay, but Kafka alone is not a manipulationssicher anchor, and topic retention does not create immutability. This alignment track therefore documents only guardrails for a future shadow pipeline and does not claim live Kafka evidence or an active Kafka runtime.

## Decision

1. The BSI audit-ledger shadow pipeline remains prepared only and runtime inactive. No Kafka broker, compose service, producer, consumer, or runtime credential is introduced in the active stack.
2. Kafka topic retention, compaction, or broker replication is not treated as immutability, legal retention, or tamper-evident proof by itself.
3. Kafka alone is not a sufficient tamper-resistant anchor. Any future hash-chaining design must be anchored to an external immutable anchor or an equivalent independently auditable proof mechanism in a separate trust domain.
4. Any future audit-ledger publish must use its own destination-scoped outbox record, claim/lease lifecycle, publish fence, reconciliation path, and repair evidence under ADR-026. It must not share RabbitMQ claim or publish state.
5. Repair, replay, and backfill paths must remain auditable. Operator identity, reason, source range, resulting proof identifiers, and outcome must be retained as reviewable evidence outside the mutable publish stream.
6. Failure, lag, or repair of the audit-ledger shadow pipeline must never delay, block, or reinterpret RabbitMQ command semantics in the active runtime.
7. No operational verification is claimed for the audit-ledger shadow pipeline while Kafka remains inactive by design. A later rollout requires separate runtime evidence for anchor durability, replay auditability, and incident handling.

## Consequences

- Positive: The project avoids a false compliance claim that "Kafka retention equals immutable audit ledger".
- Positive: Future replay and repair work must produce auditable evidence instead of an opaque broker-side rewrite.
- Negative: A later rollout will need separate external anchoring, credentials, incident procedures, and validation evidence before any compliance claim is supportable.

## Verification Hooks

- `docs/adr/ADR-026-Destination-Scoped-Dual-Bus-Guardrails.md`
- `docs/security/control-mapping.md`
- `docs/security/threat-model.md`
- `tests/test_architecture_guards.py`
- `scripts/security/check_security_posture.py`
