# Threat Model

## System Boundaries

1. Edge boundary:
   - Traefik
   - oauth2-proxy
   - FastAPI ingestion boundary
2. Evidence and processing boundary:
   - Object-Lock evidence bucket
   - processing bucket
   - PHI vault bucket
3. Pipeline trust boundary:
   - RabbitMQ
   - Postgres
   - async workers
   - outbox dispatcher
4. Manual review boundary:
   - backend manual review endpoint
   - dashboard
   - pseudonymized review payloads only
5. Clinical export boundary:
   - FHIR export worker
   - downstream FHIR server over HTTPS only
6. Research/vector boundary:
   - semantic chunk contracts
   - Qdrant runtime harness policy
   - future research bridge isolation guardrails
7. Prepared shadow-pipeline boundary (inactive by design):
   - future BSI audit-ledger Kafka topics
   - future Research-Bridge Kafka topics
   - no runtime services, credentials, producers, or consumers are active in the current stack

## Trust Assumptions Explicitly Rejected

- Internal networks are not trusted.
- End-user JWTs are not trusted beyond the policy-enforcement boundary.
- Message delivery alone does not prove state consistency.
- Runtime schema bootstrap is not trusted.
- URL parameters do not authorize clinical visibility or review actions.
- Short internal-auth TTL alone is not trusted as a backlog or retry control.
- Retrieval similarity or patient-match hints are not trusted as an operational authority.
- Cleartext HTTP is not trusted for bearer-token or PHI-bearing review/export hops.

## Principal Threats and Mitigations

| Threat | Path | Mitigation |
| --- | --- | --- |
| Boundary-to-LLM scan shortcut | PDF ingress -> LLM queue | PDF scans always persist evidence and route through the OCR queue first |
| Backlog-driven auth expiry | outbox backlog / broker retry -> worker handoff | dispatcher reissues a fresh internal auth context at publish time while preserving `event_id`, `tenant_scope`, and `authz_decision_id` |
| Cleartext bearer-token hop | dashboard -> ingestion review/read-model API | dedicated internal HTTPS endpoint plus explicit CA validation in the dashboard client |
| Cleartext or downgraded export transport | export worker -> downstream FHIR server | `FHIR_SERVER_URL` is HTTPS-only and the `httpx` client uses explicit certificate verification |
| Orphan data across database / RabbitMQ / export side effects | worker success path | transactional outbox plus reconciliation task on downstream consistency errors |
| Duplicate outbox publish | multiple dispatcher instances | claim-token plus lease before publish; publish fencing and reconciliation on ambiguity |
| Evidence / PHI mixing or tampering | object storage and review path | separate evidence, processing, and PHI-vault buckets; Object Lock on evidence writes; orphan-evidence repair marker instead of delete compensation; if that marker write also fails, the original WORM evidence remains the only guaranteed durable artifact and recovery is manual via the deterministic evidence key plus observability correlation; backend-mediated pseudonymized review payloads only |
| Export-time evidence loss | downstream commit -> local status update / cleanup | export path reaches durable local `EXPORTED` state before any cleanup and retains repair references on failure |
| Dashboard direct review write to broker/DB | dashboard -> RabbitMQ/Postgres/MinIO | dashboard is limited to backend API calls plus Prometheus reads; direct broker/DB access is denied by network and code guards |
| Advisory retrieval becoming authoritative | Qdrant / research bridge -> export or patient match | advisory-only Qdrant gate plus mandatory manual review before export |
| Dual-bus drift | future RabbitMQ + Kafka fan-out | ADR-026 requires destination-scoped outbox records, fencing, reconciliation, and RabbitMQ-authoritative command semantics |
| Audit-ledger false immutability claim | future Kafka audit topic -> compliance assertion | ADR-029 rejects Kafka retention as immutable proof and requires an external immutable anchor or equivalent proof logic |
| Research backchannel into KRITIS runtime | research bridge -> RabbitMQ/Postgres/MinIO/export path | ADR-028 enforces one-way isolation, separate credentials/tenants/incidents, and advisory-only retrieval |
| Legacy path bypass | retired helper scripts | technical execution blockade via ADR-021 |

## Open Threats

1. Live Postgres rollout evidence remains `nicht nachweisbar`; see ADR-022.
2. Live Qdrant isolation evidence remains `nicht nachweisbar`; see ADR-023.
3. Processing and mapping artifacts can accumulate until a dedicated post-export cleanup slice is introduced; this is an operational retention concern, not a runtime security bypass.
4. If repair-marker persistence fails after an evidence write, the original WORM evidence object remains durable but no second durable repair artifact is guaranteed; operators recover manually by locating the deterministic evidence key for the submitted document and correlating the failed request in logs or OTEL.
5. Kafka shadow-pipeline live evidence remains intentionally absent because Kafka is inactive by design. Any later rollout requires separate ADR, schema, and operational evidence before activation claims are valid.
