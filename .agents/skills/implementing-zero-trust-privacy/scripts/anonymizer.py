import logging
import re
from typing import Any

from pydantic import BaseModel

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from models import AnonymizationResult

logger = logging.getLogger(__name__)

class LocalAnonymizer:
    """Zero-Trust Medical Data Anonymizer.
    Uses local spaCy NLP and Regex to strip PHI from German clinical text.
    """

    def __init__(self, spacy_model: str = "de_core_news_sm"):
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                # Note: The model 'de_core_news_sm' needs to be installed via `python -m spacy download de_core_news_sm`
                self.nlp = spacy.load(spacy_model)
            except Exception as e:
                logger.warning(f"SpaCy model {spacy_model} could not be loaded: {e}. Suggesting: python -m spacy download {spacy_model}")
        else:
            logger.warning("spacy is not installed. NLP features will be disabled. Run: pip install spacy")

        # Custom regexes
        # KVNR: 1 Letter followed by 9 digits
        self.kvnr_pattern = re.compile(r'\b[A-Z]\d{9}\b')

        # German Date roughly: dd.mm.yyyy, d.m.yy, etc.
        self.date_pattern = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{2,4}\b')

    def anonymize(self, text: str) -> AnonymizationResult:
        if not self.nlp:
            logger.error("NLP model not loaded. Applying Regex-only fallbacks.")
            # Fallback will only map KVNR and Dates

        mapping = {}
        counters = {"PER": 1, "LOC": 1, "ORG": 1, "KVNR": 1, "DATE": 1}

        # 1. Regex replacements first (to avoid NLP splitting errors on dates/IDs)
        def replace_kvnr(match):
            val = match.group(0)
            token = f"[KVNR_{counters['KVNR']}]"
            counters["KVNR"] += 1
            mapping[token] = val
            return token

        def replace_date(match):
            val = match.group(0)
            token = f"[DATE_{counters['DATE']}]"
            counters["DATE"] += 1
            mapping[token] = val
            return token

        # Apply KVNR
        tmp_text = self.kvnr_pattern.sub(replace_kvnr, text)
        # Apply DATE
        tmp_text = self.date_pattern.sub(replace_date, tmp_text)

        if not self.nlp:
            return AnonymizationResult(anonymized_text=tmp_text, mapping=mapping)

        # 2. Spacy NER replacements
        doc = self.nlp(tmp_text)

        # We need to replace from back to front to not mess up character indices
        entities = []
        for ent in doc.ents:
            if ent.label_ in ["PER", "LOC", "ORG"]:
                entities.append((ent.start_char, ent.end_char, ent.label_, ent.text))

        # Sort descending by start character
        entities.sort(key=lambda x: x[0], reverse=True)

        final_text = tmp_text
        for start_char, end_char, label, val in entities:
            # Check if this substring overlaps with something we already replaced via regex regex tokens like [DATE_1]
            if "[" in val and "]" in val:
                continue

            token = f"[{label}_{counters[label]}]"
            counters[label] += 1
            mapping[token] = val

            final_text = final_text[:start_char] + token + final_text[end_char:]

        return AnonymizationResult(anonymized_text=final_text, mapping=mapping)

    def deanonymize(self, data: Any, mapping: dict[str, str]) -> Any:
        """Traverse the data (dict, list, string) and replace tokens with original values."""
        if isinstance(data, str):
            res = data
            for token, orig in mapping.items():
                res = res.replace(token, orig)
            return res
        elif isinstance(data, list):
            return [self.deanonymize(item, mapping) for item in data]
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                new_dict[k] = self.deanonymize(v, mapping)
            return new_dict
        elif isinstance(data, BaseModel): # Pydantic model
            dump = data.model_dump()
            restored_dump = self.deanonymize(dump, mapping)
            return type(data).model_validate(restored_dump)
        else:
            return data

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    anonymizer = LocalAnonymizer()

    sample_text = (
        "Patient Max Mustermann, wohnhaft in Berlin Hauptstr. 12, "
        "wurde am 15.08.2023 im Charité Universitätsmedizin Berlin vorstellig. "
        "Seine KVNR lautet A123456789. Blutdruck war leicht erhöht."
    )

    print("\n--- ORIGINAL TEXT ---")
    print(sample_text)

    result = anonymizer.anonymize(sample_text)

    print("\n--- ANONYMIZED TEXT ---")
    print(result.anonymized_text)

    print("\n--- MAPPING ---")
    for k, v in result.mapping.items():
        print(f"{k}: {v}")

    print("\n--- DEANONYMIZED (SIMULATED JSON OUTPUT) ---")
    mock_llm_json = {
        "patient_name": "[PER_1]",
        "address": "[LOC_1] Hauptstr. 12",
        "kvnr_extracted": "[KVNR_1]",
        "admission_date": "[DATE_1]",
        "hospital": "[ORG_1] [ORG_2] [LOC_2]"
    }

    restored_json = anonymizer.deanonymize(mock_llm_json, result.mapping)
    print("MOCK LLM JSON (with tokens):", mock_llm_json)
    print("RESTORED JSON (with original PHI):", restored_json)
