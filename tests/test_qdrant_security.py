from __future__ import annotations

import pytest

from fhirbridge.core.qdrant_security import (
    QdrantPolicyError,
    QdrantRuntimeHarness,
    advisory_only_gate,
    enforce_advisory_only_transition,
)

pytestmark = pytest.mark.smoke


def test_qdrant_query_requires_explicit_tenant_filter() -> None:
    harness = QdrantRuntimeHarness(read_api_key="r" * 24, write_api_key="w" * 24)

    with pytest.raises(ValueError):
        harness.query(api_key="r" * 24, tenant_scope="tenant-a", filter_payload=None)


def test_qdrant_query_rejects_wrong_tenant() -> None:
    harness = QdrantRuntimeHarness(read_api_key="r" * 24, write_api_key="w" * 24)

    with pytest.raises(QdrantPolicyError):
        harness.query(
            api_key="r" * 24,
            tenant_scope="tenant-a",
            filter_payload={"tenant_scope": "tenant-b"},
        )


def test_qdrant_query_rejects_write_credential_on_read_path() -> None:
    harness = QdrantRuntimeHarness(read_api_key="r" * 24, write_api_key="w" * 24)

    with pytest.raises(QdrantPolicyError):
        harness.query(
            api_key="w" * 24,
            tenant_scope="tenant-a",
            filter_payload={"tenant_scope": "tenant-a"},
        )


def test_qdrant_upsert_rejects_read_credential_on_write_path() -> None:
    harness = QdrantRuntimeHarness(read_api_key="r" * 24, write_api_key="w" * 24)

    with pytest.raises(QdrantPolicyError):
        harness.upsert(
            api_key="r" * 24,
            tenant_scope="tenant-a",
            payloads=[{"tenant_scope": "tenant-a", "content": "chunk"}],
        )


def test_qdrant_upsert_rejects_cross_tenant_payload() -> None:
    harness = QdrantRuntimeHarness(read_api_key="r" * 24, write_api_key="w" * 24)

    with pytest.raises(QdrantPolicyError):
        harness.upsert(
            api_key="w" * 24,
            tenant_scope="tenant-a",
            payloads=[{"tenant_scope": "tenant-b", "content": "chunk"}],
        )


def test_qdrant_live_evidence_gap_forces_advisory_only_transition() -> None:
    gate = advisory_only_gate(live_evidence_available=False)

    with pytest.raises(QdrantPolicyError):
        enforce_advisory_only_transition(
            gate=gate,
            attempted_straight_through=True,
        )

    assert gate.manual_review_required is True
