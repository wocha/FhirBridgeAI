from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


def approximate_token_count(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


class SemanticChunk(BaseModel):
    chunk_type: str
    source_section: str
    semantic_boundary_reason: str
    token_count: int
    document_version: int
    tenant_scope: str
    aggregate_version: int
    chunk_index: int
    content: str


def _derive_chunk_type(section_title: str) -> str:
    lowered = section_title.lower()
    if "diagnos" in lowered or "befund" in lowered:
        return "clinical_finding"
    if "medik" in lowered:
        return "medication"
    if "labor" in lowered or "lab" in lowered:
        return "laboratory"
    return "narrative"


def split_semantic_chunks(
    *,
    text: str,
    tenant_scope: str,
    document_version: int,
    aggregate_version: int,
    max_tokens: int = 220,
    overlap_tokens: int = 40,
) -> list[SemanticChunk]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")

    sections: list[tuple[str, str]] = []
    current_title = "document"
    current_lines: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            current_lines.append("")
            continue
        if line.startswith("#") or line.endswith(":"):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
                current_lines = []
            current_title = line.strip("# ").rstrip(":").strip() or "document"
            continue
        current_lines.append(raw_line)
    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    chunks: list[SemanticChunk] = []
    chunk_index = 0
    overlap_buffer = ""

    for section_title, body in sections:
        if not body:
            continue
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", body.replace("\n", " ").strip())
            if sentence.strip()
        ]
        current_parts: list[str] = [overlap_buffer] if overlap_buffer else []
        current_reason = "section_boundary"
        for sentence in sentences:
            candidate = " ".join(part for part in current_parts + [sentence] if part).strip()
            if candidate and approximate_token_count(candidate) > max_tokens and current_parts:
                content = " ".join(part for part in current_parts if part).strip()
                chunks.append(
                    SemanticChunk(
                        chunk_type=_derive_chunk_type(section_title),
                        source_section=section_title,
                        semantic_boundary_reason=current_reason,
                        token_count=approximate_token_count(content),
                        document_version=document_version,
                        tenant_scope=tenant_scope,
                        aggregate_version=aggregate_version,
                        chunk_index=chunk_index,
                        content=content,
                    )
                )
                chunk_index += 1
                overlap_buffer = ""
                if overlap_tokens > 0:
                    prior_sentences = content.split(". ")
                    carry = prior_sentences[-1].strip()
                    if carry and approximate_token_count(carry) <= overlap_tokens:
                        overlap_buffer = carry
                current_parts = [overlap_buffer] if overlap_buffer else []
                current_reason = "token_budget_sentence_boundary"
            current_parts.append(sentence)

        content = " ".join(part for part in current_parts if part).strip()
        if content:
            chunks.append(
                SemanticChunk(
                    chunk_type=_derive_chunk_type(section_title),
                    source_section=section_title,
                    semantic_boundary_reason=current_reason,
                    token_count=approximate_token_count(content),
                    document_version=document_version,
                    tenant_scope=tenant_scope,
                    aggregate_version=aggregate_version,
                    chunk_index=chunk_index,
                    content=content,
                )
            )
            chunk_index += 1
            overlap_buffer = ""

    return chunks


def build_qdrant_payload(chunk: SemanticChunk) -> dict[str, Any]:
    return {
        "chunk_type": chunk.chunk_type,
        "source_section": chunk.source_section,
        "semantic_boundary_reason": chunk.semantic_boundary_reason,
        "token_count": chunk.token_count,
        "document_version": chunk.document_version,
        "tenant_scope": chunk.tenant_scope,
        "aggregate_version": chunk.aggregate_version,
        "content": chunk.content,
    }


def enforce_tenant_filter(filter_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not filter_payload or "tenant_scope" not in filter_payload:
        raise ValueError("Qdrant queries must include an explicit tenant_scope filter")
    return filter_payload
