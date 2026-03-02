---
name: generating-kdl-clinical-findings
description: Generates specialised medical findings (KDL DG*, PT*, LB*) for Radiology, Pathology, and Laboratory results using professional terminology.
---

# KDL Clinical Findings Generator

This skill manages the generation of objective diagnostic results.

## Document Types

- **Surgery (`OP150103`)**: Operative reports (e.g. Appendektomie). Focus on realistic procedures, timelines, and surgical terminology. Handled via `SurgeryReport`.
- **Radiology (`DG02*`)**: CT, MRI, X-ray, Ultrasound reports. Terminology focus: "Transversal", "Verschattung", "Kontrastmittelanreicherung". Handled via `ImagingReport`.
- **Pathology (`PT080102`)**: Histology reports. Terminology focus: "Makroskopie", "Mikroskopie", "TNM-Klassifikation". (To be integrated into the new generator pattern).
- **Lab Reports (`LB120103`)**: Tabular data with reference ranges.

## Realism Requirements

- **Surgery**: Must mention the indication, surgical procedure steps (exploration, preparation, resection, closure), and list fictional but realistic surgeon names.
- **Pathology**: Must show TNM staging for oncology cases.
- **Radiology**: Must mention the imaging technique and indication.
- **Labs**: Values must be consistent with the patient's acute state (e.g., high CRP in infection).

## Architecture & Delegation

This skill acts as a Router that delegates complex textual reports to the local `fhirbridge.core.llm_client`.

- `delegate_surgery_report(patient, indication, procedure, target_date, fall_id)` creates a `SurgeryReport` JSON object out of an unstructured query via Mistral.
- `delegate_imaging_report(patient, indication, modality, target_date, fall_id)` creates an `ImagingReport` JSON object out of an unstructured query via Mistral.
