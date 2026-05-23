from __future__ import annotations

import asyncio
import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from fhirbridge.core.auth import ExternalUserClaims, TokenExchangeService
from fhirbridge.core import outbox_dispatcher as outbox_dispatcher_module
from fhirbridge.core.database import (
    Job,
    JobStatus,
    OutboxEvent,
    OutboxStatus,
    ReconciliationTask,
    claim_pending_outbox_events_async,
    get_async_engine,
    get_async_session_factory,
    get_session_factory,
    get_sync_engine,
    verify_runtime_schema_async,
)
from fhirbridge.core.migrations import EXPECTED_SCHEMA_VERSION, apply_pending_migrations, get_current_schema_version
from fhirbridge.core.outbox_dispatcher import OutboxDispatcher, OutboxEscalationFailure

pytestmark = pytest.mark.integration

TEST_AUTH_SECRET = os.environ.setdefault("INTERNAL_AUTH_CONTEXT_SECRET", "x" * 48)


def _work_payload(event_id: str, trace_id: str, *, job_id: int, tenant_scope: str = "tenant-a") -> str:
    service = TokenExchangeService(secret=TEST_AUTH_SECRET, ttl_seconds=60)
    auth_context = service.issue(
        claims=ExternalUserClaims(sub="doctor-harness", tenant_scope=tenant_scope, roles=["PHYSICIAN"]),
        trace_id=trace_id,
        bound_event_id=event_id,
    )
    return (
        "{"
        f"\"event_id\":\"{event_id}\","
        f"\"trace_id\":\"{trace_id}\","
        f"\"tenant_scope\":\"{tenant_scope}\","
        f"\"job_id\":{job_id},"
        f"\"auth_context\":\"{auth_context}\""
        "}"
    )


def _require_test_database_url() -> str:
    database_url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not database_url:
        pytest.skip("TEST_DATABASE_URL not set; PostgreSQL runtime harness not executed.")
    if "sqlite" in database_url.lower():
        pytest.fail("TEST_DATABASE_URL must point to PostgreSQL, never SQLite.")
    return database_url


def test_postgres_migrations_and_async_schema_verification() -> None:
    database_url = _require_test_database_url()
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)

    try:
        apply_pending_migrations(sync_engine)
        assert get_current_schema_version(sync_engine) == EXPECTED_SCHEMA_VERSION
        asyncio.run(verify_runtime_schema_async(async_engine))
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())


def test_postgres_outbox_claim_is_single_winner() -> None:
    database_url = _require_test_database_url()
    suffix = uuid.uuid4().hex[:8]
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)
    sync_session_factory = get_session_factory(sync_engine)
    async_session_factory = get_async_session_factory(async_engine)

    try:
        apply_pending_migrations(sync_engine)

        with sync_session_factory() as session:
            job = Job(
                document_id=f"doc-harness-{suffix}",
                filepath=f"doc-harness-{suffix}.txt",
                tenant_scope="tenant-a",
                actor_id="harness",
                status=JobStatus.PENDING,
                aggregate_version=1,
                required_read_version=1,
            )
            session.add(job)
            session.flush()
            session.add(
                OutboxEvent(
                    event_id=f"evt-harness-{suffix}",
                    aggregate_id=int(job.id),
                    aggregate_version=1,
                    event_type="job.llm.requested",
                    destination="llm_extraction_queue",
                    payload_json=_work_payload(f"evt-harness-{suffix}", f"trace-harness-{suffix}", job_id=int(job.id)),
                    trace_id=f"trace-harness-{suffix}",
                    tenant_scope="tenant-a",
                    dedupe_key=f"dedupe-harness-{suffix}",
                )
            )
            session.commit()

        async def _claim(dispatcher_id: str) -> int:
            async with async_session_factory() as session:
                async with session.begin():
                    claimed = await claim_pending_outbox_events_async(
                        session,
                        dispatcher_id=dispatcher_id,
                        limit=1,
                        lease_seconds=60,
                    )
                return len(claimed)

        claimed_one, claimed_two = asyncio.run(
            asyncio.gather(
                _claim("dispatcher-one"),
                _claim("dispatcher-two"),
            )
        )

        assert sorted([claimed_one, claimed_two]) == [0, 1]
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())


