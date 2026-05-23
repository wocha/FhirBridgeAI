from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from fhirbridge.core.auth import ExternalUserClaims, TokenExchangeService
from fhirbridge.core import outbox_dispatcher
from fhirbridge.core.database import OutboxStatus, record_consumed_message_async
from fhirbridge.core.outbox_dispatcher import OutboxDispatcher, OutboxEscalationFailure
from tests.runtime_fakes import FakeAsyncSessionFactory, RuntimeStore


TEST_AUTH_SECRET = os.environ.setdefault("INTERNAL_AUTH_CONTEXT_SECRET", "x" * 48)


class FakePublisher:
    def __init__(self, *, delay_seconds: float = 0.0, should_fail: bool = False) -> None:
        self.delay_seconds = delay_seconds
        self.should_fail = should_fail
        self.calls: list[tuple[str, str, str]] = []

    async def publish(self, *, queue_name: str, body: bytes, message_id: str, trace_id: str) -> None:
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.should_fail:
            raise RuntimeError("publish failed")
        self.calls.append((queue_name, body.decode("utf-8"), message_id))


@dataclass(slots=True)
class _OutboxEventState:
    event_id: str
    aggregate_id: int
    destination: str
    payload_json: str
    trace_id: str
    tenant_scope: str = "tenant-a"
    status: str = OutboxStatus.PENDING
    retry_count: int = 0
    last_error: str | None = None
    claim_token: str | None = None
    claim_owner: str | None = None
    claim_expires_at: float | None = None
    publish_attempt_id: str | None = None
    publish_started_at: float | None = None


@dataclass(slots=True)
class _OutboxState:
    events: dict[str, _OutboxEventState] = field(default_factory=dict)
    reconciliation_tasks: list[dict[str, Any]] = field(default_factory=list)
    claim_sequence: int = 1
    fail_renewal_for_event_ids: set[str] = field(default_factory=set)

    def add_event(
        self,
        *,
        event_id: str,
        aggregate_id: int,
        destination: str,
        payload_json: str,
        trace_id: str,
    ) -> None:
        self.events[event_id] = _OutboxEventState(
            event_id=event_id,
            aggregate_id=aggregate_id,
            destination=destination,
            payload_json=payload_json,
            trace_id=trace_id,
        )


class _ScalarResult:
    def __init__(self, value: object | None) -> None:
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ConsumedMessageSession:
    def __init__(self) -> None:
        self.records: set[tuple[str, str]] = set()

    async def execute(self, query):
        params = query.compile().params
        consumer_name = next(value for key, value in params.items() if key.startswith("consumer_name"))
        event_id = next(value for key, value in params.items() if key.startswith("event_id"))
        existing = SimpleNamespace() if (consumer_name, event_id) in self.records else None
        return _ScalarResult(existing)

    def add(self, obj) -> None:
        self.records.add((obj.consumer_name, obj.event_id))

    async def flush(self) -> None:
        return None


