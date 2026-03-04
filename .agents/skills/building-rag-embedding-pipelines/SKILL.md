---
name: building-rag-embedding-pipelines
description: Provides best practices for secure chunking and embedding of medical guidelines and FHIR JSON profiles using local embedding models. Use when the agent needs to prepare medical text or FHIR data for vector ingestion.
---

# Building RAG Embedding Pipelines

You are the Antigravity embedding pipeline specialist. Your goal is to guide the agent in building robust, medically-aware chunking and embedding pipelines for the Vector Engine.

## 1. Local Embedding Models

- **Standard**: Always use local, datenschutzkonforme (privacy-compliant) models to prevent PHI leakage.
- **Recommended Model**: `BAAI/bge-m3` (multilingual, strong in German and English medical contexts, supports dense/sparse vectors).
- **Execution**: Run via local inference (e.g., HuggingFace Inference Endpoints locally, or `vLLM`). Never send data to OpenAI/Cohere for embeddings.

## 2. Medical Text Chunking

Standard text splitters (like recursive character splitting) often break clinical context by splitting in the middle of a diagnosis or medication list.

- **Rule**: Implement semantic chunking that respects medical boundaries.
- **Boundaries to respect**:
  - Paragraphs in "Arztbriefe" (Discharge Summaries).
  - Specific FHIR sections or blocks.
  - Markdown headers (using `MarkdownHeaderTextSplitter` if the source is markdown).
- **Overlap**: Use a meaningful overlap (e.g., 100-200 tokens) to ensure context consistency between chunks.

## 3. FHIR JSON Embedding & Metadata Payload

When embedding FHIR resources, the raw JSON can be token-heavy and confusing for standard embedding models.

- **Extract Text First**: Convert the core clinical meaning of the FHIR object into a natural language string before embedding.
- **Store Original as Payload**: Keep the rich structured data (the JSON itself) and specific metadata markers (like `resourceType`, `patientId`, `profitcenter_id`) strictly inside the Vector DB's payload (Qdrant).
- **Format Standard**:

  ```python
  payload = {
      "patient_id": fhir_resource.get("subject", {}).get("reference", "").replace("Patient/", ""),
      "resource_type": fhir_resource.get("resourceType"),
      "profitcenter_id": current_profitcenter,
      "source_text": extracted_text,
      "raw_fhir": json.dumps(fhir_resource)
  }
  ```

## 4. Error Handling

- Chunks that exceed the maximum token limit of the embedding model must be explicitly caught, logged, and sub-chunked, never silently truncated.
