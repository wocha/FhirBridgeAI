# ADR-015: OIDC Authentication Flow

## Status

Accepted

## Context

The OIDC login flow for `dashboard.docker.localhost` failed with HTTP 500 on `/oauth2/callback` due to issuer mismatch and insecure cookie configuration.

Root causes:

1. `oauth2-proxy` validated tokens against an issuer that did not align with the `iss` claim produced by Keycloak under reverse-proxy hostname handling.
2. The session cookie (`_oauth2_proxy`) was not marked `Secure`, violating BSI APP.3.1.A4 and allowing downgrade risk.

The environment is KRITIS-oriented with high protection needs and requires deterministic local auth in a zero-trust deployment.

## Decision

We standardize the authentication path to **Keycloak + oauth2-proxy** with strict issuer/cookie rules:

1. `oidc_issuer_url` remains `https://keycloak.docker.localhost/realms/FhirBridgeAI` and MUST match token `iss`.
2. `cookie_secure = true` is mandatory for all browser session cookies.
3. `oauth2-proxy` is configured with:
   - `insecure_oidc_allow_unverified_email = true`
   - `ssl_insecure_skip_verify = true` (dev-only because local self-signed certs are used behind Traefik)
4. Keycloak is configured with:
   - `KC_PROXY_HEADERS=xforwarded`
   - `KC_HOSTNAME=keycloak.docker.localhost`
   - relaxed hostname strictness for local development
   - health endpoint enabled and readiness-gated startup dependencies
5. `oauth2-proxy` startup depends on Keycloak readiness (`depends_on.condition=service_healthy`) to avoid race conditions.

Implementation trade-off:

- In local development we keep `start-dev` for operability.
- Production MUST use `start --import-realm --optimized`.

## Consequences

- Positive: OIDC callback errors caused by issuer mismatch are eliminated.
- Positive: Session cookies satisfy secure transport requirements.
- Positive: Startup order becomes deterministic and more resilient.
- Negative: `ssl_insecure_skip_verify=true` is an explicit dev-mode exception and MUST NOT be carried into production.
