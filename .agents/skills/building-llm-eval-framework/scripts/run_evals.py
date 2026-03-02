"""
LLM Evaluation Framework (Tier 7 LLMOps).
Generates in-memory synthetic KDL Discharge Summaries to establish 100% accurate ground truth,
simulates unstructured OCR text from the result, and uses LlmRetryClient to see if
the model can accurately recover the original diagnoses. Calculates Precision, Recall, F1.
"""

import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, Field

# Ensure canonical clients are importable
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
SKILLS_DIR = BASE_DIR / ".agents" / "skills"
sys.path.append(str(SKILLS_DIR / "integrating-local-llms" / "scripts"))
sys.path.append(str(SKILLS_DIR / "generating-kdl-discharge-summaries" / "scripts"))

from generate_discharge_summary import delegate_discharge_summary
from llm_retry_client import LlmConfig, LlmRetryClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("eval_framework")

# --- Mock Architecture ---

class MockIdentity:
    def __init__(self, name, birth_date, gender, base_patient_id):
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.base_patient_id = base_patient_id

class MockPatient:
    def __init__(self, identity, active_diagnoses):
        self.identity = identity
        self.active_diagnoses = active_diagnoses

# --- LLM Extraction Schema ---

class ExtractedDiagnoses(BaseModel):
    hauptdiagnose: str = Field(..., description="Die primäre Entlassungsdiagnose")
    nebendiagnosen: list[str] = Field(default_factory=list, description="Liste aller weiteren Nebendiagnosen, die im Text explizit aufgeführt sind")

# --- Evaluation Logic ---

def normalize_text(text: str) -> str:
    """Normalizes text for more robust string matching (lowercase, strip whitespace, remove some common chars)."""
    return text.lower().replace("(", "").replace(")", "").strip()

def is_match(truth_str: str, ext_str: str) -> bool:
    """Checks if there's a loose string match between the ground truth and extracted term."""
    t = normalize_text(truth_str)
    e = normalize_text(ext_str)
    return (t in e) or (e in t)

def calculate_metrics(ground_truth_list: list[str], extracted_list: list[str]):
    """Calculate TP, FP, FN based on loose string inclusion mapping."""
    tp = 0
    fp = 0
    fn = 0

    # We maintain a list of matched truths so we don't double count
    matched_truths = [False] * len(ground_truth_list)
    matched_extracted = [False] * len(extracted_list)

    # Map True Positives
    for e_idx, ext in enumerate(extracted_list):
        match_found = False
        for t_idx, truth in enumerate(ground_truth_list):
            if not matched_truths[t_idx] and is_match(truth, ext):
                tp += 1
                matched_truths[t_idx] = True
                matched_extracted[e_idx] = True
                match_found = True
                break

        # If the extracted diagnosis couldn't be mapped to ANY remaining ground truth, it's a False Positive (hallucination)
        if not match_found:
            fp += 1

    # Any ground truth not mapped represents a False Negative (missed)
    for t_idx, matched in enumerate(matched_truths):
        if not matched:
            fn += 1

    return tp, fp, fn

