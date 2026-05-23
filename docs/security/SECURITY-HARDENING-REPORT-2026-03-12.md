# Security Hardening Report (updated 2026-03-15)

## 2026-03-15 Hardening Addendum

This report now tracks multiple hardening waves. For the PostgreSQL-only governance, outbox lease-fencing, final fail-closed escalation handling, and repo-context guard expansion completed on 2026-03-15, the authoritative reproducible evidence is:

- `docs/security/test-evidence-2026-03-15.md`
- Entry-point: `python scripts/security/run_hardening_evidence.py`

Executed result on 2026-03-15:

- Pytest hardening suite: `44 passed, 5 skipped`
- Security posture check: `Security checks passed.`

Interpretation:

- The 5 skips are the optional live PostgreSQL harness tests in `tests/test_postgres_runtime_harness.py` when `TEST_DATABASE_URL` is not set; those live checks remain `nicht nachweisbar` locally.
- The outbox dispatcher now treats ambiguous publish as contained only when `ESCALATED + reconciliation` commits atomically; if that confirmation fails, the runtime persists `FATAL_ESCALATION_FAILED` or falls back to the persisted `publish_attempt_id` claim-block guard so the event cannot re-enter normal auto-claiming.
- The non-reclaimable fail-closed state is evidenced by `tests/test_outbox_dispatcher.py::test_failed_escalation_write_is_quarantined_and_stops_fail_closed`, `tests/test_outbox_dispatcher.py::test_fatal_and_started_publish_events_are_never_auto_reclaimed`, and `tests/test_postgres_runtime_harness.py::test_postgres_dispatcher_fails_closed_when_escalation_write_is_not_confirmed`.
- Repo governance now scans active skills, knowledge assets, and governed `scripts/**` assets; explicit allowlists are limited to historical ADRs, blocked retired stubs, and scanner scripts that contain forbidden strings only as search patterns.
- No aggregate count outside `docs/security/test-evidence-2026-03-15.md` is authoritative for the 2026-03-15 hardening scope.

## Historical 2026-03-12 Wave
# Security Hardening Report (updated 2026-03-13)

## Scope

Elimination of Traefik Docker-socket control-plane risk for KRITIS/BSI-200-2 (Schutzbedarf hoch):

- Socketless edge routing (file-provider only)
- Removal of Docker provider and docker.sock exposure
- Preservation of auth and control-plane route availability
- Automated proof checks with positive and negative evidence

## Changed Files

- `<project-root>/docker-compose.yml`
- `<project-root>/deploy/traefik/dynamic.yml`
- `<project-root>/scripts/security/check_security_posture.py`
- `<project-root>/scripts/security/check_network_matrix.py`
- `<project-root>/docs/adr/ADR-013-Traefik-Docker-Socket-WSL2-Trade-off.md`
- `<project-root>/docs/adr/ADR-017-Control-Plane-Isolation-and-Internal-TLS.md`
- `<project-root>/docs/security/SECURITY-HARDENING-REPORT-2026-03-12.md`

## Security Rationale by Change

### 1) `docker-compose.yml`

- Removed Traefik Docker discovery flags:
  - removed `--providers.docker=true`
  - removed `--providers.docker.exposedbydefault=false`
- Removed Traefik docker socket mount:
  - removed `/var/run/docker.sock:/var/run/docker.sock:ro`
- Kept file provider binding only:
  - `--providers.file.filename=/etc/traefik/dynamic.yml`
- Removed obsolete Traefik labels from:
  - `oauth2-proxy`
  - `keycloak`
  - `grafana`

### 2) `deploy/traefik/dynamic.yml`

- Centralized all edge routing in file-provider config:
  - `dashboard.docker.localhost` -> `oauth2-proxy:4180`
  - `keycloak.docker.localhost` -> `keycloak:8080`
  - `grafana.docker.localhost` -> `grafana:3000`
- Migrated `strip-auth-headers` middleware completely to file config.

### 3) `scripts/security/check_security_posture.py`

- Added hard-fail checks for socketless baseline:
  - fail if Traefik command enables Docker provider
  - fail if Traefik mounts `docker.sock`
  - fail if `oauth2-proxy`/`keycloak`/`grafana` still carry Traefik labels
  - fail if required dynamic routing snippets are missing in `dynamic.yml`
- Added optional compose-file override (`SECURITY_COMPOSE_FILE`) to prove negative test behavior.

### 4) `scripts/security/check_network_matrix.py`

