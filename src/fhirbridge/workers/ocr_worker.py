"""
OCR Worker Daemon for FhirBridgeAI
===================================
Polls the INBOUND directory and publishes new PDFs to RabbitMQ.
Consumes messages from `ocr_task_queue`, performs heavy computer vision tasks (PDF -> Text)
without blocking the LLM pipeline, and publishes results to `llm_task_queue`.
"""

import aiofiles
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
import os
import traceback
import sys
import shutil
from pathlib import Path
from typing import Any

import cv2
import fitz
import numpy as np
import pytesseract

import aio_pika

from fhirbridge.core.database import Job, get_session_factory, init_db
from fhirbridge.core.rabbitmq import (
    DocumentMetaData,
    OcrTaskMessage,
    get_rabbitmq_connection,
    init_rabbitmq,
)

CONFIG: dict[str, Any] = {
    "INBOUND_DIR": "data/inbound",
    "POLL_INTERVAL": 5,
    "DB_PATH": "data/dispatcher.db",
    "EPHEMERAL_DIR": "data/ephemeral",
    "ERROR_DIR": "data/errors",
    "DPI": 300,
    "LANG": "deu",
}

os.makedirs(str(CONFIG["INBOUND_DIR"]), exist_ok=True)
os.makedirs(str(CONFIG["EPHEMERAL_DIR"]), exist_ok=True)
os.makedirs(str(CONFIG["ERROR_DIR"]), exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [OCR] - %(levelname)s - %(message)s")
logger = logging.getLogger("OCRWorker")

# Initialize database globally for the worker
engine = init_db(str(CONFIG["DB_PATH"]))
SessionFactory = get_session_factory(engine)


async def ingest_new_pdfs(channel: aio_pika.abc.AbstractChannel) -> int:
    """
    Recursively find all PDFs in subfolders, create a DB record,
    and publish them to the RabbitMQ OCR task queue.
    """
    pdf_files = sorted(
        glob.glob(os.path.join(str(CONFIG["INBOUND_DIR"]), "**", "*.pdf"), recursive=True)
    )
    added = 0

    with SessionFactory() as session:
        for filepath in pdf_files:
            exists = session.query(Job).filter_by(filepath=filepath).first()
            if not exists:
                new_job = Job(filepath=filepath, status="PENDING")
                session.add(new_job)
                session.commit()  # Commit to get the ID

                # Publish to RabbitMQ
                msg = OcrTaskMessage(job_id=new_job.id, filepath=filepath)  # type: ignore[arg-type]

                await channel.default_exchange.publish(
                    aio_pika.Message(body=msg.model_dump_json().encode()),
                    routing_key="ocr_task_queue",
                )

                # Update status to reflect it's queued
                new_job.status = "QUEUED_OCR"  # type: ignore[assignment]
                session.commit()

                logger.info(f"Ingested new PDF: Job #{new_job.id}, {os.path.basename(filepath)}")
                added += 1

    return added

def extract_raw_ocr_sync(pdf_path: str) -> str:
    """
    Synchronous CPU-heavy OCR function. 
    Performs raw OCR ONLY using PyMuPDF, OpenCV, and Tesseract.
    (LLM cleanup is explicitly avoided here!)
    """
    doc = fitz.open(pdf_path)
    complete_raw_text = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)

        # Convert fitz pixmap to numpy array for OpenCV
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4: # RGBA
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3: # RGB
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else: # Grayscale
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

        # CV Preprocessing from local_extract.py (Grayscale, Blur, Otsu)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        _, processed_img = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Tesseract
        try:
            raw_ocr = pytesseract.image_to_string(processed_img, lang='deu')
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
    async with message.process(requeue=False, ignore_processed=True):
        try:
            task = OcrTaskMessage.model_validate_json(message.body)
            logger.info(
                f"Starte OCR Verarbeitung von Job #{task.job_id}: {os.path.basename(task.filepath)}"
            )

            with SessionFactory() as session:
                job = session.query(Job).filter_by(id=task.job_id).first()
                if job:
                    job.status = "OCR_PROCESSING"  # type: ignore[assignment]
                    session.commit()

            # Offload heavy CV work to ProcessPoolExecutor
            logger.info(f"  -> Executing native raw OCR via ProcessPoolExecutor for Job #{task.job_id}...")
            
            loop = asyncio.get_running_loop()
            with ProcessPoolExecutor() as pool:
                ocr_text = await loop.run_in_executor(pool, extract_raw_ocr_sync, task.filepath)

            if not ocr_text.strip():
                raise ValueError("OCR lieferte leeren Text zurück.")
                
            # Claim-Check: Save to ephemeral storage using non-blocking I/O
            # TODO (Cloud-Native): This local/shared volume approach is a Known Technical Debt.
            # In a multi-node Swarm/Kubernetes cluster, this will fail if the OCR pod and LLM pod 
            # run on different nodes. This MUST be refactored to use an S3-compatible Object Storage 
            # (e.g. MinIO via boto3) or a proper distributed file system (NFS/EFS/Longhorn) to ensure 
            # true horizontal scalability.
            payload_filename = f"job_{task.job_id}_payload.txt"
            ephemeral_path = os.path.join(str(CONFIG["EPHEMERAL_DIR"]), payload_filename)
            
            async with aiofiles.open(ephemeral_path, mode="w", encoding="utf-8") as f:
                await f.write(ocr_text)
            
            payload_uri = f"file://{os.path.abspath(ephemeral_path)}"

            # DB Operations via thread to not block the loop
            def update_db_status():
                with SessionFactory() as session:
                    job = session.query(Job).filter_by(id=task.job_id).first()
                    if job:
                        job.ocr_text = payload_uri  # type: ignore[assignment]
                        job.status = "QUEUED_LLM"  # type: ignore[assignment]
                        session.commit()
            
            await asyncio.to_thread(update_db_status)

            # Publish to LLM extraction queue (Claim Check model)
            llm_msg = DocumentMetaData(job_id=task.job_id, filepath=task.filepath, payload_uri=payload_uri)
            
            try:
                await channel.default_exchange.publish(
                    aio_pika.Message(body=llm_msg.model_dump_json().encode()),
                    routing_key="llm_extraction_queue",
                )
            except Exception as publish_error:
                logger.error(f"  [!] RabbitMQ Publish Failed for Job #{task.job_id}. Rolling back Claim-Check storage...")
                # Compensation logic: Prevent Storage Leak
                if os.path.exists(ephemeral_path):
                    await asyncio.to_thread(os.remove, ephemeral_path)
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
                            job.status = "ERROR_EMPTY" if isinstance(e, ValueError) else "ERROR_OCR"  # type: ignore[assignment]
                            job.error_trace = error_trace  # type: ignore[assignment]
                            session.commit()
                await asyncio.to_thread(fail_db_status)
                        
                # Move original file to error dir without blocking
                def move_error_file():
                    task_msg = OcrTaskMessage.model_validate_json(message.body)
                    error_dest = os.path.join(str(CONFIG["ERROR_DIR"]), os.path.basename(task_msg.filepath))
                    if os.path.exists(task_msg.filepath):
                        shutil.move(task_msg.filepath, error_dest)
                await asyncio.to_thread(move_error_file)
            except Exception:
                pass

            # Reject and do not requeue -> routes to Dead Letter Exchange
            await message.reject(requeue=False)


async def ingestion_daemon(channel: aio_pika.abc.AbstractChannel) -> None:
    """Daemon task that periodically checks for new PDFs."""
    while True:
        try:
            await ingest_new_pdfs(channel)
        except Exception as e:
            logger.error(f"Fehler im Ingestion Daemon: {e}")
        await asyncio.sleep(int(CONFIG["POLL_INTERVAL"]))


async def run_worker() -> None:
    logger.info("=======================================")
    logger.info("🚀 OCR Worker Active (AsyncIO & RabbitMQ)")
    logger.info("=======================================")

    async with get_rabbitmq_connection() as connection:
        channel, ocr_queue, _ = await init_rabbitmq(connection)

        # Start consumer
        await ocr_queue.consume(lambda msg: process_ocr_message(msg, channel))

        # Start ingestion loop daemon concurrently
        ingestion_task = asyncio.create_task(ingestion_daemon(channel))

        # Keep worker alive
        await ingestion_task


if __name__ == "__main__":
    asyncio.run(run_worker())
