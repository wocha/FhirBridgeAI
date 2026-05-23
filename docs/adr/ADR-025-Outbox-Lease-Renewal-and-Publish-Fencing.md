# ADR-025: Outbox Lease Renewal and Publish Fencing

## Status

Accepted

## Context

`FOR UPDATE SKIP LOCKED` prevents concurrent claims at claim time, but it does not by itself protect against a slow or hanging publish that outlives the original lease. Without additional fencing, a second dispatcher could reclaim the same event after lease expiry and publish it again while the first publish attempt is still in flight. A plain `CLAIMED` row is therefore not a safe terminal state once broker publish has already started.

## Decision

1. Claim state is split into two phases:
   - `CLAIMED` without `publish_attempt_id` means the worker owns the lease but has not yet started broker publish and may be reclaimed after lease expiry.
   - `CLAIMED` with a persisted `publish_attempt_id` means broker publish has started and the row is never auto-claimable again.
2. Each claimed outbox event receives a unique `publish_attempt_id` before the dispatcher starts broker publish.
3. The dispatcher renews the claim lease on a fixed heartbeat interval while publish is in flight.
4. Final `DISPATCHED` transition is fenced by both `claim_token` and `publish_attempt_id`.
5. If publish confirmation becomes ambiguous because of timeout, lease-loss, or another publish-path exception, the dispatcher writes `ESCALATED` and creates the reconciliation task in the same database transaction.
6. Reconciliation is created only after the `ESCALATED` row update is positively confirmed.
7. If the `ESCALATED` write cannot be confirmed, the dispatcher persists `FATAL_ESCALATION_FAILED` and a dedicated fatal reconciliation entry instead of leaving the row in a recyclable state.
   - The fatal fallback is fenced to the same publish instance as the normal escalation path: `event_id + claim_token + publish_attempt_id`.
8. If the fatal-quarantine transaction itself cannot commit, the previously persisted `publish_attempt_id` still blocks auto-claiming of that row; the dispatcher stops fail-closed and manual recovery is required.
9. Neither `ESCALATED` nor `FATAL_ESCALATION_FAILED` is ever auto-returned to `PENDING`; recovery is explicit and manual.

## State Machine

- `PENDING`: claimable by dispatcher.
- `CLAIMED` without `publish_attempt_id`: lease-owned, pre-publish, reclaimable after lease expiry.
- `CLAIMED` with `publish_attempt_id`: publish in flight or publish outcome unresolved, never auto-claimable.
- `ESCALATED`: ambiguous publish was atomically recorded and routed to standard reconciliation.
- `FATAL_ESCALATION_FAILED`: standard escalation write could not be confirmed; row is quarantined and routed to fatal reconciliation / incident handling.
- `DISPATCHED`: terminal success.

## Consequences

- Slow publish no longer becomes eligible for a second dispatcher merely because the original lease duration elapsed.
- Ambiguous broker outcomes are contained instead of retried blindly.
- There is no supported state in which a reconciliation task exists without a confirmed `ESCALATED` outbox row.
- `CLAIMED` after broker publish has started is no longer a recyclable runtime state.
- Failure to persist the `ESCALATED + reconciliation` pair is treated as a visible hard failure, not as a best-effort retry path.
- The fatal fallback does not broaden authority beyond the original publish instance; it cannot quarantine an unrelated claim attempt.
- Manual recovery is mandatory for `FATAL_ESCALATION_FAILED` or claim-blocked started-publish rows; no automatic retry path exists.

## Technical Evidence

- `src/fhirbridge/core/database.py`
- `src/fhirbridge/core/outbox_dispatcher.py`
- `tests/test_outbox_dispatcher.py`
- `tests/test_postgres_runtime_harness.py`
- `docs/security/test-evidence-2026-03-15.md`

## Time-Boxed Exception

No additional architecture exception is introduced by this ADR.
