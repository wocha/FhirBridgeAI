# ADR-016: Internal Network Segmentation and TLS

## Status

Superseded in parts by ADR-017, still Accepted for segmentation baseline.

## Context

Audit findings for KRITIS (BSI-200-2, hoher Schutzbedarf) identified two core weaknesses:

1. Unnecessary cross-segment connectivity between `frontend` and pipeline services.
2. Incomplete transport hardening for security-critical control paths.

## Decision

We enforce strict five-zone segmentation with least privilege:

1. `dmz`: external ingress edge (`traefik`, `oauth2-proxy`).
2. `auth`: identity control plane (`keycloak`, `keycloak-db`, `oauth2-proxy`).
3. `frontend`: UI runtime only (`dashboard`, `oauth2-proxy`).
4. `pipeline`: processing plane (`ingestion`, workers, `rabbitmq`, `postgres`, `minio`).
5. `observability`: metrics/traces (`prometheus`, `grafana`, `jaeger`, `grafana-db`, `dashboard`).

### Mandatory deny paths

- `frontend` -> `rabbitmq:5672/15672` is denied by network isolation.
- `frontend` -> `postgres:5432` is denied by network isolation.
- Dashboard queue visibility is only allowed via `prometheus` in `observability`.

### TLS baseline

- Browser/OIDC ingress is HTTPS-only via Traefik.
- PostgreSQL transport remains TLS-enabled (`ssl=on`, `sslmode=require`).
- Internal OIDC endpoint hardening and control-plane isolation details are moved to ADR-017.

## Consequences

- Positive: Reduced east-west blast radius and clear trust boundaries.
- Positive: Frontend no longer carries broker-admin or productive DB credentials.
- Positive: Security controls are enforceable via deterministic network membership.
- Negative: Additional operational complexity (more explicit wiring and tests).
