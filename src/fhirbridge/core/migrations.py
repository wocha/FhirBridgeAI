"""
Versioned database migrations for the hardened runtime.

Runtime services must only verify the schema version. Applying DDL is restricted
to this module and the explicit migration script that calls it.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    inspect,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.engine import Connection, Engine


SCHEMA_MIGRATIONS_TABLE = "schema_migrations"
EXPECTED_SCHEMA_VERSION = 4


class SchemaVersionError(RuntimeError):
    """Raised when the runtime schema version is missing or out of date."""


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    apply: Callable[[Connection], None]


def _migration_metadata() -> MetaData:
    metadata = MetaData()

    Table(
        "jobs",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("document_id", String(255), nullable=False, unique=True),
        Column("filepath", String(512), nullable=False, unique=True),
        Column("source_kind", String(64), nullable=True),
        Column("submitted_filename", String(512), nullable=True),
        Column("tenant_scope", String(255), nullable=False),
        Column("actor_id", String(255), nullable=False),
        Column("authz_decision_id", String(255), nullable=True),
        Column("break_glass_flag", Boolean, nullable=False, default=False),
        Column("aggregate_version", Integer, nullable=False, default=1),
        Column("required_read_version", Integer, nullable=False, default=1),
        Column("status", String(64), nullable=False),
        Column("evidence_bucket", String(255), nullable=True),
        Column("evidence_object_key", String(512), nullable=True),
        Column("evidence_media_type", String(255), nullable=True),
        Column("evidence_sha256", String(128), nullable=True),
        Column("processing_bucket", String(255), nullable=True),
        Column("processing_object_key", String(512), nullable=True),
        Column("processing_media_type", String(255), nullable=True),
        Column("mapping_bucket", String(255), nullable=True),
        Column("mapping_object_key", String(512), nullable=True),
        Column("ocr_text", Text, nullable=True),
        Column("fhir_json", Text, nullable=True),
        Column("output_path", String(512), nullable=True),
        Column("error_trace", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )

    outbox_events = Table(
        "outbox_events",
        metadata,
        Column("event_id", String(64), primary_key=True),
        Column("aggregate_type", String(64), nullable=False),
        Column("aggregate_id", Integer, nullable=False),
        Column("aggregate_version", Integer, nullable=False),
        Column("event_type", String(128), nullable=False),
        Column("destination", String(128), nullable=False),
        Column("payload_json", Text, nullable=False),
        Column("trace_id", String(64), nullable=False),
        Column("tenant_scope", String(255), nullable=False),
        Column("dedupe_key", String(255), nullable=False, unique=True),
        Column("retry_count", Integer, nullable=False, default=0),
        Column("status", String(64), nullable=False),
        Column("available_at", DateTime, nullable=False),
        Column("last_error", Text, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("dispatched_at", DateTime, nullable=True),
        Column("claim_token", String(64), nullable=True),
        Column("claim_owner", String(128), nullable=True),
        Column("claimed_at", DateTime, nullable=True),
        Column("claim_expires_at", DateTime, nullable=True),
        Column("last_lease_renewed_at", DateTime, nullable=True),
        Column("publish_attempt_id", String(64), nullable=True),
        Column("publish_started_at", DateTime, nullable=True),
    )
    Index("ix_outbox_events_status_available", outbox_events.c.status, outbox_events.c.available_at)
    Index("ix_outbox_events_claim_expires", outbox_events.c.claim_expires_at)
    Index(
        "ix_outbox_events_status_publish_attempt_claim_expires",
        outbox_events.c.status,
        outbox_events.c.publish_attempt_id,
        outbox_events.c.claim_expires_at,
    )

    Table(
        "consumed_messages",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("consumer_name", String(128), nullable=False),
        Column("event_id", String(64), nullable=False),
        Column("created_at", DateTime, nullable=False),
        UniqueConstraint("consumer_name", "event_id", name="uq_consumer_event"),
    )

    Table(
        "read_model_states",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("projection_name", String(128), nullable=False),
        Column("job_id", Integer, nullable=False),
        Column("visible_version", Integer, nullable=False, default=0),
        Column("required_version", Integer, nullable=False, default=0),
        Column("status", String(64), nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
        UniqueConstraint("projection_name", "job_id", name="uq_projection_job"),
    )

    Table(
        "manual_review_cases",
        metadata,
        Column("id", String(64), primary_key=True),
        Column("job_id", Integer, nullable=False),
        Column("tenant_scope", String(255), nullable=False),
        Column("status", String(64), nullable=False),
        Column("reason_code", String(128), nullable=False),
        Column("decision_notes", Text, nullable=True),
        Column("reviewer_actor_id", String(255), nullable=True),
        Column("reviewer_authz_decision_id", String(255), nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
        Column("reviewed_at", DateTime, nullable=True),
        UniqueConstraint("job_id", name="uq_manual_review_job"),
    )

    Table(
        "reconciliation_tasks",
        metadata,
        Column("id", String(64), primary_key=True),
        Column("job_id", Integer, nullable=False),
        Column("source_event_id", String(64), nullable=False),
        Column("failure_category", String(128), nullable=False),
        Column("payload_json", Text, nullable=False),
        Column("status", String(64), nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("resolved_at", DateTime, nullable=True),
    )

    Table(
        "security_audit_events",
        metadata,
        Column("id", String(64), primary_key=True),
        Column("job_id", Integer, nullable=True),
        Column("tenant_scope", String(255), nullable=False),
        Column("actor_id", String(255), nullable=False),
        Column("event_type", String(128), nullable=False),
        Column("severity", String(64), nullable=False),
        Column("authz_decision_id", String(255), nullable=False),
        Column("details_json", Text, nullable=False),
        Column("created_at", DateTime, nullable=False),
    )

    Table(
        "semantic_chunks",
        metadata,
        Column("id", String(64), primary_key=True),
        Column("job_id", Integer, nullable=False),
        Column("chunk_index", Integer, nullable=False),
        Column("chunk_type", String(64), nullable=False),
        Column("source_section", String(255), nullable=False),
        Column("semantic_boundary_reason", String(128), nullable=False),
        Column("token_count", Integer, nullable=False),
        Column("document_version", Integer, nullable=False),
        Column("tenant_scope", String(255), nullable=False),
        Column("aggregate_version", Integer, nullable=False),
        Column("content", Text, nullable=False),
        Column("created_at", DateTime, nullable=False),
        UniqueConstraint("job_id", "chunk_index", name="uq_job_chunk"),
    )

    return metadata


def _ensure_schema_migrations_table(connection: Connection) -> Table:
    metadata = MetaData()
    schema_migrations = Table(
        SCHEMA_MIGRATIONS_TABLE,
        metadata,
        Column("version", Integer, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("applied_at", DateTime, nullable=False),
    )
    metadata.create_all(connection, checkfirst=True)
    return schema_migrations


def _apply_initial_runtime_schema(connection: Connection) -> None:
    _migration_metadata().create_all(connection, checkfirst=True)


def _apply_outbox_lease_fencing(connection: Connection) -> None:
    statements = (
        "ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS last_lease_renewed_at TIMESTAMP NULL",
        "ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS publish_attempt_id VARCHAR(64) NULL",
        "ALTER TABLE outbox_events ADD COLUMN IF NOT EXISTS publish_started_at TIMESTAMP NULL",
        "CREATE INDEX IF NOT EXISTS ix_outbox_events_publish_attempt ON outbox_events (publish_attempt_id)",
    )
    for statement in statements:
        connection.execute(text(statement))


def _apply_outbox_fail_closed_claim_guard(connection: Connection) -> None:
    connection.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_outbox_events_status_publish_attempt_claim_expires "
            "ON outbox_events (status, publish_attempt_id, claim_expires_at)"
        )
    )


def _apply_manual_review_storage_contracts(connection: Connection) -> None:
    statements = (
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_kind VARCHAR(64) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS submitted_filename VARCHAR(512) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS evidence_bucket VARCHAR(255) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS evidence_object_key VARCHAR(512) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS evidence_media_type VARCHAR(255) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS evidence_sha256 VARCHAR(128) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS processing_bucket VARCHAR(255) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS processing_object_key VARCHAR(512) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS processing_media_type VARCHAR(255) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS mapping_bucket VARCHAR(255) NULL",
        "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS mapping_object_key VARCHAR(512) NULL",
        "UPDATE jobs SET source_kind = 'PDF_SCAN' WHERE source_kind IS NULL",
        """
        CREATE TABLE IF NOT EXISTS manual_review_cases (
            id VARCHAR(64) PRIMARY KEY,
            job_id INTEGER NOT NULL,
            tenant_scope VARCHAR(255) NOT NULL,
            status VARCHAR(64) NOT NULL,
            reason_code VARCHAR(128) NOT NULL,
            decision_notes TEXT NULL,
            reviewer_actor_id VARCHAR(255) NULL,
            reviewer_authz_decision_id VARCHAR(255) NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            reviewed_at TIMESTAMP NULL,
            CONSTRAINT uq_manual_review_job UNIQUE (job_id)
        )
        """,
    )
    for statement in statements:
        connection.execute(text(statement))


MIGRATIONS = (
    Migration(version=1, name="001_hardened_runtime_baseline", apply=_apply_initial_runtime_schema),
    Migration(version=2, name="002_outbox_lease_fencing", apply=_apply_outbox_lease_fencing),
    Migration(version=3, name="003_outbox_fail_closed_claim_guard", apply=_apply_outbox_fail_closed_claim_guard),
    Migration(version=4, name="004_manual_review_storage_contracts", apply=_apply_manual_review_storage_contracts),
)


def get_current_schema_version(engine: Engine) -> int | None:
    inspector = inspect(engine)
    if not inspector.has_table(SCHEMA_MIGRATIONS_TABLE):
        return None
    schema_migrations = Table(SCHEMA_MIGRATIONS_TABLE, MetaData(), autoload_with=engine)
    with engine.connect() as connection:
        version = connection.execute(select(schema_migrations.c.version).order_by(schema_migrations.c.version.desc())).scalar()
    return int(version) if version is not None else None


def apply_pending_migrations(engine: Engine) -> list[int]:
    applied_versions: list[int] = []

    with engine.begin() as connection:
        schema_migrations = _ensure_schema_migrations_table(connection)
        existing = {
            int(row[0])
            for row in connection.execute(select(schema_migrations.c.version))
        }

        for migration in MIGRATIONS:
            if migration.version in existing:
                continue
            migration.apply(connection)
            connection.execute(
                schema_migrations.insert().values(
                    version=migration.version,
                    name=migration.name,
                    applied_at=utcnow(),
                )
            )
            applied_versions.append(migration.version)

    return applied_versions


def verify_schema_version(engine: Engine, *, expected_version: int = EXPECTED_SCHEMA_VERSION) -> int:
    current_version = get_current_schema_version(engine)
    if current_version != expected_version:
        raise SchemaVersionError(
            "Database schema version mismatch: "
            f"expected {expected_version}, found {current_version}. "
            "Apply migrations before starting runtime services."
        )
    return current_version


async def get_current_schema_version_async(engine: AsyncEngine) -> int | None:
    async with engine.connect() as connection:
        has_table = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).has_table(SCHEMA_MIGRATIONS_TABLE)
        )
        if not has_table:
            return None
        result = await connection.execute(
            text(f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE} ORDER BY version DESC LIMIT 1")
        )
        version = result.scalar_one_or_none()
    return int(version) if version is not None else None


async def verify_schema_version_async(
    engine: AsyncEngine,
    *,
    expected_version: int = EXPECTED_SCHEMA_VERSION,
) -> int:
    current_version = await get_current_schema_version_async(engine)
    if current_version != expected_version:
        raise SchemaVersionError(
            "Database schema version mismatch: "
            f"expected {expected_version}, found {current_version}. "
            "Apply migrations before starting runtime services."
        )
    return current_version
