"""FHIR export worker with deterministic reconciliation on downstream inconsistencies."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aio_pika
import aioboto3
import httpx
from fhir.resources.bundle import Bundle
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from fhirbridge.core.auth import TokenExchangeService
from fhirbridge.core.base_worker import BaseRabbitMQWorker
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import (
    JobStatus,
    create_reconciliation_task_async,
    get_async_engine,
    get_async_session_factory,
    get_or_create_read_model_async,
    load_job_async,
    record_consumed_message_async,
    verify_runtime_schema_async,
)
from fhirbridge.core.failure_handling import (
    DownstreamConsistencyError,
    PermanentDataError,
    TransientInfrastructureError,
)
from fhirbridge.core.rabbitmq import FhirExportMessage
from fhirbridge.core.storage import s3_client_kwargs
from fhirbridge.privacy.pseudonymizer import LocalAnonymizer


class CorrelationIdFilter(logging.Filter):
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

AsyncEngineRef: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


def _get_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global AsyncEngineRef, AsyncSessionFactory

    if AsyncEngineRef is None:
        AsyncEngineRef = get_async_engine()
    if AsyncSessionFactory is None:
        AsyncSessionFactory = get_async_session_factory(AsyncEngineRef)
    return AsyncEngineRef, AsyncSessionFactory


def _fhir_server_url() -> str:
    return get_settings().require_fhir_server_url()


def _fhir_auth_headers(correlation_id: str) -> dict[str, str]:
    settings = get_settings()
    return {
        "Content-Type": "application/fhir+json",
        "X-Correlation-ID": correlation_id,
        "Authorization": f"Bearer {settings.require_fhir_auth_bearer()}",
    }


async def send_fhir_bundle(client: httpx.AsyncClient, bundle_json: str, correlation_id: str) -> None:
    response = await client.post(
        _fhir_server_url(),
        content=bundle_json,
        headers=_fhir_auth_headers(correlation_id),
        timeout=httpx.Timeout(10.0),
    )
    if response.status_code == 429 or response.status_code >= 500:
        raise TransientInfrastructureError(f"FHIR server transient response {response.status_code}")
    if 400 <= response.status_code < 500:
        raise PermanentDataError(f"Permanent client error {response.status_code}: {response.text}")


def inject_idempotency_logic(bundle: Bundle) -> str:
    if bundle.type not in ["transaction", "batch"]:
        bundle.type = "transaction"
    if bundle.entry:
        for entry in bundle.entry:
            if not entry.request:
                from fhir.resources.bundle import BundleEntryRequest

                resource_name = entry.resource.__class__.__name__
                entry.request = BundleEntryRequest(method="POST", url=resource_name)
            if entry.resource and entry.resource.__class__.__name__ == "Patient":
                patient = entry.resource
                if getattr(patient, "identifier", None) and len(patient.identifier) > 0:
                    system_url = patient.identifier[0].system or ""
                    value = patient.identifier[0].value or ""
                    if system_url and value:
                        entry.request.ifNoneExist = f"identifier={system_url}|{value}"
    return bundle.model_dump_json(exclude_none=True)


def mock_request_handler(request: httpx.Request) -> httpx.Response:
    logging.info("[MOCK] Simulated FHIR server received 200 OK for %s", request.url)
    return httpx.Response(200, json={"resourceType": "Bundle", "type": "transaction-response"})


class FhirExportWorker(BaseRabbitMQWorker):
    def __init__(self) -> None:
        super().__init__("fhir-export-worker", "fhir_export_queue", prefetch_count=1)
        self.session_s3 = aioboto3.Session()
        self.client: httpx.AsyncClient | None = None

    async def setup(self) -> None:
        settings = get_settings()
        settings.require_database_url()
        settings.require_rabbitmq_url()
        settings.require_internal_auth_context_secret()
        settings.require_minio_credentials()
        settings.require_minio_url()
        settings.minio_http_verify()
        settings.object_storage_buckets()
        settings.require_fhir_server_url()
        settings.require_fhir_auth_bearer()
        settings.fhir_http_verify()

        engine, _ = _get_database()
        await verify_runtime_schema_async(engine)

        client_kwargs: dict[str, Any] = {
            "timeout": 10.0,
            "verify": settings.fhir_http_verify(),
        }
        if "mock" in _fhir_server_url().lower():
            self.logger.info("Configured with MOCK transport.")
            client_kwargs["transport"] = httpx.MockTransport(mock_request_handler)
        self.client = httpx.AsyncClient(**client_kwargs)

    async def teardown(self) -> None:
        if self.client:
            await self.client.aclose()

    async def process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        task = FhirExportMessage.model_validate_json(message.body)
        span = trace.get_current_span()
        span.set_attribute("job_id", task.job_id)
        span.set_attribute("tenant_scope", task.tenant_scope)
        span.set_attribute("source_kind", task.source_kind.value)

        correlation_id = str(message.correlation_id or f"job-{task.job_id}")
        token_exchange = TokenExchangeService.from_settings()
        token_exchange.verify(
            task.auth_context,
            expected_tenant_scope=task.tenant_scope,
            expected_event_id=task.event_id,
        )

        try:
            async with self.session_s3.client("s3", **s3_client_kwargs()) as s3:
                response = await s3.get_object(Bucket=task.mapping.bucket, Key=task.mapping.object_key)
                mapping_data = await response["Body"].read()
                mapping = json.loads(mapping_data.decode("utf-8"))
        except Exception as exc:
            raise TransientInfrastructureError("Failed to retrieve de-anonymization mapping") from exc

        extraction_data_masked = json.loads(task.bundle_json)
        anonymizer = LocalAnonymizer()
        extraction_data = anonymizer.deanonymize(extraction_data_masked, mapping)

        fhir_bundle_dict: dict[str, Any] = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [],
        }
        if "Patient" in extraction_data and extraction_data["Patient"]:
            fhir_bundle_dict["entry"].append(
                {"resource": extraction_data["Patient"], "request": {"method": "POST", "url": "Patient"}}
            )
        if "Encounter" in extraction_data and extraction_data["Encounter"]:
            fhir_bundle_dict["entry"].append(
                {"resource": extraction_data["Encounter"], "request": {"method": "POST", "url": "Encounter"}}
            )

        bundle = Bundle.model_validate(fhir_bundle_dict)
        safe_bundle_json = await asyncio.to_thread(lambda: inject_idempotency_logic(bundle))

        if not self.client:
            raise RuntimeError("HTTP client not initialized")
        await send_fhir_bundle(self.client, safe_bundle_json, correlation_id)

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
                    job.status = JobStatus.EXPORTED
                    job.aggregate_version += 1
                    job.required_read_version = job.aggregate_version
                    job.output_path = f"{_fhir_server_url()}#correlation-id={correlation_id}"
                    job.error_trace = None
                    projection = await get_or_create_read_model_async(session, job_id=int(job.id))
                    projection.required_version = int(job.aggregate_version)
                    projection.visible_version = int(job.aggregate_version)
                    projection.status = str(job.status.value)
        except Exception as exc:
            async with session_factory() as session:
                async with session.begin():
                    await create_reconciliation_task_async(
                        session,
                        job_id=task.job_id,
                        source_event_id=task.event_id,
                        failure_category="DOWNSTREAM_CONSISTENCY",
                        payload={
                            "job_id": task.job_id,
                            "correlation_id": correlation_id,
                            "reason": "status_update_failed_after_fhir_commit",
                            "fhir_server_url": _fhir_server_url(),
                            "mapping_bucket": task.mapping.bucket,
                            "mapping_object_key": task.mapping.object_key,
                            "processing_bucket": task.processing.bucket,
                            "processing_object_key": task.processing.object_key,
                        },
                    )
            raise DownstreamConsistencyError(
                "FHIR export committed downstream but local status update failed",
                details={"job_id": task.job_id, "event_id": task.event_id},
            ) from exc

        self.logger.info(
            "FHIR export committed for job=%s; cleanup stays out of the commit window to preserve repair evidence",
            task.job_id,
        )


if __name__ == "__main__":
    worker = FhirExportWorker()
    asyncio.run(worker.run())
