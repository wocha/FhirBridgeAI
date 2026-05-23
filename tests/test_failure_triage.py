from __future__ import annotations

import pytest

from fhirbridge.core.auth import PolicyAuthError
from fhirbridge.core.failure_handling import (
    DownstreamConsistencyError,
    FailureCategory,
    PermanentDataError,
    TransientInfrastructureError,
    classify_exception,
    decide_failure_route,
)

pytestmark = pytest.mark.smoke


def test_transient_infrastructure_errors_route_to_retry_queue() -> None:
    decision = decide_failure_route(TransientInfrastructureError("timeout"), retry_count=2)

    assert decision.category == FailureCategory.TRANSIENT_INFRASTRUCTURE
    assert decision.destination == "retry"
    assert decision.retry_delay_ms is not None


def test_permanent_data_errors_route_to_dlq() -> None:
    decision = decide_failure_route(PermanentDataError("invalid bundle"), retry_count=0)

    assert decision.category == FailureCategory.PERMANENT_DATA
    assert decision.destination == "dlq"
    assert decision.retry_delay_ms is None


def test_policy_errors_route_to_security_alerts() -> None:
    decision = decide_failure_route(PolicyAuthError("missing tenant scope"), retry_count=0)

    assert decision.category == FailureCategory.POLICY_AUTH
    assert decision.destination == "security_alert"


def test_consistency_errors_route_to_reconciliation() -> None:
    error = DownstreamConsistencyError("status update failed after downstream commit")
    assert classify_exception(error) == FailureCategory.DOWNSTREAM_CONSISTENCY
    assert decide_failure_route(error, retry_count=0).destination == "reconciliation"
