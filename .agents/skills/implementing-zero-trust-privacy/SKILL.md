---
name: implementing-zero-trust-privacy
description: Guides the agent to implement a Zero-Trust Data Privacy Layer that pseudonymises PHI (Protected Health Information) in medical texts before LLM processing, using local NLP (Spacy/Regex).
---

# Implementing Zero-Trust Privacy

## Architecture Rules

1. **Local Only**: No cloud APIs may be used for anonymization. We rely on fast, local models like Spacy (`de_core_news_sm`) and custom Regex patterns for highly specific German identifiers (e.g., KVNR, Fallnummer).
2. **Pydantic Driven**: All mapping metadata is passed via strict Pydantic models.
3. **Pre-processing**: The text anonymization runs *before* the prompt is sent to `LlmRetryClient`.
4. **Post-processing**: The structured JSON response from the LLM or raw text must be securely re-identified using the mapping.

## Standard Token Replacements

- `[PER_1]`, `[PER_2]` - for Persons
- `[LOC_1]`, `[LOC_2]` - for Locations / Addresses
- `[ORG_1]`, `[ORG_2]` - for Organizations (Hospitals, Clinics)
- `[KVNR_1]` - for Krankenversichertennummer
- `[DATE_1]` - for Dates

## File Structure

- `scripts/models.py`: Defines `AnonymizationResult`, `DeanonymizeRequest`.
- `scripts/anonymizer.py`: The core `LocalAnonymizer` class.
