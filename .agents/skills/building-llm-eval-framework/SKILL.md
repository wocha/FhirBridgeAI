---
name: building-llm-eval-framework
description: Provides an LLMOps evaluation script to quantitatively measure the performance  (Precision, Recall, F1-Score) of our local LLM (Mistral) for medical extraction tasks.
---

# LLM Evaluation Framework

This skill establishes the foundation for tracking and evaluating model performance over time. Knowing *that* an LLM produces JSON is not enough for an Enterprise context; we must know *how accurate* the mapped data points are compared to the ground truth.

## Core Principles

1. **Strict Ground Truth Generation**: The evaluation avoids relying on potentially hallucinated text without an anchor. Instead, it generates synthetic `DischargeSummary` documents whose origin variables (the exact diagnoses injected) act as the 100% strict Ground Truth.
2. **Text Simulation**: To simulate the real-world OCR text mapping scenario, the generated structured KDL document is concatenated into a raw "dirty" string of free medical text (combining Anamnese, Therapie, Epikrise).
3. **Structured Recovery Check**: The raw text is passed to the Canonical `LlmRetryClient` to force it to re-extract the exact diagnoses.
4. **Metrics (Precision, Recall, F1)**:
   - **True Positives (TP)**: System correctly extracted a diagnosis that was present in the ground truth.
   - **False Positives (FP)**: System hallucinated or incorrectly extracted an irrelevant term as a diagnosis.
   - **False Negatives (FN)**: System missed a diagnosis present in the ground truth.

## Workflow

Run the evaluation suite by invoking the standalone script:

```bash
python .agents/skills/building-llm-eval-framework/scripts/run_evals.py
```

The script will:

- Generate an in-memory sample batch of `DischargeSummary` documents.
- Use the Canonical `LlmRetryClient` for extraction.
- Calculate and average the evaluation metrics.
- Generate a `eval_report.md` artifact with the final summary.
