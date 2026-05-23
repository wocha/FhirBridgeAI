# FhirBridgeAI

FhirBridgeAI is a methodology-focused prototype for sovereign AI document processing in regulated healthcare environments.

> **Status**
>
> Active prototype, methodology-focused, predecessor to EigenState.
> **NOT production-ready.**

## What This Project Shows

FhirBridgeAI is best read as an architectural and engineering-methodology repository, not as a turnkey product. It demonstrates:

- Architecture patterns for sovereign AI processing in regulated healthcare contexts.
- A 25-ADR decision record set documenting privacy, inference, messaging, storage, observability, and security trade-offs, with additional review and legacy ADR material in `docs/adr` and `docs/architecture`.
- A Zero-Trust-oriented approach where LLM inference is intended to run locally or inside a controlled sovereign perimeter.
- ISiK/FHIR R4-native Pydantic models for structured validation of healthcare payloads.
- Transactional Outbox Pattern usage for reliable worker-to-broker publication.
- Comprehensive security tooling and documentation, including threat modeling, control mapping, runtime guardrails, and security evidence notes.

## What This Project Is Not

FhirBridgeAI is not:

- Production-ready software.
- Fully reproducible from a fresh clone without setup effort.
- Currently runnable with minimal dependencies.
- A certified medical device, clinical decision support system, or compliant hospital integration product.
- Evidence that all intended local AI infrastructure is wired into the current default Compose stack.

## Current Limitations

- The local LLM service in `docker-compose.yml` is currently commented out. The `llm-worker` expects an `OLLAMA_URL`, but the default Compose file does not currently start an active Ollama or vLLM service.
- The Compose file contains a commented vLLM block that refers to `INFERENCE_BASE_URL`, while the current Python LLM client uses `OLLAMA_URL` as the base URL and `INFERENCE_ENGINE=vllm` to switch endpoint style. Reviewers should verify this before relying on the vLLM path.
- Fresh-clone test reproducibility is not guaranteed. The repository expects local certificates, non-placeholder secrets, service-specific environment variables, and in some paths GPU-capable local inference infrastructure.
- Active development branches diverge. This repository should be understood as a public-release prototype snapshot and a predecessor to EigenState, not as the canonical live architecture.
- Several environment variables are referenced by code or scripts but are not represented in `.env.example`. Some are optional tunables, direct-run settings, or test/security-script settings:
  - Runtime and tuning: `LLM_MODEL`, `INFERENCE_ENGINE`, `INTERNAL_AUTH_CONTEXT_TTL_SECONDS`, `BROKER_RETRY_INITIAL_DELAY_MS`, `BROKER_RETRY_MAX_DELAY_MS`, `MINIO_CA_BUNDLE_PATH`, `FHIR_SERVER_CA_BUNDLE_PATH`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `PHI_STRICT_MODE`.
  - Dashboard direct-run settings: `PROMETHEUS_TIMEOUT_SECONDS`, `DASHBOARD_API_TIMEOUT_SECONDS`, `DASHBOARD_API_BASE_URL`, `DASHBOARD_API_CA_BUNDLE_PATH`, `DASHBOARD_REQUIRED_PROXY_HEADER`.
  - Test and security-script settings: `TEST_API_KEY`, `TEST_DATABASE_URL`, `SECURITY_COMPOSE_FILE`, `OIDC_BASE_URL`, `OIDC_DASHBOARD_HOST`, `OIDC_KEYCLOAK_HOST`, `OIDC_E2E_USERNAME`, `OIDC_E2E_PASSWORD`, `OIDC_VERIFY_TLS`, `OIDC_ALLOW_INSECURE_DEV`, `OIDC_E2E_TIMEOUT`, `OIDC_CA_BUNDLE`.

## Setup For Interested Reviewers

This setup is for review and local exploration. It is not a production deployment guide.

### Prerequisites

- Docker and Docker Compose.
- Python 3.12 if running tests, scripts, or modules directly.
- Local TLS material under `certs/` for the current Compose topology.
- A populated `.env` derived from `.env.example`. The example file contains demo values so Compose can render, but they are not production or service-start secrets.
- A local LLM runtime if exercising the LLM worker path, for example Ollama with a compatible model such as `mistral-nemo`, or a verified vLLM-compatible endpoint.

### Environment Variables

Start with `.env.example`:

```bash
cp .env.example .env
docker compose config --quiet
```

