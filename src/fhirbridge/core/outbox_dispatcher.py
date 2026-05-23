from __future__ import annotations

import asyncio
import json
import logging
import socket
import uuid
from dataclasses import dataclass
from typing import Protocol

import aio_pika
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fhirbridge.core.auth import PolicyAuthError, TokenExchangeService
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import (
    OutboxEvent,
    OutboxStatus,
    claim_pending_outbox_events_async,
    create_reconciliation_task_async,
    escalate_outbox_event_async,
    get_async_engine,
    get_async_session_factory,
    mark_outbox_dispatched_async,
    quarantine_outbox_event_async,
    renew_outbox_claim_async,
    start_outbox_publish_attempt_async,
    verify_runtime_schema_async,
)
from fhirbridge.core.failure_handling import TransientInfrastructureError
from fhirbridge.core.rabbitmq import destination_requires_auth_context, get_rabbitmq_connection

logger = logging.getLogger(__name__)

AsyncEngineRef: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


class OutboxEscalationFailure(RuntimeError):
    """Raised when an ambiguous publish cannot be atomically escalated."""


class Publisher(Protocol):
    async def publish(
        self,
        *,
        queue_name: str,
        body: bytes,
        message_id: str,
        trace_id: str,
    ) -> None: ...


@dataclass(slots=True)
class RabbitMqPublisher:
    channel: aio_pika.abc.AbstractChannel

    async def publish(
        self,
        *,
        queue_name: str,
        body: bytes,
        message_id: str,
        trace_id: str,
    ) -> None:
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                message_id=message_id,
                correlation_id=trace_id,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )


def _get_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global AsyncEngineRef, AsyncSessionFactory

    if AsyncEngineRef is None:
        AsyncEngineRef = get_async_engine()
    if AsyncSessionFactory is None:
        AsyncSessionFactory = get_async_session_factory(AsyncEngineRef)
    return AsyncEngineRef, AsyncSessionFactory


@dataclass(slots=True)
class ClaimedOutboxItem:
    event_id: str
    claim_token: str
    aggregate_id: int
    destination: str
    payload_json: str
    trace_id: str
    tenant_scope: str


