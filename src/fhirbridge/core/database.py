"""
Database models plus sync/async access helpers for the hardened runtime.

Active runtime services must use the async helpers from this module and must not
apply DDL themselves. Schema creation is delegated to the controlled migration
flow in ``fhirbridge.core.migrations``.
"""

from __future__ import annotations

import enum
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Engine, Integer, String, Text, UniqueConstraint, and_, create_engine, delete, or_, select, update
from sqlalchemy import Enum as SAEnum
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from fhirbridge.core.config import get_settings
from fhirbridge.core.migrations import verify_schema_version, verify_schema_version_async

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _enum_column(enum_type: type[enum.StrEnum]) -> SAEnum:
    return SAEnum(
        enum_type,
        values_callable=lambda members: [member.value for member in members],
        native_enum=False,
        validate_strings=True,
    )


class Base(DeclarativeBase):
    pass


class JobStatus(enum.StrEnum):
    """Single source of truth for pipeline job status."""

    PENDING = "PENDING"
    OCR_PROCESSING = "OCR_PROCESSING"
    LLM_EXTRACTION = "LLM_EXTRACTION"
    REVIEW_PENDING = "REVIEW_PENDING"
    FHIR_GENERATED = "FHIR_GENERATED"
    EXPORTING = "EXPORTING"
    EXPORTED = "EXPORTED"
    QUARANTINED = "QUARANTINED"
    SECURITY_REJECTED = "SECURITY_REJECTED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    RETRY_PENDING = "RETRY_PENDING"
    FAILED = "FAILED"
    EXPORT_FAILED = "EXPORT_FAILED"


class OutboxStatus(enum.StrEnum):
    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    ESCALATED = "ESCALATED"
    FATAL_ESCALATION_FAILED = "FATAL_ESCALATION_FAILED"
    DISPATCHED = "DISPATCHED"


