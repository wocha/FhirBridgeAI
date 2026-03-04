# ADR 007: Cognitive Resilience with Tenacity & Strict Feedback Loops

## Status

Accepted

## Context

When interacting with local, air-gapped LLMs (e.g., Mistral NeMo 12B via Ollama), we rely heavily on strict structured output guarantees using Pydantic schemas. However, local models are prone to hallucinating formats or violating complex JSON schemas.

Historically, the `llm_worker.py` captured Pydantic validation errors (`LlmValidationError`) and immediately marked the job as `FAILED` in the database, resulting in a fragile ingestion pipeline where minor syntax hallucinations caused complete document extraction failures. A naive `for`-loop retry was implemented but lacked robust backoff and proper context injection for the LLM.

## Decision

We establish **Tenacity** (`AsyncRetrying`) as the absolute Enterprise-Standard for all LLM interaction loops within the FhirBridgeAI architecture.

### 1. Robust Exponential Backoff

All LLM generation functions MUST wrap their execution in a Tenacity `async for attempt in AsyncRetrying(...)` block, configured with:

* `stop=stop_after_attempt(max_retries)` (default: 3)
* `wait=wait_exponential(...)`
* `reraise=True`: To ensure that if the LLM cannot heal itself within the allotted attempts, the `LlmValidationError` natively bubbles up to the caller (e.g., the RabbitMQ worker), which then explicitly routes the payload to the Dead-Letter Queue (`llm_dlq`) and sets the job status to `FAILED`.
* Observability hooks (`before_sleep_log`) to log retry metrics.

### 2. Strict Self-Correction Feedback Loop

When a `ValidationError` occurs, we do not simply ask the model to "try again". We must inject maximum context so the "Right Brain" reasoning engine can spot its mistake. The feedback prompt appended to the retried request MUST contain:

1. The explicit string representation of the `ValidationError` (what went wrong structurally).
2. The exact **raw hallucinated JSON output** (what the model actually generated).
3. The explicit instruction: *"Fix this JSON error."*

## Consequences

* **Positive:** Massive reduction in fragility. The local model is given the mechanistic capability to act as an agent and self-refine its output based on deterministic Python errors, significantly increasing our extraction yield without manual intervention.
* **Positive:** Unified telemetry. Because `reraise=True` is used, exhaustion of attempts perfectly aligns with our standard async worker error catching, natively falling into our DLQ architecture without custom status-handling hacks.
* **Negative:** Increased inference latency on broken documents (up to 3 inference passes required to fail). This is an acceptable trade-off for higher automation rates in Medical OCR extraction.