def test_postgres_started_publish_claim_is_not_auto_reclaimed() -> None:
    database_url = _require_test_database_url()
    suffix = uuid.uuid4().hex[:8]
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)
    sync_session_factory = get_session_factory(sync_engine)
    async_session_factory = get_async_session_factory(async_engine)
    event_id = f"evt-started-publish-{suffix}"

    try:
        apply_pending_migrations(sync_engine)

        with sync_session_factory() as session:
            job = Job(
                document_id=f"doc-started-publish-{suffix}",
                filepath=f"doc-started-publish-{suffix}.txt",
                tenant_scope="tenant-a",
                actor_id="harness",
                status=JobStatus.PENDING,
                aggregate_version=1,
                required_read_version=1,
            )
            session.add(job)
            session.flush()
            started_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=2)
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_id=int(job.id),
                    aggregate_version=1,
                    event_type="job.llm.requested",
                    destination="llm_extraction_queue",
                    payload_json=_work_payload(event_id, f"trace-started-publish-{suffix}", job_id=int(job.id)),
                    trace_id=f"trace-started-publish-{suffix}",
                    tenant_scope="tenant-a",
                    dedupe_key=f"dedupe-started-publish-{suffix}",
                    status=OutboxStatus.CLAIMED,
                    claim_token=f"claim-{suffix}",
                    claim_owner="dispatcher-old",
                    claimed_at=started_at,
                    claim_expires_at=started_at,
                    last_lease_renewed_at=started_at,
                    publish_attempt_id=f"attempt-{suffix}",
                    publish_started_at=started_at,
                )
            )
            session.commit()
            job_id = int(job.id)

        async def _claim_again() -> int:
            async with async_session_factory() as session:
                async with session.begin():
                    claimed = await claim_pending_outbox_events_async(
                        session,
                        dispatcher_id="dispatcher-reclaimer",
                        limit=1,
                        lease_seconds=60,
                    )
                return len(claimed)

        assert asyncio.run(_claim_again()) == 0

        with sync_session_factory() as session:
            event = session.get(OutboxEvent, event_id)
            assert event is not None
            assert event.status == OutboxStatus.CLAIMED
            assert event.claim_token == f"claim-{suffix}"
            assert event.publish_attempt_id == f"attempt-{suffix}"

            session.query(OutboxEvent).filter_by(event_id=event_id).delete()
            session.query(Job).filter_by(id=job_id).delete()
            session.commit()
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())


class _HarnessPublisher:
    def __init__(self, *, delay_seconds: float = 0.0) -> None:
        self.delay_seconds = delay_seconds
        self.calls: list[str] = []

    async def publish(self, *, queue_name: str, body: bytes, message_id: str, trace_id: str) -> None:
        _ = queue_name, body, trace_id
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        self.calls.append(message_id)


def test_postgres_dispatcher_renews_lease_during_slow_publish() -> None:
    database_url = _require_test_database_url()
    suffix = uuid.uuid4().hex[:8]
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)
    sync_session_factory = get_session_factory(sync_engine)
    async_session_factory = get_async_session_factory(async_engine)
    event_id = f"evt-lease-{suffix}"

    try:
        apply_pending_migrations(sync_engine)

        with sync_session_factory() as session:
            job = Job(
                document_id=f"doc-lease-{suffix}",
                filepath=f"doc-lease-{suffix}.txt",
                tenant_scope="tenant-a",
                actor_id="harness",
                status=JobStatus.PENDING,
                aggregate_version=1,
                required_read_version=1,
            )
            session.add(job)
            session.flush()
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_id=int(job.id),
                    aggregate_version=1,
                    event_type="job.llm.requested",
                    destination="llm_extraction_queue",
                    payload_json=_work_payload(event_id, f"trace-lease-{suffix}", job_id=int(job.id)),
                    trace_id=f"trace-lease-{suffix}",
                    tenant_scope="tenant-a",
                    dedupe_key=f"dedupe-lease-{suffix}",
                )
            )
            session.commit()
            job_id = int(job.id)

        publisher = _HarnessPublisher(delay_seconds=1.5)
        dispatcher_one = OutboxDispatcher(
            async_session_factory,
            publisher,
            dispatcher_id="harness-one",
            lease_seconds=1,
            publish_timeout_seconds=4,
            lease_renewal_interval_seconds=0.2,
        )
        dispatcher_two = OutboxDispatcher(
            async_session_factory,
            publisher,
            dispatcher_id="harness-two",
            lease_seconds=1,
            publish_timeout_seconds=4,
            lease_renewal_interval_seconds=0.2,
        )

        async def _run() -> tuple[int, int]:
            first = asyncio.create_task(dispatcher_one.dispatch_once(limit=1))
            await asyncio.sleep(1.1)
            second = asyncio.create_task(dispatcher_two.dispatch_once(limit=1))
            return await asyncio.gather(first, second)

        dispatched_one, dispatched_two = asyncio.run(_run())

        assert sorted([dispatched_one, dispatched_two]) == [0, 1]
        assert publisher.calls == [event_id]

        with sync_session_factory() as session:
            event = session.get(OutboxEvent, event_id)
            assert event is not None
            assert event.status == OutboxStatus.DISPATCHED

            session.query(ReconciliationTask).filter_by(source_event_id=event_id).delete()
            session.query(OutboxEvent).filter_by(event_id=event_id).delete()
            session.query(Job).filter_by(id=job_id).delete()
            session.commit()
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())


