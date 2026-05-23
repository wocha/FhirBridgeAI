# Implementation Plan

## Scope

This plan covers the no-regret refactor necessary to enforce:

1. token exchange instead of user-JWT pass-through
2. transactional outbox as the default multi-system write pattern
3. four-stage failure triage with broker-side retry delay
4. explicit BSI/GAiN control mapping
5. semantic chunking plus read-your-own-writes version gating

## Executed Refactor Steps

1. Introduced boundary-only JWT validation and internal auth-context exchange.
2. Added transactional outbox, consumer dedupe, read-model state, reconciliation tasks, and security audit tables.
3. Added a dedicated outbox dispatcher and broker retry/DLQ/security/reconciliation routing.
4. Reworked active workers so successful stage handoffs go through the outbox instead of direct publish.
5. Added semantically aware chunking and read-model gating.
6. Added evidence-focused tests for token exchange, outbox, triage, reconciliation, version gating, and semantic chunking.

## ADR-Required Follow-Ups

1. Legacy script retirement:
   - `src/fhirbridge/workers/parse_ocr_to_fhir.py`
   - `src/verify_export.py`
2. Postgres production migration path for new tables and columns.
3. Qdrant runtime enforcement evidence for tenant filters and read/write credential separation.

## 2026-03-17 Audit Delta

This section captures the no-regret work packages that remain before the project can plausibly claim KRITIS-ready hospital deployment maturity.

1. Secure the internal transport plane end to end.
   - RabbitMQ must move from `amqp://` to TLS-backed transport with explicit trust configuration.
   - The inference plane must stop relying on implicit local HTTP trust.
   - OTLP export must use a governed secure path or be explicitly scoped as non-production telemetry.

2. Remove dev-only identity and bootstrap exceptions from the runtime baseline.
   - Replace Keycloak `start-dev` with an optimized production mode.
   - Enforce bootstrap password rotation on first login or remove bootstrap users from default deployment.
   - Replace static long-lived downstream bearer credentials where possible with short-lived service identity.

3. Harden all runtime containers to a consistent baseline.
   - Non-root execution for workers, export worker, dashboard, and generator.
   - Tighten writable paths and runtime privileges.
   - Review image contents for unnecessary packages and tools.

4. Close the live-evidence exceptions that are currently documented but still open.
   - PostgreSQL rollout evidence
   - Keycloak JWKS validation evidence
   - Qdrant tenant-isolation evidence

5. Add the missing compliance artifacts outside the codebase itself.
   - DPIA / DSFA
   - records of processing activities
   - TOM document
   - retention and deletion concept
   - access-control concept
   - backup/restore and BCM evidence with RTO/RPO

6. Update the legal control mapping to the 2025/2026 regulatory baseline.
   - Map the platform to the current BSIG (effective 2025-12-06), current BSI-KritisV, DSGVO, SGB V section 373, and the AI Act timeline.
   - Freeze the intended use so MDR / SaMD obligations can be assessed formally instead of implicitly.

7. Decide whether audit evidence must become tamper-evident in the active runtime.
   - If yes, add an immutable anchoring design instead of relying solely on mutable Postgres audit tables.
