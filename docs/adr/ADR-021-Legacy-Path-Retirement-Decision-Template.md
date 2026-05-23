# ADR-021: Legacy Path Retirement

## Status

Accepted

## Context

The legacy scripts below bypass the hardened runtime controls:

- `src/fhirbridge/workers/parse_ocr_to_fhir.py`
- `src/verify_export.py`

They previously allowed local file I/O, direct broker publish, uncontrolled schema bootstrap, and secret fallbacks. Keeping them silently executable would leave production-adjacent anti-patterns inside the repository.

## Decision

1. Retire both legacy paths as runtime entrypoints.
2. Replace the files with blocked stubs that terminate immediately and point operators to the hardened worker pipeline and this ADR.
3. Treat any future reactivation as a new architecture decision that requires a separate ADR and fresh security review.

## Consequences

- Legacy scripts can no longer be used accidentally in production or test automation.
- Direct RabbitMQ publish and local file output are technically blocked on those paths.
- Functional validation must move to the async runtime, migration script, and dedicated tests.

## Technical Evidence

- `src/fhirbridge/workers/parse_ocr_to_fhir.py`
- `src/verify_export.py`
- `tests/test_legacy_blockade.py`

## Exceptions

None. Productive use is not tolerated.
