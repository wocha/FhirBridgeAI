"""OCR worker with delegated auth verification and transactional outbox transitions."""

from __future__ import annotations

import asyncio
import json
import logging
from concurrent.futures import ProcessPoolExecutor
from uuid import uuid4

import aio_pika
import aioboto3
import cv2
import fitz
import numpy as np
import pytesseract
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fhirbridge.core.auth import TokenExchangeService
from fhirbridge.core.base_worker import BaseRabbitMQWorker
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import (
    JobStatus,
    OutboxEvent,
    get_async_engine,
    get_async_session_factory,
    get_or_create_read_model_async,
    load_job_async,
    record_consumed_message_async,
    verify_runtime_schema_async,
)
from fhirbridge.core.failure_handling import PermanentDataError, TransientInfrastructureError
from fhirbridge.core.rabbitmq import DocumentMetaData, OcrTaskMessage
from fhirbridge.core.storage import build_phi_vault_claim_check, build_processing_claim_check, s3_client_kwargs
from fhirbridge.privacy.pseudonymizer import LocalAnonymizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [OCR] - %(levelname)s - %(message)s")

AsyncEngineRef: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global AsyncEngineRef, AsyncSessionFactory

    if AsyncEngineRef is None:
        AsyncEngineRef = get_async_engine()
    if AsyncSessionFactory is None:
        AsyncSessionFactory = get_async_session_factory(AsyncEngineRef)
    return AsyncEngineRef, AsyncSessionFactory


def extract_raw_ocr_sync(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    complete_raw_text: list[str] = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4:
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3:
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else:
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, processed_img = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        raw_ocr = pytesseract.image_to_string(processed_img, lang="deu")
        if raw_ocr.strip():
            complete_raw_text.append(f"--- PAGE {page_num + 1} ---\n{raw_ocr}")
    return "\n\n".join(complete_raw_text)


async def _persist_failure(job_id: int, status: JobStatus, error_trace: str) -> None:
    _, session_factory = _get_database()
    async with session_factory() as session:
        async with session.begin():
            job = await load_job_async(session, job_id=job_id)
            if not job:
                return
            job.status = status
            job.aggregate_version += 1
            job.required_read_version = job.aggregate_version
            job.error_trace = error_trace
            projection = await get_or_create_read_model_async(session, job_id=int(job.id))
            projection.required_version = int(job.aggregate_version)
            projection.visible_version = int(job.aggregate_version)
            projection.status = str(job.status.value)


class OcrWorker(BaseRabbitMQWorker):
    def __init__(self) -> None:
        super().__init__("ocr-worker", "ocr_task_queue", prefetch_count=1)
        self.anonymizer = LocalAnonymizer()
        self.session_s3 = aioboto3.Session()

    async def setup(self) -> None:
        settings = get_settings()
        settings.require_database_url()
        settings.require_rabbitmq_url()
        settings.require_internal_auth_context_secret()
        settings.require_minio_credentials()
        settings.require_minio_url()
        settings.minio_http_verify()
        settings.object_storage_buckets()

        engine, _ = _get_database()
        await verify_runtime_schema_async(engine)

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        task = OcrTaskMessage.model_validate_json(message.body)
        span = trace.get_current_span()
        span.set_attribute("job_id", task.job_id)
        span.set_attribute("tenant_scope", task.tenant_scope)
        span.set_attribute("submitted_filename", task.submitted_filename)

        token_exchange = TokenExchangeService.from_settings()
        internal_context = token_exchange.verify(
            task.auth_context,
            expected_tenant_scope=task.tenant_scope,
            expected_event_id=task.event_id,
        )

        try:
            async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=task.evidence.bucket, Key=task.evidence.object_key)
                pdf_bytes = await response["Body"].read()
        except Exception as exc:
            raise TransientInfrastructureError("Failed to retrieve source document from evidence storage") from exc

        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=2) as pool:
            ocr_text = await loop.run_in_executor(pool, extract_raw_ocr_sync, pdf_bytes)

        if not ocr_text.strip():
            await _persist_failure(
                task.job_id,
                JobStatus.QUARANTINED,
                "OCR returned empty content",
            )
            raise PermanentDataError("OCR produced no readable text")

        anon_result = self.anonymizer.anonymize(ocr_text)
        processing_ref = build_processing_claim_check(job_id=task.job_id, source_kind=task.source_kind)
        mapping_ref = build_phi_vault_claim_check(job_id=task.job_id)
        try:
            async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                await s3.put_object(
                    Bucket=processing_ref.bucket,
                    Key=processing_ref.object_key,
                    Body=anon_result.anonymized_text.encode("utf-8"),
                )
                await s3.put_object(
                    Bucket=mapping_ref.bucket,
                    Key=mapping_ref.object_key,
                    Body=json.dumps(anon_result.mapping, sort_keys=True).encode("utf-8"),
                )
        except Exception as exc:
            raise TransientInfrastructureError("Failed to persist OCR processing artifacts") from exc

        _, session_factory = _get_database()
        try:
            async with session_factory() as session:
                async with session.begin():
                    job = await load_job_async(session, job_id=task.job_id)
                    if not job:
                        raise PermanentDataError(f"Unknown job_id {task.job_id}")
                    if not await record_consumed_message_async(
                        session,
                        consumer_name=self.worker_name,
                        event_id=task.event_id,
                    ):
                        return

                    job.processing_bucket = processing_ref.bucket
                    job.processing_object_key = processing_ref.object_key
                    job.processing_media_type = processing_ref.media_type
                    job.mapping_bucket = mapping_ref.bucket
                    job.mapping_object_key = mapping_ref.object_key
                    job.status = JobStatus.LLM_EXTRACTION
                    job.aggregate_version += 1
                    job.required_read_version = job.aggregate_version

                    projection = await get_or_create_read_model_async(session, job_id=int(job.id))
                    projection.required_version = int(job.aggregate_version)
                    projection.visible_version = int(job.aggregate_version)
                    projection.status = str(job.status.value)

                    next_event_id = str(uuid4())
                    next_auth_context = token_exchange.delegate(
                        existing_context=internal_context,
                        trace_id=task.trace_id,
                        bound_event_id=next_event_id,
                    )
                    llm_msg = DocumentMetaData(
                        event_id=next_event_id,
                        trace_id=task.trace_id,
                        tenant_scope=task.tenant_scope,
                        aggregate_version=int(job.aggregate_version),
                        auth_context=next_auth_context,
                        job_id=task.job_id,
                        source_kind=task.source_kind,
                        submitted_filename=task.submitted_filename,
                        review_required=task.review_required,
                        document=processing_ref,
                        evidence=task.evidence,
                    )

                    session.add(
                        OutboxEvent(
                            aggregate_id=int(job.id),
                            aggregate_version=int(job.aggregate_version),
                            event_type="job.llm.requested",
                            destination="llm_extraction_queue",
                            payload_json=llm_msg.model_dump_json(),
                            trace_id=task.trace_id,
                            tenant_scope=task.tenant_scope,
                            dedupe_key=f"job:{job.id}:version:{job.aggregate_version}:llm",
                        )
                    )
        except Exception as exc:
            async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                await s3.delete_object(Bucket=processing_ref.bucket, Key=processing_ref.object_key)
                await s3.delete_object(Bucket=mapping_ref.bucket, Key=mapping_ref.object_key)
            raise TransientInfrastructureError("Failed to persist OCR state and outbox event") from exc

        self.logger.info("OCR complete for job=%s", task.job_id)


if __name__ == "__main__":
    worker = OcrWorker()
    asyncio.run(worker.run())
