from __future__ import annotations

import asyncio
import json
import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://runtime-user:runtime-pass@db.internal/fhirbridge")
os.environ.setdefault("MINIO_ROOT_USER", "test-minio-user")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test-minio-password")
os.environ.setdefault("INTERNAL_AUTH_CONTEXT_SECRET", "x" * 48)

from fhirbridge.core.auth import ExternalUserClaims, HTTPException, require_manual_review_role
from fhirbridge.core.database import Job, JobStatus, ManualReviewCase, ReadModelState
from fhirbridge.ingestion import api
from tests.runtime_fakes import (
    RuntimeStore,
    fake_create_security_audit_event_async,
    fake_database_bundle,
    fake_fetch_manual_review_case_async,
    fake_get_or_create_read_model_async,
)


def _configure_runtime(monkeypatch: pytest.MonkeyPatch) -> RuntimeStore:
    store = RuntimeStore()
    monkeypatch.setattr(api, "_get_database", lambda: fake_database_bundle(store))
    monkeypatch.setattr(api, "fetch_manual_review_case_async", fake_fetch_manual_review_case_async)
    monkeypatch.setattr(api, "get_or_create_read_model_async", fake_get_or_create_read_model_async)
    monkeypatch.setattr(api, "create_security_audit_event_async", fake_create_security_audit_event_async)
    return store


def test_manual_review_rbac_blocks_non_reviewer() -> None:
    user = ExternalUserClaims(sub="nurse-1", tenant_scope="tenant-a", roles=["NURSE"])

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(require_manual_review_role(user=user))

    assert exc_info.value.status_code == 403


def test_manual_review_endpoint_returns_backend_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _configure_runtime(monkeypatch)
    job = Job(
        document_id="doc-review",
        filepath="evidence/doc-review.pdf",
        source_kind="PDF_SCAN",
        submitted_filename="doc-review.pdf",
        tenant_scope="tenant-a",
        actor_id="actor-a",
        status=JobStatus.REVIEW_PENDING,
        aggregate_version=3,
        required_read_version=3,
        evidence_sha256="abc123",
        processing_bucket="processing-artifacts",
        processing_object_key="processing/job-1/ocr.txt",
        processing_media_type="text/plain; charset=utf-8",
        mapping_bucket="phi-vault",
        mapping_object_key="vault/job-1/mapping.json",
        fhir_json='{"resourceType":"Bundle"}',
    )
    review_case = ManualReviewCase(
        job_id=1,
        tenant_scope="tenant-a",
        status="PENDING",
        reason_code="PDF_SCAN_MANUAL_REVIEW_REQUIRED",
    )
    projection = ReadModelState(
        projection_name="dashboard",
        job_id=1,
        required_version=3,
        visible_version=2,
        status="REVIEW_PENDING",
    )
    store.add(job)
    review_case.job_id = int(job.id)
    projection.job_id = int(job.id)
    store.add(review_case)
    store.add(projection)

    async def _fake_read_claim_check_text(_claim_check) -> str:
        return "Pseudonymized OCR preview"

    monkeypatch.setattr(api, "_read_claim_check_text", _fake_read_claim_check_text)
    user = ExternalUserClaims(sub="doctor-1", tenant_scope="tenant-a", roles=["PHYSICIAN"])

    response = asyncio.run(api.get_manual_review_case(job_id=int(job.id), user=user))

    assert response.job_id == int(job.id)
    assert response.review_status == "PENDING"
    assert response.pseudonymized_preview == "Pseudonymized OCR preview"
    assert response.qdrant_advisory_only is True
    assert "s3://" not in response.extracted_bundle_json


def test_manual_review_approval_persists_export_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _configure_runtime(monkeypatch)
    job = Job(
        document_id="doc-approve",
        filepath="evidence/doc-approve.pdf",
        source_kind="PDF_SCAN",
        submitted_filename="doc-approve.pdf",
        tenant_scope="tenant-a",
        actor_id="actor-a",
        authz_decision_id="ingest-authz",
        status=JobStatus.REVIEW_PENDING,
        aggregate_version=4,
        required_read_version=4,
        processing_bucket="processing-artifacts",
        processing_object_key="processing/job-1/ocr.txt",
        processing_media_type="text/plain; charset=utf-8",
        mapping_bucket="phi-vault",
        mapping_object_key="vault/job-1/mapping.json",
        fhir_json='{"resourceType":"Bundle"}',
    )
    review_case = ManualReviewCase(
        job_id=1,
        tenant_scope="tenant-a",
        status="PENDING",
        reason_code="PDF_SCAN_MANUAL_REVIEW_REQUIRED",
    )
    projection = ReadModelState(
        projection_name="dashboard",
        job_id=1,
        required_version=4,
        visible_version=4,
        status="REVIEW_PENDING",
    )
    store.add(job)
    review_case.job_id = int(job.id)
    projection.job_id = int(job.id)
    store.add(review_case)
    store.add(projection)

    user = ExternalUserClaims(sub="doctor-2", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    response = asyncio.run(
        api.submit_manual_review_decision(
            job_id=int(job.id),
            request=api.ManualReviewDecisionRequest(decision="approve", notes="Looks correct"),
            user=user,
        )
    )

    assert response.review_status == "APPROVED"
    assert response.job_status == "EXPORTING"
    assert len(store.outbox_events) == 1
    payload = json.loads(store.outbox_events[0].payload_json)
    assert store.outbox_events[0].destination == "fhir_export_queue"
    assert payload["mapping"]["bucket"] == "phi-vault"
    assert payload["processing"]["bucket"] == "processing-artifacts"
    assert store.manual_review_cases[0].status == "APPROVED"
    assert len(store.security_audit_events) == 1


def test_manual_review_rejects_to_quarantine(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _configure_runtime(monkeypatch)
    job = Job(
        document_id="doc-reject",
        filepath="evidence/doc-reject.pdf",
        source_kind="PDF_SCAN",
        submitted_filename="doc-reject.pdf",
        tenant_scope="tenant-a",
        actor_id="actor-a",
        authz_decision_id="ingest-authz",
        status=JobStatus.REVIEW_PENDING,
        aggregate_version=2,
        required_read_version=2,
        processing_bucket="processing-artifacts",
        processing_object_key="processing/job-1/ocr.txt",
        processing_media_type="text/plain; charset=utf-8",
        mapping_bucket="phi-vault",
        mapping_object_key="vault/job-1/mapping.json",
        fhir_json='{"resourceType":"Bundle"}',
    )
    review_case = ManualReviewCase(
        job_id=1,
        tenant_scope="tenant-a",
        status="PENDING",
        reason_code="PDF_SCAN_MANUAL_REVIEW_REQUIRED",
    )
    projection = ReadModelState(
        projection_name="dashboard",
        job_id=1,
        required_version=2,
        visible_version=2,
        status="REVIEW_PENDING",
    )
    store.add(job)
    review_case.job_id = int(job.id)
    projection.job_id = int(job.id)
    store.add(review_case)
    store.add(projection)

    user = ExternalUserClaims(sub="doctor-3", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    response = asyncio.run(
        api.submit_manual_review_decision(
            job_id=int(job.id),
            request=api.ManualReviewDecisionRequest(decision="reject", notes="Ambiguous findings"),
            user=user,
        )
    )

    assert response.review_status == "REJECTED"
    assert response.job_status == "QUARANTINED"
    assert store.manual_review_cases[0].status == "REJECTED"
    assert store.jobs[0].status == JobStatus.QUARANTINED
    assert store.outbox_events == []
    assert len(store.security_audit_events) == 1
