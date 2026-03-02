"""
Standalone Reference Implementation: RabbitMQ Worker for the Autonomous Dispatcher.
====================================================================================
This is a SIMPLIFIED, standalone prototype that demonstrates the core RabbitMQ patterns
(At-Least-Once Delivery, Dead-Letter Exchange) used by the production workers.

For the canonical production implementations, see:
    - src/fhirbridge/workers/ocr_worker.py  (OCR Consumer)
    - src/fhirbridge/workers/llm_worker.py  (LLM Consumer)
    - src/fhirbridge/core/rabbitmq.py       (Connection & DLX Setup)
    - src/fhirbridge/core/database.py       (Job Model & DB Init)

This script can be run standalone for local testing without the full package:
    py .agents/skills/building-autonomous-dispatchers/scripts/mq_worker.py
"""

import asyncio
import json
import logging
import os
import sys
import traceback

import aio_pika
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import our schema and constants from sibling skill script
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
from schema_reference import Base, Job, JobStatus

# Import Canonical LLM Client
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "integrating-local-llms", "scripts")))
from llm_retry_client import LlmRetryClient

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("mq_worker")

# ─── Configuration ────────────────────────────────────────────────────────────
DB_PATH = os.getenv(
    "DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "dispatcher.db"))
)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://mq_admin:secure_mq_pass@localhost:5672/")

llm_client = LlmRetryClient()

QUEUE_NAME = "fhir_jobs_queue"
DLX_NAME = "fhir_dlx"
DLQ_NAME = "fhir_dlq"


# ─── Message Processing ──────────────────────────────────────────────────────
async def process_message(message: aio_pika.abc.AbstractIncomingMessage):
    """
    Callback for processing an incoming AMQP message.

    Implements At-Least-Once Delivery:
        - ACK is sent ONLY after the FHIR result is committed to the database.
        - NACK (reject with requeue=False) routes the message to the DLX on failure.
    """
    async with message.process(requeue=False, ignore_processed=True):
        try:
            body = json.loads(message.body.decode())
            job_id = body.get("job_id")
            file_path = body.get("file_path")

            if not job_id or not file_path:
                logger.error(f"Invalid message format, missing job_id or file_path: {body}")
                await message.reject(requeue=False)  # Route to DLX
                return

            logger.info(f"Received job {job_id} for file: {file_path}")

            # --- Business Logic ---
            # 1. Update DB to Processing
            with SessionLocal() as session:
                job = session.get(Job, job_id)
                if not job:
                    logger.warning(f"Job {job_id} not found in DB, skipping.")
                    await message.ack()
                    return
                job.status = JobStatus.OCR_PROCESSING
                session.commit()

            # 2. Mock OCR
            logger.info(f"Worker processing OCR for job {job_id}")
            await asyncio.sleep(1)  # Simulated async I/O

            # 3. LLM Extraction
            with SessionLocal() as session:
                job = session.get(Job, job_id)
                job.status = JobStatus.LLM_EXTRACTION
                session.commit()

            logger.info(f"Worker running LLM Extraction for job {job_id}")

            # Zero-Trust Data Privacy Layer (optional pre-processing)
            ocr_text_raw = f"Mock OCR Text für Patient Max Mustermann (KVNR: A123456789) aus Datei {file_path}."
            zero_trust_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "implementing-zero-trust-privacy", "scripts"))
            if zero_trust_dir not in sys.path:
                sys.path.append(zero_trust_dir)

            try:
                from anonymizer import LocalAnonymizer
                anonymizer = LocalAnonymizer()
                anon_result = anonymizer.anonymize(ocr_text_raw)
                logger.info(f"Anonymisiert vor LLM: {anon_result.anonymized_text[:50]}...")
            except Exception as e:
                logger.warning(f"Feature 'Zero-Trust' not fully available: {e}. Falling back.")

                class FakeResult:
                    anonymized_text = ocr_text_raw
                    mapping = {}

                anon_result = FakeResult()
                anonymizer = None

            # Simulate extraction (in production: use llm_client.extract_structured)
            from pydantic import BaseModel, Field

            class ClinicalExtraction(BaseModel):
                summary: str = Field(..., description="A short summary of the text.")

            # Intentional failure for DLX testing
            if "Testbrief_Fail" in file_path:
                raise ValueError("Intentional failure for DLX testing")

            result = ClinicalExtraction(summary=f"Mocked Summary für extracted {anon_result.anonymized_text[:20]}")

            if anonymizer and anon_result.mapping:
                result = anonymizer.deanonymize(result, anon_result.mapping)

            logger.info(f"Extraction yield: {result.summary}")

            # 4. Final DB Update — COMMIT BEFORE ACK (At-Least-Once guarantee)
            with SessionLocal() as session:
                job = session.get(Job, job_id)
                job.status = JobStatus.FHIR_GENERATED
                job.lock_id = None
                job.locked_at = None
                session.commit()

            logger.info(f"Job {job_id} successfully finished.")
            await message.ack()

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())

            # Update DB with error status if possible
            try:
                body = json.loads(message.body.decode())
                job_id_to_fail = body.get("job_id")
                if job_id_to_fail:
                    with SessionLocal() as session:
                        job = session.get(Job, job_id_to_fail)
                        if job:
                            job.status = JobStatus.FAILED_PERMANENTLY
                            job.error_message = str(e)
                            session.commit()
            except Exception as db_err:
                logger.error(f"Could not update DB status for failed message: {db_err}")

            # NACK → DLX
            logger.warning("NACKing message to DLX.")
            await message.reject(requeue=False)


# ─── Main Entrypoint ─────────────────────────────────────────────────────────
async def main():
    """Connects to RabbitMQ with retry, declares queues with DLX, and starts consuming."""
    while True:
        try:
            logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}...")
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            break
        except Exception as e:
            logger.info(f"Waiting for RabbitMQ... {e}")
            await asyncio.sleep(5)

    async with connection:
        channel = await connection.channel()

        # Fair dispatch: process one message at a time
        await channel.set_qos(prefetch_count=1)

        # Declare Dead Letter Exchange & Queue
        dlx = await channel.declare_exchange(DLX_NAME, aio_pika.ExchangeType.DIRECT)
        dlq = await channel.declare_queue(DLQ_NAME, durable=True)
        await dlq.bind(dlx, routing_key="dlx_routing_key")

        # Declare Main Queue with DLX binding
        queue = await channel.declare_queue(
            QUEUE_NAME,
            durable=True,
            arguments={
                "x-dead-letter-exchange": DLX_NAME,
                "x-dead-letter-routing-key": "dlx_routing_key"
            }
        )

        logger.info(f" [*] Waiting for messages in '{QUEUE_NAME}'. To exit press CTRL+C")
        await queue.consume(process_message)

        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            logger.info("Worker cancelled, shutting down...")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker gracefully shutting down.")
