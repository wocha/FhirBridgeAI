# Test Evidence 2026-03-15

## Evidence Entry-Point

Run this harness to reproduce the evidence below:
```text
python3 <project-root>/scripts/security/run_hardening_evidence.py
```

Generated at: `2026-03-15 21:59:34Z`

## Local Pytest Suite

Files:
- `tests/test_evidence_harness.py`
- `tests/test_boundary_contracts.py`
- `tests/test_database_runtime.py`
- `tests/test_outbox_dispatcher.py`
- `tests/test_runtime_config.py`
- `tests/test_read_model_gate.py`
- `tests/test_qdrant_security.py`
- `tests/test_legacy_blockade.py`
- `tests/test_dashboard_read_model_endpoint.py`
- `tests/test_ingestion_saga_compensation.py`
- `tests/test_review_endpoint.py`
- `tests/test_architecture_guards.py`
- `tests/test_token_exchange.py`
- `tests/test_postgres_runtime_harness.py`

## Optional Live Harness

- `tests/test_postgres_runtime_harness.py` is part of the standard pytest command.
- If `TEST_DATABASE_URL` is unset, those live PostgreSQL harness tests are expected to skip and remain `nicht nachweisbar` for live execution.

## Pytest Hardening Suite

Command:
```text
python3 -m pytest tests/test_evidence_harness.py tests/test_boundary_contracts.py tests/test_database_runtime.py tests/test_outbox_dispatcher.py tests/test_runtime_config.py tests/test_read_model_gate.py tests/test_qdrant_security.py tests/test_legacy_blockade.py tests/test_dashboard_read_model_endpoint.py tests/test_ingestion_saga_compensation.py tests/test_review_endpoint.py tests/test_architecture_guards.py tests/test_token_exchange.py tests/test_postgres_runtime_harness.py -q
```

Exit code: `0`

Stdout:
```text
........................................................................ [ 85%]
......ssssss                                                             [100%]
78 passed, 6 skipped in 6.86s
```

## Security Posture Check

Command:
```text
python3 <project-root>/scripts/security/check_security_posture.py
```

Exit code: `0`

Stdout:
```text
Security checks passed.
```