class OutboxDispatcher:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: Publisher,
        *,
        dispatcher_id: str,
        lease_seconds: int = 60,
        publish_timeout_seconds: int = 45,
        lease_renewal_interval_seconds: int = 15,
    ) -> None:
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")
        if publish_timeout_seconds <= 0:
            raise ValueError("publish_timeout_seconds must be positive")
        if lease_renewal_interval_seconds <= 0:
            raise ValueError("lease_renewal_interval_seconds must be positive")
        if lease_renewal_interval_seconds >= lease_seconds:
            raise ValueError("lease_renewal_interval_seconds must remain below lease_seconds")
        self._session_factory = session_factory
        self._publisher = publisher
        self._dispatcher_id = dispatcher_id
        self._lease_seconds = lease_seconds
        self._publish_timeout_seconds = publish_timeout_seconds
        self._lease_renewal_interval_seconds = lease_renewal_interval_seconds
        self._token_exchange = TokenExchangeService.from_settings()

    def _refresh_queue_safe_payload(self, event: ClaimedOutboxItem) -> bytes:
        if not destination_requires_auth_context(event.destination):
            return event.payload_json.encode("utf-8")

        try:
            payload = json.loads(event.payload_json)
        except json.JSONDecodeError as exc:
            raise PolicyAuthError(
                f"Outbox payload for {event.event_id} is not valid JSON for auth refresh"
            ) from exc

        message_event_id = str(payload.get("event_id") or "").strip()
        auth_context = str(payload.get("auth_context") or "").strip()
        trace_id = str(payload.get("trace_id") or event.trace_id).strip()
        if not message_event_id or not auth_context:
            raise PolicyAuthError(
                f"Outbox payload for {event.event_id} is missing auth_context refresh metadata"
            )

        payload["auth_context"] = self._token_exchange.reissue_bound_context(
            auth_context,
            expected_tenant_scope=event.tenant_scope,
            expected_event_id=message_event_id,
            trace_id=trace_id,
        )
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    async def _load_outbox_state(
        self,
        session: AsyncSession,
        *,
        event_id: str,
    ) -> tuple[OutboxStatus | None, str | None, str | None]:
        if not hasattr(session, "get"):
            return None, None, None
        current_state = await session.get(OutboxEvent, event_id)
        return (
            getattr(current_state, "status", None),
            getattr(current_state, "claim_token", None),
            getattr(current_state, "publish_attempt_id", None),
        )

    async def _start_publish_attempt(self, event: ClaimedOutboxItem, publish_attempt_id: str) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                started = await start_outbox_publish_attempt_async(
                    session,
                    event_id=event.event_id,
                    claim_token=event.claim_token,
                    publish_attempt_id=publish_attempt_id,
                )
                if not started:
                    raise TransientInfrastructureError(
                        f"Unable to fence outbox publish attempt for {event.event_id}"
                    )

    async def _renew_claim_until_stopped(
        self,
        event: ClaimedOutboxItem,
        *,
        stop_event: asyncio.Event,
        lease_lost: asyncio.Event,
    ) -> None:
        try:
            while not stop_event.is_set():
                try:
                    await asyncio.wait_for(
                        stop_event.wait(),
                        timeout=self._lease_renewal_interval_seconds,
                    )
                    return
                except TimeoutError:
                    pass

                async with self._session_factory() as session:
                    async with session.begin():
                        renewed = await renew_outbox_claim_async(
                            session,
                            event_id=event.event_id,
                            claim_token=event.claim_token,
                            dispatcher_id=self._dispatcher_id,
                            lease_seconds=self._lease_seconds,
                        )
                if not renewed:
                    lease_lost.set()
                    return
        except asyncio.CancelledError:
            raise
        except Exception:
            lease_lost.set()
            raise

    async def _publish_with_lease_guard(
        self,
        event: ClaimedOutboxItem,
        *,
        publish_attempt_id: str,
    ) -> str:
        await self._start_publish_attempt(event, publish_attempt_id)
        publish_body = self._refresh_queue_safe_payload(event)

        stop_event = asyncio.Event()
        lease_lost = asyncio.Event()
        heartbeat_task = asyncio.create_task(
            self._renew_claim_until_stopped(
                event,
                stop_event=stop_event,
                lease_lost=lease_lost,
            )
        )
        publish_task = asyncio.create_task(
            self._publisher.publish(
                queue_name=event.destination,
                body=publish_body,
                message_id=event.event_id,
                trace_id=event.trace_id,
            )
        )
        lease_lost_task = asyncio.create_task(lease_lost.wait())

        try:
            async with asyncio.timeout(self._publish_timeout_seconds):
                done, _ = await asyncio.wait(
                    {publish_task, lease_lost_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if lease_lost_task in done:
                    raise TransientInfrastructureError(
                        f"Outbox lease renewal lost during publish for {event.event_id}"
                    )
                await publish_task
            return publish_attempt_id
        finally:
            stop_event.set()
            if not publish_task.done():
                publish_task.cancel()
            heartbeat_task.cancel()
            lease_lost_task.cancel()
            await asyncio.gather(publish_task, return_exceptions=True)
            await asyncio.gather(heartbeat_task, return_exceptions=True)
            await asyncio.gather(lease_lost_task, return_exceptions=True)

    async def _escalate_publish_failure(
        self,
        event: ClaimedOutboxItem,
        *,
        publish_attempt_id: str,
        error_text: str,
    ) -> None:
        post_commit_failure: OutboxEscalationFailure | None = None
        try:
            async with self._session_factory() as session:
                async with session.begin():
                    escalated = await escalate_outbox_event_async(
                        session,
                        event_id=event.event_id,
                        claim_token=event.claim_token,
                        publish_attempt_id=publish_attempt_id,
                        error_text=error_text,
                    )
                    if escalated:
                        await create_reconciliation_task_async(
                            session,
                            job_id=event.aggregate_id,
                            source_event_id=event.event_id,
                            failure_category="OUTBOX_PUBLISH_AMBIGUOUS",
                            payload={
                                "event_id": event.event_id,
                                "dispatcher_id": self._dispatcher_id,
                                "publish_attempt_id": publish_attempt_id,
                                "reason": error_text,
                            },
                        )
                    else:
                        current_status, current_claim_token, current_publish_attempt_id = (
                            await self._load_outbox_state(session, event_id=event.event_id)
                        )
                        quarantined = await quarantine_outbox_event_async(
                            session,
                            event_id=event.event_id,
                            claim_token=event.claim_token,
                            publish_attempt_id=publish_attempt_id,
                            error_text=(
                                "ESCALATION_WRITE_FAILED: "
                                f"{error_text}"
                            ),
                        )
                        if quarantined:
                            await create_reconciliation_task_async(
                                session,
                                job_id=event.aggregate_id,
                                source_event_id=event.event_id,
                                failure_category="OUTBOX_ESCALATION_FATAL",
                                payload={
                                    "event_id": event.event_id,
                                    "dispatcher_id": self._dispatcher_id,
                                    "publish_attempt_id": publish_attempt_id,
                                    "reason": error_text,
                                    "guardrail": OutboxStatus.FATAL_ESCALATION_FAILED,
                                },
                            )
                            post_commit_failure = OutboxEscalationFailure(
                                "Fail-closed: ambiguous publish quarantined as "
                                f"{OutboxStatus.FATAL_ESCALATION_FAILED} for outbox event {event.event_id}"
                            )
                        else:
                            current_status, current_claim_token, current_publish_attempt_id = (
                                await self._load_outbox_state(session, event_id=event.event_id)
                            )
                            guardrail_text = "publish_attempt_id guard absent"
                            if current_publish_attempt_id:
                                guardrail_text = "publish_attempt_id claim guard active"
                            post_commit_failure = OutboxEscalationFailure(
                                "Fail-closed: unable to persist ESCALATED for "
                                f"outbox event {event.event_id}; "
                                f"status={current_status!s} "
                                f"claim_token={current_claim_token!s} "
                                f"publish_attempt_id={current_publish_attempt_id!s} "
                                f"guardrail={guardrail_text}"
                            )
        except OutboxEscalationFailure:
            logger.critical(
                "Outbox escalation failed closed for event_id=%s publish_attempt_id=%s dispatcher_id=%s",
                event.event_id,
                publish_attempt_id,
                self._dispatcher_id,
                exc_info=True,
            )
            raise
        except Exception as exc:
            logger.critical(
                "Outbox escalation transaction failed closed for event_id=%s publish_attempt_id=%s dispatcher_id=%s",
                event.event_id,
                publish_attempt_id,
                self._dispatcher_id,
                exc_info=exc,
            )
            raise OutboxEscalationFailure(
                "Fail-closed: unable to persist a terminal outbox guardrail for "
                f"outbox event {event.event_id}"
            ) from exc

        if post_commit_failure is not None:
            logger.critical(
                "Outbox event moved to fail-closed escalation guardrail event_id=%s publish_attempt_id=%s dispatcher_id=%s",
                event.event_id,
                publish_attempt_id,
                self._dispatcher_id,
            )
            raise post_commit_failure

        logger.error(
            "Outbox publish ambiguity escalated for reconciliation event_id=%s publish_attempt_id=%s dispatcher_id=%s",
            event.event_id,
            publish_attempt_id,
            self._dispatcher_id,
        )

    async def dispatch_once(self, limit: int = 20) -> int:
        async with self._session_factory() as session:
            async with session.begin():
                claimed_events = await claim_pending_outbox_events_async(
                    session,
                    dispatcher_id=self._dispatcher_id,
                    limit=limit,
                    lease_seconds=self._lease_seconds,
                )
            pending = [
                ClaimedOutboxItem(
                    event_id=str(event.event_id),
                    claim_token=str(event.claim_token),
                    aggregate_id=int(event.aggregate_id),
                    destination=str(event.destination),
                    payload_json=str(event.payload_json),
                    trace_id=str(event.trace_id),
                    tenant_scope=str(event.tenant_scope),
                )
                for event in claimed_events
                if event.claim_token
            ]

        dispatched = 0
        for event in pending:
            publish_attempt_id = uuid.uuid4().hex
            try:
                publish_attempt_id = await self._publish_with_lease_guard(
                    event,
                    publish_attempt_id=publish_attempt_id,
                )
            except Exception as exc:
                await self._escalate_publish_failure(
                    event,
                    publish_attempt_id=publish_attempt_id,
                    error_text=str(exc),
                )
                raise TransientInfrastructureError(
                    f"Outbox publish escalated for reconciliation: {event.event_id}"
                ) from exc

            async with self._session_factory() as session:
                async with session.begin():
                    updated = await mark_outbox_dispatched_async(
                        session,
                        event_id=event.event_id,
                        claim_token=event.claim_token,
                        publish_attempt_id=publish_attempt_id,
                    )
                    if not updated:
                        await self._escalate_publish_failure(
                            event,
                            publish_attempt_id=publish_attempt_id,
                            error_text=(
                                f"Claim or fencing token lost before dispatch completion for {event.event_id}"
                            ),
                        )
                        raise TransientInfrastructureError(
                            f"Claim lost before dispatch completion for {event.event_id}"
                        )
            dispatched += 1

        return dispatched


async def run_dispatcher(poll_interval_seconds: float = 2.0) -> None:
    settings = get_settings()
    settings.require_database_url()
    settings.require_rabbitmq_url()
    settings.require_internal_auth_context_secret()

    engine, session_factory = _get_database()
    await verify_runtime_schema_async(engine)

    shutdown_event = asyncio.Event()
    dispatcher_id = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    async with get_rabbitmq_connection() as connection:
        channel = await connection.channel()
        dispatcher = OutboxDispatcher(
            session_factory,
            RabbitMqPublisher(channel),
            dispatcher_id=dispatcher_id,
        )
        logger.info("Outbox dispatcher active as dispatcher_id=%s", dispatcher_id)
        while not shutdown_event.is_set():
            try:
                await dispatcher.dispatch_once()
            except OutboxEscalationFailure:
                logger.critical(
                    "Outbox dispatcher stopped fail-closed for dispatcher_id=%s",
                    dispatcher_id,
                    exc_info=True,
                )
                raise
            except Exception:
                logger.exception("Outbox dispatcher iteration failed for dispatcher_id=%s", dispatcher_id)
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=poll_interval_seconds)
            except TimeoutError:
                continue
