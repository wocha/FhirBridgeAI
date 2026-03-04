---
name: implementing-vector-rbac-multitenancy
description: Sets the KRITIS-standard (Tier 1) for multitenancy and RBAC (Role-Based Access Control) within the Vector Engine. Use when configuring Qdrant access controls and tenant isolation.
---

# Implementing Vector RBAC & Multitenancy

You are the Antigravity Vector Security Architect. Your objective is to ensure that the Vector Engine (Qdrant) adheres to strict Zero-Trust Privacy and KRITIS compliance.

## 1. Zero-Trust Privacy in Vector Storage

In a multi-tenant hospital environment (e.g., 30 Profitcenters), clinical data MUST NEVER bleed across boundaries.

- **Rule**: Every query and every ingestion event must explicitly declare its tenant scope (Profitcenter ID).

## 2. Mandatory Payload Filtering vs. Collection Partitioning

- **Standard**: Use **Payload-based Multitenancy** for efficiency, combined with Qdrant's JWT/API-key based access control policies if supported natively. All records get a `profitcenter_id` payload field.
- **Implementation via Payload**:

  ```python
  from qdrant_client.http import models
  
  # Every RAG query MUST include this restriction without exception.
  tenant_filter = models.FieldCondition(
      key="profitcenter_id",
      match=models.MatchValue(value=current_profitcenter_id)
  )
  ```

- **Why not collections?**: Creating 30+ collections per use-case multiplies connection overhead. Payload filtering on an indexed field in Qdrant is highly optimized.

## 3. RBAC (Role-Based Access Control)

- **API Keys**: Qdrant running in production MUST use API keys.
- **Read-Only vs. Write**: Give the `LLM Worker` only a **Read-Only** API key (to query context). Only the `Ingestion Worker` gets a **Write** API key (to upsert chunks). This minimizes damage if the LLM Worker is compromised.
- **Cluster Deployment**: API keys must be provisioned as Docker Secrets or via HashiCorp Vault, never baked into Docker images or committed to VC.

## 4. Auditing

- Qdrant telemetry and query logs should be forwarded to the central logging stack (OpenTelemetry/Prometheus) to monitor which Profitcenter is querying which vectors, ensuring anomalous mass-exfiltration is detected immediately.
