"""LLM worker with delegated auth verification, advisory-only Qdrant gating, and manual review."""

from __future__ import annotations

import asyncio
import json
import logging
import traceback

import aio_pika
import aioboto3
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fhirbridge.core.auth import PolicyAuthError, TokenExchangeService
from fhirbridge.core.base_worker import BaseRabbitMQWorker
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import (
    JobStatus,
    ManualReviewStatus,
    create_security_audit_event_async,
    get_async_engine,
    get_async_session_factory,
    get_or_create_manual_review_case_async,
    get_or_create_read_model_async,
    load_job_async,
    record_consumed_message_async,
    store_semantic_chunks_async,
    verify_runtime_schema_async,
)
from fhirbridge.core.failure_handling import PermanentDataError, TransientInfrastructureError
from fhirbridge.core.llm import LlmConfig, LlmConnectionError, LlmRetryClient, LlmValidationError
from fhirbridge.core.qdrant_security import advisory_only_gate, enforce_advisory_only_transition
from fhirbridge.core.rabbitmq import DocumentMetaData, IngestionSourceKind
from fhirbridge.core.semantic_chunking import split_semantic_chunks
from fhirbridge.core.storage import HL7_MEDIA_TYPE, PDF_MEDIA_TYPE, build_phi_vault_claim_check, build_processing_claim_check, s3_client_kwargs
from fhirbridge.models.fhir_models import BundleExtraction
from fhirbridge.privacy.pseudonymizer import LocalAnonymizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [LLM] - %(levelname)s - %(message)s")

AsyncEngineRef: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global AsyncEngineRef, AsyncSessionFactory

    if AsyncEngineRef is None:
        AsyncEngineRef = get_async_engine()
    if AsyncSessionFactory is None:
        AsyncSessionFactory = get_async_session_factory(AsyncEngineRef)
    return AsyncEngineRef, AsyncSessionFactory


async def _persist_terminal_state(job_id: int, status: JobStatus, error_trace: str) -> None:
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


