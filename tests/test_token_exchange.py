from __future__ import annotations

import asyncio
import base64
import json
from datetime import UTC, datetime, timedelta

import pytest

from fhirbridge.core.auth import (
    ExternalUserClaims,
    HTTPException,
    PolicyAuthError,
    TokenExchangeService,
    require_clinical_role,
)

pytestmark = pytest.mark.smoke


def _decode_payload(token: str) -> dict[str, object]:
    payload_b64 = token.split(".", maxsplit=1)[0]
    padding = "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8"))


def test_token_exchange_minimizes_claims_and_verifies() -> None:
    claims = ExternalUserClaims(sub="doctor-123", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    service = TokenExchangeService(secret="s" * 48, ttl_seconds=60)

    token = service.issue(claims=claims, trace_id="trace-1", bound_event_id="evt-1")
    payload = _decode_payload(token)
    context = service.verify(token, expected_tenant_scope="tenant-a", expected_event_id="evt-1")

    assert set(payload) == {
        "trace_id",
        "tenant_scope",
        "actor_id",
        "role_scope",
        "authz_decision_id",
        "token_expiry",
        "break_glass_flag",
        "issued_at",
        "jti",
        "bound_event_id",
    }
    assert "doctor-123" not in token
    assert context.actor_id != "doctor-123"
    assert context.tenant_scope == "tenant-a"
    assert context.role_scope == ["PHYSICIAN"]


def test_oversized_internal_token_is_rejected() -> None:
    claims = ExternalUserClaims(
        sub="doctor-123",
        tenant_scope="tenant-a",
        roles=["ROLE_" + ("X" * 200)] * 20,
    )
    service = TokenExchangeService(secret="s" * 48, ttl_seconds=60)

    with pytest.raises(PolicyAuthError):
        service.issue(claims=claims, trace_id="trace-1", bound_event_id="evt-1")


def test_break_glass_requires_reason() -> None:
    user = ExternalUserClaims(
        sub="emergency-123",
        tenant_scope="tenant-a",
        roles=["EMERGENCY"],
        break_glass=True,
        break_glass_reason=None,
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(require_clinical_role(user=user))

    assert exc_info.value.status_code == 403


def test_expired_internal_auth_context_can_be_reissued_for_dispatch() -> None:
    claims = ExternalUserClaims(sub="doctor-456", tenant_scope="tenant-a", roles=["PHYSICIAN"])
    service = TokenExchangeService(secret="s" * 48, ttl_seconds=60)
    issued_at = datetime.now(UTC) - timedelta(minutes=10)

    expired_token = service.issue(
        claims=claims,
        trace_id="trace-dispatch",
        bound_event_id="evt-dispatch",
        now=issued_at,
    )

    with pytest.raises(PolicyAuthError):
        service.verify(
            expired_token,
            expected_tenant_scope="tenant-a",
            expected_event_id="evt-dispatch",
        )

    rebound_token = service.reissue_bound_context(
        expired_token,
        expected_tenant_scope="tenant-a",
        expected_event_id="evt-dispatch",
        trace_id="trace-dispatch",
    )
    rebound_payload = _decode_payload(rebound_token)
    rebound_context = service.verify(
        rebound_token,
        expected_tenant_scope="tenant-a",
        expected_event_id="evt-dispatch",
    )

    assert rebound_context.authz_decision_id == _decode_payload(expired_token)["authz_decision_id"]
    assert rebound_context.bound_event_id == "evt-dispatch"
    assert rebound_payload["trace_id"] == "trace-dispatch"
