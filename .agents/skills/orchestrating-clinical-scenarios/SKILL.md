---
name: orchestrating-clinical-scenarios
description: A state-machine orchestrated skill that plans and executes complex medical "Patient Arcs" by calling specialized KDL document skills.
---

# Clinical Scenario Orchestrator

This skill is the "Right Brain" of the synthetic data pipeline. It doesn't generate PDFs itself; instead, it manages the medical logic and chronology of a patient's history.

## Role

- **Storytelling**: Defines the sequence of clinical events (Admission -> Surgery -> Complications -> Recovery -> Discharge).
- **Context Management**: Passes the state of the patient (diagnoses, symptoms, medications) to the specialized document skills.
- **Case Integrity**: Group documents into logical "Behandlungsfälle" (Encounters) with a shared `Fallnummer`.

## Workflow: Scenario Execution

1. **Define the Arc**: Use the local LLM to draft a "Scenario JSON" that lists encounters and their duration.
2. **Sequential Invocations**:
   - For each encounter, generate a `Fall-ID`.
   - Call the specialized KDL skills (e.g., `generating-kdl-discharge-summaries`) with the current encounter context.
3. **Medication Continuity**: Carry over medications from previous cases to ensure the final "Medikationsplan" is realistic.

## Clinical Context Template

When calling a sub-skill, always provide the following context:

```json
{
  "patient": "Name, DOB, Gender",
  "case_id": "FALL_2024_0815",
  "clinical_context": "Post-OP day 3 of TURP. Patient is mobilised but pain is 4/10.",
  "medications": ["Drug A", "Drug B"],
  "kdl_class": "AD010103"
}
```
