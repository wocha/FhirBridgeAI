# FhirBridgeAi

**An air-gapped, zero-trust LLM pipeline framework for the synthetic generation and processing of KRITIS medical data.**

## Overview

FhirBridgeAi is an enterprise-grade, privacy-preserving integration engine designed specifically for Critical Infrastructure (KRITIS) healthcare environments. It enables the secure extraction, structuring, and synthetic generation of highly sensitive Patient Health Information (PHI) without ever relying on external cloud APIs.

By combining local Open-Source Large Language Models (LLMs) with robust asynchronous messaging and strict data contracts, FhirBridgeAi ensures complete data sovereignty and strict compliance with the GDPR (DSGVO) and German hospital regulations.

## Key Features

* **Zero-Trust Architecture:** 100% locally executed LLM inference (no data exfiltration to third-party cloud providers).
* **Asynchronous Microservices:** High-throughput processing powered by persistent, stateful message queues.
* **ISiK & FHIR Native:** Strict validation of all medical data using nested Pydantic models aligned with official ISiK (Informationstechnische Systeme in Krankenhäusern) and FHIR R4 profiles.
* **Synthetic Patient Arc Simulation:** Advanced state-machine orchestration for generating longitudinal, causally linked synthetic patient lifelines (including realistic KDL documents and lab results).

## Architecture

At its core, FhirBridgeAi utilizes a scalable, queue-driven worker architecture:

1. **RabbitMQ:** Acts as the central nervous system, distributing tasks (e.g., OCR processing, semantic FHIR mapping) reliably to worker nodes with robust retry and backoff mechanisms.
2. **Ollama (Mistral NeMo):** Provides the "Right Brain" capabilities. Local, domain-aware LLM instances perform complex medical text reasoning, forced into structured JSON outputs via Pydantic schemas.
3. **PostgreSQL:** Serves as the robust, transactional persistence layer for patient state, event logs, and processed intermediate medical findings.
4. **Worker Fleet:** Python-based services orchestrated via Docker Compose, built with strict typing (PEP 484) and comprehensive error handling.

## Quickstart Guide

To bootstrap the complete local environment, including the message broker, database, and background workers:

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) and Docker Compose
* [Ollama](https://ollama.com/) installed and running locally on your host system.
* Pull the Mistral NeMo model: `ollama pull mistral-nemo`

### Spinning up the Pipeline

1. **Navigate to the project root:**

   ```bash
   cd FhirBridgeAi
   ```

2. **Start the infrastructure and workers:**
   Deploy the RabbitMQ broker, PostgreSQL database, and the AI worker services in detached mode.

   ```bash
   docker-compose up -d
   ```

3. **Verify the deployment:**
   Check the logs to ensure the workers have successfully connected to the MQ and DB.

   ```bash
   docker-compose logs -f
   ```

   The architecture is now actively listening to its queues, ready to receive medical data extraction tasks or synthetic patient generation triggers.

## Development Standard (Antigravity Gold)

This project strictly adheres to the "Antigravity Skill Goldstandard":

* **Python Enterprise:** Strict typings (`mypy`), Pydantic everywhere, and no magic numbers.
* **CI/CD Enforced:** All code is formatted and verified by `black`, `ruff`, and `pytest`.
* **Modular Skill Routing:** Flow logic is cleanly separated from prompt templates and execution delegates.

---
*For detailed architectural decisions regarding data sovereignty, please refer to [`docs/architecture/ADR-001-local-llms-over-cloud-apis.md`](docs/architecture/ADR-001-local-llms-over-cloud-apis.md).*