def run_evaluation(num_samples: int = 3):
    """Orchestrates the evaluation flow."""
    logger.info(f"Starting LLM Evaluation Run with {num_samples} document samples...")

    # Let's seed our evaluation with strict sets of diagnoses
    test_cases = [
        ["Akute Appendizitis", "Diabetes Mellitus Typ 2", "Arterielle Hypertonie"],
        ["Schenkelhalsfraktur rechts", "Osteoporose", "Chronische Herzinsuffizienz NYHA II"],
        ["Pneumonie", "COPD GOLD II", "Vorhofflimmern"]
    ]

    # Cycle if num_samples > len(test_cases)
    test_cases = (test_cases * (num_samples // len(test_cases) + 1))[:num_samples]

    # Use LlmRetryClient with 0 temperature for strict analytical extraction
    eval_client = LlmRetryClient(config=LlmConfig(temperature=0.0))

    aggregate_tp = 0
    aggregate_fp = 0
    aggregate_fn = 0

    results_log = []

    for i, diagnoses_set in enumerate(test_cases):
        logger.info(f"--- Running Test Sample {i+1}/{num_samples} ---")
        hauptdiagnose = diagnoses_set[0]
        nebendiagnosen = diagnoses_set[1:]

        # 1. Establish Mock Patient and Target Ground Truth
        patient = MockPatient(
            identity=MockIdentity("Max Mustermann", date(1950, 1, 1), "m", f"EVAL-{i}"),
            active_diagnoses=diagnoses_set
        )

        ground_truth_all = [hauptdiagnose] + nebendiagnosen
        logger.info(f"Ground Truth Diagnoses: {ground_truth_all}")

        # 2. Generate Discharge Summary to get realistic full text
        logger.info("Generating realistic Discharge Summary document based on Ground Truth...")
        try:
            doc = delegate_discharge_summary(
                patient=patient,
                hauptdiagnose=hauptdiagnose,
                target_date=date.today(),
                fall_id=f"FALL-{i}"
            )
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            continue

        # 3. Formulate Unstructured "OCR-like" free text from resulting narrative fields
        ocr_mock_text = f"Anamnese:\n{doc.anamnese}\n\nTherapie und Verlauf:\n{doc.therapie_und_verlauf}\n\nEpikrise:\n{doc.epikrise}"

        # 4. Extract with canonical client
        prompt = (
            "Bitte extrahiere aus dem folgenden medizinischen Freitext die primäre "
            "Hauptdiagnose und alle zutreffenden Nebendiagnosen, derentwegen der Patient "
            "behandelt wurde. Extrahiere NUR die Diagnosen.\n\n"
            f"=== TEXT START ===\n{ocr_mock_text}\n=== TEXT ENDE ==="
        )

        logger.info("Extracting data points via Local LLM...")
        try:
            extraction_result = eval_client.generate_structured(
                prompt=prompt,
                schema=ExtractedDiagnoses,
                system_context="Du bist ein Data Science Extraction Bot, der exakt auf JSON Schemata mappt."
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            continue

        extracted_all = [extraction_result.hauptdiagnose] + extraction_result.nebendiagnosen
        logger.info(f"Extracted Diagnoses: {extracted_all}")

        # 5. Evaluate Matches
        tp, fp, fn = calculate_metrics(ground_truth_all, extracted_all)

        # Accumulate
        aggregate_tp += tp
        aggregate_fp += fp
        aggregate_fn += fn

        results_log.append({
            "sample_id": i+1,
            "ground_truth": ground_truth_all,
            "extracted": extracted_all,
            "tp": tp, "fp": fp, "fn": fn
        })

        logger.info(f"Sample {i+1} Metrics -> TP: {tp}, FP: {fp}, FN: {fn}")

    # --- Calculate Final Averages ---
    precision = aggregate_tp / (aggregate_tp + aggregate_fp) if (aggregate_tp + aggregate_fp) > 0 else 0.0
    recall = aggregate_tp / (aggregate_tp + aggregate_fn) if (aggregate_tp + aggregate_fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    logger.info("=== EVALUATION COMPLETE ===")
    logger.info(f"Global TP: {aggregate_tp} | Global FP: {aggregate_fp} | Global FN: {aggregate_fn}")
    logger.info(f"Precision: {precision:.2f}")
    logger.info(f"Recall:    {recall:.2f}")
    logger.info(f"F1 Score:  {f1:.2f}")

    # Create the markdown report
    generate_markdown_report(
        num_samples=num_samples,
        precision=precision,
        recall=recall,
        f1=f1,
        aggregate_tp=aggregate_tp,
        aggregate_fp=aggregate_fp,
        aggregate_fn=aggregate_fn,
        results_log=results_log
    )

def generate_markdown_report(num_samples, precision, recall, f1, aggregate_tp, aggregate_fp, aggregate_fn, results_log):
    """Renders the HTML-like markdown table as an artifact."""

    # Locate User Artifact Brain directory (which Antigravity uses to output reports)
    brain_dir = os.getenv("CONVERSATION_BRAIN_DIR")
    # By default put it in current working directory if not set
    report_path = Path(brain_dir) / "eval_report.md" if brain_dir else Path(os.getcwd()) / "eval_report.md"

    md_content = f"""# LLM Diagnosis Extraction Evaluation Report

## Executive Summary

Evaluation run executed on **{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}**. A total of **{num_samples}** locally generated (Mistral) mock discharge summaries were converted to free-text and run back into the `LlmRetryClient` extraction pipeline.

### Core Metrics

| Metric | Score | Definition |
|---|---|---|
| **Precision** | **{precision:.2f}** | % of extracted diagnoses that were actually in the ground truth. |
| **Recall** | **{recall:.2f}** | % of ground truth diagnoses the LLM managed to find. |
| **F1-Score** | **{f1:.2f}** | Harmonic mean of Precision and Recall. |

**Aggregates**: TP: {aggregate_tp}, FP: {aggregate_fp}, FN: {aggregate_fn}

---

## Detailed Sample Logs

"""
    for entry in results_log:
        md_content += f"### Sample {entry['sample_id']}\n"
        md_content += f"- **Ground Truth**: `{entry['ground_truth']}`\n"
        md_content += f"- **Extracted**: `{entry['extracted']}`\n"
        md_content += f"- **Stats**: TP: {entry['tp']}, FP: {entry['fp']}, FN: {entry['fn']}\n\n"

    report_path.write_text(md_content, encoding="utf-8")
    logger.info(f"Wrote report to {report_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=3, help="Number of synthetic samples to use.")
    args = parser.parse_args()

    run_evaluation(num_samples=args.samples)
