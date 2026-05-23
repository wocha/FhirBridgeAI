# Security Incident Runbook

## Trigger

Use this runbook when:

- `security_alert_queue` receives a message
- `security_audit_events` records break-glass access
- an internal auth context fails validation
- the dashboard read-model endpoint denies visibility unexpectedly

## Immediate Steps

1. Identify `tenant_scope`, `actor_id`, `authz_decision_id`, and `trace_id`.
2. Determine whether the event is:
   - invalid tenant scope
   - expired or malformed delegated token
   - break-glass misuse
   - repeated replay attempt
   - secret misuse or missing credential rotation
3. Freeze any associated automated replay or repair action.

## Containment

1. Block the affected principal in Keycloak if the event is malicious or unexplained.
2. Invalidate the shared internal auth-context secret if compromise is suspected.
3. Rotate RabbitMQ, MinIO, FHIR export, and Qdrant credentials if the event suggests credential exposure.
4. Disable dashboard clinical visibility if the backend read-model policy cannot be trusted.

## Investigation Evidence

- `security_audit_events`
- RabbitMQ `security_alert_queue` payload
- application logs correlated by `trace_id`
- affected `job_id` and `tenant_scope`
- dashboard read-model response and required/visible version values when applicable
- reviewer notes and decision timestamp
