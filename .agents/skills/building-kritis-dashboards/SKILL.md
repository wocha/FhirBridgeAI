---
name: building-kritis-dashboards
description: Guides the agent to build secure, locally-hosted Streamlit dashboards for monitoring batch processes and auditing KI decisions, compliant with KRITIS environments (no external dependencies, safe database reads).
---

# KRITIS Dashboard Builder

You are a Frontend Security Engineer for FhirBridgeAI. Your objective is to build a modern, intuitive, and highly secure `Streamlit` dashboard that visualizes the progress of the Autonomous Dispatcher (Phase 4) and provides an audit log for all LLM decisions.

## Core Architecture Principles

1. **Air-Gapped & Secure**: The UI must run 100% locally. Do NOT include ANY external CDN links, Google Fonts, or external tracking analytics in the Streamlit config or custom HTML components.
2. **Read-Only Database Access**: The dashboard is primarily an observer. When querying the Dispatcher's SQLite database, ensure queries are efficient and non-blocking (e.g., using `READ UNCOMMITTED` or proper SQLAlchemy session management) to avoid locking the database while the background worker is writing.
3. **Auditability (KRITIS Focus)**: Every LLM transformation (from OCR Text -> FHIR JSON) must be traceable. The UI needs dedicated views allowing users to click a processed file and see:
   - The raw input (OCR text / HL7 message)
   - The intermediate LLM reasoning (if captured)
   - The final FHIR Resource

## Workflow: Scaffolding a KRITIS Dashboard

1. **Setup the Framework**:
   - Create a structured Streamlit app entry point (e.g., `app.py`) with a multi-page setup or a sidebar for navigation (e.g., `Dashboard`, `Audit Log`, `Settings`).
2. **Data Integration**:
   - Write safe reading functions that connect to the SQLite DB created by the `building-autonomous-dispatchers` skill.
   - Example: Implement metrics for "Total Files", "Processing", "Success", and "Failed".
3. **Visualization**:
   - Use built-in Streamlit charts (e.g., `st.bar_chart`, `st.metric`) or local Plotly/Altair visualizations to show throughput over time without relying on cloud rendering.
4. **Error Handling & Resilience**:
   - Wrap DB calls in `try/except` and use `st.error` to gracefully handle locked databases or missing tables without crashing the UI.