class ReconciliationStatus(enum.StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ManualReviewStatus(enum.StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, unique=True, nullable=False)
    filepath = Column(String, unique=True, nullable=False)
    source_kind = Column(String, nullable=True)
    submitted_filename = Column(String, nullable=True)
    tenant_scope = Column(String, nullable=False, default="default")
    actor_id = Column(String, nullable=False, default="system")
    authz_decision_id = Column(String, nullable=True)
    break_glass_flag = Column(Boolean, nullable=False, default=False)
    aggregate_version = Column(Integer, nullable=False, default=1)
    required_read_version = Column(Integer, nullable=False, default=1)
    status = Column(_enum_column(JobStatus), nullable=False, default=JobStatus.PENDING)

    evidence_bucket = Column(String, nullable=True)
    evidence_object_key = Column(String, nullable=True)
    evidence_media_type = Column(String, nullable=True)
    evidence_sha256 = Column(String, nullable=True)
    processing_bucket = Column(String, nullable=True)
    processing_object_key = Column(String, nullable=True)
    processing_media_type = Column(String, nullable=True)
    mapping_bucket = Column(String, nullable=True)
    mapping_object_key = Column(String, nullable=True)

    ocr_text = Column(Text, nullable=True)
    fhir_json = Column(Text, nullable=True)

    output_path = Column(String, nullable=True)
    error_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    event_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type = Column(String, nullable=False, default="job")
    aggregate_id = Column(Integer, nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    trace_id = Column(String, nullable=False)
    tenant_scope = Column(String, nullable=False)
    dedupe_key = Column(String, nullable=False, unique=True)
    retry_count = Column(Integer, nullable=False, default=0)
    status = Column(_enum_column(OutboxStatus), nullable=False, default=OutboxStatus.PENDING)
    available_at = Column(DateTime, nullable=False, default=utcnow)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    claim_token = Column(String, nullable=True)
    claim_owner = Column(String, nullable=True)
    claimed_at = Column(DateTime, nullable=True)
    claim_expires_at = Column(DateTime, nullable=True)
    last_lease_renewed_at = Column(DateTime, nullable=True)
    publish_attempt_id = Column(String, nullable=True)
    publish_started_at = Column(DateTime, nullable=True)


class ConsumedMessage(Base):
    __tablename__ = "consumed_messages"
    __table_args__ = (UniqueConstraint("consumer_name", "event_id", name="uq_consumer_event"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    consumer_name = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class ReadModelState(Base):
    __tablename__ = "read_model_states"
    __table_args__ = (UniqueConstraint("projection_name", "job_id", name="uq_projection_job"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    projection_name = Column(String, nullable=False, default="dashboard")
    job_id = Column(Integer, nullable=False)
    visible_version = Column(Integer, nullable=False, default=0)
    required_version = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default=JobStatus.PENDING.value)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class ManualReviewCase(Base):
    __tablename__ = "manual_review_cases"
    __table_args__ = (UniqueConstraint("job_id", name="uq_manual_review_job"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(Integer, nullable=False)
    tenant_scope = Column(String, nullable=False)
    status = Column(_enum_column(ManualReviewStatus), nullable=False, default=ManualReviewStatus.PENDING)
    reason_code = Column(String, nullable=False)
    decision_notes = Column(Text, nullable=True)
    reviewer_actor_id = Column(String, nullable=True)
    reviewer_authz_decision_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    reviewed_at = Column(DateTime, nullable=True)


class ReconciliationTask(Base):
    __tablename__ = "reconciliation_tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(Integer, nullable=False)
    source_event_id = Column(String, nullable=False)
    failure_category = Column(String, nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(_enum_column(ReconciliationStatus), nullable=False, default=ReconciliationStatus.OPEN)
    created_at = Column(DateTime, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(Integer, nullable=True)
    tenant_scope = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    authz_decision_id = Column(String, nullable=False)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=utcnow)


class SemanticChunkRecord(Base):
    __tablename__ = "semantic_chunks"
    __table_args__ = (UniqueConstraint("job_id", "chunk_index", name="uq_job_chunk"),)

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(Integer, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_type = Column(String, nullable=False)
    source_section = Column(String, nullable=False)
    semantic_boundary_reason = Column(String, nullable=False)
    token_count = Column(Integer, nullable=False)
    document_version = Column(Integer, nullable=False)
    tenant_scope = Column(String, nullable=False)
    aggregate_version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)


def _normalize_postgresql_url(database_url: str) -> str:
    normalized = database_url.strip()
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)

    driver_name = make_url(normalized).drivername
    if not driver_name.startswith("postgresql"):
        raise RuntimeError(
            "Active runtime supports PostgreSQL only. "
            f"Unsupported database URL driver '{driver_name}'."
        )
    return normalized


def _resolve_database_url(database_url: str | None = None) -> str:
    configured_url = database_url or get_settings().require_database_url()
    return _normalize_postgresql_url(configured_url)


def _to_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        normalized = database_url
    elif database_url.startswith("postgresql+psycopg://"):
        normalized = database_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql+psycopg2://"):
        normalized = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        normalized = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        raise RuntimeError(f"Unsupported database URL for async runtime: {database_url}")

    url = make_url(normalized)
    query = dict(url.query)
    sslmode = str(query.pop("sslmode", "")).strip().lower()
    if sslmode:
        if sslmode == "disable":
            query["ssl"] = "false"
        else:
            query["ssl"] = sslmode
    return url.set(query=query).render_as_string(hide_password=False)


def get_sync_engine(*, database_url: str | None = None) -> Engine:
    resolved_url = _resolve_database_url(database_url=database_url)
    return create_engine(resolved_url, pool_pre_ping=True)


def get_async_engine(
    *,
    database_url: str | None = None,
) -> AsyncEngine:
    resolved_url = _to_async_database_url(_resolve_database_url(database_url=database_url))
    return create_async_engine(resolved_url, pool_pre_ping=True)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def get_async_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


def init_db(*_args: Any, **_kwargs: Any) -> Engine:
    raise RuntimeError(
        "Runtime DDL has been removed. Apply migrations explicitly via "
        "fhirbridge.core.migrations.apply_pending_migrations."
    )


def verify_runtime_schema(engine: Engine) -> None:
    verify_schema_version(engine)


async def verify_runtime_schema_async(engine: AsyncEngine) -> None:
    await verify_schema_version_async(engine)


async def load_job_async(session: AsyncSession, *, job_id: int) -> Job | None:
    result = await session.execute(select(Job).where(Job.id == job_id))
    return result.scalar_one_or_none()


async def get_or_create_read_model_async(
    session: AsyncSession,
    *,
    job_id: int,
    projection_name: str = "dashboard",
) -> ReadModelState:
    result = await session.execute(
        select(ReadModelState).where(
            ReadModelState.job_id == job_id,
            ReadModelState.projection_name == projection_name,
        )
    )
    projection = result.scalar_one_or_none()
    if projection:
        return projection
    projection = ReadModelState(job_id=job_id, projection_name=projection_name)
    session.add(projection)
    await session.flush()
    return projection


async def record_consumed_message_async(
    session: AsyncSession,
    *,
    consumer_name: str,
    event_id: str,
) -> bool:
    result = await session.execute(
        select(ConsumedMessage).where(
            ConsumedMessage.consumer_name == consumer_name,
            ConsumedMessage.event_id == event_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return False
    session.add(ConsumedMessage(consumer_name=consumer_name, event_id=event_id))
    await session.flush()
    return True


async def get_or_create_manual_review_case_async(
    session: AsyncSession,
    *,
    job_id: int,
    tenant_scope: str,
    reason_code: str,
) -> ManualReviewCase:
    result = await session.execute(
        select(ManualReviewCase).where(ManualReviewCase.job_id == job_id)
    )
    review_case = result.scalar_one_or_none()
    if review_case:
        return review_case
    review_case = ManualReviewCase(
        job_id=job_id,
        tenant_scope=tenant_scope,
        reason_code=reason_code,
    )
    session.add(review_case)
    await session.flush()
    return review_case


async def fetch_manual_review_case_async(
    session: AsyncSession,
    *,
    job_id: int | None = None,
    document_id: str | None = None,
) -> tuple[Job, ManualReviewCase, ReadModelState | None] | None:
    if job_id is None and document_id is None:
        raise ValueError("job_id or document_id is required")

    job_query = select(Job)
    if job_id is not None:
        job_query = job_query.where(Job.id == job_id)
    if document_id is not None:
        job_query = job_query.where(Job.document_id == document_id)

    job_result = await session.execute(job_query)
    job = job_result.scalar_one_or_none()
    if job is None:
        return None

    review_result = await session.execute(
        select(ManualReviewCase).where(ManualReviewCase.job_id == int(job.id))
    )
    review_case = review_result.scalar_one_or_none()
    if review_case is None:
        return None

    projection_result = await session.execute(
        select(ReadModelState).where(
            ReadModelState.job_id == int(job.id),
            ReadModelState.projection_name == "dashboard",
        )
    )
    projection = projection_result.scalar_one_or_none()
    return job, review_case, projection


async def create_security_audit_event_async(
    session: AsyncSession,
    *,
    job_id: int | None,
    tenant_scope: str,
    actor_id: str,
    event_type: str,
    severity: str,
    authz_decision_id: str,
    details: dict[str, Any] | None = None,
) -> SecurityAuditEvent:
    audit = SecurityAuditEvent(
        job_id=job_id,
        tenant_scope=tenant_scope,
        actor_id=actor_id,
        event_type=event_type,
        severity=severity,
        authz_decision_id=authz_decision_id,
        details_json=json.dumps(details or {}, sort_keys=True),
    )
    session.add(audit)
    await session.flush()
    return audit


async def create_reconciliation_task_async(
    session: AsyncSession,
    *,
    job_id: int,
    source_event_id: str,
    failure_category: str,
    payload: dict[str, Any],
) -> ReconciliationTask:
    task = ReconciliationTask(
        job_id=job_id,
        source_event_id=source_event_id,
        failure_category=failure_category,
        payload_json=json.dumps(payload, sort_keys=True),
    )
    session.add(task)
    await session.flush()
    return task


async def store_semantic_chunks_async(
    session: AsyncSession,
    *,
    job_id: int,
    chunks: list[Any],
) -> None:
    await session.execute(delete(SemanticChunkRecord).where(SemanticChunkRecord.job_id == job_id))
    for chunk in chunks:
        session.add(
            SemanticChunkRecord(
                job_id=job_id,
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                source_section=chunk.source_section,
                semantic_boundary_reason=chunk.semantic_boundary_reason,
                token_count=chunk.token_count,
                document_version=chunk.document_version,
                tenant_scope=chunk.tenant_scope,
                aggregate_version=chunk.aggregate_version,
                content=chunk.content,
            )
        )
    await session.flush()


async def fetch_read_model_state_async(
    session: AsyncSession,
    *,
    projection_name: str = "dashboard",
    job_id: int | None = None,
    document_id: str | None = None,
) -> tuple[Job, ReadModelState] | None:
    if job_id is None and document_id is None:
        raise ValueError("job_id or document_id is required")

    query = (
        select(Job, ReadModelState)
        .join(
            ReadModelState,
            and_(
                ReadModelState.job_id == Job.id,
                ReadModelState.projection_name == projection_name,
            ),
        )
    )
    if job_id is not None:
        query = query.where(Job.id == job_id)
    if document_id is not None:
        query = query.where(Job.document_id == document_id)

    result = await session.execute(query)
    row = result.one_or_none()
    if not row:
        return None
    return row[0], row[1]


async def claim_pending_outbox_events_async(
    session: AsyncSession,
    *,
    dispatcher_id: str,
    limit: int = 20,
    lease_seconds: int = 30,
) -> list[OutboxEvent]:
    now = utcnow()
    lease_expires_at = now + timedelta(seconds=lease_seconds)
    claim_result = await session.execute(
        select(OutboxEvent)
        .where(
            OutboxEvent.available_at <= now,
            or_(
                OutboxEvent.status == OutboxStatus.PENDING,
                and_(
                    OutboxEvent.status == OutboxStatus.CLAIMED,
                    OutboxEvent.claim_expires_at.is_not(None),
                    OutboxEvent.claim_expires_at <= now,
                    OutboxEvent.publish_attempt_id.is_(None),
                ),
            ),
        )
        .order_by(OutboxEvent.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    claimed = list(claim_result.scalars().all())
    for event in claimed:
        event.status = OutboxStatus.CLAIMED
        event.claim_token = uuid.uuid4().hex
        event.claim_owner = dispatcher_id
        event.claimed_at = now
        event.claim_expires_at = lease_expires_at
        event.last_lease_renewed_at = now
        event.publish_attempt_id = None
        event.publish_started_at = None

    await session.flush()
    return claimed


async def start_outbox_publish_attempt_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    publish_attempt_id: str,
) -> bool:
    now = utcnow()
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
        )
        .values(
            publish_attempt_id=publish_attempt_id,
            publish_started_at=now,
            last_lease_renewed_at=now,
        )
    )
    await session.flush()
    return bool(result.rowcount)


async def renew_outbox_claim_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    dispatcher_id: str,
    lease_seconds: int,
) -> bool:
    now = utcnow()
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
            OutboxEvent.claim_owner == dispatcher_id,
        )
        .values(
            claim_expires_at=now + timedelta(seconds=lease_seconds),
            last_lease_renewed_at=now,
        )
    )
    await session.flush()
    return bool(result.rowcount)


async def mark_outbox_dispatched_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    publish_attempt_id: str,
) -> bool:
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
            OutboxEvent.publish_attempt_id == publish_attempt_id,
        )
        .values(
            status=OutboxStatus.DISPATCHED,
            dispatched_at=utcnow(),
            claim_token=None,
            claim_owner=None,
            claimed_at=None,
            claim_expires_at=None,
            last_lease_renewed_at=None,
            publish_attempt_id=None,
            publish_started_at=None,
        )
    )
    await session.flush()
    return bool(result.rowcount)


async def reschedule_outbox_event_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    error_text: str,
    publish_attempt_id: str | None = None,
) -> bool:
    from fhirbridge.core.failure_handling import reschedule_for_retry

    event = await session.get(OutboxEvent, event_id)
    if not event:
        return False
    if event.status != OutboxStatus.CLAIMED or event.claim_token != claim_token:
        return False
    if publish_attempt_id is not None and event.publish_attempt_id != publish_attempt_id:
        return False
    next_retry_count = event.retry_count + 1
    next_available_at = reschedule_for_retry(event.available_at, next_retry_count)
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
        )
        .values(
            retry_count=next_retry_count,
            last_error=error_text,
            available_at=next_available_at,
            status=OutboxStatus.PENDING,
            claim_token=None,
            claim_owner=None,
            claimed_at=None,
            claim_expires_at=None,
            last_lease_renewed_at=None,
            publish_attempt_id=None,
            publish_started_at=None,
        )
    )
    await session.flush()
    return bool(result.rowcount)


