# ADR-005: S3 Storage & Claim-Check Pattern

## Status

Proposed

## Context

At present, our local components rely on local Docker volumes (`data/inbound` and `data/outbound`) to exchange document payloads. When RabbitMQ messages route work among services, they pass file URLs (e.g., `file:///data/inbound/...`).

In distributed Swarm or Kubernetes clusters, local volume mounts are an anti-pattern because the filesystem state is not inherently shared across nodes. This approach causes file-not-found exceptions when a worker container processes a message referring to a file stored on the local filesystem of a different node.

To fix this architectural flaw and build a robust, scalable system in compliance with Tier 1 Data Architecture, we must separate storage from compute.

## Decision

We will transition to an Object Storage-based approach using **MinIO** (S3-compatible) to implement the **Claim-Check Pattern**.

1. **Storage Layer (Claim-Check)**: All generated KDL documents will be persisted as objects in MinIO instead of local directories.
2. **Metadata Layer & Zero-Trust Security**: Our message queue (RabbitMQ) will no longer hold raw payload data or local file paths. Instead, the payload will contain a **Presigned URL** (valid for a limited time), which the downstream consumers use to retrieve the document safely and ephemerally from any node without needing hardcoded S3 credentials. All underlying MinIO buckets are strictly configured as `private`.
3. **Database Model**: We will introduce a lightweight Pydantic model for a PostgreSQL table `patient_longitudinal_records` to establish a relational track `patient_id` -> `encounter_id` -> `document_id` (MinIO S3 Key). This robustly replaces the in-memory `MockPatient` tracking.

## Consequences

### Positive

- **Stateless Compute**: Complete decoupling of storage from compute nodes. Swarm nodes are entirely stateless.
- **Scalability**: Workers can scale horizontally without worrying about distributed filesystem locks or replication issues.
- **Performance**: Small message queue size, reducing RabbitMQ memory and network overhead significantly (Claim-Check pattern).
- **Durability**: MinIO opens up the possibility for robust long-term archival policies (e.g., tiering to AWS S3 Glacier).

### Negative

- **Infrastructure Footprint**: Adds the `minio` service to our stack.
- **Latency**: Additional network latency per object fetch vs block-level local read.
- **Complexity**: Requires S3 API integration (e.g., via `boto3` or `minio` SDKs) within our Python workers.
