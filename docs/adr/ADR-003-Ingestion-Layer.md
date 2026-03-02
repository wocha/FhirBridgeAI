# ADR-003: Ingestion Layer Architecture

## Status

Accepted

## Context

Currently, the FhirBridgeAi system relies on an SQLite-backed dispatcher for document ingestion, utilizing simple synchronous polling (`dispatch_documents.py`). As the system targets KRITIS-compliant enterprise environments with requirements to handle up to 50,000 parallel events, this approach introduces significant bottlenecks.

A synchronous polling mechanism does not scale horizontally, risks overwhelming the database with concurrent locking, and creates high latency for clients submitting documents. We require an ingestion gateway that can handle bursts of traffic asynchronously, decoupling the receiving layer from the processing workers.

## Decision

We will deploy a dedicated Ingestion Gateway using **FastAPI** as the entry point for all incoming document extractions.

1. **Framework**: FastAPI (Python 3.11/3.12). Selected for its native asynchronous capabilities (`asyncio`), high performance, built-in validation (Pydantic), and automatic OpenAPI documentation.
2. **Event Queueing**: Incoming requests will be immediately published to a RabbitMQ queue via `aio_pika`. The gateway will not wait for processing to complete.
3. **Response**: The gateway will immediately return HTTP `202 Accepted` along with a task or correlation ID, signifying that the document has been successfully queued for processing.
4. **Validation**: Pydantic models will enforce strict validation of incoming requests to reject malformed data early in the pipeline without polluting the queues.

### KRITIS Auth Strategy

To maintain a high-security posture (Tier 1 baseline) without unnecessarily complex initial overhead:

- **API Key Authentication**: The ingestion gateway will mandate an API key passed securely via HTTP headers (e.g., `X-API-Key`).
- **TLS**: In production, traffic to this gateway must be strictly routed over HTTPS (e.g., via Traefik), ensuring API keys and medical data are never transmitted in plaintext.
- **Future Compatibility**: The mechanism is designed to be easily extensible to Mutual TLS (mTLS) or robust Identity Provider integrations (e.g., OAuth2 proxy/Keycloak).

## Consequences

### Positive

- **High Throughput**: Capable of handling bursts of up to 50,000 concurrent events thanks to non-blocking I/O.
- **Decoupling**: The ingestion layer is purely responsible for validation and queueing. Worker failures or scale-downs do not affect the system's ability to accept new jobs.
- **Security**: Hardened entry point for KRITIS environments, validating inputs before they touch internal storage or LLMs.

### Negative

- **Complexity**: Adds a new microservice to the orchestration stack.
- **Asynchronous Flow**: Clients must adapt to an asynchronous response model (`202 Accepted`) and optionally query the state of a job later via webhooks or a separate polling endpoint.
