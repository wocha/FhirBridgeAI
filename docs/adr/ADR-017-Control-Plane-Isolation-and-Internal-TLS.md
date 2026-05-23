# ADR-017: Control-Plane Isolation, Internal TLS, and Socketless Edge Routing

## Status

Accepted (implementation active, audit evidence enforced)

## Date

2026-03-13

## Supersedes

- ADR-013: Traefik Docker Socket in WSL2 Trade-off

## Context

For KRITIS/BSI-200-2 (Schutzbedarf hoch), the platform must eliminate trust transitivity across control-plane and auth-plane boundaries. Residual risk drivers were:

1. Docker-socket based edge discovery (`/var/run/docker.sock`, Docker provider) in Traefik.
2. Non-pinned control-plane images.
3. Admin bootstrap path exposure over non-hardened transport.
4. Dashboard over-reach into broader observability/control surfaces.
5. Ingestion saga behavior that could delete S3 payload after confirmed publish.

## Decision

### 1) Socketless Edge Routing (new mandatory baseline)

- Traefik must not mount `/var/run/docker.sock`.
- Traefik must not enable Docker provider (`--providers.docker=true` forbidden).
- Edge routing is file-provider only (`deploy/traefik/dynamic.yml`).
- Routers/services/middleware for `dashboard.docker.localhost`, `keycloak.docker.localhost`, and `grafana.docker.localhost` are declared statically in file config.

### 2) Control-plane isolation and pinning

- Traefik and Keycloak images are pinned by digest in Compose.
- Traefik insecure API remains forbidden (`--api.insecure=true` forbidden).
- Dashboard is restricted to `frontend` plus dedicated `metrics_read` network.

### 3) Internal auth transport hardening

- Keycloak bootstrap must use HTTPS endpoint (`KEYCLOAK_BOOTSTRAP_URL=https://...`).
- HTTP bootstrap is explicitly rejected in `deploy/keycloak/bootstrap.sh`.
- TLS validation is mandatory for bootstrap via CA-backed truststore (`KC_OPTS` trustStore/trustStorePassword).
- OIDC E2E verification defaults to `OIDC_VERIFY_TLS=true`.

### 4) Secrets and fail-fast

- Security-critical fallback defaults are prohibited for:
  - `API_KEY_SECRET`
  - `MINIO_ROOT_USER`
  - `MINIO_ROOT_PASSWORD`
- Compose interpolation is fail-fast (`${VAR:?error}`) for these variables.

### 5) Dashboard trust boundary and least privilege

- Dashboard reads queue status only via Prometheus metrics path.
- Dashboard has no broker-admin and no pipeline-DB credentials.
- Header trust boundary remains enforced via trusted oauth2-proxy headers.

### 6) Saga-safe ingestion consistency

- S3 rollback is allowed only before publish confirmation.
- If publish succeeded but DB status update fails:
  - no S3 delete,
  - deterministic repair marker is written (`ingestion_status_repair_queue` + DB error trace marker),
  - response remains accepted to avoid duplicate client retries.

## Security Exceptions (explicit)

### EX-017-DEV-01: Temporary insecure OIDC test mode

- Scope: `OIDC_VERIFY_TLS=false` in local E2E script only.
- Owner: Platform Security Lead.
- Expiry: 2026-06-30.
- Exit criterion: all local/dev test nodes trust the internal CA and E2E runs with `OIDC_VERIFY_TLS=true` only.
- Guardrail: explicit opt-in required via `OIDC_ALLOW_INSECURE_DEV=true`.

### EX-017-DEV-02: Keycloak `start-dev` runtime mode

- Scope: local/dev compose only.
- Owner: IAM Platform Owner.
- Expiry: 2026-09-30.
- Exit criterion: migration to `start --optimized` with hardened production profile and immutable rollout.
- Guardrail: no HTTP admin bootstrap allowed despite `start-dev`.

## Consequences

### Positive

- Confidentiality: socketless edge removes privileged Docker control-plane access from reverse proxy.
- Integrity: deterministic compensation semantics prevent destructive rollback after confirmed publish.
- Availability: repair markers avoid data loss while allowing asynchronous reconciliation.
- Auditability: routing and security controls are static, reviewable, and script-verifiable.

### Trade-offs

- Route lifecycle is no longer auto-discovered and requires explicit file updates.
- Bootstrap complexity increases due to CA truststore management.

## Verification Hooks

- `python scripts/security/check_security_posture.py`
- `python scripts/security/check_network_matrix.py`
- `python scripts/security/oidc_e2e.py`
- `docker compose config`
- `pytest -q`
