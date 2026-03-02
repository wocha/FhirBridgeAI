---
name: generating-kdl-discharge-summaries
description: Specialised skill for generating DIN-compliant German "Arztbriefe" (KDL AD*) with realistic clinical text, diagnoses (ICD-10), and therapeutic epikrisis.
---

# KDL Discharge Summary Generator

This skill focuses on the most complex document type in German hospitals: the **Arztbrief** (Discharge Summary).

## Standards

- **Layout**: Follows **DIN 5008** for business letters (Header, Recipient, Subject, Text).
- **Structure**:
  - **Diagnosen**: Listed with ICD-10 codes where applicable.
  - **Anamnese**: Brief history of the current case.
  - **Therapie/Verlauf**: Clinical narrative of the stay.
  - **Epikrise/Empfehlung**: Future treatment plan.
  - **Medikation**: Discharge medication table.

## LLM Interaction

Use the parameterized prompt template for high realism:

```python
from pathlib import Path

template_path = Path(__file__).parent / "templates" / "discharge_summary_prompt.txt"
prompt = template_path.read_text(encoding="utf-8").format(
    diagnose="Akute Appendizitis (K35.8)",
    patient_context="Patient: Max Mustermann, geb. 15.05.1980",
)
```

See [discharge_summary_prompt.txt](templates/discharge_summary_prompt.txt) for the full template.

## Mandatory KDL Mapping

| KDL-Code | Dokumenttyp |
|---|---|
| `AD010103` | Entlassungsbericht intern |
| `AD010111` | Ambulanzbrief / Kurzbericht |
