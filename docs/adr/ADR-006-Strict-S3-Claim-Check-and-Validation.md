# ADR-006: Strict S3 Claim-Check Pattern and Anti-Schema-Evasion

## Status

Accepted

## Context

In our cloud-native, KRITIS-compliant architecture (FhirBridgeAI), we encountered two major architectural anti-patterns during end-to-end testing:

1. **The "Stateful Sinner"**: The Ingestion Gateway was writing temporary files to a local `ephemeral_dir` (`os.makedirs`), creating a stateful bottleneck and violating distributed system principles.
2. **The "Schema Evader"**: When the local LLM (Mistral NeMo) hallucinated during the extraction of FHIR bundles, the strict Pydantic validation (`fhir.resources`) was replaced with lenient dictionary parsing to force a successful pipeline run. This bypassed our strict "Design by Contract" (NFR #5) requirements.

## Decision

We enforce the following Tier-1 architectural standards:

1. **Strict S3 Claim-Check Pattern**:
   - All payloads (e.g., PDFs, large texts) MUST be stored in S3-compatible object storage (MinIO) immediately upon ingestion.
   - Message brokers (RabbitMQ) MUST ONLY transmit the S3 object key (`s3_object_key`) as a reference.
   - Local ephemeral directories for inter-process or inter-container communication are strictly forbidden. Asynchronous operations using `aioboto3` must be used to stream data into memory.

2. **Strict Anti-Schema-Evasion (Design by Contract)**:
   - Pydantic validation (e.g., via `fhir.resources`) is absolute and non-negotiable.
   - If the LLM generates output that fails to validate against the strict schema (and self-correction retries are exhausted), the system MUST NOT downgrade to lenient parsing (like dictionaries).
   - Validation failures MUST result in a caught exception (`LlmValidationError`), and the Job Status MUST be explicitly set to `FAILED`. A failing test with correct architectural behavior is always preferable to a "green" test with compromised data integrity.

## Consequences

- **Positive**: Complete horizontal scalability and statelessness for all workers. NFR #5 (Design by Contract) is mathematically guaranteed. We ensure that no invalid or hallucinated structures ever reach the downstream FHIR servers.
- **Negative**: Increased storage dependency (MinIO must be highly available). Tests will fail more frequently if the LLM hallucinates, requiring better prompt engineering or fine-tuning, rather than pipeline hacks.
