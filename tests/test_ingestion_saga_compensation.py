from __future__ import annotations

import asyncio
import base64
import json
import os
from types import SimpleNamespace

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://runtime-user:runtime-pass@db.internal/fhirbridge")
os.environ.setdefault("MINIO_ROOT_USER", "test-minio-user")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test-minio-password")
os.environ.setdefault("MINIO_URL", "https://minio.docker.localhost:9000")
os.environ.setdefault("MINIO_CA_BUNDLE_PATH", __file__)
os.environ.setdefault("INTERNAL_AUTH_CONTEXT_SECRET", "x" * 48)

from fhirbridge.core.auth import ExternalUserClaims
from fhirbridge.core.rabbitmq import IngestionSourceKind
from fhirbridge.ingestion import api
from tests.runtime_fakes import (
    RuntimeStore,
    fake_create_security_audit_event_async,
    fake_database_bundle,
    fake_get_or_create_read_model_async,
)


def _configure_runtime(monkeypatch) -> RuntimeStore:
    store = RuntimeStore()
    monkeypatch.setattr(api, "_get_database", lambda: fake_database_bundle(store))
    monkeypatch.setattr(api, "get_or_create_read_model_async", fake_get_or_create_read_model_async)
    monkeypatch.setattr(api, "create_security_audit_event_async", fake_create_security_audit_event_async)
    return store


class StorageRecorder:
    def __init__(self, *, fail_repair_marker_put: bool = False) -> None:
        self.fail_repair_marker_put = fail_repair_marker_put
        self.put_attempts: list[dict[str, object]] = []
        self.successful_puts: list[dict[str, object]] = []
        self.deletes: list[dict[str, object]] = []


class RecordingS3Client:
    def __init__(self, recorder: StorageRecorder) -> None:
        self.recorder = recorder

    async def __aenter__(self) -> "RecordingS3Client":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False

    async def put_object(self, **kwargs) -> None:
        attempt = dict(kwargs)
        self.recorder.put_attempts.append(attempt)
        object_key = str(kwargs.get("Key", ""))
        if self.recorder.fail_repair_marker_put and object_key.startswith("repair/orphan-evidence/"):
            raise RuntimeError("repair marker storage unavailable")
        self.recorder.successful_puts.append(attempt)

    async def delete_object(self, **kwargs) -> None:
        self.recorder.deletes.append(dict(kwargs))
        raise AssertionError("Delete compensation must never run on the evidence path")


class RecordingS3Session:
    def __init__(self, recorder: StorageRecorder) -> None:
        self.recorder = recorder

    def client(self, _service_name: str, **_kwargs) -> RecordingS3Client:
        return RecordingS3Client(self.recorder)


def _install_storage_recorder(monkeypatch: pytest.MonkeyPatch, recorder: StorageRecorder) -> None:
    monkeypatch.setattr(api.aioboto3, "Session", lambda: RecordingS3Session(recorder))


