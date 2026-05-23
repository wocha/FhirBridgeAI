# ADR-024: Keycloak Live Evidence Exception

## Status

Accepted

## Context

The boundary path validates external JWTs against Keycloak configuration, but this local session does not include a retained end-to-end evidence package proving live JWKS validation against the target Keycloak deployment.

## Decision

1. Keep the boundary validation implementation and unit tests in place.
2. Mark live Keycloak JWKS evidence as a time-boxed exception until an operational validation run is executed and archived.

## Technical Evidence

- `src/fhirbridge/core/auth.py`
- `src/fhirbridge/ingestion/api.py`
- `tests/test_token_exchange.py`

## Time-Boxed Exception

- Exception: Live Keycloak JWKS evidence remains `nicht nachweisbar`.
- Owner: IAM Platform Owner.
- Ablaufdatum: 2026-04-30.
- Exit-Kriterium: Execute an end-to-end login and token-validation run against the target Keycloak deployment and archive the resulting evidence.
- Technischer Guardrail: Boundary code still enforces JWT validation and tenant-scope checks; no worker path accepts end-user JWTs directly.