async def escalate_outbox_event_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    publish_attempt_id: str,
    error_text: str,
) -> bool:
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
            OutboxEvent.publish_attempt_id == publish_attempt_id,
        )
        .values(
            status=OutboxStatus.ESCALATED,
            retry_count=OutboxEvent.retry_count + 1,
            last_error=error_text,
            claim_token=None,
            claim_owner=None,
            claimed_at=None,
            claim_expires_at=None,
            last_lease_renewed_at=None,
            publish_attempt_id=None,
            publish_started_at=None,
        )
    )
    await session.flush()
    return bool(result.rowcount)


async def quarantine_outbox_event_async(
    session: AsyncSession,
    *,
    event_id: str,
    claim_token: str,
    publish_attempt_id: str,
    error_text: str,
) -> bool:
    result = await session.execute(
        update(OutboxEvent)
        .where(
            OutboxEvent.event_id == event_id,
            OutboxEvent.status == OutboxStatus.CLAIMED,
            OutboxEvent.claim_token == claim_token,
            OutboxEvent.publish_attempt_id == publish_attempt_id,
        )
        .values(
            status=OutboxStatus.FATAL_ESCALATION_FAILED,
            retry_count=OutboxEvent.retry_count + 1,
            last_error=error_text,
            claim_owner=None,
            claim_expires_at=None,
            last_lease_renewed_at=None,
        )
    )
    await session.flush()
    return bool(result.rowcount)
