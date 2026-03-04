# Architecture Zones Registry

Central lookup for the 7 Architecture Zones defined in our Enterprise Non-Functional Requirements (NFRs). Every skill and component must clearly operate within and be aware of these zones.

## The 7 Zones

| Zone | Name | Description | Example Components |
|---|---|---|---|
| `Z1` | Network | Defines boundaries, ingress/egress, API gateways, and routing layers. | Traefik, Load Balancers, Reverse Proxies |
| `Z2` | Identity | Authentication, Authorization, RBAC, and Identity Provider integrations. | JWT Tokens, Keycloak, Zero-Trust checks |
| `Z3` | Data Flow | Asynchronous messaging, event-driven architectures, queues, and streams. | RabbitMQ, Kafka, DLQs (Dead-Letter-Queues) |
| `Z4` | Resilience | Strategies and patterns for fault tolerance, retries, idempotency, and state recovery. | Circuit Breakers, Retry Loops, Idempotent APIs |
| `Z5` | Observability | Distributed tracing, logging, metrics, and monitoring of system health. | OpenTelemetry, Prometheus, Trace-IDs |
| `Z6` | Domain | The core business logic, medical extraction models, FHIR mapping, and orchestrators. | Local LLMs (Mistral), Synthea Generators, KDL Parsers |
| `Z7` | Infrastructure | Underlying storage, vector engines, databases, and compute nodes. | Qdrant, PostgreSQL, SQLite, MinIO (S3) |

## Usage

Skills must declare which zone(s) they primarily effect to enforce strict Tier-1 enterprise boundaries and prevent "Stateful Sinner" or "Blind Spots" anti-patterns.
