from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from fhirbridge.core.database import Job, ManualReviewCase, OutboxEvent, ReadModelState, SecurityAuditEvent


@dataclass(slots=True)
class RuntimeStore:
    jobs: list[Job] = field(default_factory=list)
    outbox_events: list[OutboxEvent] = field(default_factory=list)
    read_model_states: list[ReadModelState] = field(default_factory=list)
    manual_review_cases: list[ManualReviewCase] = field(default_factory=list)
    security_audit_events: list[SecurityAuditEvent] = field(default_factory=list)
    _job_id_seq: int = 1
    _projection_id_seq: int = 1

    def add(self, obj: Any) -> None:
        if isinstance(obj, Job):
            if getattr(obj, "id", None) is None:
                obj.id = self._job_id_seq
                self._job_id_seq += 1
            if obj not in self.jobs:
                self.jobs.append(obj)
            return

        if isinstance(obj, OutboxEvent):
            if not getattr(obj, "event_id", None):
                obj.event_id = str(uuid4())
            if obj not in self.outbox_events:
                self.outbox_events.append(obj)
            return

        if isinstance(obj, ReadModelState):
            if getattr(obj, "id", None) is None:
                obj.id = self._projection_id_seq
                self._projection_id_seq += 1
            if obj not in self.read_model_states:
                self.read_model_states.append(obj)
            return

        if isinstance(obj, ManualReviewCase):
            if not getattr(obj, "id", None):
                obj.id = str(uuid4())
            if obj not in self.manual_review_cases:
                self.manual_review_cases.append(obj)
            return

        if isinstance(obj, SecurityAuditEvent):
            if not getattr(obj, "id", None):
                obj.id = str(uuid4())
            if obj not in self.security_audit_events:
                self.security_audit_events.append(obj)
            return

        raise TypeError(f"Unsupported fake runtime entity: {type(obj)!r}")

    def get_projection(self, *, job_id: int, projection_name: str = "dashboard") -> ReadModelState | None:
        for projection in self.read_model_states:
            if projection.job_id == job_id and projection.projection_name == projection_name:
                return projection
        return None

    def get_manual_review_case(self, *, job_id: int) -> ManualReviewCase | None:
        for review_case in self.manual_review_cases:
            if review_case.job_id == job_id:
                return review_case
        return None


class FakeAsyncTransaction:
    async def __aenter__(self) -> FakeAsyncTransaction:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeAsyncSession:
    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    async def __aenter__(self) -> FakeAsyncSession:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    def begin(self) -> FakeAsyncTransaction:
        return FakeAsyncTransaction()

    def add(self, obj: Any) -> None:
        self.store.add(obj)

    async def flush(self) -> None:
        return None


class FakeAsyncSessionFactory:
    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def __call__(self) -> FakeAsyncSession:
        return FakeAsyncSession(self.store)


async def fake_get_or_create_read_model_async(
    session: FakeAsyncSession,
    *,
    job_id: int,
    projection_name: str = "dashboard",
) -> ReadModelState:
    projection = session.store.get_projection(job_id=job_id, projection_name=projection_name)
    if projection:
        return projection

    projection = ReadModelState(
        projection_name=projection_name,
        job_id=job_id,
        required_version=0,
        visible_version=0,
        status="PENDING",
    )
    session.add(projection)
    await session.flush()
    return projection


async def fake_fetch_read_model_state_async(
    _session: FakeAsyncSession,
    *,
    projection_name: str = "dashboard",
    job_id: int | None = None,
    document_id: str | None = None,
) -> tuple[Job, ReadModelState] | None:
    if job_id is None and document_id is None:
        raise ValueError("job_id or document_id is required")

    for job in _session.store.jobs:
        if job_id is not None and int(job.id) != job_id:
            continue
        if document_id is not None and str(job.document_id) != document_id:
            continue
        projection = _session.store.get_projection(job_id=int(job.id), projection_name=projection_name)
        if projection:
            return job, projection
    return None


async def fake_create_security_audit_event_async(
    session: FakeAsyncSession,
    *,
    job_id: int | None,
    tenant_scope: str,
    actor_id: str,
    event_type: str,
    severity: str,
    authz_decision_id: str,
    details: dict[str, Any] | None = None,
) -> SecurityAuditEvent:
    event = SecurityAuditEvent(
        job_id=job_id,
        tenant_scope=tenant_scope,
        actor_id=actor_id,
        event_type=event_type,
        severity=severity,
        authz_decision_id=authz_decision_id,
        details_json="{}" if details is None else json.dumps(details, sort_keys=True),
    )
    session.add(event)
    await session.flush()
    return event


async def fake_get_or_create_manual_review_case_async(
    session: FakeAsyncSession,
    *,
    job_id: int,
    tenant_scope: str,
    reason_code: str,
) -> ManualReviewCase:
    review_case = session.store.get_manual_review_case(job_id=job_id)
    if review_case:
        return review_case

    review_case = ManualReviewCase(
        job_id=job_id,
        tenant_scope=tenant_scope,
        reason_code=reason_code,
        status="PENDING",
    )
    session.add(review_case)
    await session.flush()
    return review_case


async def fake_fetch_manual_review_case_async(
    session: FakeAsyncSession,
    *,
    job_id: int | None = None,
    document_id: str | None = None,
) -> tuple[Job, ManualReviewCase, ReadModelState | None] | None:
    if job_id is None and document_id is None:
        raise ValueError("job_id or document_id is required")

    for job in session.store.jobs:
        if job_id is not None and int(job.id) != job_id:
            continue
        if document_id is not None and str(job.document_id) != document_id:
            continue
        review_case = session.store.get_manual_review_case(job_id=int(job.id))
        if review_case is None:
            return None
        projection = session.store.get_projection(job_id=int(job.id))
        return job, review_case, projection
    return None


def fake_database_bundle(store: RuntimeStore) -> tuple[SimpleNamespace, FakeAsyncSessionFactory]:
    return SimpleNamespace(name="fake-postgresql-engine"), FakeAsyncSessionFactory(store)
