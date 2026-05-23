# Reconciliation Runbook

## Trigger

Use this runbook when a message or workflow is routed to the reconciliation queue, when a `reconciliation_tasks` row is created, or when an outbox row enters `FATAL_ESCALATION_FAILED`.

## Detection

1. Check RabbitMQ `reconciliation_queue` backlog.
2. Query `reconciliation_tasks` for `status=OPEN`.
3. Correlate with `trace_id`, `job_id`, `source_event_id`, and any outbox `claim_token` still present.
4. Verify the active schema version before making repair writes.
5. Treat either of these as an immediate manual incident:
   - `outbox_events.status = FATAL_ESCALATION_FAILED`
   - `outbox_events.status = CLAIMED` with `publish_attempt_id IS NOT NULL`, even when `claim_expires_at` is already in the past

## Triage

1. Confirm whether the downstream side effect already committed.
2. Confirm whether the outbox event was already dispatched.
3. Confirm whether duplicate suppression already recorded the source event.
4. Confirm whether the read model is stale because `required_version > visible_version`.
5. For `FATAL_ESCALATION_FAILED`, capture the exact `claim_token`, `publish_attempt_id`, `last_error`, and matching reconciliation row before any repair write.
6. For `CLAIMED + publish_attempt_id`, treat the row as publish-ambiguous and non-reclaimable until a human determines whether the downstream side effect happened.

## Repair Actions

1. If downstream committed and local status is stale:
   - update local job state to the intended terminal state
   - set read-model visible version to the repaired aggregate version
   - mark reconciliation task `RESOLVED`
2. If downstream did not commit:
   - create a fresh replacement outbox event or work item with a new event identity
   - preserve the original fatal or claim-blocked row as evidence
   - mark reconciliation task `RESOLVED` only after the replacement path is durably persisted
3. If the outbox row is `FATAL_ESCALATION_FAILED`:
   - open or attach an incident ticket
   - preserve the original row, `claim_token`, `publish_attempt_id`, and broker evidence
   - repair only via explicit reconciliation or a fresh replacement event
4. If the outbox row is `CLAIMED` with `publish_attempt_id` set and the lease has expired:
   - do not re-run dispatcher against the original row
   - determine whether the broker publish succeeded, timed out, or remained indeterminate
   - either reconcile to the downstream truth or create a fresh replacement event after evidence capture
5. If data is corrupt:
   - move the job to `QUARANTINED`
   - attach a clinical review note

## Forbidden Steps

1. Do not set `FATAL_ESCALATION_FAILED` back to `PENDING`.
2. Do not set `CLAIMED` rows with `publish_attempt_id` back to `PENDING`.
3. Do not clear `publish_attempt_id` or `claim_token` on the original row before evidence capture.
4. Do not rely on lease expiry to make a started publish claimable again.
5. Do not delete the original outbox row before reconciliation evidence is attached to the incident.

## Required Evidence

- `job_id`
- `source_event_id`
- `trace_id`
- `claim_token` when relevant
- `publish_attempt_id` when present
- outbox status before and after manual repair
- downstream confirmation or rejection evidence
- broker confirmation, timeout, or delivery uncertainty evidence
- operator identity
- timestamp of resolution

## Manual Recovery Boundary

There is no automatic return path from `FATAL_ESCALATION_FAILED` or from `CLAIMED` rows with persisted `publish_attempt_id` back into normal dispatcher claim flow. Any recovery is manual, evidence-driven, and must create a fresh replacement path instead of reusing the ambiguous original row.