def _break_persistence_after_evidence_write(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenTransaction:
        async def __aenter__(self):
            raise RuntimeError("database unavailable during commit")

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

    class BrokenSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        def begin(self) -> BrokenTransaction:
            return BrokenTransaction()

    class BrokenSessionFactory:
        def __call__(self) -> BrokenSession:
            return BrokenSession()

    monkeypatch.setattr(
        api,
        "_get_database",
        lambda: (SimpleNamespace(name="fake-postgresql-engine"), BrokenSessionFactory()),
    )


def test_ingestion_persists_job_and_outbox_event(monkeypatch) -> None:
    store = _configure_runtime(monkeypatch)
    uploaded: list[tuple[str, str, str]] = []

    async def _fake_put_payload(claim_check, payload: bytes) -> None:
        uploaded.append((claim_check.bucket, claim_check.object_key, payload.decode("latin-1")))

    monkeypatch.setattr(api, "_put_claim_check_payload", _fake_put_payload)

    request = api.DocumentIngestionRequest(
        document_id="doc-outbox",
        source_kind=IngestionSourceKind.PDF_SCAN,
        submitted_filename="doc-outbox.pdf",
        payload_base64=base64.b64encode(b"%PDF-1.4\nklinischer text").decode("ascii"),
    )
    user = ExternalUserClaims(sub="doctor-123", tenant_scope="tenant-a", roles=["PHYSICIAN"])

    response = asyncio.run(api.ingest_document(request=request, user=user))

    assert response.status == "accepted"
    assert response.required_version == 1
    assert uploaded == [("evidence-originals", "evidence/doc-outbox.pdf", "%PDF-1.4\nklinischer text")]
    assert len(store.jobs) == 1
    assert len(store.outbox_events) == 1

    job = store.jobs[0]
    outbox = store.outbox_events[0]
    payload = json.loads(outbox.payload_json)

    assert job.tenant_scope == "tenant-a"
    assert job.source_kind == "PDF_SCAN"
    assert outbox.destination == "ocr_task_queue"
    assert payload["tenant_scope"] == "tenant-a"
    assert payload["job_id"] == job.id
    assert payload["source_kind"] == "PDF_SCAN"
    assert "doctor-123" not in outbox.payload_json
    assert payload["auth_context"]
    assert payload["evidence"]["bucket"] == "evidence-originals"


def test_break_glass_ingestion_emits_high_priority_audit(monkeypatch) -> None:
    store = _configure_runtime(monkeypatch)

    async def _fake_put_payload(_claim_check, _payload: bytes) -> None:
        return None

    monkeypatch.setattr(api, "_put_claim_check_payload", _fake_put_payload)

    request = api.DocumentIngestionRequest(
        document_id="doc-break-glass",
        source_kind=IngestionSourceKind.HL7_V2,
        submitted_filename="doc-break-glass.hl7",
        hl7_message="MSH|^~\\&|ADT|HOSP|LAB|HOSP|202603151200||ADT^A01|1|P|2.5",
    )
    user = ExternalUserClaims(
        sub="emergency-1",
        tenant_scope="tenant-b",
        roles=["EMERGENCY"],
        break_glass=True,
        break_glass_reason="Massive blood loss in trauma bay",
        station="ER-1",
    )

    asyncio.run(api.ingest_document(request=request, user=user))

    assert len(store.security_audit_events) == 1
    audit = store.security_audit_events[0]
    details = json.loads(audit.details_json)

    assert audit.severity == "HIGH"
    assert audit.event_type == "break_glass_access"
    assert audit.tenant_scope == "tenant-b"
    assert details["station"] == "ER-1"


def test_ingestion_failure_after_evidence_write_forbids_delete_and_persists_repair_marker(monkeypatch) -> None:
    recorder = StorageRecorder()
    _install_storage_recorder(monkeypatch, recorder)
    _break_persistence_after_evidence_write(monkeypatch)

    request = api.DocumentIngestionRequest(
        document_id="doc-orphan-evidence",
        source_kind=IngestionSourceKind.PDF_SCAN,
        submitted_filename="scan.pdf",
        payload_base64=base64.b64encode(b"%PDF-1.4\nscan").decode("ascii"),
    )
    user = ExternalUserClaims(sub="doctor-5", tenant_scope="tenant-c", roles=["PHYSICIAN"])

    with pytest.raises(api.HTTPException) as exc_info:
        asyncio.run(api.ingest_document(request=request, user=user))

    assert exc_info.value.status_code == 500
    assert "repair marker persisted" in exc_info.value.detail
    assert recorder.deletes == []
    assert len(recorder.put_attempts) == 2
    assert len(recorder.successful_puts) == 2

    evidence_write = recorder.successful_puts[0]
    marker_write = recorder.successful_puts[1]

    assert evidence_write["Bucket"] == "evidence-originals"
    assert evidence_write["Key"] == "evidence/doc-orphan-evidence.pdf"
    assert evidence_write["Body"] == b"%PDF-1.4\nscan"
    assert evidence_write["ObjectLockMode"] == "GOVERNANCE"
    assert "ObjectLockRetainUntilDate" in evidence_write

    assert marker_write["Bucket"] == "processing-artifacts"
    assert str(marker_write["Key"]).startswith("repair/orphan-evidence/doc-orphan-evidence-")
    assert "ObjectLockMode" not in marker_write

    marker_payload = json.loads(bytes(marker_write["Body"]).decode("utf-8"))
    assert marker_payload["repair_required"] is True
    assert marker_payload["failure_stage"] == "ingestion_post_evidence_pre_commit"
    assert marker_payload["evidence"]["bucket"] == "evidence-originals"
    assert marker_payload["evidence"]["object_key"] == "evidence/doc-orphan-evidence.pdf"


def test_ingestion_double_failure_leaves_worm_evidence_and_fails_closed(monkeypatch) -> None:
    recorder = StorageRecorder(fail_repair_marker_put=True)
    _install_storage_recorder(monkeypatch, recorder)
    _break_persistence_after_evidence_write(monkeypatch)

    request = api.DocumentIngestionRequest(
        document_id="doc-orphan-double-failure",
        source_kind=IngestionSourceKind.PDF_SCAN,
        submitted_filename="scan.pdf",
        payload_base64=base64.b64encode(b"%PDF-1.4\ndouble-failure").decode("ascii"),
    )
    user = ExternalUserClaims(sub="doctor-6", tenant_scope="tenant-d", roles=["PHYSICIAN"])

    with pytest.raises(api.HTTPException) as exc_info:
        asyncio.run(api.ingest_document(request=request, user=user))

    assert exc_info.value.status_code == 500
    assert "repair marker persistence failed" in exc_info.value.detail
    assert recorder.deletes == []
    assert len(recorder.put_attempts) == 2
    assert len(recorder.successful_puts) == 1

    evidence_write = recorder.successful_puts[0]
    marker_attempt = recorder.put_attempts[1]

    assert evidence_write["Bucket"] == "evidence-originals"
    assert evidence_write["Key"] == "evidence/doc-orphan-double-failure.pdf"
    assert evidence_write["Body"] == b"%PDF-1.4\ndouble-failure"
    assert evidence_write["ObjectLockMode"] == "GOVERNANCE"
    assert "ObjectLockRetainUntilDate" in evidence_write

    assert marker_attempt["Bucket"] == "processing-artifacts"
    assert str(marker_attempt["Key"]).startswith("repair/orphan-evidence/doc-orphan-double-failure-")
    assert "ObjectLockMode" not in marker_attempt
