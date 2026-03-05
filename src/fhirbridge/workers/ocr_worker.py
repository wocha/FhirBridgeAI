"""
OCR Worker Daemon for FhirBridgeAI
===================================
Polls the INBOUND directory and publishes new PDFs to RabbitMQ.
Consumes messages from `ocr_task_queue`, performs heavy computer vision tasks (PDF -> Text)
without blocking the LLM pipeline, and publishes results to `llm_task_queue`.
"""

import asyncio
import json
import logging
import os
import traceback
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import aio_pika
import aioboto3
import cv2
import fitz
import numpy as np
import pytesseract
from opentelemetry import context as otel_context
from opentelemetry.propagate import extract, inject

from fhirbridge.core.database import Job, JobStatus, get_session_factory, init_db
from fhirbridge.core.rabbitmq import (
    DocumentMetaData,
    OcrTaskMessage,
    get_rabbitmq_connection,
    init_rabbitmq,
)
from fhirbridge.core.telemetry import init_tracer
from fhirbridge.privacy.pseudonymizer import LocalAnonymizer

CONFIG: dict[str, Any] = {
    "DB_PATH": "data/dispatcher.db",
    "DPI": 300,
    "LANG": "deu",
    "MINIO_URL": os.getenv("MINIO_URL", "http://minio:9000"),
    "MINIO_ROOT_USER": os.getenv("MINIO_ROOT_USER", "admin"),
    "MINIO_ROOT_PASSWORD": os.getenv("MINIO_ROOT_PASSWORD", "admin123"),
    "S3_BUCKET": "ephemeral-payloads",
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [OCR] - %(levelname)s - %(message)s")
logger = logging.getLogger("OCRWorker")

# Initialize database globally for the worker
engine = init_db(str(CONFIG["DB_PATH"]))
SessionFactory = get_session_factory(engine)

tracer = init_tracer("ocr-worker")




def extract_raw_ocr_sync(pdf_bytes: bytes) -> str:
    """
    Synchronous CPU-heavy OCR function.
    Performs raw OCR ONLY using PyMuPDF, OpenCV, and Tesseract.
    (LLM cleanup is explicitly avoided here!)
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    complete_raw_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)

        # Convert fitz pixmap to numpy array for OpenCV
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:  # RGBA
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:  # RGB
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:  # Grayscale
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

        # CV Preprocessing from local_extract.py (Grayscale, Blur, Otsu)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, processed_img = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Tesseract
        try:
            raw_ocr = pytesseract.image_to_string(processed_img, lang="deu")
            if raw_ocr.strip():
                complete_raw_text.append(f"--- SEITE {page_num + 1} ---\n{raw_ocr}")
        except Exception as e:
            logger.error(f"  [!] Tesseract Error on page {page_num+1}: {e}")
            continue

    return "\n\n".join(complete_raw_text)


async def process_ocr_message(
    message: aio_pika.abc.AbstractIncomingMessage,
    channel: aio_pika.abc.AbstractChannel,
) -> None:
    """
    RabbitMQ Consumer Callback for OCR Tasks.
    """
    headers = message.headers or {}
    ctx = extract(headers)

    token = otel_context.attach(ctx)
    try:
        with tracer.start_as_current_span("process_ocr_message", context=ctx) as span:
            async with message.process(requeue=False, ignore_processed=True):
                try:
                    task = OcrTaskMessage.model_validate_json(message.body)
                    span.set_attribute("job_id", task.job_id)
                    span.set_attribute("filepath", task.filepath)
                    logger.info(
                        f"Starte OCR Verarbeitung von Job #{task.job_id}: {os.path.basename(task.filepath)}"
                    )

                    with SessionFactory() as session:
                        job = session.query(Job).filter_by(id=task.job_id).first()
                        if job:
                            job.status = JobStatus.OCR_PROCESSING
                            session.commit()

                    # Fetch PDF from S3 Claim-Check into memory
                    logger.info(
                        f"  -> Fetching PDF from S3 {task.s3_object_key} for Job #{task.job_id}..."
                    )
                    
                    session_s3 = aioboto3.Session()
                    async with session_s3.client(
                        "s3",
                        endpoint_url=CONFIG["MINIO_URL"],
                        aws_access_key_id=CONFIG["MINIO_ROOT_USER"],
                        aws_secret_access_key=CONFIG["MINIO_ROOT_PASSWORD"],
                    ) as s3:
                        response = await s3.get_object(Bucket=CONFIG["S3_BUCKET"], Key=task.s3_object_key)
                        pdf_bytes = await response['Body'].read()

                    # Offload heavy CV work to ProcessPoolExecutor
                    logger.info(
                        f"  -> Executing native raw OCR via ProcessPoolExecutor for Job #{task.job_id}..."
                    )

                    loop = asyncio.get_running_loop()
                    with ProcessPoolExecutor(max_workers=2) as pool:
                        ocr_text = await loop.run_in_executor(pool, extract_raw_ocr_sync, pdf_bytes)

                    if not ocr_text.strip():
                        raise ValueError("OCR lieferte leeren Text zurück.")

                    # 1. Anonymize the raw text
                    logger.info(f"  -> Anonymizing OCR text for Job #{task.job_id}...")
                    anonymizer = LocalAnonymizer()
                    anon_result = anonymizer.anonymize(ocr_text)

                    # Claim-Check: Save to ephemeral storage using S3 object storage
                    object_key = f"job_{task.job_id}_payload.txt"
                    mapping_key = f"mappings/{task.job_id}.json"
                    session_s3 = aioboto3.Session()
                    async with session_s3.client(
                        "s3",
                        endpoint_url=CONFIG["MINIO_URL"],
                        aws_access_key_id=CONFIG["MINIO_ROOT_USER"],
                        aws_secret_access_key=CONFIG["MINIO_ROOT_PASSWORD"],
                    ) as s3:
                        # Upload anonymized payload
                        await s3.put_object(
                            Bucket=CONFIG["S3_BUCKET"], Key=object_key, Body=anon_result.anonymized_text.encode("utf-8")
                        )
                        # Upload mapping securely to Vault
                        await s3.put_object(
                            Bucket=CONFIG["S3_BUCKET"], Key=mapping_key, Body=json.dumps(anon_result.mapping).encode("utf-8")
                        )

                    s3_uri = f"s3://ephemeral-payloads/{object_key}"

                    # DB Operations via thread to not block the loop
                    def update_db_status():
                        with SessionFactory() as session:
                            job = session.query(Job).filter_by(id=task.job_id).first()
                            if job:
                                job.ocr_text = s3_uri  # type: ignore[assignment]
                                job.status = JobStatus.LLM_EXTRACTION
                                session.commit()

                    await asyncio.to_thread(update_db_status)

                    # Publish to LLM extraction queue (Claim Check model)
                    llm_msg = DocumentMetaData(
                        job_id=task.job_id, filepath=task.filepath, s3_object_key=object_key
                    )

                    out_headers = {}
                    inject(out_headers)

                    try:
                        await channel.default_exchange.publish(
                            aio_pika.Message(body=llm_msg.model_dump_json().encode(), headers=out_headers),
                            routing_key="llm_extraction_queue",
                        )
                    except Exception as publish_error:
                        logger.error(
                            f"  [!] RabbitMQ Publish Failed for Job #{task.job_id}. Rolling back Claim-Check storage..."
                        )
                        # Compensation logic: Prevent Storage Leak
                        async with session_s3.client(
                            "s3",
                            endpoint_url=CONFIG["MINIO_URL"],
                            aws_access_key_id=CONFIG["MINIO_ROOT_USER"],
                            aws_secret_access_key=CONFIG["MINIO_ROOT_PASSWORD"],
                        ) as s3:
                            await s3.delete_object(Bucket=CONFIG["S3_BUCKET"], Key=object_key)
                            await s3.delete_object(Bucket=CONFIG["S3_BUCKET"], Key=mapping_key)
                        raise publish_error

                    # Explicitly ACK the message
                    await message.ack()
                    logger.info(f"  ✓ OCR abgeschlossen. Job #{task.job_id} an LLM-Queue übergeben.")

                except Exception as e:
                    error_trace = traceback.format_exc()
                    logger.error(f"  ✗ Job fehlgeschlagen! {type(e).__name__}: {e}")

                    # Try to save error to DB
                    try:
                        # Database update via thread
                        def fail_db_status():
                            task_msg = OcrTaskMessage.model_validate_json(message.body)
                            with SessionFactory() as session:
                                job = session.query(Job).filter_by(id=task_msg.job_id).first()
                                if job:
                                    job.status = JobStatus.FAILED
                                    job.error_trace = error_trace  # type: ignore[assignment]
                                    session.commit()

                        await asyncio.to_thread(fail_db_status)
                    except Exception:
                        pass

                    # Reject and do not requeue -> routes to Dead Letter Exchange
                    await message.reject(requeue=False)
    finally:
        otel_context.detach(token)


async def run_worker() -> None:
    logger.info("=======================================")
    logger.info("🚀 OCR Worker Active (AsyncIO & RabbitMQ)")
    logger.info("=======================================")

    async with get_rabbitmq_connection() as connection:
        channel, queues = await init_rabbitmq(connection)
        ocr_queue = queues["ocr_queue"]

        # Start consumer
        await ocr_queue.consume(lambda msg: process_ocr_message(msg, channel))

        # Keep worker alive
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(run_worker())
