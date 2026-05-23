from __future__ import annotations

import pytest

from fhirbridge.core.read_models import (
    bind_materialized_read_model,
    evaluate_materialized_version_gate,
    evaluate_version_gate,
)

pytestmark = pytest.mark.smoke


def test_read_model_gate_allows_current_projection() -> None:
    gate = evaluate_version_gate(required_version=4, visible_version=4)

    assert gate.allowed is True
    assert "materialized" in gate.message


def test_read_model_gate_blocks_stale_projection() -> None:
    gate = evaluate_version_gate(required_version=7, visible_version=6)

    assert gate.allowed is False
    assert "stale" in gate.message


def test_materialized_gate_uses_backend_versions_not_only_requested_version() -> None:
    state = bind_materialized_read_model(
        {
            "job_id": 17,
            "document_id": "doc-17",
            "projection_name": "dashboard",
            "status": "FHIR_GENERATED",
            "required_version": 5,
            "visible_version": 4,
        }
    )

    gate = evaluate_materialized_version_gate(
        actual_required_version=state.required_version,
        visible_version=state.visible_version,
        requested_version=3,
    )

    assert gate.allowed is False
    assert gate.required_version == 5


def test_materialized_gate_blocks_when_requested_version_exceeds_visible_version() -> None:
    gate = evaluate_materialized_version_gate(
        actual_required_version=2,
        visible_version=4,
        requested_version=5,
    )

    assert gate.allowed is False
    assert gate.required_version == 5
    assert gate.visible_version == 4
