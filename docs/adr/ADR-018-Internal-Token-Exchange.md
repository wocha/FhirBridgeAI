# ADR-018: Internal Token Exchange for Worker Handoffs

## Status

Accepted

## Context

End-user JWTs must not be forwarded into RabbitMQ payloads, deep workers, or future Qdrant paths.

## Decision

Validate the external JWT only at the ingestion boundary and immediately exchange it for a minimal signed internal auth context that carries only:

- `trace_id`
- `tenant_scope`
- `actor_id`
- `role_scope`
- `authz_decision_id`
- `token_expiry`
- `break_glass_flag`

The internal auth context is bound to an event id and verified again by each worker.

## Consequences

- Downstream workers never see the original user JWT.
- Replay attempts fail when the bound event id does not match.
- Break-glass remains visible as a dedicated audit event, not as a silent role exception.
