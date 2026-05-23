from __future__ import annotations

import pytest

from fhirbridge.core.semantic_chunking import (
    build_qdrant_payload,
    enforce_tenant_filter,
    split_semantic_chunks,
)

pytestmark = pytest.mark.smoke


def test_semantic_chunking_respects_section_boundaries() -> None:
    text = """
# Diagnosen
Pneumonie rechts basal. Kein Pleuraerguss.

# Medikation
Amoxicillin 500 mg dreimal taeglich. Paracetamol bei Bedarf.
""".strip()

    chunks = split_semantic_chunks(
        text=text,
        tenant_scope="tenant-a",
        document_version=3,
        aggregate_version=3,
        max_tokens=20,
    )

    assert len(chunks) >= 2
    assert chunks[0].source_section == "Diagnosen"
    assert chunks[1].source_section == "Medikation"
    assert all(chunk.token_count <= 20 for chunk in chunks)
    assert all(chunk.semantic_boundary_reason for chunk in chunks)


def test_qdrant_payload_contains_required_contract_fields() -> None:
    chunk = split_semantic_chunks(
        text="# Befund\nUnauffaellige Herzgroesse.",
        tenant_scope="tenant-a",
        document_version=2,
        aggregate_version=2,
        max_tokens=30,
    )[0]

    payload = build_qdrant_payload(chunk)

    assert payload["tenant_scope"] == "tenant-a"
    assert payload["document_version"] == 2
    assert payload["aggregate_version"] == 2
    assert payload["semantic_boundary_reason"]


def test_missing_tenant_filter_is_rejected() -> None:
    with pytest.raises(ValueError):
        enforce_tenant_filter({})
