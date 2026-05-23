# ADR-028: Research Bridge Isolation and Advisory-Only Retrieval

## Status

Accepted (guardrail-only, runtime inactive)

## Date

2026-03-15

## Context

ADR-023 already records that live Qdrant tenant-isolation evidence is not yet operationally proven. At the same time, future research work may want retrieval hints, similarity search, or a Kafka-backed research bridge into a separate research zone. Those paths must not become an unreviewed runtime shortcut or a return channel into clinical command processing.

## Decision

1. The Research-Bridge shadow pipeline remains prepared only and runtime inactive. No Kafka broker, compose service, producer, consumer, or hidden activation shortcut is introduced into the active runtime.
2. Production KRITIS data may flow only one-way into a future research zone. No return path is permitted from the research bridge into operational RabbitMQ queues, operational Postgres state, MinIO evidence buckets, or export workers.
3. A future research bridge must use separate credentials, separate tenant boundaries, separate storage/network isolation, and a separate incident model from the operational command path.
4. Under ADR-026, any future research-bridge publish requires its own destination-scoped outbox record, claim/lease lifecycle, publish fence, reconciliation path, and repair evidence.
5. Qdrant retrieval, research-bridge output, and RAG hints remain advisory-only. No operational worker may auto-export, auto-merge, auto-match, or otherwise grant operational authority based on retrieval similarity or research output.
6. The LLM worker may record semantic chunks for later governed ingestion, but it must stop at manual review before any export side effect.
7. Manual review remains the fail-closed gate whenever retrieval evidence is incomplete or ambiguous.
8. No operational verification is claimed for the Research-Bridge shadow pipeline while Kafka remains inactive by design.

## Consequences

- Positive: Research experiments can continue without creating a backchannel into the operational KRITIS runtime.
- Positive: Advisory evidence remains visible to reviewers while staying non-authoritative.
- Negative: Straight-through automation stays intentionally limited until ADR-023 is operationally closed and a separate research-zone rollout is approved.

## Verification Hooks

- `docs/adr/ADR-023-Qdrant-Live-Evidence-Exception.md`
- `docs/adr/ADR-026-Destination-Scoped-Dual-Bus-Guardrails.md`
- `docs/security/control-mapping.md`
- `docs/security/threat-model.md`
- `tests/test_architecture_guards.py`