- Extended runtime allow/deny checks to show stricter segment isolation:
  - deny `dashboard -> grafana:3000`
  - deny `dashboard -> keycloak:8080`

### 5) ADR updates

- `ADR-013` marked as superseded.
- `ADR-017` expanded with mandatory "Socketless Edge Routing" decision and ADR-013 supersession.

## Test Evidence

### A) Compose validation

Command:
```bash
export API_KEY_SECRET='test-api-key'
docker compose config --quiet
```
Result: **PASS** (exit code 0)

### B) Security posture positive

Command:
```bash
export API_KEY_SECRET='test-api-key'
python3 scripts/security/check_security_posture.py
```
Result: **PASS**

Output:
```text
Security checks passed.
```

### C) Security posture negative proof (must fail on docker provider/socket)

Command:
```bash
export API_KEY_SECRET='test-api-key'
tmp="$(mktemp /tmp/fhirbridge-insecure-compose.XXXXXX.yml)"
python3 - "$tmp" <<'PY'
from pathlib import Path
import sys

source = Path("docker-compose.yml").read_text(encoding="utf-8")
source = source.replace(
    "      - --providers.file.filename=/etc/traefik/dynamic.yml",
    "      - --providers.docker=true\n      - --providers.file.filename=/etc/traefik/dynamic.yml",
)
source = source.replace(
    "      - ./certs:/etc/traefik/certs:ro",
    "      - /var/run/docker.sock:/var/run/docker.sock:ro\n      - ./certs:/etc/traefik/certs:ro",
)
Path(sys.argv[1]).write_text(source, encoding="utf-8")
PY
export SECURITY_COMPOSE_FILE="$tmp"
python3 scripts/security/check_security_posture.py
unset SECURITY_COMPOSE_FILE
rm -f "$tmp"
```
Result: **PASS (expected fail behavior confirmed)**

Output:
```text
Security checks failed:
- traefik docker provider is enabled; socketless mode requires file provider only
- traefik still mounts docker.sock
```

### D) Runtime smoke for route reachability

Command:
```bash
# TLS-verified smoke via root CA
# URLs checked: dashboard, keycloak, grafana
```
Result: **PASS**

Output:
```text
https://dashboard.docker.localhost -> 403
https://keycloak.docker.localhost -> 302
https://grafana.docker.localhost -> 302
```

Interpretation:
- Dashboard reachable and protected by auth challenge.
- Keycloak and Grafana route endpoints reachable.

### E) OIDC E2E with TLS verify=true

Command:
```bash
export OIDC_E2E_USERNAME='demo-clinician-a'
export OIDC_E2E_PASSWORD='<demo-password>'
export OIDC_VERIFY_TLS='true'
export OIDC_ALLOW_INSECURE_DEV='false'
python3 scripts/security/oidc_e2e.py
```
Result: **PASS**

Output:
```text
OIDC TLS mode: verify=true; ca_bundle=<project-root>\certs\rootCA.pem
[PASS] Missing-header request is challenged by oauth2-proxy
[PASS] Forged headers do not bypass oauth2-proxy
[PASS] Successful OIDC flow completed without callback 500/403 regression
OIDC E2E checks passed.
```

### F) Network matrix runtime checks

Command:
```bash
export API_KEY_SECRET='test-api-key'
python3 scripts/security/check_network_matrix.py
```
Result: **PASS**

Output:
```text
[PASS] dashboard -> prometheus:9090 expected=allow (tcp=open, http=ok)
[PASS] dashboard -> rabbitmq:5672 expected=deny (tcp=closed)
[PASS] dashboard -> postgres:5432 expected=deny (tcp=closed)
[PASS] dashboard -> jaeger:16686 expected=deny (tcp=closed)
[PASS] dashboard -> grafana:3000 expected=deny (tcp=closed)
[PASS] dashboard -> keycloak:8080 expected=deny (tcp=closed)
[PASS] ingestion-gateway -> rabbitmq:5672 expected=allow (tcp=open)
Runtime network matrix validation passed.
```

## Residual Risks

1. Route lifecycle is now explicit (file-driven) and no longer auto-discovered.
   - Mitigation: static reviewable config + posture checks.
   - Reference: ADR-017.

2. Local dev still uses Keycloak `start-dev` (not related to socketless edge, but still tracked).
   - Mitigation: bounded exception governance.
   - Reference: ADR-017 EX-017-DEV-02.







