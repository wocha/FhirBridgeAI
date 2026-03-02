"""
LLM Worker Daemon for FhirBridgeAI
===================================
Consumes events (Claim-Check IDs) from RabbitMQ `llm_task_queue`, fetches OCR text,
forces the Mistral model to yield structured JSON via Pydantic validation loops,
and routes the result to the next stage (FHIR-Transformation).
"""

import asyncio
import json
import logging
import os
import traceback
from functools import partial
from typing import Any

import aio_pika

from fhirbridge.core.database import Job, get_session_factory, init_db
from fhirbridge.core.rabbitmq import (
    FhirExportMessage,
    LlmTaskMessage,
    get_rabbitmq_connection,
    init_rabbitmq,
)
from fhirbridge.models.fhir_models import BundleExtraction
from fhirbridge.core.llm import LlmConfig, LlmRetryClient, LlmValidationError

CONFIG: dict[str, Any] = {
    "DB_PATH": "data/dispatcher.db",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [LLM] - %(levelname)s - %(message)s")
logger = logging.getLogger("LLMWorker")

engine = init_db(str(CONFIG["DB_PATH"]))
SessionFactory = get_session_factory(engine)


def _update_job_sync(job_id: int, status: str, fhir_json: str | None = None, error_trace: str | None = None) -> None:
    """Synchronous DB operation to update job state, meant to be run in a thread pool."""
    with SessionFactory() as session:
        job = session.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = status
            if fhir_json is not None:
                job.fhir_json = fhir_json
            if error_trace is not None:
                job.error_trace = error_trace
            session.commit()


async def process_llm_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    channel: aio_pika.abc.AbstractChannel,
    dlq_exchange: aio_pika.abc.AbstractExchange,
) -> None:
    """
    RabbitMQ Consumer Callback for LLM Tasks.
    """
    try:
        task = LlmTaskMessage.model_validate_json(message.body)
        logger.info(
            f"Starte LLM Verarbeitung von Job #{task.job_id}: {os.path.basename(task.filepath)}"
        )

        # Mark state (non-blocking)
        await asyncio.to_thread(_update_job_sync, task.job_id, "LLM_EXTRACTION")

        if not task.ocr_text:
            raise ValueError("Kein OCR Text in der Notification vorhanden.")

        logger.info(f"  -> Extrahieren der klinischen Parameter via lokaler GPU (Job #{task.job_id}).")

        # Initialize self-healing LLM Client (Arch-Rule #2: max_retries=2)
        config = LlmConfig(
            max_retries=2,
            temperature=0.1,  # Low temp for deterministic extraction
            max_tokens=4096,
        )
        client = LlmRetryClient(config)

        system_context = (
            "Du bist ein medizinischer Dokumentations-Assistent. "
            "Extrahiere die klinischen Daten in das vorgegebene JSON Schema."
        )
        prompt = (
            "Aufgabe: Analysiere den folgenden Krankenhaus-Bericht und generiere "
            "exakt EIN JSON Objekt mit allen gefundenen Werten. Erfinde keine Daten.\n\n"
            f"--- OCR TEXT ---\n{task.ocr_text}\n--- ENDE OCR TEXT ---"
        )

        try:
            # Client hands ValidationError back to LLM automatically
            bundle = await client.generate_structured(
                prompt=prompt,
                schema=BundleExtraction,
                system_context=system_context,
            )
            
            fhir_bundle_dict = json.loads(bundle.model_dump_json(exclude_none=True))
            json_str = json.dumps(fhir_bundle_dict, indent=2, ensure_ascii=False)

            # Persist Claim-Check Payload (non-blocking)
            await asyncio.to_thread(_update_job_sync, task.job_id, "FHIR_GENERATED", fhir_json=json_str)

            # Route to next pipeline stage (FHIR-Transformation)
            export_msg = FhirExportMessage(job_id=task.job_id, bundle_json=json_str)
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=export_msg.model_dump_json().encode("utf-8"),
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key="fhir_export_queue"
            )

            await message.ack()
            logger.info(f"  ✓ LLM Job #{task.job_id} beendet. Routing zur FHIR-Transformation ok.")

        except LlmValidationError as e:
            # Arch-Rule #3: Final Retry fails -> Manual DLQ Publish and explicit reject
            logger.error(f"  ✗ LLM Validation Error für Job #{task.job_id} (retries exhausted): {e}")
            
            await dlq_exchange.publish(
                aio_pika.Message(
                    body=message.body,
                    headers={
                        "x-error-type": "LlmValidationError",
                        "x-validation-errors": str(e.validation_errors),
                        "x-last-raw-output": str(e.last_raw_output)[:2000],
                    }
                ),
                routing_key=""
            )
            await message.reject(requeue=False)
            logger.info(f"  -> Job #{task.job_id} wurde in llm_dlq verschoben und Message rejected.")

            await asyncio.to_thread(_update_job_sync, task.job_id, "ERROR", error_trace=f"LlmValidationError: {str(e)}")

    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"  ✗ Unbehandelter Fehler! {type(e).__name__}: {e}")

        # Generic error handling sets DB and natively dead-letters (requeue=False)
        try:
            task = LlmTaskMessage.model_validate_json(message.body)
            await asyncio.to_thread(_update_job_sync, task.job_id, "ERROR", error_trace=error_trace)
        except Exception:
            pass

        await message.reject(requeue=False)


async def run_worker() -> None:
    async with get_rabbitmq_connection() as connection:
        channel, _, llm_queue, _ = await init_rabbitmq(connection)
        
        # Arch-Rule #1: STRIKT auf prefetch_count=1 konfigurieren für VRAM Protection
        await channel.set_qos(prefetch_count=1)

        # Arch-Rule #3: Designierter llm_dlq Exchange (Fanout for DLQ logic)
        dlq_exchange = await channel.declare_exchange(
            "llm_dlq", aio_pika.ExchangeType.FANOUT, durable=True
        )

        logger.info("=======================================")
        logger.info("🧠 LLM Worker Active (AsyncIO & prefetch=1, No Semaphore)")
        logger.info("=======================================")

        callback = partial(
            process_llm_message,
            channel=channel,
            dlq_exchange=dlq_exchange,
        )
        # Consume incoming inference requests
        await llm_queue.consume(callback)

        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(run_worker())
