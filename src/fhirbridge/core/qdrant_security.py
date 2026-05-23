from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from fhirbridge.core.config import get_settings
from fhirbridge.core.semantic_chunking import enforce_tenant_filter


class QdrantPolicyError(RuntimeError):
    """Raised when a Qdrant access path violates tenant or credential policy."""


class QdrantCredentialScope(StrEnum):
    READ = "READ"
    WRITE = "WRITE"


@dataclass(slots=True)
class QdrantAdvisoryGate:
    advisory_only: bool
    blocking_adr: str
    reason: str
    manual_review_required: bool


@dataclass(slots=True)
class QdrantOperationRecord:
    scope: QdrantCredentialScope
    tenant_scope: str
    filter_payload: dict[str, Any] | None = None
    payload_count: int = 0


@dataclass(slots=True)
class QdrantRuntimeHarness:
    read_api_key: str
    write_api_key: str
    operations: list[QdrantOperationRecord] = field(default_factory=list)

    def query(
        self,
        *,
        api_key: str,
        tenant_scope: str,
        filter_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if api_key != self.read_api_key:
            raise QdrantPolicyError("Qdrant read path must use the dedicated read credential")
        enforced_filter = enforce_tenant_filter(filter_payload)
        if enforced_filter.get("tenant_scope") != tenant_scope:
            raise QdrantPolicyError("Qdrant read path tenant filter does not match the caller tenant")
        self.operations.append(
            QdrantOperationRecord(
                scope=QdrantCredentialScope.READ,
                tenant_scope=tenant_scope,
                filter_payload=enforced_filter,
            )
        )
        return enforced_filter

    def upsert(
        self,
        *,
        api_key: str,
        tenant_scope: str,
        payloads: list[dict[str, Any]],
    ) -> None:
        if api_key != self.write_api_key:
            raise QdrantPolicyError("Qdrant write path must use the dedicated write credential")
        for payload in payloads:
            if payload.get("tenant_scope") != tenant_scope:
                raise QdrantPolicyError("Qdrant write payload tenant does not match the caller tenant")
        self.operations.append(
            QdrantOperationRecord(
                scope=QdrantCredentialScope.WRITE,
                tenant_scope=tenant_scope,
                payload_count=len(payloads),
            )
        )


def build_runtime_harness_from_settings() -> QdrantRuntimeHarness:
    read_key, write_key = get_settings().require_qdrant_credentials()
    return QdrantRuntimeHarness(read_api_key=read_key, write_api_key=write_key)


def advisory_only_gate(*, live_evidence_available: bool = False) -> QdrantAdvisoryGate:
    if live_evidence_available:
        return QdrantAdvisoryGate(
            advisory_only=False,
            blocking_adr="",
            reason="Live tenant-isolation evidence is available.",
            manual_review_required=False,
        )
    return QdrantAdvisoryGate(
        advisory_only=True,
        blocking_adr="ADR-023",
        reason="Live Qdrant isolation evidence remains nicht nachweisbar.",
        manual_review_required=True,
    )


def enforce_advisory_only_transition(
    *,
    gate: QdrantAdvisoryGate,
    attempted_straight_through: bool,
) -> None:
    if gate.advisory_only and attempted_straight_through:
        raise QdrantPolicyError(
            "Qdrant evidence is advisory only until ADR-023 is operationally closed"
        )
