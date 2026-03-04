---
name: integrating-qdrant-vector-engine
description: Defines the architecture standard for connecting to the Qdrant database and implementing RAG retrieval in the LLM-worker. Use when writing code that queries or writes to Qdrant.
---

# Integrating Qdrant Vector Engine

You are the Antigravity Qdrant integration specialist. Your goal is to enforce asynchronous, typed, and robust Vector DB operations within the system.

## 1. Async Qdrant Client

- **Standard**: Always use the asynchronous Python client (`qdrant_client.AsyncQdrantClient`).
- **Initialization**:

  ```python
  from qdrant_client import AsyncQdrantClient
  
  # Inject credentials via Environment Variables, never hardcode.
  client = AsyncQdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
  ```

## 2. Robust CRUD Operations

- **Upserting (Writing)**: Use batch processing for ingesting multiple vectors.
- **Collections**: Ensure collections are created safely (check if exists first `client.collection_exists()`). Define the correct vector size matching the embedding model (e.g., 1024 for `bge-m3`).

## 3. Strict Payload Filtering

Qdrant excels at filtering metadata before performing vector similarity search. This is crucial for FHIR.

- **Rule**: Never retrieve vectors strictly by similarity without applying contextual filters (e.g., limit search to specific `patientId` or `resourceType`).
- **Implementation**:

  ```python
  from qdrant_client.http import models

  # Example: Find similar documents for a specific patient
  search_result = await client.search(
      collection_name="clinical_guidelines",
      query_vector=embedded_query,
      query_filter=models.Filter(
          must=[
              models.FieldCondition(
                  key="patient_id",
                  match=models.MatchValue(value="pat-12345")
              )
          ]
      ),
      limit=5
  )
  ```

## 4. Integration in LLM Worker

- The retrieval call MUST happen asynchronously before the Mistral NeMo LLM call.
- The retrieved `source_text` from the payload should be injected cleanly into the `context` section of the LLM prompt.
- Timeouts: Implement strict timeouts (e.g., `asyncio.wait_for`) on the `client.search` to prevent slow Vector searches from blocking the RabbitMQ worker.
