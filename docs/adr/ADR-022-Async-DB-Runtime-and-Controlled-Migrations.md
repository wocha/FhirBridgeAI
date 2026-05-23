# ADR-022: Async DB Runtime and Controlled Migrations

## Status

Accepted

## Context

The active runtime previously used synchronous SQLAlchemy sessions inside async request and worker paths, and it bootstrapped schema opportunistically via `Base.metadata.create_all()`. Both patterns violate Tier-1 enterprise rules for event-loop safety and controlled change management.

## Decision

1. Active runtime paths use SQLAlchemy async engines and async session factories only.
2. Runtime services verify schema version on startup and fail fast on mismatch.
3. Schema creation and mutation are moved to a versioned migration flow in `fhirbridge.core.migrations` and `python -m fhirbridge.scripts.migrate_db`.
4. PostgreSQL is the only supported repository-state persistence backend; SQLite is removed from runtime, tests, and operator tooling.

## Consequences

- Async request and worker paths no longer execute synchronous database I/O.
- Runtime startup aborts before processing traffic when the schema version is missing or stale.
- Database rollout, rollback, and verification become explicit operational steps instead of hidden side effects.
- Portable unit tests use explicit fakes, and optional integration evidence is executed only against an explicitly provided PostgreSQL harness.
- Repo governance rejects SQLite reintroduction in active skills, knowledge assets, and operative helper scripts.

## Technical Evidence

- `src/fhirbridge/core/database.py`
- `src/fhirbridge/core/migrations.py`
- `src/fhirbridge/scripts/migrate_db.py`
- `tests/test_database_runtime.py`
- `tests/test_postgres_runtime_harness.py`
- `tests/test_architecture_guards.py`
- `docs/security/test-evidence-2026-03-15.md`

## Time-Boxed Exception

- Exception: Live Postgres rollout evidence is not produced in this local session and remains `nicht nachweisbar`.
- Owner: Platform Database Owner.
- Ablaufdatum: 2026-04-30.
- Exit-Kriterium: Execute the migration runbook against the production-like Postgres deployment, capture schema version evidence, and attach the result to the release record.
- Technischer Guardrail: Runtime services reject startup on schema-version mismatch; no `create_all()` fallback remains in active start paths.
