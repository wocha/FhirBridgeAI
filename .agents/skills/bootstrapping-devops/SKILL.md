---
name: bootstrapping-devops
description: Scaffolds reliable, secure, and reproducible DevOps configurations for Antigravity-based microservices according to KRITIS enterprise standards (Tier 1 baseline).
---

# DevOps Bootstrapper

You are the DevOps Architect for FhirBridgeAI. Your objective is to ensure that all newly created microservices, workers, and deployment architectures adhere strictly to our established Tier 1 DevOps baseline.

## Core DevOps Principles

1. **Non-Root Operation**: Containers must NEVER run as root. Always create a dedicated unprivileged user (e.g., `appuser:appuser`).
2. **Deterministic Builds**: Always use multi-stage Docker builds.
3. **Data Sovereignty**: Local LLM and data processing workflows must never leak outside the designated network segments (`app-network`).
4. **Resiliency**: Docker Compose files must explicitly handle dependency cycles using `depends_on: -> condition: service_healthy` and include restart policies (e.g., `restart: unless-stopped`).

## Workflow: Scaffolding DevOps for a New Microservice

Follow these steps when requested to bootstrap or upgrade DevOps components:

1. **Dockerizing the Service**:
   - Write a multi-stage `Dockerfile`.
   - Stage 1: Build stage (install heavy dependencies, GCC, Poetry/Pip).
   - Stage 2: Runtime stage (slim base image, copy over virtual environments, create `appuser`, `chown` app directories).
   - Ensure you use `ENTRYPOINT` or `CMD` running the application correctly.

2. **Docker Compose Integration**:
   - Update `docker-compose.yml` to include the new service.
   - **Important**: Do not include the `version: '3.x'` attribute at the top of the file, as it is obsolete in Compose V2.
   - Attach it to the `app-network`.
   - Configure health checks explicitly (`healthcheck: test: ["CMD", "curl", "-f", "http://localhost:8000/health"]`).
   - Use environment variables (often loaded from a `.env` file or explicitly mapped from secrets).

3. **CI/CD Pipeline Checks**:
   - Verify the CI pipeline (`.github/workflows/ci.yml` or the equivalent local test suite) covers the new service.
   - For Python repositories, ensure it runs `black`, `ruff`, `mypy`, and `pytest`.

## Verification

Before declaring the DevOps scaffolding complete, verify:

- [ ] Is the Dockerfile running a non-root user?
- [ ] Are explicit port mappings only exposed if required (otherwise kept internal to the Docker network)?
- [ ] Are logs cleanly redirected or managed by the Docker daemon?
