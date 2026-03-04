"""
FHIR Export Worker Daemon
=========================
Consumes FHIR Bundles from the `fhir_export_queue` and exports them to an external FHIR server (e.g., HAPI-FHIR).
Uses httpx for asynchronous HTTP requests with connection pooling.
Enforces strict Pydantic FHIR Validation natively in RAM.
Injects Conditional Updates to prevent duplications.
"""

import asyncio
import logging
import os
import signal
import traceback
from functools import partial
from typing import Any

import aio_pika
import httpx
from fhir.resources.bundle import Bundle

from fhirbridge.core.database import Job, JobStatus, get_session_factory, init_db
from fhirbridge.core.rabbitmq import (
    FhirExportMessage,
    get_rabbitmq_connection,
    init_rabbitmq,
)

CONFIG = {
    "DB_PATH": os.getenv("DB_PATH", "data/dispatcher.db"),
    "FHIR_SERVER_URL": os.getenv("FHIR_SERVER_URL", "http://localhost:8080/fhir"),
    "FHIR_AUTH_BEARER": os.getenv("FHIR_AUTH_BEARER", ""),
}


class CorrelationIdFilter(logging.Filter):
    """Ensures correlation_id is present on all log records to prevent KeyError in formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "N/A"
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [FHIR Export] - [%(correlation_id)s] - %(levelname)s - %(message)s",
)
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())

logger = logging.getLogger("FHIRExportWorker")

engine = init_db(CONFIG["DB_PATH"])
SessionFactory = get_session_factory(engine)


MAX_RETRIES = 5
BASE_DELAY_MS = 2000


async def send_fhir_bundle(
    client: httpx.AsyncClient, bundle_json: str, correlation_id: str
) -> None:
    """
    Asynchronously POSTs a FHIR bundle to the configured FHIR server via the provided AsyncClient pool.
    """
    url = CONFIG["FHIR_SERVER_URL"]
    headers = {
        "Content-Type": "application/fhir+json",
        "X-Correlation-ID": correlation_id,
    }

    if CONFIG["FHIR_AUTH_BEARER"]:
        headers["Authorization"] = f"Bearer {CONFIG['FHIR_AUTH_BEARER']}"

    response = await client.post(url, content=bundle_json, headers=headers)
    response.raise_for_status()


def inject_idempotency_logic(bundle: Bundle) -> str:
    """
    Validates a FHIR bundle and injects `ifNoneExist` logical rules for idempotency.
    Returns the updated bundle as a JSON string.
    """
    if bundle.type not in ["transaction", "batch"]:
        bundle.type = "transaction"

    if bundle.entry:
        for entry in bundle.entry:
            if not entry.request:
                from fhir.resources.bundle import BundleEntryRequest

                entry.request = BundleEntryRequest(method="POST", url=entry.resource.resource_type)

            # If it's a Patient, try to inject conditional create
            if entry.resource and entry.resource.resource_type == "Patient":
                patient = entry.resource
                # Attempt to find an identifier to use for the Conditional Create
                if getattr(patient, "identifier", None) and len(patient.identifier) > 0:
                    sysUrl = patient.identifier[0].system or ""
                    val = patient.identifier[0].value or ""
                    if sysUrl and val:
                        entry.request.ifNoneExist = f"identifier={sysUrl}|{val}"

    return bundle.model_dump_json(exclude_none=True)


async def process_export_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    client: httpx.AsyncClient,
    channel: aio_pika.abc.AbstractChannel,
) -> None:
    """
    RabbitMQ Consumer Callback for FHIR Export Tasks.
    """
    async with message.process(requeue=False, ignore_processed=True):
        correlation_id = "unknown"
        if message.correlation_id:
            correlation_id = str(message.correlation_id)
        elif message.headers and "correlation_id" in message.headers:
            correlation_id = str(message.headers["correlation_id"])

        retry_count = 0
        if message.headers and "x-retry-count" in message.headers:
            retry_count = int(message.headers["x-retry-count"])

        try:
            task = FhirExportMessage.model_validate_json(message.body)
            if correlation_id == "unknown":
                correlation_id = f"job-{task.job_id}"

            logger.info(
                f"Starte FHIR Export für Job #{task.job_id} (Attempt {retry_count + 1})",
                extra={"correlation_id": correlation_id},
            )

            with SessionFactory() as session:
                job = session.query(Job).filter_by(id=task.job_id).first()
                if job:
                    job.status = JobStatus.EXPORTING
                    session.commit()

            # 1. STRICT VALIDATION + IDEMPOTENCY INJECTION
            logger.info(
                f"  -> Validating FHIR Bundle for Job #{task.job_id} natively via fhir.resources...",
                extra={"correlation_id": correlation_id},
            )
            bundle = Bundle.model_validate_json(task.bundle_json)
            safe_bundle_json = inject_idempotency_logic(bundle)

            # 2. SEND WITH INJECTED CLIENT (POOL)
            await send_fhir_bundle(client, safe_bundle_json, correlation_id)

            with SessionFactory() as session:
                job = session.query(Job).filter_by(id=task.job_id).first()
                if job:
                    job.status = JobStatus.EXPORTED
                    session.commit()

            await message.ack()
            logger.info(
                f"  ✓ FHIR Export erfolgreich. Job #{task.job_id} abgeschlossen.",
                extra={"correlation_id": correlation_id},
            )

        except (TimeoutError, httpx.HTTPStatusError, httpx.RequestError) as e:
            is_transient = True
            if isinstance(e, httpx.HTTPStatusError):
                if e.response.status_code < 500 and e.response.status_code != 429:
                    is_transient = False

            if is_transient:
                if retry_count < MAX_RETRIES:
                    delay_ms = BASE_DELAY_MS * (2**retry_count)
                    logger.warning(
                        f"  ! Transient Network Error: {e}. Retrying job #{task.job_id} in {delay_ms}ms (Attempt {retry_count + 1}/{MAX_RETRIES})",
                        extra={"correlation_id": correlation_id},
                    )

                    with SessionFactory() as session:
                        job = session.query(Job).filter_by(id=task.job_id).first()
                        if job:
                            job.status = JobStatus.EXPORTING
                            session.commit()

                    headers = message.headers.copy() if message.headers else {}
                    headers["x-retry-count"] = retry_count + 1
                    headers["correlation_id"] = correlation_id

                    import datetime

                    retry_message = aio_pika.Message(
                        body=message.body,
                        headers=headers,
                        expiration=datetime.timedelta(milliseconds=delay_ms),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        correlation_id=correlation_id,
                    )

                    retry_exchange = await channel.get_exchange("fhir_retry.dlx")
                    await retry_exchange.publish(retry_message, routing_key="fhir_export_retry")
                    await message.ack()
                    return
                else:
                    logger.error(
                        f"  ✗ Job #{task.job_id} gescheitert nach {MAX_RETRIES} Retries. Network Error: {e}",
                        extra={"correlation_id": correlation_id},
                    )
                    error_trace = traceback.format_exc()
                    try:
                        task = FhirExportMessage.model_validate_json(message.body)
                        with SessionFactory() as session:
                            job = session.query(Job).filter_by(id=task.job_id).first()
                            if job:
                                job.status = JobStatus.EXPORT_FAILED
                                job.error_trace = error_trace  # type: ignore[assignment]
                                session.commit()
                    except Exception:
                        pass

                    await message.reject(requeue=False)
                    return

            # Permanent HTTP error
            logger.error(
                f"  ✗ Job permanent fehlgeschlagen! {e.response.status_code} - {e.response.text}",
                extra={"correlation_id": correlation_id},
            )
            error_trace = traceback.format_exc()
            try:
                task = FhirExportMessage.model_validate_json(message.body)
                with SessionFactory() as session:
                    job = session.query(Job).filter_by(id=task.job_id).first()
                    if job:
                        job.status = JobStatus.EXPORT_FAILED
                        job.error_trace = error_trace  # type: ignore[assignment]
                        session.commit()
            except Exception:
                pass

            await message.reject(requeue=False)

        except Exception as e:
            # Handles fhir.resources ValidationError, JSONDecodeError, or tenacity exhaustion for 5xx/Timeouts
            error_trace = traceback.format_exc()
            logger.error(
                f"  ✗ Job fehlgeschlagen! Unbekannter Fehler: {type(e).__name__}: {e}",
                extra={"correlation_id": correlation_id},
            )

            try:
                task = FhirExportMessage.model_validate_json(message.body)
                with SessionFactory() as session:
                    job = session.query(Job).filter_by(id=task.job_id).first()
                    if job:
                        job.status = JobStatus.EXPORT_FAILED
                        job.error_trace = error_trace  # type: ignore[assignment]
                        session.commit()
            except Exception:
                pass

            await message.reject(requeue=False)


def mock_request_handler(request: httpx.Request) -> httpx.Response:
    """Mock handler that simulates a successful FHIR server response."""
    logger.info(f"[MOCK] Simulated FHIR server received 200 OK for {request.url}")
    return httpx.Response(200, json={"resourceType": "Bundle", "type": "transaction-response"})


async def run_worker() -> None:
    logger.info("=======================================")
    logger.info("🚀 FHIR Export Worker Active (AsyncIO & RabbitMQ)")
    logger.info("=======================================")

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def signal_handler() -> None:
        logger.info("Signal (SIGINT/SIGTERM) received. Initiating graceful shutdown...")
        loop.call_soon_threadsafe(shutdown_event.set)

    try:
        loop.add_signal_handler(signal.SIGINT, signal_handler)
        loop.add_signal_handler(signal.SIGTERM, signal_handler)
    except NotImplementedError:
        # Fallback for Windows ProactorEventLoop
        signal.signal(signal.SIGINT, lambda sig, frame: signal_handler())
        signal.signal(signal.SIGTERM, lambda sig, frame: signal_handler())

    # Setup the long-lived httpx AsyncClient (Connection Pooling)
    client_kwargs: dict[str, Any] = {"timeout": 10.0}
    if "mock" in CONFIG["FHIR_SERVER_URL"].lower():
        logger.info("Configured with MOCK Transport (12-Factor compliant testing).")
        client_kwargs["transport"] = httpx.MockTransport(mock_request_handler)

    async with httpx.AsyncClient(**client_kwargs) as client:
        async with get_rabbitmq_connection() as connection:
            channel, queues = await init_rabbitmq(connection)
            export_queue = queues["fhir_export_queue"]

            # Inject the client into the consumer
            callback = partial(process_export_message, client=client, channel=channel)
            await export_queue.consume(callback)

            logger.info("Worker is waiting for tasks. Press Ctrl+C to exit.")
            # Block until shutdown_event is set
            await shutdown_event.wait()

            logger.info(
                "Graceful shutdown triggered. Waiting for in-flight tasks to finish and connections to close..."
            )


if __name__ == "__main__":
    asyncio.run(run_worker())