def _install_outbox_mocks(monkeypatch: pytest.MonkeyPatch, state: _OutboxState) -> None:
    async def _claim(_session, *, dispatcher_id: str, limit: int = 20, lease_seconds: int = 30):
        now = asyncio.get_running_loop().time()
        claimed: list[SimpleNamespace] = []
        for event in state.events.values():
            if len(claimed) >= limit:
                break
            claimable = event.status == OutboxStatus.PENDING or (
                event.status == OutboxStatus.CLAIMED
                and event.claim_expires_at is not None
                and event.claim_expires_at <= now
                and event.publish_attempt_id is None
            )
            if not claimable:
                continue

            claim_token = f"{dispatcher_id}-claim-{state.claim_sequence}"
            state.claim_sequence += 1
            event.status = OutboxStatus.CLAIMED
            event.claim_token = claim_token
            event.claim_owner = dispatcher_id
            event.claim_expires_at = now + lease_seconds
            event.publish_attempt_id = None
            event.publish_started_at = None
            claimed.append(
                SimpleNamespace(
                    event_id=event.event_id,
                    aggregate_id=event.aggregate_id,
                    claim_token=claim_token,
                    destination=event.destination,
                    payload_json=event.payload_json,
                    trace_id=event.trace_id,
                    tenant_scope=event.tenant_scope,
                )
            )
        return claimed

    async def _start_attempt(_session, *, event_id: str, claim_token: str, publish_attempt_id: str) -> bool:
        event = state.events[event_id]
        if event.status != OutboxStatus.CLAIMED or event.claim_token != claim_token:
            return False
        event.publish_attempt_id = publish_attempt_id
        event.publish_started_at = asyncio.get_running_loop().time()
        return True

    async def _renew(_session, *, event_id: str, claim_token: str, dispatcher_id: str, lease_seconds: int) -> bool:
        event = state.events[event_id]
        if event_id in state.fail_renewal_for_event_ids:
            return False
        if event.status != OutboxStatus.CLAIMED:
            return False
        if event.claim_token != claim_token or event.claim_owner != dispatcher_id:
            return False
        event.claim_expires_at = asyncio.get_running_loop().time() + lease_seconds
        return True

    async def _mark(_session, *, event_id: str, claim_token: str, publish_attempt_id: str) -> bool:
        event = state.events[event_id]
        if event.status != OutboxStatus.CLAIMED or event.claim_token != claim_token:
            return False
        if event.publish_attempt_id != publish_attempt_id:
            return False
        event.status = OutboxStatus.DISPATCHED
        event.claim_token = None
        event.claim_owner = None
        event.claim_expires_at = None
        event.publish_attempt_id = None
        event.publish_started_at = None
        return True

    async def _escalate(_session, *, event_id: str, claim_token: str, publish_attempt_id: str, error_text: str) -> bool:
        event = state.events[event_id]
        if event.status != OutboxStatus.CLAIMED or event.claim_token != claim_token:
            return False
        if event.publish_attempt_id != publish_attempt_id:
            return False
        event.status = OutboxStatus.ESCALATED
        event.retry_count += 1
        event.last_error = error_text
        event.claim_token = None
        event.claim_owner = None
        event.claim_expires_at = None
        event.publish_attempt_id = None
        event.publish_started_at = None
        return True

    async def _create_reconciliation(_session, *, job_id: int, source_event_id: str, failure_category: str, payload: dict[str, Any]):
        state.reconciliation_tasks.append(
            {
                "job_id": job_id,
                "source_event_id": source_event_id,
                "failure_category": failure_category,
                "payload": payload,
            }
        )
        return SimpleNamespace(id=f"recon-{len(state.reconciliation_tasks)}")

    async def _quarantine(
        _session,
        *,
        event_id: str,
        claim_token: str,
        publish_attempt_id: str,
        error_text: str,
    ) -> bool:
        event = state.events[event_id]
        if event.status != OutboxStatus.CLAIMED:
            return False
        if event.claim_token != claim_token:
            return False
        if event.publish_attempt_id != publish_attempt_id:
            return False
        event.status = OutboxStatus.FATAL_ESCALATION_FAILED
        event.retry_count += 1
        event.last_error = error_text
        event.claim_owner = None
        event.claim_expires_at = None
        return True

    monkeypatch.setattr(outbox_dispatcher, "claim_pending_outbox_events_async", _claim)
    monkeypatch.setattr(outbox_dispatcher, "start_outbox_publish_attempt_async", _start_attempt)
    monkeypatch.setattr(outbox_dispatcher, "renew_outbox_claim_async", _renew)
    monkeypatch.setattr(outbox_dispatcher, "mark_outbox_dispatched_async", _mark)
    monkeypatch.setattr(outbox_dispatcher, "escalate_outbox_event_async", _escalate)
    monkeypatch.setattr(outbox_dispatcher, "quarantine_outbox_event_async", _quarantine)
    monkeypatch.setattr(outbox_dispatcher, "create_reconciliation_task_async", _create_reconciliation)


def _work_payload(event_id: str, trace_id: str, *, job_id: int, tenant_scope: str = "tenant-a") -> str:
    claims = ExternalUserClaims(sub="doctor-1", tenant_scope=tenant_scope, roles=["PHYSICIAN"])
    service = TokenExchangeService(secret=TEST_AUTH_SECRET, ttl_seconds=60)
    auth_context = service.issue(
        claims=claims,
        trace_id=trace_id,
        bound_event_id=event_id,
    )
    return json.dumps(
        {
            "event_id": event_id,
            "trace_id": trace_id,
            "tenant_scope": tenant_scope,
            "job_id": job_id,
            "auth_context": auth_context,
        },
        sort_keys=True,
    )


def test_dispatcher_marks_outbox_dispatched(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-1",
        aggregate_id=1,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-1", "trace-1", job_id=1),
        trace_id="trace-1",
    )
    _install_outbox_mocks(monkeypatch, state)

    publisher = FakePublisher()
    dispatcher = OutboxDispatcher(FakeAsyncSessionFactory(RuntimeStore()), publisher, dispatcher_id="dispatcher-a")

    dispatched = asyncio.run(dispatcher.dispatch_once())

    assert dispatched == 1
    published_payload = json.loads(publisher.calls[0][1])
    assert publisher.calls[0][0] == "llm_extraction_queue"
    assert publisher.calls[0][2] == "evt-1"
    assert published_payload["job_id"] == 1
    assert published_payload["auth_context"]
    assert state.events["evt-1"].status == OutboxStatus.DISPATCHED
    assert state.reconciliation_tasks == []


