# ADR-002: Inference Engine Strategy

**Status:** Accepted  
**Date:** 2026-03-01  
**Deciders:** AI Infrastructure Team  
**Supersedes:** —  
**Related:** [ADR-001 – Local LLMs over Cloud APIs](../architecture/ADR-001-local-llms-over-cloud-apis.md)

---

## Context

ADR-001 established that FhirBridgeAi exclusively uses **locally hosted LLMs** (Mistral NeMo) to comply with KRITIS data sovereignty regulations. The current inference backend is **Ollama**, which serves models via a REST API on `localhost:11434`.

Ollama works perfectly for single-node development workflows. However, it exhibits a critical architectural bottleneck when scaling to production workloads:

- **Serial Model Loading:** Ollama loads the model into GPU VRAM per-request and processes inference sequentially. When 100+ medical documents arrive simultaneously through RabbitMQ, requests queue behind each other, creating **Thread Starvation** in the `llm-worker` containers.
- **No Continuous Batching:** Each request occupies the full GPU until completion. There is no mechanism to batch multiple pending prompts into a single forward pass, wasting GPU cycles on memory allocation overhead.
- **VRAM Fragmentation:** Ollama's memory management does not optimize KV-cache allocation, leading to premature OOM errors on GPUs with 24 GB+ VRAM that should theoretically handle higher concurrency.

Our current `LlmRetryClient` (in `integrating-local-llms/scripts/llm_retry_client.py`) already uses `httpx` for async HTTP and has a configurable `base_url` (via `OLLAMA_URL` environment variable). The throttle delay in `llm_worker.py` (`LLM_THROTTLE_DELAY = 3s`) is a symptom-level workaround for the underlying serial processing limitation.

**The question:** Which inference engine should replace Ollama for production-grade throughput while remaining fully on-premise and KRITIS-compliant?

---

## Options Evaluated

### Option A: Ollama (Status Quo)

| Aspect | Assessment |
|---|---|
| **Deployment** | Single binary, trivial setup (`ollama run mistral-nemo`) |
| **API** | Proprietary `/api/generate` and `/api/chat` endpoints |
| **Batching** | ❌ None — strictly serial, one request at a time |
| **GPU Utilisation** | Low — model load/unload per session, no KV-cache optimization |
| **Throughput** | ~5–8 req/min on RTX 4090 (24 GB VRAM) for 1200-token outputs |
| **Scalability** | Vertical only — no native multi-GPU or cluster support |
| **Strengths** | Excellent DX for local development, zero config, model registry |
| **Weaknesses** | Thread starvation under concurrent load, no production batching |

**Verdict:** Ideal for development and testing. Insufficient for production workloads with 100+ concurrent documents.

---

### Option B: vLLM (Recommended)

| Aspect | Assessment |
|---|---|
| **Deployment** | Docker container or pip install; requires CUDA-capable GPU |
| **API** | ✅ Fully **OpenAI-compatible** API (`/v1/completions`, `/v1/chat/completions`) |
| **Batching** | ✅ **Continuous Batching** — dynamically groups pending requests into micro-batches |
| **GPU Utilisation** | ✅ **PagedAttention** — allocates KV-cache in non-contiguous pages, eliminating fragmentation and achieving near-100% VRAM utilisation |
| **Throughput** | ~40–80 req/min on RTX 4090 (24 GB VRAM) — **8-10x improvement** over Ollama |
| **Scalability** | Multi-GPU via tensor parallelism; distributed serving via Ray |
| **Strengths** | Production-proven (used by Anyscale, Mistral, Meta); built for throughput |
| **Weaknesses** | Heavier resource footprint, CUDA-only (no CPU fallback), more complex deployment |

**Verdict:** The clear production choice. Continuous batching and PagedAttention directly solve the thread starvation problem. The OpenAI-compatible API means our `LlmRetryClient` requires near-zero code changes.

---

### Option C: llama.cpp Server (llama-server)

| Aspect | Assessment |
|---|---|
| **Deployment** | Compiled binary or Docker; supports CPU, CUDA, Metal, Vulkan |
| **API** | Partial OpenAI-compatible API (`/v1/chat/completions`); some extensions |
| **Batching** | ⚠️ Limited — static slot-based concurrency (`--parallel N`), not true continuous batching |
| **GPU Utilisation** | Good with `--n-gpu-layers` for hybrid CPU+GPU offloading |
| **Throughput** | ~15–25 req/min on RTX 4090 with full GPU offload |
| **Scalability** | Single-node only; no native multi-GPU tensor parallelism |
| **Strengths** | Extremely lightweight (~2 MB binary), CPU+GPU hybrid, excellent for edge/embedded |
| **Weaknesses** | No true continuous batching, no PagedAttention, limited observability |

**Verdict:** Excellent for resource-constrained environments or CPU-heavy deployments. Not suitable for GPU-saturated production workloads where throughput is the primary concern.

---

## Decision

We adopt **vLLM** as the production inference engine for FhirBridgeAi.

### Rationale

1. **Throughput (8-10x improvement):** Continuous Batching allows vLLM to dynamically group incoming requests from RabbitMQ, eliminating the serial bottleneck. This directly addresses the Thread Starvation problem identified in the Context.

