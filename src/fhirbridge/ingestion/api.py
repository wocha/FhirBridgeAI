"""Ingestion boundary with JWT validation, token exchange, outbox handoffs, and manual review."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import aioboto3
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

try:
    from fastapi import Depends, FastAPI, HTTPException, Query, status
except ImportError:  # pragma: no cover - local unit-test fallback
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class status:
        HTTP_202_ACCEPTED = 202
        HTTP_400_BAD_REQUEST = 400
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_500_INTERNAL_SERVER_ERROR = 500

    def Depends(dependency):  # type: ignore[override]
        return dependency

    def Query(default=None, **_kwargs):  # type: ignore[override]
        return default

    class FastAPI:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:
            pass

        def on_event(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def get(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def post(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

from fhirbridge.core.auth import (
    ExternalUserClaims,
    TokenExchangeService,
    build_break_glass_audit,
    require_clinical_role,
    require_manual_review_role,
)
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import (
    Job,
    JobStatus,
    ManualReviewStatus,
    OutboxEvent,
    create_security_audit_event_async,
    fetch_manual_review_case_async,
    fetch_read_model_state_async,
    get_async_engine,
    get_async_session_factory,
    get_or_create_read_model_async,
    utcnow,
    verify_runtime_schema_async,
)
from fhirbridge.core.qdrant_security import advisory_only_gate
from fhirbridge.core.rabbitmq import (
    ClaimCheck,
    DocumentMetaData,
    FHIR_EXPORT_QUEUE,
    FhirExportMessage,
    IngestionSourceKind,
    LLM_EXTRACTION_QUEUE,
    OCR_TASK_QUEUE,
    OcrTaskMessage,
)
from fhirbridge.core.storage import (
    HL7_MEDIA_TYPE,
    PDF_MEDIA_TYPE,
    JSON_MEDIA_TYPE,
    build_orphan_evidence_marker_claim_check,
    build_evidence_claim_check,
    evidence_bucket_name,
    s3_client_kwargs,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

AsyncEngineRef: AsyncEngine | None = None
AsyncSessionFactory: async_sessionmaker[AsyncSession] | None = None


class DocumentIngestionRequest(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_kind: IngestionSourceKind
    submitted_filename: str | None = None
    payload_base64: str | None = None
    hl7_message: str | None = None
    sha256: str | None = None
    document_type: str | None = Field(default="unknown")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def media_type(self) -> str:
        if self.source_kind == IngestionSourceKind.PDF_SCAN:
            return PDF_MEDIA_TYPE
        return HL7_MEDIA_TYPE

    def materialize_payload(self) -> bytes:
        if self.source_kind == IngestionSourceKind.PDF_SCAN:
            if not self.payload_base64 or self.hl7_message:
                raise ValueError("PDF ingestion requires payload_base64 and forbids hl7_message")
            try:
                payload = base64.b64decode(self.payload_base64, validate=True)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("payload_base64 must contain valid base64-encoded PDF bytes") from exc
            if not payload.startswith(b"%PDF"):
                raise ValueError("PDF payload must start with %PDF")
            return payload

        if self.payload_base64:
            raise ValueError("HL7 ingestion forbids payload_base64")
        if not self.hl7_message or not self.hl7_message.strip():
            raise ValueError("HL7 ingestion requires hl7_message")
        if not self.hl7_message.lstrip().startswith("MSH|"):
            raise ValueError("HL7 v2 ingestion requires an MSH segment prefix")
        return self.hl7_message.encode("utf-8")

    def resolved_filename(self) -> str:
        if self.submitted_filename:
            return self.submitted_filename
        if self.source_kind == IngestionSourceKind.PDF_SCAN:
            return f"{self.document_id}.pdf"
        return f"{self.document_id}.hl7"


class DocumentIngestionResponse(BaseModel):
    status: str
    document_id: str
    message: str
    trace_id: str
    required_version: int


class DashboardReadModelResponse(BaseModel):
    job_id: int
    document_id: str
    projection_name: str
    status: str
    required_version: int
    visible_version: int


class ManualReviewResponse(BaseModel):
    job_id: int
    document_id: str
    source_kind: str
    submitted_filename: str
    job_status: str
    review_status: str
    review_reason_code: str
    evidence_sha256: str | None
    required_version: int
    visible_version: int
    pseudonymized_preview: str | None
    extracted_bundle_json: str | None
    qdrant_advisory_only: bool
    qdrant_blocking_adr: str
    qdrant_reason: str


class ManualReviewDecisionRequest(BaseModel):
    decision: Literal["approve", "reject"]
    notes: str | None = None


class ManualReviewDecisionResponse(BaseModel):
    job_id: int
    review_status: str
    job_status: str
    trace_id: str | None = None
    message: str


app = FastAPI(
    title="FhirBridgeAi Ingestion Gateway",
    description="Zero-trust ingestion boundary with transactional outbox.",
    version="2.1.0",
)


def _get_database() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    global AsyncEngineRef, AsyncSessionFactory

    if AsyncEngineRef is None:
        AsyncEngineRef = get_async_engine()
    if AsyncSessionFactory is None:
        AsyncSessionFactory = get_async_session_factory(AsyncEngineRef)
    return AsyncEngineRef, AsyncSessionFactory


async def _put_claim_check_payload(claim_check: ClaimCheck, payload: bytes) -> None:
    settings = get_settings()
    put_kwargs: dict[str, Any] = {
        "Bucket": claim_check.bucket,
        "Key": claim_check.object_key,
        "Body": payload,
    }
    if claim_check.bucket == evidence_bucket_name():
        put_kwargs["ObjectLockMode"] = "GOVERNANCE"
        put_kwargs["ObjectLockRetainUntilDate"] = datetime.now(UTC) + timedelta(
            days=settings.evidence_retention_days()
        )

    session_s3 = aioboto3.Session()
    async with session_s3.client("s3", **s3_client_kwargs()) as s3:
        await s3.put_object(**put_kwargs)


async def _persist_orphan_evidence_marker(
    *,
    request: DocumentIngestionRequest,
    user: ExternalUserClaims,
    trace_id: str,
    evidence_ref: ClaimCheck,
    exc: Exception,
) -> ClaimCheck:
    marker_ref = build_orphan_evidence_marker_claim_check(
        document_id=request.document_id,
        trace_id=trace_id,
    )
    marker_payload = {
        "document_id": request.document_id,
        "trace_id": trace_id,
        "tenant_scope": user.tenant_scope,
        "actor_id": user.actor_id,
        "source_kind": request.source_kind.value,
        "repair_required": True,
        "failure_stage": "ingestion_post_evidence_pre_commit",
        "failure_type": type(exc).__name__,
        "failure_message": str(exc),
        "occurred_at": datetime.now(UTC).isoformat(),
        "evidence": evidence_ref.model_dump(mode="json"),
    }
    await _put_claim_check_payload(
        marker_ref,
        json.dumps(marker_payload, sort_keys=True).encode("utf-8"),
    )
    return marker_ref


async def _read_claim_check_text(claim_check: ClaimCheck) -> str:
    session_s3 = aioboto3.Session()
    async with session_s3.client("s3", **s3_client_kwargs()) as s3:
        response = await s3.get_object(Bucket=claim_check.bucket, Key=claim_check.object_key)
        async with response["Body"] as stream:
            return (await stream.read()).decode("utf-8")


def _claim_check_from_job(
    job: Job,
    *,
    bucket_attr: str,
    key_attr: str,
    media_attr: str,
    sha_attr: str | None = None,
) -> ClaimCheck | None:
    bucket = getattr(job, bucket_attr, None)
    object_key = getattr(job, key_attr, None)
    media_type = getattr(job, media_attr, None)
    if not bucket or not object_key or not media_type:
        return None
    sha256 = getattr(job, sha_attr, None) if sha_attr else None
    return ClaimCheck(
        bucket=str(bucket),
        object_key=str(object_key),
        media_type=str(media_type),
        sha256=str(sha256) if sha256 else None,
    )


def _validate_request_payload(request: DocumentIngestionRequest) -> bytes:
    try:
        return request.materialize_payload()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    settings.require_database_url()
    settings.require_internal_auth_context_secret()
    settings.require_minio_credentials()
    settings.require_minio_url()
    settings.minio_http_verify()
    settings.object_storage_buckets()
    settings.evidence_retention_days()

    engine, _ = _get_database()
    await verify_runtime_schema_async(engine)
    logger.info("Ingestion boundary ready. JWT validation, storage classes, and manual review enabled.")


@app.get(
    "/api/v1/read-models/dashboard",
    response_model=DashboardReadModelResponse,
    summary="Return the materialized dashboard read-model state for a clinical document",
)
async def get_dashboard_read_model(
    job_id: int | None = Query(default=None),
    document_id: str | None = Query(default=None),
    user: ExternalUserClaims = Depends(require_clinical_role),
) -> DashboardReadModelResponse:
    _ = user
    _, session_factory = _get_database()

    async with session_factory() as session:
        row = await fetch_read_model_state_async(
            session,
            projection_name="dashboard",
            job_id=job_id,
            document_id=document_id,
        )

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Read-model state not found")

    job, projection = row
    return DashboardReadModelResponse(
        job_id=int(job.id),
        document_id=str(job.document_id),
        projection_name=str(projection.projection_name),
        status=str(projection.status),
        required_version=int(projection.required_version),
        visible_version=int(projection.visible_version),
    )


@app.get(
    "/api/v1/manual-review/{job_id}",
    response_model=ManualReviewResponse,
    summary="Return the backend-mediated manual review payload for a clinical document",
)
async def get_manual_review_case(
    job_id: int,
    user: ExternalUserClaims = Depends(require_manual_review_role),
) -> ManualReviewResponse:
    _, session_factory = _get_database()

    async with session_factory() as session:
        row = await fetch_manual_review_case_async(session, job_id=job_id)

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual review case not found")

    job, review_case, projection = row
    if str(job.tenant_scope) != user.tenant_scope:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual review case not found")

    preview_ref = _claim_check_from_job(
        job,
        bucket_attr="processing_bucket",
        key_attr="processing_object_key",
        media_attr="processing_media_type",
    )
    preview_text: str | None = None
    if preview_ref is not None:
        preview_text = await _read_claim_check_text(preview_ref)

    advisory_gate = advisory_only_gate()
    return ManualReviewResponse(
        job_id=int(job.id),
        document_id=str(job.document_id),
        source_kind=str(job.source_kind or ""),
        submitted_filename=str(job.submitted_filename or job.filepath),
        job_status=str(job.status),
        review_status=str(review_case.status),
        review_reason_code=str(review_case.reason_code),
        evidence_sha256=str(job.evidence_sha256) if job.evidence_sha256 else None,
        required_version=int(projection.required_version) if projection else int(job.required_read_version),
        visible_version=int(projection.visible_version) if projection else 0,
        pseudonymized_preview=preview_text[:4000] if preview_text else None,
        extracted_bundle_json=str(job.fhir_json) if job.fhir_json else None,
        qdrant_advisory_only=advisory_gate.advisory_only,
        qdrant_blocking_adr=advisory_gate.blocking_adr,
        qdrant_reason=advisory_gate.reason,
    )


@app.post(
    "/api/v1/manual-review/{job_id}/decision",
    response_model=ManualReviewDecisionResponse,
    summary="Persist a manual review decision and, on approval, enqueue export via outbox",
)
async def submit_manual_review_decision(
    job_id: int,
    request: ManualReviewDecisionRequest,
    user: ExternalUserClaims = Depends(require_manual_review_role),
) -> ManualReviewDecisionResponse:
    _, session_factory = _get_database()
    trace_id = uuid.uuid4().hex
    internal_event_id = str(uuid.uuid4())
    token_exchange = TokenExchangeService.from_settings()

    async with session_factory() as session:
        async with session.begin():
            row = await fetch_manual_review_case_async(session, job_id=job_id)
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual review case not found")

            job, review_case, projection = row
            if str(job.tenant_scope) != user.tenant_scope:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manual review case not found")
            if review_case.status != ManualReviewStatus.PENDING:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Manual review case is no longer pending")
            if not job.fhir_json:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="FHIR bundle is not ready for review")

            review_case.decision_notes = request.notes
            review_case.reviewer_actor_id = user.actor_id

            if request.decision == "approve":
                mapping_ref = None
                if job.mapping_bucket and job.mapping_object_key:
                    mapping_ref = ClaimCheck(
                        bucket=str(job.mapping_bucket),
                        object_key=str(job.mapping_object_key),
                        media_type=JSON_MEDIA_TYPE,
                    )
                processing_ref = _claim_check_from_job(
                    job,
                    bucket_attr="processing_bucket",
                    key_attr="processing_object_key",
                    media_attr="processing_media_type",
                )
                if mapping_ref is None or processing_ref is None:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Review approval is blocked until processing and vault artifacts exist",
                    )

                internal_auth_context = token_exchange.issue(
                    claims=user,
                    trace_id=trace_id,
                    bound_event_id=internal_event_id,
                )
                verified_context = token_exchange.verify(
                    internal_auth_context,
                    expected_tenant_scope=user.tenant_scope,
                    expected_event_id=internal_event_id,
                )

                next_message = FhirExportMessage(
                    event_id=internal_event_id,
                    trace_id=trace_id,
                    tenant_scope=user.tenant_scope,
                    aggregate_version=int(job.aggregate_version) + 1,
                    auth_context=internal_auth_context,
                    job_id=int(job.id),
                    source_kind=IngestionSourceKind(str(job.source_kind)),
                    submitted_filename=str(job.submitted_filename or job.filepath),
                    review_required=True,
                    bundle_json=str(job.fhir_json),
                    processing=processing_ref,
                    mapping=mapping_ref,
                )

                review_case.status = ManualReviewStatus.APPROVED
                review_case.reviewed_at = utcnow()
                review_case.reviewer_authz_decision_id = verified_context.authz_decision_id

                job.status = JobStatus.EXPORTING
                job.aggregate_version += 1
                job.required_read_version = job.aggregate_version
                projection = projection or await get_or_create_read_model_async(session, job_id=int(job.id))
                projection.required_version = int(job.aggregate_version)
                projection.visible_version = int(job.aggregate_version)
                projection.status = str(job.status.value)

                session.add(
                    OutboxEvent(
                        aggregate_id=int(job.id),
                        aggregate_version=int(job.aggregate_version),
                        event_type="job.fhir_export.requested",
                        destination=FHIR_EXPORT_QUEUE,
                        payload_json=next_message.model_dump_json(),
                        trace_id=trace_id,
                        tenant_scope=user.tenant_scope,
                        dedupe_key=f"job:{job.id}:version:{job.aggregate_version}:fhir_export",
                    )
                )
                await create_security_audit_event_async(
                    session,
                    job_id=int(job.id),
                    tenant_scope=user.tenant_scope,
                    actor_id=user.actor_id,
                    event_type="manual_review_approved",
                    severity="HIGH",
                    authz_decision_id=verified_context.authz_decision_id,
                    details={
                        "source_kind": str(job.source_kind),
                        "notes_present": bool(request.notes),
                    },
                )
                return ManualReviewDecisionResponse(
                    job_id=int(job.id),
                    review_status=str(review_case.status.value),
                    job_status=str(job.status.value),
                    trace_id=trace_id,
                    message="Manual review approved; export request persisted to the outbox",
                )

            reject_authz_decision_id = uuid.uuid4().hex
            review_case.status = ManualReviewStatus.REJECTED
            review_case.reviewed_at = utcnow()
            review_case.reviewer_authz_decision_id = reject_authz_decision_id

            job.status = JobStatus.QUARANTINED
            job.aggregate_version += 1
            job.required_read_version = job.aggregate_version
            projection = projection or await get_or_create_read_model_async(session, job_id=int(job.id))
            projection.required_version = int(job.aggregate_version)
            projection.visible_version = int(job.aggregate_version)
            projection.status = str(job.status.value)

            await create_security_audit_event_async(
                session,
                job_id=int(job.id),
                tenant_scope=user.tenant_scope,
                actor_id=user.actor_id,
                event_type="manual_review_rejected",
                severity="HIGH",
                authz_decision_id=reject_authz_decision_id,
                details={
                    "source_kind": str(job.source_kind),
                    "notes_present": bool(request.notes),
                },
            )

    return ManualReviewDecisionResponse(
        job_id=job_id,
        review_status=ManualReviewStatus.REJECTED.value,
        job_status=JobStatus.QUARANTINED.value,
        message="Manual review rejected; document remains quarantined",
    )


@app.post(
    "/api/v1/documents",
    response_model=DocumentIngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a new PDF scan or HL7 message for asynchronous processing",
)
async def ingest_document(
    request: DocumentIngestionRequest,
    user: ExternalUserClaims = Depends(require_clinical_role),
) -> DocumentIngestionResponse:
    trace_id = uuid.uuid4().hex
    internal_event_id = str(uuid.uuid4())
    token_exchange = TokenExchangeService.from_settings()
    _, session_factory = _get_database()
    payload = _validate_request_payload(request)
    evidence_ref = build_evidence_claim_check(
        document_id=request.document_id,
        source_kind=request.source_kind,
        media_type=request.media_type,
        payload=payload,
    )
    if request.sha256 and request.sha256 != evidence_ref.sha256:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload SHA-256 mismatch")

    evidence_written = False
    try:
        await _put_claim_check_payload(evidence_ref, payload)
        evidence_written = True

        async with session_factory() as session:
            async with session.begin():
                initial_status = (
                    JobStatus.OCR_PROCESSING
                    if request.source_kind == IngestionSourceKind.PDF_SCAN
                    else JobStatus.LLM_EXTRACTION
                )
                job = Job(
                    document_id=request.document_id,
                    filepath=str(evidence_ref.object_key),
                    source_kind=request.source_kind.value,
                    submitted_filename=request.resolved_filename(),
                    tenant_scope=user.tenant_scope,
                    actor_id=user.actor_id,
                    break_glass_flag=user.break_glass,
                    status=initial_status,
                    aggregate_version=1,
                    required_read_version=1,
                    evidence_bucket=evidence_ref.bucket,
                    evidence_object_key=evidence_ref.object_key,
                    evidence_media_type=evidence_ref.media_type,
                    evidence_sha256=evidence_ref.sha256,
                )
                session.add(job)
                await session.flush()

                internal_auth_context = token_exchange.issue(
                    claims=user,
                    trace_id=trace_id,
                    bound_event_id=internal_event_id,
                )

                auth_context = token_exchange.verify(
                    internal_auth_context,
                    expected_tenant_scope=user.tenant_scope,
                    expected_event_id=internal_event_id,
                )
                job.authz_decision_id = auth_context.authz_decision_id

                if request.source_kind == IngestionSourceKind.PDF_SCAN:
                    task: OcrTaskMessage | DocumentMetaData = OcrTaskMessage(
                        event_id=internal_event_id,
                        trace_id=trace_id,
                        tenant_scope=user.tenant_scope,
                        aggregate_version=int(job.aggregate_version),
                        auth_context=internal_auth_context,
                        job_id=int(job.id),
                        source_kind=request.source_kind,
                        submitted_filename=request.resolved_filename(),
                        review_required=True,
                        evidence=evidence_ref,
                    )
                    destination = OCR_TASK_QUEUE
                    event_type = "job.ocr.requested"
                    dedupe_suffix = "ocr"
                else:
                    task = DocumentMetaData(
                        event_id=internal_event_id,
                        trace_id=trace_id,
                        tenant_scope=user.tenant_scope,
                        aggregate_version=int(job.aggregate_version),
                        auth_context=internal_auth_context,
                        job_id=int(job.id),
                        source_kind=request.source_kind,
                        submitted_filename=request.resolved_filename(),
                        review_required=True,
                        document=evidence_ref,
                        evidence=evidence_ref,
                    )
                    destination = LLM_EXTRACTION_QUEUE
                    event_type = "job.llm.requested"
                    dedupe_suffix = "llm"

                projection = await get_or_create_read_model_async(session, job_id=int(job.id))
                projection.required_version = int(job.aggregate_version)
                projection.visible_version = int(job.aggregate_version)
                projection.status = str(job.status.value)

                session.add(
                    OutboxEvent(
                        aggregate_id=int(job.id),
                        aggregate_version=int(job.aggregate_version),
                        event_type=event_type,
                        destination=destination,
                        payload_json=task.model_dump_json(),
                        trace_id=trace_id,
                        tenant_scope=user.tenant_scope,
                        dedupe_key=f"job:{job.id}:version:{job.aggregate_version}:{dedupe_suffix}",
                    )
                )

                if user.break_glass:
                    audit = build_break_glass_audit(
                        user,
                        authz_decision_id=job.authz_decision_id or "missing",
                    )
                    await create_security_audit_event_async(
                        session,
                        job_id=int(job.id),
                        tenant_scope=audit.tenant_scope,
                        actor_id=audit.actor_id,
                        event_type=audit.event_type,
                        severity=audit.severity,
                        authz_decision_id=audit.authz_decision_id,
                        details=audit.details,
                    )

        logger.info(
            "Accepted %s document %s for tenant=%s trace_id=%s actor_id=%s",
            request.source_kind.value,
            request.document_id,
            user.tenant_scope,
            trace_id,
            user.actor_id,
        )
        return DocumentIngestionResponse(
            status="accepted",
            document_id=request.document_id,
            message="Document accepted; evidence stored and outbox handoff persisted",
            trace_id=trace_id,
            required_version=1,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error ingesting document %s", request.document_id)
        if evidence_written:
            try:
                marker_ref = await _persist_orphan_evidence_marker(
                    request=request,
                    user=user,
                    trace_id=trace_id,
                    evidence_ref=evidence_ref,
                    exc=exc,
                )
            except Exception as marker_exc:
                logger.exception(
                    "Failed to persist orphan-evidence repair marker for document %s",
                    request.document_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error after evidence write; repair marker persistence failed",
                ) from marker_exc
            logger.error(
                "Ingestion failed after evidence write for document %s; repair marker stored at %s/%s",
                request.document_id,
                marker_ref.bucket,
                marker_ref.object_key,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error after evidence write; repair marker persisted for follow-up",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while persisting the ingestion request",
        ) from exc
