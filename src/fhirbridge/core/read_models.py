from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MaterializedReadModelState:
    job_id: int
    document_id: str
    projection_name: str
    status: str
    required_version: int
    visible_version: int


@dataclass(slots=True)
class VersionGateResult:
    allowed: bool
    required_version: int
    visible_version: int
    actual_required_version: int
    requested_version: int | None
    message: str


def bind_materialized_read_model(payload: dict[str, Any]) -> MaterializedReadModelState:
    return MaterializedReadModelState(
        job_id=int(payload["job_id"]),
        document_id=str(payload["document_id"]),
        projection_name=str(payload["projection_name"]),
        status=str(payload["status"]),
        required_version=int(payload["required_version"]),
        visible_version=int(payload["visible_version"]),
    )


def evaluate_version_gate(required_version: int, visible_version: int) -> VersionGateResult:
    return evaluate_materialized_version_gate(
        actual_required_version=required_version,
        visible_version=visible_version,
        requested_version=required_version,
    )


def evaluate_materialized_version_gate(
    *,
    actual_required_version: int,
    visible_version: int,
    requested_version: int | None,
) -> VersionGateResult:
    effective_required = (
        max(actual_required_version, requested_version)
        if requested_version is not None
        else actual_required_version
    )

    if visible_version >= effective_required:
        return VersionGateResult(
            allowed=True,
            required_version=effective_required,
            visible_version=visible_version,
            actual_required_version=actual_required_version,
            requested_version=requested_version,
            message="Read model is materialized up to the required version.",
        )

    return VersionGateResult(
        allowed=False,
        required_version=effective_required,
        visible_version=visible_version,
        actual_required_version=actual_required_version,
        requested_version=requested_version,
        message="Read model is stale; clinical content must remain hidden.",
    )
