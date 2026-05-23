# ADR-013: Traefik Docker Socket in WSL2 Trade-off

## Status

Superseded

## Superseded By

- ADR-017: Control-Plane Isolation and Internal TLS (socketless edge routing update, 2026-03-13)

## Date

2026-03-13

## Context (Historical)

This ADR previously documented a dev-operability trade-off where Traefik consumed Docker metadata via `/var/run/docker.sock` and `--providers.docker=true` to simplify route discovery in WSL2/local environments.

## Superseding Decision

The trade-off is no longer accepted for KRITIS/BSI-200-2 high protection needs.

1. Traefik must not mount `docker.sock`.
2. Traefik must not enable Docker provider.
3. All edge routing must be declared through file-provider configuration (`deploy/traefik/dynamic.yml`).

## Security Rationale

Docker socket exposure gives broad host/control-plane capabilities that violate zero-trust assumptions and materially increase blast radius.

## Migration Outcome

- Docker provider removed.
- Docker socket mount removed.
- Router/service/middleware definitions migrated to file-provider.

## Residual Exceptions

None for docker-socket exposure. Any future exception requires a new ADR with explicit owner, expiry, and exit criteria.
