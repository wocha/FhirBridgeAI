"""
ADR-020: Keycloak validation at the boundary, internal token exchange afterwards.

This module intentionally never forwards the original user JWT beyond the
policy-enforcement boundary. Workers only receive a minimal signed auth
context that is short-lived, scope-bound, and safe to persist in broker/DB
payloads.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from fhirbridge.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    from fastapi import Depends, HTTPException, Security, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except ImportError:  # pragma: no cover - local unit-test fallback
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class status:
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403

    def Depends(dependency):  # type: ignore[override]
        return dependency

    def Security(dependency):  # type: ignore[override]
        return dependency

    class HTTPAuthorizationCredentials(BaseModel):
        credentials: str

    class HTTPBearer:  # type: ignore[override]
        def __init__(self, auto_error: bool = True) -> None:
            self.auto_error = auto_error

try:
    import jwt as pyjwt
except ImportError:  # pragma: no cover - optional dependency in tests
    pyjwt = None


MAX_INTERNAL_TOKEN_BYTES = 1024
security = HTTPBearer(auto_error=True)


class Role(StrEnum):
    PHYSICIAN = "PHYSICIAN"
    NURSE = "NURSE"
    ADMIN = "ADMIN"
    EMERGENCY = "EMERGENCY"


class ExternalUserClaims(BaseModel):
    """PHI-safe boundary claims extracted from the external JWT."""

    sub: str
    tenant_scope: str
    roles: list[str] = Field(default_factory=list)
    break_glass: bool = False
    break_glass_reason: str | None = None
    station: str | None = None

    @property
    def actor_id(self) -> str:
        digest = hashlib.sha256(self.sub.encode("utf-8")).hexdigest()
        return digest[:24]

    @property
    def has_clinical_access(self) -> bool:
        return bool(set(self.roles) & {Role.PHYSICIAN, Role.NURSE, Role.EMERGENCY})

    @property
    def can_manual_review(self) -> bool:
        return bool(set(self.roles) & {Role.PHYSICIAN, Role.ADMIN})


class InternalAuthContext(BaseModel):
    trace_id: str
    tenant_scope: str
    actor_id: str
    role_scope: list[str]
    authz_decision_id: str
    token_expiry: datetime
    break_glass_flag: bool = False
    issued_at: datetime
    jti: str
    bound_event_id: str


class SecurityAuditRecord(BaseModel):
    event_type: str
    severity: str
    actor_id: str
    tenant_scope: str
    authz_decision_id: str
    details: dict[str, Any] = Field(default_factory=dict)


class PolicyAuthError(Exception):
    def __init__(self, message: str, *, audit_record: SecurityAuditRecord | None = None) -> None:
        super().__init__(message)
        self.audit_record = audit_record


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _from_b64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


class TokenExchangeService:
    def __init__(self, secret: str, ttl_seconds: int = 300) -> None:
        if not secret:
            raise RuntimeError("INTERNAL_AUTH_CONTEXT_SECRET is required for token exchange")
        self._secret = secret.encode("utf-8")
        self._ttl_seconds = ttl_seconds

    @classmethod
    def from_settings(cls) -> "TokenExchangeService":
        settings = get_settings()
        return cls(
            secret=settings.internal_auth_context_secret,
            ttl_seconds=settings.internal_auth_context_ttl_seconds,
        )

    def issue(
        self,
        *,
        claims: ExternalUserClaims,
        trace_id: str,
        bound_event_id: str,
        now: datetime | None = None,
    ) -> str:
        issued_at = now or datetime.now(UTC)
        auth_context = InternalAuthContext(
            trace_id=trace_id,
            tenant_scope=claims.tenant_scope,
            actor_id=claims.actor_id,
            role_scope=list(claims.roles),
            authz_decision_id=str(uuid.uuid4()),
            token_expiry=issued_at + timedelta(seconds=self._ttl_seconds),
            break_glass_flag=claims.break_glass,
            issued_at=issued_at,
            jti=str(uuid.uuid4()),
            bound_event_id=bound_event_id,
        )
        return self._encode_context(auth_context)

    def _encode_context(self, context: InternalAuthContext) -> str:
        payload = context.model_dump(mode="json")
        encoded_payload = _b64url(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        signature = _b64url(hmac.new(self._secret, encoded_payload.encode("ascii"), hashlib.sha256).digest())
        token = f"{encoded_payload}.{signature}"
        if len(token.encode("utf-8")) > MAX_INTERNAL_TOKEN_BYTES:
            raise PolicyAuthError("Internal auth context exceeds broker-safe size limits")
        return token

    def _decode_context(
        self,
        token: str,
        *,
        expected_tenant_scope: str,
        expected_event_id: str,
        now: datetime | None = None,
        allow_expired: bool = False,
    ) -> InternalAuthContext:
        try:
            encoded_payload, encoded_signature = token.split(".", maxsplit=1)
        except ValueError as exc:
            raise PolicyAuthError("Malformed internal auth context") from exc

        expected_signature = _b64url(
            hmac.new(self._secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(encoded_signature, expected_signature):
            raise PolicyAuthError("Internal auth context signature verification failed")

        payload_bytes = _from_b64url(encoded_payload)
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
            context = InternalAuthContext.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise PolicyAuthError("Internal auth context payload is invalid") from exc

        current_time = now or datetime.now(UTC)
        if not allow_expired and context.token_expiry <= current_time:
            raise PolicyAuthError("Internal auth context expired")
        if context.tenant_scope != expected_tenant_scope:
            raise PolicyAuthError("Tenant scope mismatch in internal auth context")
        if context.bound_event_id != expected_event_id:
            raise PolicyAuthError("Internal auth context replay binding mismatch")
        return context

    def verify(
        self,
        token: str,
        *,
        expected_tenant_scope: str,
        expected_event_id: str,
        now: datetime | None = None,
    ) -> InternalAuthContext:
        return self._decode_context(
            token,
            expected_tenant_scope=expected_tenant_scope,
            expected_event_id=expected_event_id,
            now=now,
            allow_expired=False,
        )

    def delegate(
        self,
        *,
        existing_context: InternalAuthContext,
        trace_id: str,
        bound_event_id: str,
        now: datetime | None = None,
    ) -> str:
        issued_at = now or datetime.now(UTC)
        delegated_context = InternalAuthContext(
            trace_id=trace_id,
            tenant_scope=existing_context.tenant_scope,
            actor_id=existing_context.actor_id,
            role_scope=list(existing_context.role_scope),
            authz_decision_id=existing_context.authz_decision_id,
            token_expiry=issued_at + timedelta(seconds=self._ttl_seconds),
            break_glass_flag=existing_context.break_glass_flag,
            issued_at=issued_at,
            jti=str(uuid.uuid4()),
            bound_event_id=bound_event_id,
        )
        try:
            return self._encode_context(delegated_context)
        except PolicyAuthError as exc:
            raise PolicyAuthError("Delegated auth context exceeds broker-safe size limits") from exc

    def reissue_bound_context(
        self,
        token: str,
        *,
        expected_tenant_scope: str,
        expected_event_id: str,
        trace_id: str | None = None,
        now: datetime | None = None,
    ) -> str:
        existing_context = self._decode_context(
            token,
            expected_tenant_scope=expected_tenant_scope,
            expected_event_id=expected_event_id,
            now=now,
            allow_expired=True,
        )
        issued_at = now or datetime.now(UTC)
        rebound_context = InternalAuthContext(
            trace_id=trace_id or existing_context.trace_id,
            tenant_scope=existing_context.tenant_scope,
            actor_id=existing_context.actor_id,
            role_scope=list(existing_context.role_scope),
            authz_decision_id=existing_context.authz_decision_id,
            token_expiry=issued_at + timedelta(seconds=self._ttl_seconds),
            break_glass_flag=existing_context.break_glass_flag,
            issued_at=issued_at,
            jti=str(uuid.uuid4()),
            bound_event_id=expected_event_id,
        )
        return self._encode_context(rebound_context)


async def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


async def validate_external_jwt(token: str) -> ExternalUserClaims:
    """
    Validate the external user JWT at the policy-enforcement boundary.

    RS256/JWKS validation is preferred. Tests may monkeypatch this function.
    """
    settings = get_settings()
    if pyjwt is None:
        raise RuntimeError("PyJWT is required for external JWT validation")

    issuer = ""
    if settings.keycloak_url and settings.keycloak_realm:
        issuer = f"{settings.keycloak_url.rstrip('/')}/realms/{settings.keycloak_realm}"
    jwks_url = settings.keycloak_jwks_url or (
        f"{issuer}/protocol/openid-connect/certs" if issuer else ""
    )
    if not jwks_url or not settings.keycloak_client_id:
        raise RuntimeError("Keycloak issuer/JWKS/client configuration is incomplete")

    jwks = await _fetch_jwks(jwks_url)
    header = pyjwt.get_unverified_header(token)
    kid = header.get("kid")
    jwk = next((key for key in jwks.get("keys", []) if key.get("kid") == kid), None)
    if not jwk:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown signing key")

    public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
    try:
        payload = pyjwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            issuer=issuer,
        )
    except Exception as exc:  # pragma: no cover - depends on crypto backend
        logger.warning("JWT validation failed: %s", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    roles = payload.get("realm_access", {}).get("roles", [])
    tenant_scope = str(payload.get("tenant_scope") or payload.get("tenant") or "").strip()
    if not tenant_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing tenant scope in external token",
        )
    claims = ExternalUserClaims(
        sub=str(payload.get("sub", "")),
        tenant_scope=tenant_scope,
        roles=[str(role) for role in roles],
        break_glass=bool(payload.get("break_glass", False)),
        break_glass_reason=payload.get("break_glass_reason"),
        station=payload.get("station"),
    )
    return claims


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> ExternalUserClaims:
    return await validate_external_jwt(credentials.credentials)


def build_break_glass_audit(user: ExternalUserClaims, authz_decision_id: str) -> SecurityAuditRecord:
    return SecurityAuditRecord(
        event_type="break_glass_access",
        severity="HIGH",
        actor_id=user.actor_id,
        tenant_scope=user.tenant_scope,
        authz_decision_id=authz_decision_id,
        details={"station": user.station or "UNKNOWN"},
    )


async def require_clinical_role(
    user: ExternalUserClaims = Depends(get_current_user),
) -> ExternalUserClaims:
    if not user.has_clinical_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinical role required",
        )
    if user.break_glass and not user.break_glass_reason:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Break-glass requires a reason",
        )
    return user


async def require_manual_review_role(
    user: ExternalUserClaims = Depends(get_current_user),
) -> ExternalUserClaims:
    if not user.can_manual_review:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual review role required",
        )
    if user.break_glass and not user.break_glass_reason:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Break-glass requires a reason",
        )
    return user
