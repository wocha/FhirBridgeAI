from __future__ import annotations

import asyncio
import base64
import json
import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://runtime-user:runtime-pass@db.internal/fhirbridge")
os.environ.setdefault("MINIO_ROOT_USER", "test-minio-user")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test-minio-password")
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


def _configure_runtime(monkeypatch: pytest.MonkeyPatch) -> RuntimeStore:
    store = RuntimeStore()
    monkeypatch.setattr(api, "_get_database", lambda: fake_database_bundle(store))
    monkeypatch.setattr(api, "get_or_create_read_model_async", fake_get_or_create_read_model_async)
    monkeypatch.setattr(api, "create_security_audit_event_async", fake_create_security_audit_event_async)
    return store


def test_pdf_boundary_contract_routes_to_ocr_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _configure_runtime(monkeypatch)
    uploaded: list[tuple[str, str, str]] = []

    async def _fake_put(claim_check, payload: bytes) -> None:
        uploaded.append((claim_check.bucket, claim_check.object_key, payload.decode("latin-1")))

    monkeypatch.setattr(api, "_put_claim_check_payload", _fake_put)

    request = api.DocumentIngestionRequest(
        document_id="doc-pdf-contract",
        source_kind=IngestionSourceKind.PDF_SCAN,
        submitted_filename="scan.pdf",
        payload_base64=base64.b64encode(b"%PDF-1.4\nscan body").decode("ascii"),
    )
    user = ExternalUserClaims(sub="doctor-1", tenant_scope="tenant-a", roles=["PHYSICIAN"])

    response = asyncio.run(api.ingest_document(request=request, user=user))

    assert response.status == "accepted"
    assert uploaded == [("evidence-originals", "evidence/doc-pdf-contract.pdf", "%PDF-1.4\nscan body")]
    payload = json.loads(store.outbox_events[0].payload_json)
    assert store.outbox_events[0].destination == "ocr_task_queue"
    assert payload["source_kind"] == "PDF_SCAN"
    assert payload["evidence"]["bucket"] == "evidence-originals"
    assert "doctor-1" not in store.outbox_events[0].payload_json


def test_hl7_boundary_contract_routes_to_llm_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    store = _configure_runtime(monkeypatch)

    async def _fake_put(_claim_check, _payload: bytes) -> None:
        return None

    monkeypatch.setattr(api, "_put_claim_check_payload", _fake_put)

    request = api.DocumentIngestionRequest(
        document_id="doc-hl7-contract",
        source_kind=IngestionSourceKind.HL7_V2,
        submitted_filename="adt.hl7",
        hl7_message="MSH|^~\\&|ADT|HOSP|LAB|HOSP|202603151200||ADT^A01|1|P|2.5",
    )
    user = ExternalUserClaims(sub="doctor-2", tenant_scope="tenant-b", roles=["PHYSICIAN"])

    response = asyncio.run(api.ingest_document(request=request, user=user))

    assert response.status == "accepted"
    payload = json.loads(store.outbox_events[0].payload_json)
    assert store.outbox_events[0].destination == "llm_extraction_queue"
    assert payload["source_kind"] == "HL7_V2"
    assert payload["document"]["media_type"] == "application/hl7-v2"
    assert "doctor-2" not in store.outbox_events[0].payload_json


def test_pdf_boundary_contract_rejects_non_pdf_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_runtime(monkeypatch)

    async def _unexpected_put(_claim_check, _payload: bytes) -> None:
        raise AssertionError("Invalid PDF payload must fail before storage")

    monkeypatch.setattr(api, "_put_claim_check_payload", _unexpected_put)
    user = ExternalUserClaims(sub="doctor-3", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    request = api.DocumentIngestionRequest(
        document_id="doc-invalid-pdf",
        source_kind=IngestionSourceKind.PDF_SCAN,
        payload_base64=base64.b64encode(b"not-a-pdf").decode("ascii"),
    )

    with pytest.raises(api.HTTPException) as exc_info:
        asyncio.run(api.ingest_document(request=request, user=user))

    assert exc_info.value.status_code == 400


def test_hl7_boundary_contract_rejects_missing_msh(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure_runtime(monkeypatch)
    user = ExternalUserClaims(sub="doctor-4", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    request = api.DocumentIngestionRequest(
        document_id="doc-invalid-hl7",
        source_kind=IngestionSourceKind.HL7_V2,
        hl7_message="PID|1||12345",
    )

    with pytest.raises(api.HTTPException) as exc_info:
        asyncio.run(api.ingest_document(request=request, user=user))

    assert exc_info.value.status_code == 400
