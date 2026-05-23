# ADR 0001: Local LLMs vs Cloud APIs for Medical Document Processing

## Status

Accepted

## Context

The FhirBridgeAI system processes highly sensitive medical documents, including discharge summaries, lab results, and diagnostic imaging texts. The goal is to perform sophisticated NLP tasks like OCR validation, medical entity extraction, and transformation of unstructured text into structured FHIR constraints.
A key architectural decision is whether to utilize managed Cloud APIs (e.g., OpenAI's GPT-4, Google Cloud Vertex AI) or host inference via localized Large Language Models (LLMs) (e.g., Mistral-NeMo, Llama 3) via an orchestration framework like Ollama.

The primary operational constraint stems from deploying in a KRITIS (Kritische Infrastruktur - Critical Infrastructure) environment, typical in German healthcare (e.g., a regional demo clinic). Such environments mandate stringent data sovereignty and GDPR compliance restrictions, strictly limiting or forbidding the transmission of Protected Health Information (PHI) to external, third-party cloud infrastructure.

## Decision

We will exclusively use **Local LLMs (e.g., Mistral-NeMo) hosted within the internal network perimeter** rather than utilizing public Cloud APIs. The local LLM will be interfaced using Ollama (or a similar local orchestration tool) with endpoints only available via internal networking (e.g., `http://host.docker.internal:11434` or a Kubernetes internal service).

## Rationale

1. **Data Sovereignty and GDPR Compliance:** By processing all data locally, no PHI leaves the hospital's secured intranet. This guarantees full compliance with KRITIS standards and European GDPR regulations regarding highly sensitive health data, preventing any accidental leaks to third-party providers.
2. **Air-gapped Capability:** The local infrastructure can operate in a fully air-gapped network state. Cloud APIs require constant outbound internet access, which poses an unacceptable risk in deeply secured clinic networks.
3. **Predictable Costs:** Running inference locally on fixed hardware (such as dedicated GPU servers) converts variable OPEX costs (API tokens) into predictable CAPEX. With high-volume data streams (e.g., processing thousands of HL7/PDF documents), API costs would rapidly become exorbitant.
4. **Latency and Availability:** A localized model provides deterministic, low-latency responses not dependent on public internet routing or cloud provider rate limits, improving system reliability for background workers.
5. **Model Determinism and Fine-tuning:** We retain full control over the model weights and versions. A local model won't suddenly deprecate or subtly change behavior (model drift), which is crucial for deterministic clinical mappings.

## Consequences

### Positive

* Absolute data privacy; aligns perfectly with KRITIS mandates.
* No recurring per-token inference costs.
* Robust offline capability.
* No rate limits from third-party services.

### Negative

* **Hardware Requirements:** Requires significant upfront investment in GPU-enabled infrastructure (e.g., NVIDIA A100/H100 or consumer-grade equivalents with high VRAM) to support the desired concurrency and latency.
* **Maintenance Overhead:** The DevOps burden is higher. We must manage model checkpoints, configure orchestration runtimes (Ollama/vLLM), monitor VRAM usage, and deal with GPU driver compatibilities.
* **Accuracy Trade-offs:** Smaller, parameter-constrained open-weights models (like Mistral-NeMo 12B) might fall slightly short of the bleeding-edge qualitative reasoning found in frontier cloud models (like GPT-4o). We compensate through strict prompting (RAG, few-shot) and targeted finetuning, taking advantage of open weights.