class LlmWorker(BaseRabbitMQWorker):
    def __init__(self) -> None:
        super().__init__("llm-worker", "llm_extraction_queue", prefetch_count=1)
        self.session_s3 = aioboto3.Session()
        self.anonymizer = LocalAnonymizer()

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
        task = DocumentMetaData.model_validate_json(message.body)
        span = trace.get_current_span()
        span.set_attribute("job_id", task.job_id)
        span.set_attribute("tenant_scope", task.tenant_scope)
        span.set_attribute("source_kind", task.source_kind.value)

        token_exchange = TokenExchangeService.from_settings()
        internal_context = token_exchange.verify(
            task.auth_context,
            expected_tenant_scope=task.tenant_scope,
            expected_event_id=task.event_id,
        )

        self.logger.info(
            "Start LLM processing for job=%s tenant=%s source_kind=%s",
            task.job_id,
            task.tenant_scope,
            task.source_kind.value,
        )

        if task.source_kind == IngestionSourceKind.PDF_SCAN and task.document.media_type == PDF_MEDIA_TYPE:
            raise PolicyAuthError("PDF scan arrived at LLM without OCR stage handoff")

        try:
            async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=task.document.bucket, Key=task.document.object_key)
                async with response["Body"] as stream:
                    source_text = (await stream.read()).decode("utf-8")
        except Exception as exc:
            raise TransientInfrastructureError(f"S3 fetch failed for job {task.job_id}") from exc

        processing_ref = task.document
        mapping_ref = None
        cleanup_refs: list[tuple[str, str]] = []
        llm_input_text = source_text
        if task.source_kind == IngestionSourceKind.HL7_V2:
            anonymized = self.anonymizer.anonymize(source_text)
            llm_input_text = anonymized.anonymized_text
            processing_ref = build_processing_claim_check(job_id=task.job_id, source_kind=task.source_kind)
            mapping_ref = build_phi_vault_claim_check(job_id=task.job_id)
            try:
                async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                    await s3.put_object(
                        Bucket=processing_ref.bucket,
                        Key=processing_ref.object_key,
                        Body=llm_input_text.encode("utf-8"),
                    )
                    await s3.put_object(
                        Bucket=mapping_ref.bucket,
                        Key=mapping_ref.object_key,
                        Body=json.dumps(anonymized.mapping, sort_keys=True).encode("utf-8"),
                    )
                cleanup_refs = [
                    (processing_ref.bucket, processing_ref.object_key),
                    (mapping_ref.bucket, mapping_ref.object_key),
                ]
            except Exception as exc:
                raise TransientInfrastructureError("Failed to persist HL7 processing artifacts") from exc

        config = LlmConfig(max_retries=3, temperature=0.1, max_tokens=4096)
        client = LlmRetryClient(config)

        system_context = (
            "Du bist ein medizinischer Dokumentations-Assistent. "
            "Extrahiere die klinischen Daten in das vorgegebene JSON Schema."
        )
        prompt = (
            "Aufgabe: Analysiere den folgenden Krankenhaus-Bericht und generiere "
            "exakt EIN JSON Objekt mit allen gefundenen Werten. Erfinde keine Daten.\n\n"
            f"--- SOURCE TEXT ---\n{llm_input_text}\n--- ENDE SOURCE TEXT ---"
        )

        try:
            bundle = await client.generate_structured(
                prompt=prompt,
                schema=BundleExtraction,
                system_context=system_context,
            )
        except LlmValidationError as exc:
            await _persist_terminal_state(
                task.job_id,
                JobStatus.QUARANTINED,
                traceback.format_exc(),
            )
            raise PermanentDataError("Structured extraction failed validation") from exc
        except LlmConnectionError as exc:
            raise TransientInfrastructureError("Local LLM endpoint is temporarily unavailable") from exc

        fhir_bundle_dict = json.loads(bundle.model_dump_json(exclude_none=True))
        json_str = json.dumps(fhir_bundle_dict, indent=2, ensure_ascii=False)
        semantic_chunks = split_semantic_chunks(
            text=llm_input_text,
            tenant_scope=task.tenant_scope,
            document_version=task.aggregate_version,
            aggregate_version=task.aggregate_version,
        )
        advisory_gate = advisory_only_gate()
        manual_review_required = bool(task.review_required or advisory_gate.manual_review_required)
        enforce_advisory_only_transition(
            gate=advisory_gate,
            attempted_straight_through=not manual_review_required,
        )

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

                    if processing_ref is not None:
                        job.processing_bucket = processing_ref.bucket
                        job.processing_object_key = processing_ref.object_key
                        job.processing_media_type = processing_ref.media_type
                    if mapping_ref is not None:
                        job.mapping_bucket = mapping_ref.bucket
                        job.mapping_object_key = mapping_ref.object_key

                    job.fhir_json = json_str
                    job.status = JobStatus.REVIEW_PENDING
                    job.aggregate_version += 1
                    job.required_read_version = job.aggregate_version

                    projection = await get_or_create_read_model_async(session, job_id=int(job.id))
                    projection.required_version = int(job.aggregate_version)
                    projection.visible_version = int(job.aggregate_version)
                    projection.status = str(job.status.value)

                    await store_semantic_chunks_async(
                        session,
                        job_id=int(job.id),
                        chunks=semantic_chunks,
                    )

                    review_case = await get_or_create_manual_review_case_async(
                        session,
                        job_id=int(job.id),
                        tenant_scope=task.tenant_scope,
                        reason_code=f"{task.source_kind.value}_MANUAL_REVIEW_REQUIRED",
                    )
                    review_case.status = ManualReviewStatus.PENDING
                    review_case.decision_notes = None
                    review_case.reviewer_actor_id = None
                    review_case.reviewer_authz_decision_id = None
                    review_case.reviewed_at = None

                    await create_security_audit_event_async(
                        session,
                        job_id=int(job.id),
                        tenant_scope=task.tenant_scope,
                        actor_id=internal_context.actor_id,
                        event_type="manual_review_requested",
                        severity="HIGH",
                        authz_decision_id=internal_context.authz_decision_id,
                        details={
                            "source_kind": task.source_kind.value,
                            "qdrant_advisory_only": advisory_gate.advisory_only,
                            "blocking_adr": advisory_gate.blocking_adr,
                        },
                    )
        except PolicyAuthError as exc:
            await _persist_terminal_state(
                task.job_id,
                JobStatus.SECURITY_REJECTED,
                traceback.format_exc(),
            )
            raise exc
        except PermanentDataError:
            raise
        except Exception as exc:
            if cleanup_refs:
                async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                    for bucket, object_key in cleanup_refs:
                        await s3.delete_object(Bucket=bucket, Key=object_key)
            raise TransientInfrastructureError("Failed to persist LLM review state") from exc

        self.logger.info("LLM processing complete for job=%s", task.job_id)


if __name__ == "__main__":
    worker = LlmWorker()
    asyncio.run(worker.run())
