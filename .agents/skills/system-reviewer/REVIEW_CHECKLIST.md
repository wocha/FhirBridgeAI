## Principal Architect Review Checklist: The 5 Anti-Patterns

As the System-Auditor, you MUST actively scan the codebase and session history for the following critical Tier-1 Enterprise Anti-Patterns. Copy this checklist into your thought process or task boundary during the audit.

- [ ] **1. THE EVENT LOOP BLOCKER**
  - *Symptom:* Synchronous network or I/O calls (e.g., `requests.get()`, `time.sleep()`, synchronous DB drivers) inside asynchronous Python code.
  - *Remediation:* Enforce `httpx`/`aiohttp` in `asyncio` or asynchronous database clients (`asyncpg`, `motor`).

- [ ] **2. THE STATEFUL SINNER**
  - *Symptom:* Writing or reading local state to/from disk (e.g., `with open('file.pdf', 'wb')`) in scalable worker nodes.
  - *Remediation:* Enforce the S3 Claim-Check pattern using MinIO/S3. Workers must only pass object keys/URIs via queues.

- [ ] **3. THE SILENT FAILURE**
  - *Symptom:* Exceptions that are caught (e.g., `except Exception: pass`) or swallowed, but neither correctly instrumented nor requeued.
  - *Remediation:* Ensure all caught exceptions are marked as errors in an OpenTelemetry Span (`span.record_exception()`, `span.set_status(Status(StatusCode.ERROR))`) OR properly routed to a RabbitMQ Dead-Letter-Queue (DLQ).

- [ ] **4. THE ORPHAN DATA**
  - *Symptom:* Multi-step database write operations without a Distributed Transaction or Saga Pattern. (e.g., Step 1 saves to Postgres, Step 2 fails to publish to RabbitMQ, leaving the system in an inconsistent state).
  - *Remediation:* Enforce the Transactional Outbox Pattern or Saga Pattern for distributed multi-step operations.

- [ ] **5. THE NAKED ENDPOINT**
  - *Symptom:* API endpoints or internal consumers processing requests without verifying authentication/authorization.
  - *Remediation:* Enforce Zero-Trust Architecture. Validate JWT Claims, verify RBAC scopes, and never trust internal network traffic implicitly.

**Audit Protocol:**
If any of these anti-patterns are detected, you must immediately flag them to the user and require an architectural override implementation plan before proceeding.