def test_postgres_dispatcher_timeout_escalates_event() -> None:
    database_url = _require_test_database_url()
    suffix = uuid.uuid4().hex[:8]
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)
    sync_session_factory = get_session_factory(sync_engine)
    async_session_factory = get_async_session_factory(async_engine)
    event_id = f"evt-timeout-{suffix}"

    try:
        apply_pending_migrations(sync_engine)

        with sync_session_factory() as session:
            job = Job(
                document_id=f"doc-timeout-{suffix}",
                filepath=f"doc-timeout-{suffix}.txt",
                tenant_scope="tenant-a",
                actor_id="harness",
                status=JobStatus.PENDING,
                aggregate_version=1,
                required_read_version=1,
            )
            session.add(job)
            session.flush()
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_id=int(job.id),
                    aggregate_version=1,
                    event_type="job.llm.requested",
                    destination="llm_extraction_queue",
                    payload_json=_work_payload(event_id, f"trace-timeout-{suffix}", job_id=int(job.id)),
                    trace_id=f"trace-timeout-{suffix}",
                    tenant_scope="tenant-a",
                    dedupe_key=f"dedupe-timeout-{suffix}",
                )
            )
            session.commit()
            job_id = int(job.id)

        dispatcher = OutboxDispatcher(
            async_session_factory,
            _HarnessPublisher(delay_seconds=2.0),
            dispatcher_id="harness-timeout",
            lease_seconds=2,
            publish_timeout_seconds=1,
            lease_renewal_interval_seconds=0.2,
        )

        with pytest.raises(Exception):
            asyncio.run(dispatcher.dispatch_once(limit=1))

        with sync_session_factory() as session:
            event = session.get(OutboxEvent, event_id)
            assert event is not None
            assert event.status == OutboxStatus.ESCALATED

            reconciliation = session.query(ReconciliationTask).filter_by(source_event_id=event_id).one()
            assert reconciliation.failure_category == "OUTBOX_PUBLISH_AMBIGUOUS"

            session.query(ReconciliationTask).filter_by(source_event_id=event_id).delete()
            session.query(OutboxEvent).filter_by(event_id=event_id).delete()
            session.query(Job).filter_by(id=job_id).delete()
            session.commit()
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())


def test_postgres_dispatcher_fails_closed_when_escalation_write_is_not_confirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = _require_test_database_url()
    suffix = uuid.uuid4().hex[:8]
    sync_engine = get_sync_engine(database_url=database_url)
    async_engine = get_async_engine(database_url=database_url)
    sync_session_factory = get_session_factory(sync_engine)
    async_session_factory = get_async_session_factory(async_engine)
    event_id = f"evt-escalation-fail-{suffix}"

    try:
        apply_pending_migrations(sync_engine)

        with sync_session_factory() as session:
            job = Job(
                document_id=f"doc-escalation-fail-{suffix}",
                filepath=f"doc-escalation-fail-{suffix}.txt",
                tenant_scope="tenant-a",
                actor_id="harness",
                status=JobStatus.PENDING,
                aggregate_version=1,
                required_read_version=1,
            )
            session.add(job)
            session.flush()
            session.add(
                OutboxEvent(
                    event_id=event_id,
                    aggregate_id=int(job.id),
                    aggregate_version=1,
                    event_type="job.llm.requested",
                    destination="llm_extraction_queue",
                    payload_json=_work_payload(event_id, f"trace-escalation-fail-{suffix}", job_id=int(job.id)),
                    trace_id=f"trace-escalation-fail-{suffix}",
                    tenant_scope="tenant-a",
                    dedupe_key=f"dedupe-escalation-fail-{suffix}",
                )
            )
            session.commit()
            job_id = int(job.id)

        async def _fail_escalation(*_args, **_kwargs) -> bool:
            return False

        monkeypatch.setattr(outbox_dispatcher_module, "escalate_outbox_event_async", _fail_escalation)

        dispatcher = OutboxDispatcher(
            async_session_factory,
            _HarnessPublisher(delay_seconds=2.0),
            dispatcher_id="harness-escalation-fail",
            lease_seconds=2,
            publish_timeout_seconds=1,
            lease_renewal_interval_seconds=0.2,
        )

        with pytest.raises(
            OutboxEscalationFailure,
            match="Fail-closed: ambiguous publish quarantined as FATAL_ESCALATION_FAILED",
        ):
            asyncio.run(dispatcher.dispatch_once(limit=1))

        async def _claim_again() -> int:
            async with async_session_factory() as session:
                async with session.begin():
                    claimed = await claim_pending_outbox_events_async(
                        session,
                        dispatcher_id="harness-reclaimer",
                        limit=1,
                        lease_seconds=1,
                    )
                return len(claimed)

        with sync_session_factory() as session:
            event = session.get(OutboxEvent, event_id)
            assert event is not None
            assert event.status == OutboxStatus.FATAL_ESCALATION_FAILED
            assert event.claim_token is not None
            assert event.publish_attempt_id is not None

            reconciliation = session.query(ReconciliationTask).filter_by(source_event_id=event_id).one()
            assert reconciliation.failure_category == "OUTBOX_ESCALATION_FATAL"

        assert asyncio.run(_claim_again()) == 0

        with sync_session_factory() as session:
            session.query(ReconciliationTask).filter_by(source_event_id=event_id).delete()
            session.query(OutboxEvent).filter_by(event_id=event_id).delete()
            session.query(Job).filter_by(id=job_id).delete()
            session.commit()
    finally:
        sync_engine.dispose()
        asyncio.run(async_engine.dispose())
