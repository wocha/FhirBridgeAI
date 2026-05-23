from __future__ import annotations

import hashlib

from fhirbridge.core.config import get_settings
from fhirbridge.core.rabbitmq import ClaimCheck, IngestionSourceKind

PDF_MEDIA_TYPE = "application/pdf"
HL7_MEDIA_TYPE = "application/hl7-v2"
TEXT_MEDIA_TYPE = "text/plain; charset=utf-8"
JSON_MEDIA_TYPE = "application/json"


def s3_client_kwargs() -> dict[str, str]:
    settings = get_settings()
    access_key, secret_key = settings.require_minio_credentials()
    return {
        "endpoint_url": settings.require_minio_url(),
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "verify": settings.minio_http_verify(),
    }


def evidence_bucket_name() -> str:
    evidence_bucket, _, _ = get_settings().object_storage_buckets()
    return evidence_bucket


def processing_bucket_name() -> str:
    _, processing_bucket, _ = get_settings().object_storage_buckets()
    return processing_bucket


def phi_vault_bucket_name() -> str:
    _, _, phi_vault_bucket = get_settings().object_storage_buckets()
    return phi_vault_bucket


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_extension(*, source_kind: IngestionSourceKind, media_type: str) -> str:
    if media_type == PDF_MEDIA_TYPE or source_kind == IngestionSourceKind.PDF_SCAN:
        return ".pdf"
    if media_type == HL7_MEDIA_TYPE or source_kind == IngestionSourceKind.HL7_V2:
        return ".hl7"
    return ".bin"


def build_evidence_claim_check(
    *,
    document_id: str,
    source_kind: IngestionSourceKind,
    media_type: str,
    payload: bytes,
) -> ClaimCheck:
    return ClaimCheck(
        bucket=evidence_bucket_name(),
        object_key=f"evidence/{document_id}{_source_extension(source_kind=source_kind, media_type=media_type)}",
        media_type=media_type,
        sha256=sha256_hex(payload),
    )


def build_processing_claim_check(
    *,
    job_id: int,
    source_kind: IngestionSourceKind,
) -> ClaimCheck:
    suffix = "ocr.txt" if source_kind == IngestionSourceKind.PDF_SCAN else "normalized.hl7"
    return ClaimCheck(
        bucket=processing_bucket_name(),
        object_key=f"processing/job-{job_id}/{suffix}",
        media_type=TEXT_MEDIA_TYPE,
    )


def build_phi_vault_claim_check(*, job_id: int) -> ClaimCheck:
    return ClaimCheck(
        bucket=phi_vault_bucket_name(),
        object_key=f"vault/job-{job_id}/mapping.json",
        media_type=JSON_MEDIA_TYPE,
    )


def build_orphan_evidence_marker_claim_check(*, document_id: str, trace_id: str) -> ClaimCheck:
    return ClaimCheck(
        bucket=processing_bucket_name(),
        object_key=f"repair/orphan-evidence/{document_id}-{trace_id}.json",
        media_type=JSON_MEDIA_TYPE,
    )
