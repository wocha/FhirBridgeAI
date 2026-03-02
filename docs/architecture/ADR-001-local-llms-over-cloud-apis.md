# ADR 001: Usage of Local LLMs over Cloud APIs in KRITIS Environments

## Context

The FhirBridgeAi project operates within a highly sensitive healthcare context, specifically targeting environments classified as Critical Infrastructure (KRITIS) in Germany. The core functionality involves processing, analyzing, and structuring highly confidential patient data (incl. diagnoses, laboratory results, nursing logs, and physician letters) into standardized formats (FHIR/ISiK) and KDL-compliant documents.

Historically, cloud-based Large Language Models (LLMs) such as OpenAI's GPT-4 or Anthropic's Claude 3 offer the highest performance for complex natural language reasoning tasks. However, relying on these external cloud services introduces significant challenges regarding data privacy, regulatory compliance (GDPR/DSGVO), and data sovereignty. Any leakage or external transfer of clear-text Patient Health Information (PHI) poses an unacceptable risk in a KRITIS environment.

## Decision

We have decided to **exclusively use locally hosted Open-Source LLMs** (specifically Mistral NeMo running via Ollama on `localhost:11434`) for all text analysis, extraction, and generation tasks, outright rejecting the use of external Cloud APIs (e.g., GPT-4) for processing production or realistic synthetic patient data.

## Rationale

1. **Strict Data Sovereignty (Privacy-Preserving AI):** By keeping the model weights and inference execution entirely within the local secure perimeter (on-premise or within a controlled KRITIS-compliant sovereign cloud), PHI never leaves the physical and logical control of the healthcare provider.
2. **Regulatory Compliance:** It eliminates the complex legal overhead of Data Processing Agreements (AVV - Auftragsverarbeitungsvertrag) with US-based cloud providers and inherently complies with the strictest interpretations of the DSGVO and German hospital laws (Krankenhausgesetz).
3. **Availability & Resilience:** In a KRITIS environment, the system must remain operational even during internet outages or external service degradations. Local LLMs guarantee extreme resilience, as inference relies solely on local compute resources (e.g., local GPUs).
4. **Predictable Costs:** While local infrastructure has upfront and maintenance costs, the variable costs of processing massive volumes of medical data through token-based cloud pricing are avoided.
5. **Security by Design:** We prevent accidental data leakage through developer error or misconfiguration by physically not integrating any external API clients into the worker services.

## Consequences

### Positive

* Complete adherence to the "Antigravity Skill Gold Standard" for privacy-preserving AI.
* Zero risk of PHI exfiltration to third-party model providers.
* System functions autonomously without internet dependencies.

### Negative / Trade-offs

* **Model Capabilities:** Mistral NeMo, while highly capable, might require more sophisticated prompt engineering and validation logic (retry-loops, strict structured outputs via Pydantic) to match the zero-shot performance of frontier models like GPT-4.
* **Infrastructure Requirements:** Running local LLMs robustly at scale (e.g., for 50,000 parallel events) requires substantial local GPU provisions (or heavy CPU batch processing queues using RabbitMQ).
* **Slower Inference:** Depending on the hardware, token generation speed might be a bottleneck, necessitating a highly asynchronous, queue-driven architecture (already implemented via our RabbitMQ and Postgres setup).

## Status

**Accepted**

## References

* BSI IT-Grundschutz-Kompendium
* DSGVO (General Data Protection Regulation)
* Antigravity Skill Architectures: `integrating-local-llms`, `building-autonomous-dispatchers`
