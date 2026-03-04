"""
RabbitMQ Setup and Message Models for FhirBridgeAI.
Provides generic async connection initialization, queue setup, and DLX binding.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import aio_pika
from pydantic import BaseModel

from fhirbridge.core.config import get_settings

RABBITMQ_URL = get_settings().rabbitmq_url


class OcrTaskMessage(BaseModel):
    job_id: int
    filepath: str


class DocumentMetaData(BaseModel):
    job_id: int
    filepath: str
    s3_object_key: str


class FhirExportMessage(BaseModel):
    job_id: int
    bundle_json: str


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

    # 1. Dead Letter Exchange & Queue
    dlx_exchange = await channel.declare_exchange(
        "fhirbridge.dlx", aio_pika.ExchangeType.DIRECT, durable=True
    )
    dl_queue = await channel.declare_queue("dead_letter_queue", durable=True)
    await dl_queue.bind(dlx_exchange, routing_key="dead_letter")

    # DLX Arguments for main queues
    queue_args: dict[str, Any] = {
        "x-dead-letter-exchange": "fhirbridge.dlx",
        "x-dead-letter-routing-key": "dead_letter",
    }

    # 2. Main Queues
    ocr_queue = await channel.declare_queue("ocr_task_queue", durable=True, arguments=queue_args)
    llm_queue = await channel.declare_queue(
        "llm_extraction_queue", durable=True, arguments=queue_args
    )
    fhir_export_queue = await channel.declare_queue(
        "fhir_export_queue", durable=True, arguments=queue_args
    )

    # 3. Retry Exchange and Queue (Zero-Code Delay Pattern)
    retry_exchange = await channel.declare_exchange(
        "fhir_retry.dlx", aio_pika.ExchangeType.DIRECT, durable=True
    )
    # The retry queue routes dead messages back to the default exchange (""), directly to the fhir_export_queue
    retry_queue_args: dict[str, Any] = {
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "fhir_export_queue",
    }
    retry_queue = await channel.declare_queue(
        "fhir_export_retry_queue", durable=True, arguments=retry_queue_args
    )
    await retry_queue.bind(retry_exchange, routing_key="fhir_export_retry")

    return channel, {
        "ocr_queue": ocr_queue,
        "llm_queue": llm_queue,
        "fhir_export_queue": fhir_export_queue,
        "fhir_export_retry_queue": retry_queue,
    }


@asynccontextmanager
async def get_rabbitmq_connection() -> AsyncIterator[aio_pika.abc.AbstractRobustConnection]:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    try:
        yield connection
    finally:
        await connection.close()