def test_slow_publish_lease_is_renewed_until_ack(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-slow",
        aggregate_id=7,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-slow", "trace-slow", job_id=7),
        trace_id="trace-slow",
    )
    _install_outbox_mocks(monkeypatch, state)

    publisher = FakePublisher(delay_seconds=1.2)
    dispatcher = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        publisher,
        dispatcher_id="dispatcher-a",
        lease_seconds=1,
        publish_timeout_seconds=4,
        lease_renewal_interval_seconds=0.2,
    )

    dispatched = asyncio.run(dispatcher.dispatch_once())

    assert dispatched == 1
    assert len(publisher.calls) == 1
    assert state.events["evt-slow"].status == OutboxStatus.DISPATCHED


def test_dispatcher_reissues_expired_auth_context_before_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _OutboxState()
    claims = ExternalUserClaims(sub="doctor-expired", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    service = TokenExchangeService(secret=TEST_AUTH_SECRET, ttl_seconds=1)
    expired_token = service.issue(
        claims=claims,
        trace_id="trace-expired",
        bound_event_id="evt-expired",
        now=datetime.now(UTC) - timedelta(minutes=10),
    )
    expired_payload = json.dumps(
        {
            "event_id": "evt-expired",
            "trace_id": "trace-expired",
            "tenant_scope": "tenant-a",
            "job_id": 42,
            "auth_context": expired_token,
        },
        sort_keys=True,
    )
    state.add_event(
        event_id="evt-expired",
        aggregate_id=42,
        destination="llm_extraction_queue",
        payload_json=expired_payload,
        trace_id="trace-expired",
    )
    _install_outbox_mocks(monkeypatch, state)

    publisher = FakePublisher()
    dispatcher = OutboxDispatcher(FakeAsyncSessionFactory(RuntimeStore()), publisher, dispatcher_id="dispatcher-auth")

    dispatched = asyncio.run(dispatcher.dispatch_once())

    published_payload = json.loads(publisher.calls[0][1])
    assert dispatched == 1
    assert published_payload["auth_context"] != expired_token


def test_competing_dispatchers_respect_inflight_fencing(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-race",
        aggregate_id=99,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-race", "trace-race", job_id=99),
        trace_id="trace-race",
    )
    _install_outbox_mocks(monkeypatch, state)

    publisher = FakePublisher(delay_seconds=1.2)
    dispatcher_one = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        publisher,
        dispatcher_id="dispatcher-one",
        lease_seconds=1,
        publish_timeout_seconds=4,
        lease_renewal_interval_seconds=0.2,
    )
    dispatcher_two = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        publisher,
        dispatcher_id="dispatcher-two",
        lease_seconds=1,
        publish_timeout_seconds=4,
        lease_renewal_interval_seconds=0.2,
    )

    async def _run_race() -> tuple[int, int]:
        first = asyncio.create_task(dispatcher_one.dispatch_once(limit=1))
        await asyncio.sleep(1.1)
        second = asyncio.create_task(dispatcher_two.dispatch_once(limit=1))
        return await asyncio.gather(first, second)

    dispatched_one, dispatched_two = asyncio.run(_run_race())

    assert sorted([dispatched_one, dispatched_two]) == [0, 1]
    assert len(publisher.calls) == 1
    assert state.events["evt-race"].status == OutboxStatus.DISPATCHED


def test_publish_timeout_escalates_to_reconciliation(monkeypatch: pytest.MonkeyPatch) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-timeout",
        aggregate_id=5,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-timeout", "trace-timeout", job_id=5),
        trace_id="trace-timeout",
    )
    _install_outbox_mocks(monkeypatch, state)

    dispatcher = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        FakePublisher(delay_seconds=2.0),
        dispatcher_id="dispatcher-timeout",
        lease_seconds=2,
        publish_timeout_seconds=1,
        lease_renewal_interval_seconds=0.2,
    )

    with pytest.raises(Exception):
        asyncio.run(dispatcher.dispatch_once())

    event = state.events["evt-timeout"]
    assert event.status == OutboxStatus.ESCALATED
    assert event.retry_count == 1
    assert len(state.reconciliation_tasks) == 1
    assert state.reconciliation_tasks[0]["failure_category"] == "OUTBOX_PUBLISH_AMBIGUOUS"


