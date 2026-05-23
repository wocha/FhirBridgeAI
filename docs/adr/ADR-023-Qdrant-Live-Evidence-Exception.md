# ADR-023: Qdrant Live Evidence Exception

## Status

Accepted

## Context

Tenant isolation and credential separation for Qdrant are now enforced at the contract and harness level, but this local session does not include a live Qdrant deployment with distinct read/write credentials and auditable query traces. Live isolation evidence therefore remains `nicht nachweisbar`.

## Decision

1. Keep runtime contract enforcement for tenant filters and distinct read/write credentials in code and tests.
2. Mark live Qdrant isolation evidence as a time-boxed exception until a dedicated integration environment is exercised.

## Technical Evidence

- `src/fhirbridge/core/semantic_chunking.py`
- `src/fhirbridge/core/qdrant_security.py`
- `tests/test_qdrant_security.py`

## Time-Boxed Exception

- Exception: Live Qdrant tenant-isolation and credential-scope evidence remains `nicht nachweisbar`.
- Owner: Vector Platform Owner.
- Ablaufdatum: 2026-05-15.
- Exit-Kriterium: Execute a live Qdrant integration suite with distinct read/write API keys, negative tenant tests, and retained audit evidence.
- Technischer Guardrail: Settings require distinct Qdrant read/write keys, queries without tenant filter are rejected, cross-tenant payloads are rejected, and control-mapping remains explicitly marked `nicht nachweisbar` until the live suite is complete.
