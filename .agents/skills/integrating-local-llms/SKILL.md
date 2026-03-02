---
name: integrating-local-llms
description: Sets the architectural standard for communicating with Ollama and Mistral NeMo locally. Use when writing "Right Brain" logic, forcing structured outputs from local LLMs, or implementing retry loops for validation errors.
---

# Local LLM Integrator (Mistral / Ollama)

You are the AI Systems Engineer for FhirBridgeAI. Your goal is to write robust Python integration code for local, air-gapped LLMs via Ollama, specifically focusing on the Mistral NeMo 12B model.

## Core Architecture Principles

1. **No Cloud APIs**: Never use OpenAI, Anthropic, or external providers in the code unless explicitly mocking data. The system must remain KRITIS compliant.
2. **Structured Outputs are Mandatory**: Local models easily hallucinate JSON structures. You must use Ollama's native `format="json"` combined with strict prompt engineering and Pydantic validation.
3. **The Validation Loop (Self-Correction)**: Implemented in `scripts/llm_retry_client.py`. On schema mismatch, the error is fed back to the model for self-correction (up to `max_retries` attempts with exponential backoff).
4. **Deterministic Lookup over Generation**: If the task involves mapping text to ICD-10-GM codes, DO NOT let the LLM guess the code. Instruct the LLM to extract the *raw symptom/diagnosis string*, and implement Python logic to search an external dataset/catalog for the code.

## Canonical Import

All skills that need LLM interaction **MUST** use the canonical retry client:

```python
from integrating_local_llms.scripts.llm_retry_client import (
    LlmRetryClient,
    LlmConfig,
    LlmValidationError,
    LlmConnectionError,
)

# Default config reads from env vars OLLAMA_URL and LLM_MODEL
client = LlmRetryClient()

# Or override explicitly — every parameter is typed and documented
client = LlmRetryClient(LlmConfig(
    temperature=0.3,          # Higher for creative text generation
    max_retries=5,            # More retries for complex schemas
    max_tokens=4096,          # Longer outputs for discharge summaries
))

result = client.generate_structured(
    prompt="Erstelle einen OP-Bericht für ...",
    schema=SurgeryReport,
    system_context="Patient: Max Mustermann, geb. 15.05.1980",
)
```

## Workflow: Scaffolding an LLM Pipeline

1. **Define the Schema**: Use the `generating-fhir-models` skill to create the target Pydantic schema first.
2. **Set the Context Strategy**: If dealing with large OCR texts, design a chunking strategy (e.g., 2000 tokens per chunk) before passing it to Ollama to preserve context limits.
3. **Implement the Client**: Use `LlmRetryClient` (see above). For advanced use-cases, see `scripts/llm_retry_client.py` for the full API.
4. **Configure Parameters**: Justify all hyper-parameters via `LlmConfig` fields. No magic numbers!

## Error Handling

| Error Class | When Raised | Contains |
|---|---|---|
| `LlmValidationError` | Schema validation fails after all retries | `last_raw_output`, `validation_errors` |
| `LlmConnectionError` | Ollama unreachable or HTTP error after backoff | `attempts` count |

## Reference

For implementation details, see [llm_retry_client.py](scripts/llm_retry_client.py).
