# FhirBridgeAI

**Active prototype for sovereign AI processing in KRITIS healthcare.**

## Status

This is a methodology-focused active prototype, NOT production-ready.
v0.1.0 demonstrates the methodical architecture work behind sovereign AI
deployments in regulated healthcare environments.

FhirBridgeAI should be read as a public prototype snapshot and architecture
methodology record. It is not a certified clinical system, not a finished
hospital integration product, and not a turnkey deployment guide.

## What This Demonstrates

- **30 Architecture Decision Records** covering transactional outbox,
  async DB runtime, internal token exchange, semantic chunking, evidence
  anchoring, research isolation, and BSI audit ledger preparation
- **Sovereign managed-service architecture** for KRITIS healthcare
  environments: no cloud APIs in the target architecture, local LLM inference,
  controlled service boundaries, and reviewable operational evidence
- **FHIR R4 and ISiK native** modeling with strict validation for structured
  healthcare payloads
- **Transactional outbox with publish fencing** (ADR-019, ADR-025) for
  Postgres/RabbitMQ/MinIO/FHIR consistency, including lease renewal,
  publish-attempt fencing, fail-closed escalation, and reconciliation paths
- **Async DB runtime with controlled migrations** (ADR-022), including
  schema-version checks and no active `create_all()` fallback on runtime paths
- **Internal token exchange** for worker handoffs (ADR-018), so external
  user JWTs are not forwarded into queue payloads or deep worker execution
- **Semantic chunking with version-gated reads** (ADR-020), including
  section/sentence-aware chunk boundaries and read-model visibility guards
- **Live evidence exceptions** for incomplete BSI requirements (ADR-023,
  ADR-024), especially Qdrant tenant-isolation evidence and Keycloak JWKS
  validation evidence
- **BSI audit ledger shadow pipeline preparation** (ADR-026, ADR-029), with
  destination-scoped guardrails and no false immutability claim for inactive
  Kafka-based evidence replication
- **Security tooling and hardening evidence scripts** for posture checks,
  network matrix validation, OIDC evidence capture, architecture guards, and
  hardening reports

## What This Is NOT

- Production-ready
- Fully reproducible without setup work
- Multi-tenant
- A finished product
- A certified medical device or clinical decision support system
- Evidence that all intended live infrastructure has been exercised end to end

## Architecture Overview

FhirBridgeAI uses a queue-driven architecture for sovereign document
processing in regulated healthcare settings. The intended runtime separates
ingestion, asynchronous workers, object storage, structured persistence,
local inference, FHIR export, dashboard review, and security/observability
planes.

At a high level:

- The ingestion boundary validates requests and stores large artifacts through
  a claim-check pattern.
- PostgreSQL persists domain state, read models, schema migration state, and
  transactional outbox records.
- RabbitMQ carries operational worker commands after outbox dispatch.
- MinIO stores evidence, processing artifacts, and PHI-sensitive material in
  separated buckets.
- Local LLM inference is the intended extraction path; cloud LLM APIs are out
  of scope for the sovereign target architecture.
- Keycloak, OAuth2 Proxy, Traefik, Prometheus, Grafana, and Jaeger support the
  authentication, routing, monitoring, and evidence posture of the prototype.
- Qdrant is prepared for semantic retrieval paths, with live evidence
  limitations documented explicitly.

See `docs/architecture/` for architecture background and `docs/adr/` for the
current ADR set. Security posture, control mapping, and evidence notes live in
`docs/security/`; operational repair guidance lives in `docs/runbooks/`.

## Repository Structure

- `src/fhirbridge/core/` - configuration, auth, database runtime, migrations,
  outbox dispatch, RabbitMQ, storage, semantic chunking, Qdrant guards, and
  telemetry primitives
- `src/fhirbridge/ingestion/` - ingestion API boundary and request handling
- `src/fhirbridge/workers/` - OCR, LLM, FHIR export, and outbox worker entry
  points
- `src/fhirbridge/models/` - FHIR R4, ISiK-oriented, and clinical Pydantic
  models
- `src/fhirbridge/privacy/` - pseudonymization and privacy utilities
- `dashboard/` - Streamlit dashboard prototype for review workflows
- `deploy/` - local routing, auth, and service bootstrap support
- `scripts/security/` - security posture and hardening evidence scripts
- `docs/adr/` - architecture decision records
- `docs/architecture/` - architecture notes and earlier decision material
- `docs/security/` - threat model, control mapping, hardening reports, and
  audit evidence
- `docs/runbooks/` - migration, reconciliation, incident, and manual validation
  runbooks
- `tests/` - architecture guards, contract tests, runtime harnesses, and
  focused unit tests

## Setup for Reviewers

This setup is for review and local exploration. It is not a production
deployment guide.

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- 8GB RAM minimum

### Steps

1. `cp .env.example .env`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -e ".[dev]"`
4. Smoke test: `pytest tests/test_architecture_guards.py -v`

### Known Setup Caveats

- Local LLM service (Ollama) must run separately
- HAPI-FHIR (if used) is stateless
- Test reproducibility from fresh clone is not guaranteed for all paths
- Local certificates and non-placeholder secrets may be required for some
  Compose and evidence workflows
- Qdrant and Keycloak live evidence exceptions are documented in ADR-023 and
  ADR-024
- BSI audit-ledger shadow pipeline work is preparation only, not an active
  runtime claim
- See known limitations and residual evidence gaps in individual ADRs

## Methodology

This project applies the MADR-with-AI-Generation-Annex methodology documented
in EigenState (sibling project). ADRs are first-class artifacts; AI assistance
is disclosed per `AI-USAGE.md`.

The repository values explicit decision records, scoped evidence, fail-closed
runtime design, and honest limitation tracking over product-completeness
claims. v0.1.0 is therefore best evaluated as an architecture and engineering
methodology release.

## License

MIT - see `LICENSE`

## AI Usage Disclosure

See `AI-USAGE.md` for per-artifact disclosure of AI assistance levels.
