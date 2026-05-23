"""
RabbitMQ Setup and Message Models for FhirBridgeAI.
Provides generic async connection initialization, queue setup, and DLX binding.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Any

import aio_pika
from pydantic import BaseModel, Field

from fhirbridge.core.config import get_settings
SECURITY_ALERT_QUEUE = "security_alert_queue"
RECONCILIATION_QUEUE = "reconciliation_queue"
OCR_TASK_QUEUE = "ocr_task_queue"
LLM_EXTRACTION_QUEUE = "llm_extraction_queue"
FHIR_EXPORT_QUEUE = "fhir_export_queue"
AUTH_CONTEXT_DESTINATIONS = frozenset({OCR_TASK_QUEUE, LLM_EXTRACTION_QUEUE, FHIR_EXPORT_QUEUE})


class IngestionSourceKind(StrEnum):
    PDF_SCAN = "PDF_SCAN"
    HL7_V2 = "HL7_V2"


class ClaimCheck(BaseModel):
    bucket: str
    object_key: str
    media_type: str
    sha256: str | None = None


class WorkMessage(BaseModel):
    event_id: str
    trace_id: str
    tenant_scope: str
    aggregate_version: int
    auth_context: str
    job_id: int
    source_kind: IngestionSourceKind
    submitted_filename: str
    review_required: bool = Field(default=True)


class OcrTaskMessage(WorkMessage):
    evidence: ClaimCheck


class DocumentMetaData(WorkMessage):
    document: ClaimCheck
    evidence: ClaimCheck | None = None


class FhirExportMessage(WorkMessage):
    bundle_json: str
    processing: ClaimCheck
    mapping: ClaimCheck


def retry_queue_name(queue_name: str) -> str:
    return f"{queue_name}.retry"


def dlq_queue_name(queue_name: str) -> str:
    return f"{queue_name}.dlq"


def destination_requires_auth_context(destination: str) -> bool:
    return destination in AUTH_CONTEXT_DESTINATIONS


async def init_rabbitmq(
    connection: aio_pika.abc.AbstractRobustConnection,
) -> tuple[Any, dict[str, Any]]:
    """
    Initializes RabbitMQ exchanges and queues for the Document Dispatcher.
    Sets up a Dead-Letter Exchange (DLX) for failed messages.
    """
    channel = await connection.channel()

    # Pre-fetch count to prevent overwhelming consumers (Backpressure)
    prefetch_count = int(os.getenv("RABBITMQ_PREFETCH_COUNT", "1"))
    await channel.set_qos(prefetch_count=prefetch_count)

    def get_dlx_args(qname: str) -> dict[str, Any]:
        return {
            "x-dead-letter-exchange": "amq.topic",
            "x-dead-letter-routing-key": f"dlx.{qname}",
        }

    # 1. Main Queues with DLX defined
    queue_specs = {
        OCR_TASK_QUEUE: OCR_TASK_QUEUE,
        LLM_EXTRACTION_QUEUE: LLM_EXTRACTION_QUEUE,
        FHIR_EXPORT_QUEUE: FHIR_EXPORT_QUEUE,
    }
    queues: dict[str, Any] = {}
    for alias, queue_name in queue_specs.items():
        main_queue = await channel.declare_queue(queue_name, durable=True)
        await channel.declare_queue(
            retry_queue_name(queue_name),
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": queue_name,
            },
        )
        await channel.declare_queue(dlq_queue_name(queue_name), durable=True)
        queues[alias] = main_queue

    await channel.declare_queue(SECURITY_ALERT_QUEUE, durable=True)
    await channel.declare_queue(RECONCILIATION_QUEUE, durable=True)

    return channel, queues


@asynccontextmanager
async def get_rabbitmq_connection() -> AsyncIterator[aio_pika.abc.AbstractRobustConnection]:
    connection = await aio_pika.connect_robust(get_settings().require_rabbitmq_url())
    try:
        yield connection
    finally:
        await connection.close()


async def publish_with_delay(
    channel: aio_pika.abc.AbstractChannel,
    *,
    queue_name: str,
    body: bytes,
    delay_ms: int,
    headers: dict[str, Any] | None = None,
    message_id: str | None = None,
    correlation_id: str | None = None,
    content_type: str = "application/json",
) -> None:
    retry_headers = dict(headers or {})
    retry_headers["x-retry-count"] = int(retry_headers.get("x-retry-count", 0)) + 1
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=body,
            headers=retry_headers,
            message_id=message_id,
            correlation_id=correlation_id,
            content_type=content_type,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            expiration=str(delay_ms),
        ),
        routing_key=retry_queue_name(queue_name),
    )


async def publish_to_queue(
    channel: aio_pika.abc.AbstractChannel,
    *,
    queue_name: str,
    body: bytes,
    headers: dict[str, Any] | None = None,
    message_id: str | None = None,
    correlation_id: str | None = None,
    content_type: str = "application/json",
) -> None:
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=body,
            headers=headers or {},
            message_id=message_id,
            correlation_id=correlation_id,
            content_type=content_type,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key=queue_name,
    )
