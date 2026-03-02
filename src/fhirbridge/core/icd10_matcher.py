"""
ICD-10-GM Deterministic Matcher
================================
Replaces the LLM hallucination risk with a fast, deterministic lookup.
In production, this would read from a BfArM CSV/SQLite catalog.
For this prototype, we use an in-memory dictionary with basic token matching.
"""

import logging
import re

logger = logging.getLogger("ICD10Matcher")

# Prototype In-Memory Catalog (Mocked BfArM Catalog)
CATALOG = {
    # Kardiologie / Innere
    "I10": ["essentielle", "hypertonie", "bluthochdruck", "hypertension"],
    "I10.00": ["benigne", "hypertonie", "ohne", "organschädigung"],
    "E11.9": ["diabetes", "mellitus", "typ", "2", "ohne", "komplikationen"],
    "E11.8": ["diabetes", "mellitus", "typ", "2", "mit", "komplikationen"],
    "J18.9": ["pneumonie", "lungenentzündung", "nicht", "näher", "bezeichnet"],
    "I50.9": ["herzinsuffizienz", "herzschwäche", "herzversagen"],
    "R55": ["synkope", "kollaps", "kreislaufstillstand"],
    # Onkologie
    "C34.9": ["bronchialkarzinom", "lungenkrebs", "nsclc", "sclc"],
    "C50.9": ["mamma", "ca", "karzinom", "brustkrebs", "mammakarzinom"],
    "Z08.0": ["nachsorge", "tumorfrei", "rezidivfrei", "onkologische", "kontrolle"],
    # Chirurgie / Orthopädie
    "S72.00": ["schenkelhalsfraktur", "hüftfraktur", "femurfraktur"],
    "K35.8": ["appendizitis", "blinddarmentzündung", "blinddarm"],
    "M54.5": ["lws", "syndrom", "kreuzschmerz", "lumbalgie"],
    # Psychiatrie / Pulmo
    "F32.9": ["depressive", "episode", "depression"],
    "J44.9": ["copd", "chronisch", "obstruktive", "lungenerkrankung"],
}


def clean_text(text: str) -> str:
    """Normalize text for consistent token matching."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # Remove punctuation
    return text.strip()


def match_icd10_code(diagnosis_text: str) -> tuple[str, str]:
    """
    Attempts to deterministically match a diagnosis string to an ICD-10-GM code.
    Returns: (ICD_CODE, DISPLAY_TEXT)
    """
    cleaned = clean_text(diagnosis_text)
    tokens = set(cleaned.split())

    best_match: str | None = None
    best_score = 0

    for code, keywords in CATALOG.items():
        # Simple overlap score
        score = sum(1 for kw in keywords if kw in tokens)

        # Give higher weight if the exact phrase appears
        exact_phrase = " ".join(keywords)
        if exact_phrase in cleaned:
            score += 5

        if score > best_score:
            best_score = score
            best_match = code

    if best_match and best_score > 0:
        logger.debug(f"Matches '{diagnosis_text}' -> {best_match} (Score: {best_score})")
        # In a real system, the display text would come exactly from BfArM
        display_text = " ".join(CATALOG[best_match]).title()
        return best_match, display_text

    logger.debug(f"Unmapped Diagnosis: '{diagnosis_text}' -> R69")
    return "R69", "Unbekannte Diagnose"
