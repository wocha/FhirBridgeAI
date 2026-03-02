"""
FHIR Export Worker Daemon
=========================
Consumes FHIR Bundles from the `fhir_export_queue` and exports them to an external FHIR server (e.g., HAPI-FHIR).
Uses httpx for asynchronous HTTP requests with connection pooling.
Enforces strict Pydantic FHIR Validation natively in RAM.
Injects Conditional Updates to prevent duplications.
"""

import asyncio
import json
import logging
import os
import signal
import traceback
from functools import partial
from typing import Any

import aio_pika
import httpx
from fhir.resources.bundle import Bundle
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from fhirbridge.core.database import Job, get_session_factory, init_db
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
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        return True

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [FHIR Export] - [%(correlation_id)s] - %(levelname)s - %(message)s")
for handler in logging.root.handlers:
    handler.addFilter(CorrelationIdFilter())

logger = logging.getLogger("FHIRExportWorker")

engine = init_db(CONFIG["DB_PATH"])
SessionFactory = get_session_factory(engine)


def is_transient_error(e: BaseException) -> bool:
    """
    Determines if an exception should be retried.
    - True for Network Errors, Timeouts, and HTTP 429 / 5xx.
    - False for HTTP 400, 401, 403, 404 (and anything else permanent).
    """
    if isinstance(e, httpx.HTTPStatusError):
        # 429 Too Many Requests or 5xx Server Errors are transient
        if e.response.status_code == 429 or e.response.status_code >= 500:
            return True
        return False  # All other HTTP status errors (like 400, 404) are permanent
    
    if isinstance(e, (httpx.RequestError, asyncio.TimeoutError)):
        return True  # Connection errors, timeouts
        
    return False


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception(is_transient_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def send_fhir_bundle(client: httpx.AsyncClient, bundle_json: str, correlation_id: str) -> None:
    """
    Asynchronously POSTs a FHIR bundle to the configured FHIR server via the provided AsyncClient pool.
    Retries automatically with exponential backoff ONLY on transient errors.
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

        try:
            task = FhirExportMessage.model_validate_json(message.body)
            if correlation_id == "unknown":
                correlation_id = f"job-{task.job_id}"
                
            logger.info(f"Starte FHIR Export für Job #{task.job_id}", extra={"correlation_id": correlation_id})

            with SessionFactory() as session:
                job = session.query(Job).filter_by(id=task.job_id).first()
                if job:
                    job.status = "EXPORTING"  # type: ignore[assignment]
                    session.commit()

            # 1. STRICT VALIDATION + IDEMPOTENCY INJECTION
            logger.info(f"  -> Validating FHIR Bundle for Job #{task.job_id} natively via fhir.resources...", extra={"correlation_id": correlation_id})
            bundle = Bundle.model_validate_json(task.bundle_json)
            safe_bundle_json = inject_idempotency_logic(bundle)

            # 2. SEND WITH INJECTED CLIENT (POOL)
            await send_fhir_bundle(client, safe_bundle_json, correlation_id)

            with SessionFactory() as session:
                job = session.query(Job).filter_by(id=task.job_id).first()
                if job:
                    job.status = "COMPLETED"  # type: ignore[assignment]
                    session.commit()

            await message.ack()
            logger.info(f"  ✓ FHIR Export erfolgreich. Job #{task.job_id} abgeschlossen.", extra={"correlation_id": correlation_id})

        except httpx.HTTPStatusError as e:
            # Reached if the exception is permanent (e.g., 400 Bad Request, 404) or tenacity gave up
            logger.error(f"  ✗ Job permanent fehlgeschlagen! {e.response.status_code} - {e.response.text}", extra={"correlation_id": correlation_id})
            
            error_trace = traceback.format_exc()
            try:
                task = FhirExportMessage.model_validate_json(message.body)
                with SessionFactory() as session:
                    job = session.query(Job).filter_by(id=task.job_id).first()
                    if job:
                        job.status = "EXPORT_ERROR"  # type: ignore[assignment]
                        job.error_trace = error_trace  # type: ignore[assignment]
                        session.commit()
            except Exception:
                pass
            
            await message.reject(requeue=False)

        except Exception as e:
            # Handles fhir.resources ValidationError, JSONDecodeError, or tenacity exhaustion for 5xx/Timeouts
            error_trace = traceback.format_exc()
            logger.error(f"  ✗ Job fehlgeschlagen! Unbekannter Fehler: {type(e).__name__}: {e}", extra={"correlation_id": correlation_id})
            
            try:
                task = FhirExportMessage.model_validate_json(message.body)
                with SessionFactory() as session:
                    job = session.query(Job).filter_by(id=task.job_id).first()
                    if job:
                        job.status = "EXPORT_ERROR"  # type: ignore[assignment]
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
    if CONFIG["FHIR_SERVER_URL"].lower() == "mock":
        logger.info("Configured with MOCK Transport (12-Factor compliant testing).")
        client_kwargs["transport"] = httpx.MockTransport(mock_request_handler)
    
    async with httpx.AsyncClient(**client_kwargs) as client:
        async with get_rabbitmq_connection() as connection:
            channel, _, _, export_queue = await init_rabbitmq(connection)

            # Inject the client into the consumer
            callback = partial(process_export_message, client=client)
            await export_queue.consume(callback)

            logger.info("Worker is waiting for tasks. Press Ctrl+C to exit.")
            # Block until shutdown_event is set
            await shutdown_event.wait()
            
            logger.info("Graceful shutdown triggered. Waiting for in-flight tasks to finish and connections to close...")


if __name__ == "__main__":
    asyncio.run(run_worker())