That render check should pass on a fresh checkout. The values in `.env.example` are deliberately local demo values; before starting the full service graph, replace at least:

- Core platform: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`, `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS`, `RABBITMQ_URL`.
- Object storage: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_URL`, and the `MINIO_*_BUCKET` names if your environment uses different buckets.
- Internal auth: `INTERNAL_AUTH_CONTEXT_SECRET`.
- LLM runtime: `OLLAMA_URL`.
- FHIR export path: `FHIR_SERVER_URL`, `FHIR_AUTH_BEARER`. The runtime exporter enforces HTTPS and rejects localhost targets.
- Qdrant/RAG path: `QDRANT_URL`, `QDRANT_COLLECTION`, `QDRANT_READ_API_KEY`, `QDRANT_WRITE_API_KEY` if that path is exercised.
- Observability and auth services: Grafana, Keycloak, and OAuth2 Proxy variables shown in `.env.example`, especially OAuth2 client and cookie secrets.

For direct script execution, dashboard-only runs, OIDC smoke tests, or vLLM experiments, also review the "Current Limitations" list above.

### Reviewer Test Smoke

For reviewers wanting to verify the test setup:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -m smoke -v
```

Expected: 59 tests pass in under 30 seconds. The smoke marker covers fast, service-free checks for configuration guardrails, auth token exchange, FHIR/ISiK models, Qdrant policy guards, semantic chunking, read-model gating, database URL/runtime helpers, failure routing, and retired legacy path blockade.

### Local LLM Integration

The intended design is local or sovereign-perimeter inference. In the current repo state, that intent needs explicit setup:

- Host-managed Ollama: run Ollama outside Compose, pull the model, and set `OLLAMA_URL` to the reachable host endpoint for containers.
- Compose-managed Ollama: uncomment and validate the commented `ollama` service in `docker-compose.yml`, then set `OLLAMA_URL=http://ollama:11434`.
- vLLM: uncomment and validate the commented `vllm` block, set `INFERENCE_ENGINE=vllm`, and ensure the Python client base URL is configured through `OLLAMA_URL` unless the code is updated to honor a separate `INFERENCE_BASE_URL`.

## Architecture Overview

At a high level, FhirBridgeAI uses a queue-driven worker architecture:

- An ingestion gateway accepts document-processing requests.
- RabbitMQ coordinates asynchronous worker execution.
- PostgreSQL stores state and supports transactional outbox behavior.
- MinIO is used for claim-check style object storage of larger artifacts.
- Local LLM inference is the intended reasoning path for extraction and structuring, but it is not active in the default Compose stack until configured.
- Security and observability components include Keycloak, OAuth2 Proxy, Traefik, Prometheus, Grafana, and Jaeger.

See `docs/architecture/` for architecture ADRs and `docs/adr/` for the main decision log.

## Repository Structure

- `src/fhirbridge/core/` - configuration, database access, messaging, LLM client, storage, telemetry, auth, and dispatcher primitives.
- `src/fhirbridge/models/` - ISiK/FHIR-oriented Pydantic models and clinical data structures.
- `src/fhirbridge/workers/` - OCR, LLM, FHIR export, and outbox worker entry points.
- `src/fhirbridge/ingestion/` - ingestion API surface.
- `src/fhirbridge/privacy/` - PHI pseudonymization and privacy utilities.
- `dashboard/` - Streamlit dashboard prototype.
- `deploy/` - local deployment support files for routing, auth, and service bootstrap.
- `docs/adr/` - main architecture decision records.
- `docs/architecture/` - architecture notes and earlier ADR material.
- `docs/security/` - threat model, control mapping, hardening notes, and audit evidence.
- `docs/runbooks/` - operational runbooks and validation notes.
- `tests/` - unit, contract, architecture guard, and runtime-harness tests.

## Methodology

The repository is primarily valuable as a record of engineering method: ADR-first design, explicit privacy/security trade-offs, local-inference constraints, queue-driven decomposition, and repeatable review artifacts for regulated healthcare AI systems.

FhirBridgeAI predates EigenState. The design lessons documented here inform the later EigenState direction, but this repository should not be interpreted as EigenState's current implementation.

## License

This project is released under the MIT License. See `LICENSE`.

## AI Usage Disclosure

This repository includes AI-assisted design, documentation, and implementation work. See `AI-USAGE.md` for artifact-level disclosure estimates.
