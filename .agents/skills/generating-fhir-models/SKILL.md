---
name: generating-fhir-models
description: Helps construct nested Pydantic models that comply with strict FHIR and ISiK/MIO profiles. Use when the user needs to map data to FHIR, generate Pydantic schemas for FHIR resources, or resolve FHIR validation errors.
---

# FHIR Model Generator

You are an expert in HL7 FHIR (R4) and Pydantic. Your role is to help the user build robust Python backend models that map unstructured data or HL7v2 fields into strict, deeply-nested FHIR resources (specifically adhering to German ISiK/MIO profiles where applicable).

## Core Principles

1. **Strict Types**: Always use Pydantic `BaseModel` for FHIR resources. Use `Field(alias="...")` when FHIR field names conflict with Python reserved words (e.g., `class_` or `id`).
2. **Handle Nesting**: FHIR is deeply nested. Don't take shortcuts. A `Patient` resource's name is a list of `HumanName` objects, not a string.
3. **Optionality**: Most fields in FHIR are optional (`Optional[str]`), but ISiK profiles often enforce certain cardinalities (e.g., must have an identifier). Pay attention to profile constraints.
4. **Validation Loop**: When working with local LLMs to generate these models, ensure you implement a validation loop. If `Model.model_validate_json()` fails, the raw data must be returned to the LLM with the error for correction.

## Workflow: Scaffolding a FHIR Resource

1. **Identify the Profile**: Ask the user if they are targeting generic FHIR R4 or a specific profile (e.g., ISiK Patient).
2. **Review Patterns**: Consult [FHIR_PATTERNS.md](FHIR_PATTERNS.md) for standard implementations of common FHIR data types (Identifier, CodeableConcept, HumanName).
3. **Draft the Model**: Write the Pydantic models top-down, starting from the leaf nodes (Data Types) up to the Root Resource.
4. **Example Generation**: Generate a valid JSON payload that conforms to the newly created model to prove it works.

## Reference Materials

- For common data type mappings (Identifier, Reference, CodeableConcept), see: [FHIR_PATTERNS.md](FHIR_PATTERNS.md)

## KDL3. **Auto-Generation via Meta-Prompting**

   The **Batch KDL Synthesizer** (`scripts/batch_generate_kdl_models.py`) meta-generates Pydantic `BaseModel` classes for KDL document types via Mistral. Each target entry includes a researched German standard that the LLM is instructed to follow.

### Usage

```bash
# Erzeugt alle konfigurierten Modelle
python .agents\skills\generating-fhir-models\scripts\batch_generate_kdl_models.py

# Führt das Skript nur für die ersten 3 Modelle (zum Testen) aus
python .agents\skills\generating-fhir-models\scripts\batch_generate_kdl_models.py --limit 3
```

Output: `scripts/auto_generated_kdl_models.py` — run `ruff format` afterwards.

### KDL Target Registry (14 entries)

| # | KDL Code | Dokumentenname | Norm / Standard |
|---|----------|----------------|-----------------|
| 1 | `AD010103` | Entlassungsbericht | DIN 5008 + KBV/gematik eArztbrief |
| 2 | `LB120103` | Laborbefund Klinische Chemie | ISiK Laborbefund Profil (Referenzbereiche, SI-Einheiten) |
| 3 | `PT080102` | Histologischer Befund Pathologie | TNM-Klassifikation (Makro/Mikroskopie) |
| 4 | `MP030101` | Mutterpass | G-BA Mutterschafts-Richtlinien |
| 5 | `AN040101` | Anästhesieprotokoll | DGAI-Empfehlung Anästhesiedokumentation |
| 6 | `VB050101` | Verlegungsbericht | DIN 5008 + KBV eArztbrief-RL (Verlegung) |
| 7 | `KB060101` | Konsilbericht | G-BA Qualitätssicherung, ISiK ServiceRequest |
| 8 | `RE070101` | Reha-Entlassungsbericht | BAR Rahmenempfehlungen Reha-Entlassungsbericht |
| 9 | `NA080101` | Notaufnahmeprotokoll | DIVI Notaufnahmeprotokoll + CEDIS/MTS Triage |
| 10 | `GB090101` | Geburtsbericht | G-BA Mutterschafts-RL (Geburt) + DGGG-LL |
| 11 | `TP100101` | Transfusionsprotokoll | TFG §14 + BÄK Hämotherapie-RL |
| 12 | `WD110101` | Wunddokumentation | DNQP Expertenstandard chronische Wunden |
| 13 | `SP120101` | Sturzprotokoll | DNQP Expertenstandard Sturzprophylaxe |
| 14 | `MK130101` | Medikationsplan | BMP gemäß §31a SGB V |
