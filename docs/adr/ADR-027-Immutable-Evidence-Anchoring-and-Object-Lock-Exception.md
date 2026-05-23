# ADR-027: Immutable Evidence Anchoring and Object Lock

## Status

Accepted

## Date

2026-03-15

## Context

The scan/PDF ingestion slice must preserve originals as evidence, keep OCR and LLM artifacts out of reviewer-facing flows, and prevent evidence tampering in the active runtime path. The hardening-only baseline for this slice does not permit a policy-only claim of immutability.

## Decision

1. Original PDFs and optional HL7 source messages are stored only in the evidence bucket.
2. The evidence bucket is created with Object Lock enabled.
3. Evidence writes from the ingestion boundary set explicit object-lock retention metadata at write time.
4. OCR text and other transient processing artifacts are stored only in the processing bucket.
5. Re-identification mappings are stored only in the PHI vault bucket.
6. Queue payloads and dashboard flows carry only claim-check metadata; no naked object-store URLs or end-user JWTs are propagated.
7. Manual review uses backend-mediated pseudonymized artifacts only.
8. The export path does not delete processing or mapping artifacts inside the downstream-commit or local-state-commit window.
9. If ingestion fails after an evidence write, the runtime fails closed and persists an orphan-evidence repair marker; it never attempts delete compensation against WORM-protected evidence.
10. If repair-marker persistence also fails, the original WORM evidence object remains the only guaranteed durable artifact on that path; no secondary repair marker or local domain record is guaranteed.

## Consequences

- Positive: Evidence immutability is hard-wired into bucket creation and evidence writes instead of being left as a documentation claim.
- Positive: Reviewer-facing paths stay separated from raw evidence and deanonymization material.
- Positive: Export reconciliation retains the references required to repair downstream/local inconsistency.
- Positive: Even in the double-failure path, the original evidence remains durably anchored because the WORM write happened first.
- Negative: Processing and mapping artifacts can accumulate until an explicit post-export cleanup slice is introduced.
- Negative: If both the domain persistence and the repair-marker write fail, manual recovery must start from the deterministic evidence key plus observability correlation; there is no second durable repair artifact on that path.

## Verification Hooks

- `docker-compose.yml`
- `src/fhirbridge/ingestion/api.py`
- `src/fhirbridge/core/storage.py`
- `src/fhirbridge/workers/fhir_export_worker.py`
- `tests/test_architecture_guards.py`
- `scripts/security/check_security_posture.py`
