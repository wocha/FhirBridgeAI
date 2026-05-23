# ADR-020: Semantic Chunking and Version-Gated Clinical Reads

## Status

Accepted

## Context

Clinical retrieval and read models must not expose stale or byte-split content to medical users.

## Decision

1. Chunk by section and sentence boundaries with explicit `semantic_boundary_reason`.
2. Persist `tenant_scope`, `document_version`, and `aggregate_version` per chunk.
3. Gate frontend visibility on `required_version <= visible_version`.
4. Reject vector retrieval requests without explicit tenant filter.

## Consequences

- Chunk metadata becomes clinically explainable.
- Read-your-own-writes semantics are enforceable in the UI.
- Qdrant runtime rollout still requires separate operational evidence.
