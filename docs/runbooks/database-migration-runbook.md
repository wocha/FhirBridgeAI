# Database Migration Runbook

## Purpose

Apply, verify, and if necessary roll back controlled schema changes for the active runtime database.

## Preconditions

1. Stop or drain ingestion, dispatcher, and worker processes.
2. Capture a database backup or snapshot.
3. Record the current schema version from `schema_migrations`.

## Apply

1. Run `python -m fhirbridge.scripts.migrate_db`.
2. Confirm the command reports the expected target version.
3. Start runtime services only after the migration command exits successfully.

## Verification

1. Query `schema_migrations` and confirm the latest version matches the runtime expectation.
2. Start one runtime component and verify startup does not fail with a schema-version mismatch.
3. Run the database and outbox test suite before broad rollout when possible.

## Rollback

1. Stop runtime services again.
2. Restore the last known-good backup or snapshot.
3. Re-verify `schema_migrations` before allowing traffic.
4. Open an incident or reconciliation item if partial writes occurred during rollout.

## Evidence

- operator identity
- backup identifier
- migration command output
- verified schema version
- restart verification timestamp
