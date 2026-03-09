# Manual Validation Execution Report (2026-03-09)

## Objective
Execute the end-to-end validation playbook for FhirBridgeAI and collect runtime evidence.

## Executed Checks

### 1) Test Suite
- Command: `PYTHONPATH=src python -m pytest -q`
- Result: `31 passed`

### 2) Zero-Trust Auth Gate (live)
- Probe: unauthenticated `POST /ingest/text`
- Result: `401 Not authenticated`
- Evidence: request executed in ingestion container against live app.

### 3) Positive Path Simulation (live services)
Note: clinical JWT credentials were not available in this session, therefore the positive path was executed via FastAPI dependency override for `require_clinical_role` inside the running ingestion container.

- `POST /ingest/text` -> `202 Accepted`
  - `document_id`: `1a65697a-9f0d-476b-9cce-0126697b6704`
  - `job_id`: `559`
- `POST /ingest/pdf` -> `202 Accepted`
  - `document_id`: `01c5ca4c-a862-47ff-bbb6-648b9c4fdc6f`
  - `job_id`: `560`

### 4) Queue and Worker Evidence
- RabbitMQ queue snapshot:
  - `llm_extraction_queue`: `messages=1`, `messages_unacknowledged=1`
  - `dead_letter_queue`: `messages=1`
- OCR worker:
  - picked up job `560`
  - failed with `ValueError` (no PHI in log line)
- LLM worker:
  - processed job `559`
  - first validation retry occurred
  - forwarded to FHIR export
- FHIR export worker:
  - job `559` failed with `FHIR_EXPORT_UNHANDLED`

### 5) DB State Evidence
- Job `559`: `EXPORT_FAILED`
- Job `560`: `FAILED`
- Error traces are PHI-redacted (`message redacted for PHI safety`).

### 6) PHI-safe Logging Spot Check
Searched recent logs (`ingestion`, `ocr_worker`, `llm_worker`, `fhir_export_worker`) for payload terms (`Mustermann`, `Pneumonie`, `Max`).
- Result: no matches found.

## Conclusion
- Security gate is active (`401` without token).
- End-to-end pipeline mechanics (queueing, worker processing, DB persistence) are verifiable.
- Current runtime reliability gaps remain in OCR and FHIR export paths for the synthetic test inputs.
- PHI redaction behavior in error traces/logging is active in observed failure paths.