2. **GPU Efficiency (PagedAttention):** By managing KV-cache as virtual memory pages, vLLM achieves near-optimal VRAM utilisation. On our target hardware (NVIDIA A100 / RTX 4090 / H100), this translates to significantly higher concurrent request capacity before OOM.

3. **API Compatibility:** vLLM exposes a fully OpenAI-compatible REST API. Our `LlmRetryClient` currently targets Ollama's proprietary endpoints (`/api/generate`, `/api/chat`), but switching to vLLM's `/v1/completions` and `/v1/chat/completions` only requires updating the endpoint construction logic — the request/response schema is a well-documented industry standard.

4. **Production Maturity:** vLLM is battle-tested at scale by Anyscale, Mistral AI, and Meta. It supports quantised models (GPTQ, AWQ, GGUF), tensor parallelism for multi-GPU nodes, and integrates with Prometheus for metrics — aligning with our existing observability stack (ADR-001 references).

5. **Ollama Retained for Dev:** Developers continue using Ollama locally for rapid iteration. The `OLLAMA_URL` / `INFERENCE_BASE_URL` environment variable seamlessly switches between engines.

---

## Consequences

### Changes Required

#### 1. `LlmRetryClient` — Minimal Changes

The client already uses `httpx.AsyncClient` with a configurable `base_url`. The required changes are:

```diff
 class LlmConfig(BaseModel):
     base_url: str = Field(
-        default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
+        default_factory=lambda: os.getenv("INFERENCE_BASE_URL",
+            os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")),
         description="Base URL of the inference API.",
     )

 class LlmRetryClient:
     def __init__(self, config: LlmConfig | None = None) -> None:
         self.config = config or LlmConfig()
-        self._generate_url = self.config.base_url.rstrip("/") + "/api/generate"
-        self._chat_url = self.config.base_url.rstrip("/") + "/api/chat"
+        # Auto-detect engine: vLLM uses /v1/*, Ollama uses /api/*
+        base = self.config.base_url.rstrip("/")
+        if "/v1" in base or os.getenv("INFERENCE_ENGINE") == "vllm":
+            self._generate_url = base + "/v1/completions"
+            self._chat_url = base + "/v1/chat/completions"
+        else:
+            self._generate_url = base + "/api/generate"
+            self._chat_url = base + "/api/chat"
```

The response parsing already handles both `response` (Ollama) and `message.content` (OpenAI/vLLM) formats in `_execute_http_with_backoff`, requiring only minor payload key adjustments (`prompt` → `messages` for the chat completions format).

#### 2. `docker-compose.yml` — New Service Block

A commented-out `vllm` service is added as a production template. Operators uncomment it and remove the `OLLAMA_URL` reference when deploying to GPU-provisioned infrastructure.

#### 3. Environment Variables

| Variable | Dev (Ollama) | Prod (vLLM) |
|---|---|---|
| `INFERENCE_BASE_URL` | `http://127.0.0.1:11434` | `http://vllm:8000` |
| `INFERENCE_ENGINE` | `ollama` (default) | `vllm` |
| `LLM_MODEL` | `mistral-nemo` | `mistralai/Mistral-Nemo-Instruct-2407` |

#### 4. Remove Throttle Workaround

With continuous batching, the `LLM_THROTTLE_DELAY` in `llm_worker.py` is no longer necessary and can be removed for vLLM deployments to achieve maximum throughput.

---

### Positive Consequences

- **8-10x throughput improvement** for batch medical document processing.
- **Eliminates Thread Starvation** — concurrent RabbitMQ consumers can fire requests in parallel.
- **GPU cost efficiency** — fewer GPU-hours required per document batch due to PagedAttention.
- **Future-proof** — vLLM supports multi-GPU tensor parallelism when scaling to A100/H100 clusters.
- **Zero breaking changes** — existing worker code, tests, and domain facades remain functional.

### Negative Consequences / Trade-offs

- **CUDA dependency** — vLLM requires NVIDIA GPUs with CUDA. Pure CPU inference must fall back to Ollama or llama.cpp.
- **Deployment complexity** — vLLM container requires model volume mounts, GPU passthrough (`deploy.resources.reservations.devices`), and larger image size (~8 GB).
- **Model format** — vLLM prefers HuggingFace Transformers format; GGUF models (used by Ollama) require conversion or the use of vLLM's GGUF loader.

---

## Migration Path

```
Phase 1 (Current):  Ollama for all environments
Phase 2 (Next):     vLLM for staging/production, Ollama for local dev
Phase 3 (Future):   vLLM + Ray for multi-node GPU clusters
```

---

## References

- [vLLM Documentation](https://docs.vllm.ai/)
- [PagedAttention Paper (Kwon et al., 2023)](https://arxiv.org/abs/2309.06180)
- [Continuous Batching (Yu et al., 2022)](https://arxiv.org/abs/2207.02768)
- ADR-001: Local LLMs over Cloud APIs
- BSI IT-Grundschutz-Kompendium — KRITIS compliance baseline
