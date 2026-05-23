from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import httpx

from fhirbridge.core.config import get_settings


class FailureCategory(StrEnum):
    TRANSIENT_INFRASTRUCTURE = "TRANSIENT_INFRASTRUCTURE"
    PERMANENT_DATA = "PERMANENT_DATA"
    POLICY_AUTH = "POLICY_AUTH"
    DOWNSTREAM_CONSISTENCY = "DOWNSTREAM_CONSISTENCY"


class TransientInfrastructureError(Exception):
    pass


class PermanentDataError(Exception):
    pass


class DownstreamConsistencyError(Exception):
    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


@dataclass(slots=True)
class TriageDecision:
    category: FailureCategory
    retry_delay_ms: int | None
    destination: str
    audit_severity: str


def classify_exception(exc: Exception) -> FailureCategory:
    if isinstance(exc, TransientInfrastructureError):
        return FailureCategory.TRANSIENT_INFRASTRUCTURE
    if isinstance(exc, PermanentDataError):
        return FailureCategory.PERMANENT_DATA
    from fhirbridge.core.auth import PolicyAuthError

    if isinstance(exc, PolicyAuthError):
        return FailureCategory.POLICY_AUTH
    if isinstance(exc, DownstreamConsistencyError):
        return FailureCategory.DOWNSTREAM_CONSISTENCY
    if isinstance(exc, (httpx.TimeoutException, httpx.RequestError, TimeoutError, ConnectionError)):
        return FailureCategory.TRANSIENT_INFRASTRUCTURE
    return FailureCategory.PERMANENT_DATA


def compute_retry_delay_ms(retry_count: int) -> int:
    settings = get_settings()
    delay = settings.broker_retry_initial_delay_ms * (2 ** max(retry_count, 0))
    return min(delay, settings.broker_retry_max_delay_ms)


def decide_failure_route(exc: Exception, retry_count: int) -> TriageDecision:
    category = classify_exception(exc)
    if category == FailureCategory.TRANSIENT_INFRASTRUCTURE:
        return TriageDecision(
            category=category,
            retry_delay_ms=compute_retry_delay_ms(retry_count),
            destination="retry",
            audit_severity="INFO",
        )
    if category == FailureCategory.POLICY_AUTH:
        return TriageDecision(
            category=category,
            retry_delay_ms=None,
            destination="security_alert",
            audit_severity="HIGH",
        )
    if category == FailureCategory.DOWNSTREAM_CONSISTENCY:
        return TriageDecision(
            category=category,
            retry_delay_ms=None,
            destination="reconciliation",
            audit_severity="HIGH",
        )
    return TriageDecision(
        category=category,
        retry_delay_ms=None,
        destination="dlq",
        audit_severity="MEDIUM",
    )


def reschedule_for_retry(base_time: datetime | None, retry_count: int) -> datetime:
    reference = base_time or datetime.now(UTC)
    delay_ms = compute_retry_delay_ms(retry_count)
    return reference + timedelta(milliseconds=delay_ms)
