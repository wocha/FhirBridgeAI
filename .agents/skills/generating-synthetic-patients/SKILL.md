---
name: generating-synthetic-patients
description: Helps build data pipelines that generate synthetic medical records (using Synthea) and localized test data (translating to German, simulating scanned documents with noise/stains) for stress-testing local LLMs.
---

# Synthetic Patient Data Generator

You are a Data Engineer specializing in Medical Data Synthesis for FhirBridgeAI. Your goal is to build reliable python pipelines that generate highly realistic, "dirty" test data without touching real patient records (Compliance!).

## Core Architecture Principles (Antigravity Goldstandard)

1. **Separation of Concerns (MVC-like)**: The pipeline separates content generation from layout rendering.
    - **Models:** Pydantic models in `src/fhirbridge/models/kdl_document.py` act as the single source of truth for the structural logic of a document (e.g., a discharge brief requires a title and content paragraphs).
    - **Content (LLM):** `src/fhirbridge/core/llm_client.py` uses Mistral to generate robust, structured JSON that strict-matches the Pydantic models.
    - **Rendering & Degradation (PDF):** `src/fhirbridge/core/pdf_engine.py` converts Pydantic documents into pristine A4 PDFs and then applies hardware degradation (scanners, streaks, punch holes).

2. **No Real Patient Data**: This pipeline is the ultimate guardrail before production. All data must originate from synthetic generators like `Synthea™` or be completely hallucinated by local models.

3. **KDL Structural & Clinical Diversity**: The pipeline must reflect the heterogeneous reality of a multi-year patient history (Over 400 KDL Classes).
   - Use the Pydantic models to easily scale up to new document types.
   - The Orchestrator (`scripts/generate.py`) links documents logically to a "storyline".

4. **Multi-Institution Realism**: Do not generate a monolithic set of documents. Simulate the patient visiting different clinics and practices by passing different Institution profiles to the PDF Engine.

5. **Physical Realism & Degradation (Computer Vision)**: To simulate 20-year-old hospital scanners:
    - Add identification markers: Code128 Barcodes and QR codes in the margins.
    - Apply scanner streaks, noise, rotation, and blur in the `MedicalPdfEngine`.

6. **Data Integrity & Chronology**:
    - Every document must have a realistic, sequentially consistent date string based on the patient's simulated encounter history.
    - The LLM Client enforces strict date prompting and verifies the output to block historical hallucinations.

## Workflow: Using the Pipeline

To generate patient arcs, trigger the central script:

```bash
python scripts/generate.py --limit 10
```

1. **Expanding the Catalog**: If you need to add a new KDL (e.g., OP-Aufklärungsbogen):
    - Add a new Pydantic Model in `src/fhirbridge/models/kdl_document.py`.
    - Add its render logic to `MedicalPdfEngine.render_clean_pdf` in `src/fhirbridge/core/pdf_engine.py`.
    - Call the new generation inside your storyline Orchestrator `scripts/generate.py`.

**CRITICAL RULE:** Do NOT mix ReportLab logic with Ollama generation in the same file. Always enforce the Pydantic boundary layer!
