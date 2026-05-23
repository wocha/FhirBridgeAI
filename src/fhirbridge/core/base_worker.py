import asyncio
import json
import logging
import signal
from abc import ABC, abstractmethod
from typing import Optional

import aio_pika
from opentelemetry import context as otel_context
from opentelemetry.propagate import extract
from opentelemetry.trace import StatusCode

from fhirbridge.core.failure_handling import decide_failure_route
from fhirbridge.core.rabbitmq import get_rabbitmq_connection, init_rabbitmq
from fhirbridge.core.rabbitmq import (
    RECONCILIATION_QUEUE,
    SECURITY_ALERT_QUEUE,
    dlq_queue_name,
    publish_to_queue,
    publish_with_delay,
)
from fhirbridge.core.telemetry import init_tracer, mark_span_error, set_outcome_attributes


class BaseRabbitMQWorker(ABC):
    def __init__(self, worker_name: str, queue_name: str, prefetch_count: int = 1):
        self.worker_name = worker_name
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self.logger = logging.getLogger(worker_name)
        self.tracer = init_tracer(worker_name)
        self.shutdown_event = asyncio.Event()
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None

    async def setup(self) -> None:
        """Called before starting the consumer."""
        pass

    async def teardown(self) -> None:
        """Called after the consumer has stopped."""
        pass

    @abstractmethod
    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Process the incoming message. Must be implemented by subclasses."""
        pass

    def _message_retry_count(self, message: aio_pika.abc.AbstractIncomingMessage) -> int:
        headers = message.headers or {}
        return int(headers.get("x-retry-count", 0))

    def _extract_failure_context(self, message: aio_pika.abc.AbstractIncomingMessage) -> dict[str, object]:
        try:
            payload = json.loads(message.body.decode("utf-8"))
        except Exception:
            return {}
        return {
            "job_id": payload.get("job_id"),
            "tenant_scope": payload.get("tenant_scope"),
            "event_id": payload.get("event_id"),
            "trace_id": payload.get("trace_id"),
        }

    async def _route_failure(
        self,
        message: aio_pika.abc.AbstractIncomingMessage,
        exc: Exception,
    ) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel not initialized")

        retry_count = self._message_retry_count(message)
        decision = decide_failure_route(exc, retry_count)
        headers = dict(message.headers or {})
        headers["x-error-type"] = type(exc).__name__
        headers["x-failure-category"] = decision.category.value

        if decision.destination == "retry":
            await publish_with_delay(
                self.channel,
                queue_name=self.queue_name,
                body=message.body,
                delay_ms=decision.retry_delay_ms or 0,
                headers=headers,
                message_id=message.message_id,
                correlation_id=message.correlation_id,
                content_type=message.content_type or "application/json",
            )
            await message.ack()
            return

        if decision.destination == "dlq":
            await publish_to_queue(
                self.channel,
                queue_name=dlq_queue_name(self.queue_name),
                body=message.body,
                headers=headers,
                message_id=message.message_id,
                correlation_id=message.correlation_id,
                content_type=message.content_type or "application/json",
            )
            await message.ack()
            return

        if decision.destination == "security_alert":
            failure_context = self._extract_failure_context(message)
            await publish_to_queue(
                self.channel,
                queue_name=SECURITY_ALERT_QUEUE,
                body=json.dumps(
                    {
                        **failure_context,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    },
                    sort_keys=True,
                ).encode("utf-8"),
                headers=headers,
                message_id=message.message_id,
                correlation_id=message.correlation_id,
            )
            await message.ack()
            return

        if decision.destination == "reconciliation":
            failure_context = self._extract_failure_context(message)
            await publish_to_queue(
                self.channel,
                queue_name=RECONCILIATION_QUEUE,
                body=json.dumps(
                    {
                        **failure_context,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    },
                    sort_keys=True,
                ).encode("utf-8"),
                headers=headers,
                message_id=message.message_id,
                correlation_id=message.correlation_id,
            )
            await message.ack()
            return

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        headers = message.headers or {}
        ctx = extract(headers)
        token = otel_context.attach(ctx)

        try:
            with self.tracer.start_as_current_span(f"process_{self.queue_name}", context=ctx) as span:
                retry_count = self._message_retry_count(message)
                span.set_attribute("messaging.destination", self.queue_name)
                span.set_attribute("messaging.retry_count", retry_count)
                try:
                    await self.process_message(message)
                    span.set_status(StatusCode.OK)
                    await message.ack()
                except Exception as e:
                    decision = decide_failure_route(e, retry_count)
                    mark_span_error(
                        span,
                        e,
                        error_code=decision.category.value,
                        component=self.worker_name,
                    )
                    set_outcome_attributes(
                        span,
                        category=decision.category.value,
                        action=decision.destination,
                        retry_count=retry_count,
                    )
                    self.logger.error(f"Error processing message: {type(e).__name__}: {e}")
                    await self._route_failure(message, e)
        finally:
            otel_context.detach(token)

    def _signal_handler(self) -> None:
        self.logger.info("Signal (SIGINT/SIGTERM) received. Initiating graceful shutdown...")
        loop = asyncio.get_running_loop()
        loop.call_soon_threadsafe(self.shutdown_event.set)

    async def _connect_and_consume(self) -> None:
        async with get_rabbitmq_connection() as connection:
            channel, queues = await init_rabbitmq(connection)

            if self.queue_name not in queues:
                raise ValueError(f"Queue {self.queue_name} not found in declared queues.")

            queue = queues[self.queue_name]
            await channel.set_qos(prefetch_count=self.prefetch_count)

            self.channel = channel
            await queue.consume(self._on_message)

            self.logger.info(f"Worker is waiting for tasks on {self.queue_name}. Press Ctrl+C to exit.")
            await self.shutdown_event.wait()

    async def run(self) -> None:
        self.logger.info("=======================================")
        self.logger.info(f"🚀 {self.worker_name} Active (AsyncIO & RabbitMQ)")
        self.logger.info("=======================================")

        loop = asyncio.get_running_loop()

        try:
            loop.add_signal_handler(signal.SIGINT, self._signal_handler)
            loop.add_signal_handler(signal.SIGTERM, self._signal_handler)
        except NotImplementedError:
            signal.signal(signal.SIGINT, lambda sig, frame: self._signal_handler())
            signal.signal(signal.SIGTERM, lambda sig, frame: self._signal_handler())

        await self.setup()

        try:
            await self._connect_and_consume()
        except Exception as e:
            self.logger.error(f"Fatal connection error: {e}")
        finally:
            self.logger.info("Graceful shutdown triggered. Waiting for in-flight tasks to finish and connections to close...")
            await self.teardown()