def test_failed_escalation_write_is_quarantined_and_stops_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-escalation-fail",
        aggregate_id=8,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-escalation-fail", "trace-escalation-fail", job_id=8),
        trace_id="trace-escalation-fail",
    )
    _install_outbox_mocks(monkeypatch, state)

    async def _fail_escalation(*_args, **_kwargs) -> bool:
        return False

    monkeypatch.setattr(outbox_dispatcher, "escalate_outbox_event_async", _fail_escalation)

    dispatcher = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        FakePublisher(delay_seconds=2.0),
        dispatcher_id="dispatcher-escalation-fail",
        lease_seconds=2,
        publish_timeout_seconds=1,
        lease_renewal_interval_seconds=0.2,
    )

    with pytest.raises(
        OutboxEscalationFailure,
        match="Fail-closed: ambiguous publish quarantined as FATAL_ESCALATION_FAILED",
    ):
        asyncio.run(dispatcher.dispatch_once())

    event = state.events["evt-escalation-fail"]
    assert event.status == OutboxStatus.FATAL_ESCALATION_FAILED
    assert event.claim_token is not None
    assert event.publish_attempt_id is not None
    assert len(state.reconciliation_tasks) == 1
    assert state.reconciliation_tasks[0]["failure_category"] == "OUTBOX_ESCALATION_FATAL"


def test_fatal_and_started_publish_events_are_never_auto_reclaimed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-fatal",
        aggregate_id=21,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-fatal", "trace-fatal", job_id=21),
        trace_id="trace-fatal",
    )
    state.add_event(
        event_id="evt-started-publish",
        aggregate_id=22,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-started-publish", "trace-started-publish", job_id=22),
        trace_id="trace-started-publish",
    )
    _install_outbox_mocks(monkeypatch, state)

    fatal_event = state.events["evt-fatal"]
    fatal_event.status = OutboxStatus.FATAL_ESCALATION_FAILED
    fatal_event.claim_token = "fatal-claim"
    fatal_event.claim_owner = "dispatcher-old"
    fatal_event.claim_expires_at = -10.0

    started_publish_event = state.events["evt-started-publish"]
    started_publish_event.status = OutboxStatus.CLAIMED
    started_publish_event.claim_token = "started-claim"
    started_publish_event.claim_owner = "dispatcher-old"
    started_publish_event.claim_expires_at = -10.0
    started_publish_event.publish_attempt_id = "attempt-123"

    publisher = FakePublisher()
    dispatcher = OutboxDispatcher(FakeAsyncSessionFactory(RuntimeStore()), publisher, dispatcher_id="dispatcher-a")

    dispatched = asyncio.run(dispatcher.dispatch_once(limit=10))

    assert dispatched == 0
    assert publisher.calls == []
    assert fatal_event.status == OutboxStatus.FATAL_ESCALATION_FAILED
    assert fatal_event.claim_token == "fatal-claim"
    assert started_publish_event.status == OutboxStatus.CLAIMED
    assert started_publish_event.claim_token == "started-claim"


def test_fence_mismatch_keeps_started_publish_claim_blocked_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _OutboxState()
    state.add_event(
        event_id="evt-fence-mismatch",
        aggregate_id=23,
        destination="llm_extraction_queue",
        payload_json=_work_payload("evt-fence-mismatch", "trace-fence-mismatch", job_id=23),
        trace_id="trace-fence-mismatch",
    )
    _install_outbox_mocks(monkeypatch, state)

    async def _fail_escalation(*_args, **_kwargs) -> bool:
        return False

    async def _fail_quarantine(*_args, **_kwargs) -> bool:
        return False

    monkeypatch.setattr(outbox_dispatcher, "escalate_outbox_event_async", _fail_escalation)
    monkeypatch.setattr(outbox_dispatcher, "quarantine_outbox_event_async", _fail_quarantine)

    dispatcher = OutboxDispatcher(
        FakeAsyncSessionFactory(RuntimeStore()),
        FakePublisher(delay_seconds=2.0),
        dispatcher_id="dispatcher-fence-mismatch",
        lease_seconds=2,
        publish_timeout_seconds=1,
        lease_renewal_interval_seconds=0.2,
    )

    with pytest.raises(OutboxEscalationFailure, match="Fail-closed: unable to persist ESCALATED"):
        asyncio.run(dispatcher.dispatch_once())

    event = state.events["evt-fence-mismatch"]
    assert event.status == OutboxStatus.CLAIMED
    assert event.publish_attempt_id is not None
    assert event.claim_token is not None
    assert state.reconciliation_tasks == []


def test_duplicate_suppression_uses_consumer_event_key() -> None:
    session = _ConsumedMessageSession()

    async def _exercise() -> tuple[bool, bool]:
        first = await record_consumed_message_async(
            session,  # type: ignore[arg-type]
            consumer_name="llm-worker",
            event_id="evt-1",
        )
        second = await record_consumed_message_async(
            session,  # type: ignore[arg-type]
            consumer_name="llm-worker",
            event_id="evt-1",
        )
        return first, second

    first, second = asyncio.run(_exercise())
    assert first is True
    assert second is False
