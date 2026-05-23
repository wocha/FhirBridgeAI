"""
Zero-Trust PHI Pseudonymizer for FhirBridgeAI
================================================
Local NLP (spaCy) + Regex-based anonymization of Protected Health Information.

KRITIS Â§8a COMPLIANCE:
    - PHI MUST NEVER appear in logs, exceptions, span attributes, or message queues.
    - All mappings are stored exclusively via S3 Claim-Check (see ADR-011).
    - If PHI_STRICT_MODE=true, the worker MUST abort if spaCy is unavailable.
"""

import logging
import os
import re
import sys
from typing import Any

from pydantic import BaseModel, Field

from fhirbridge.core.telemetry import init_tracer, mark_span_error

try:
    import spacy

    SPACY_AVAILABLE = True
except ImportError:
    import types

    SPACY_AVAILABLE = False
    spacy = types.ModuleType("spacy")

    def _missing_spacy_load(*_args, **_kwargs):
        raise OSError("spaCy package is not installed.")

    spacy.load = _missing_spacy_load  # type: ignore[attr-defined]
    sys.modules.setdefault("spacy", spacy)

logger = logging.getLogger(__name__)

# KRITIS Â§8a: NEVER log PHI variables (text, val, ent.text, mapping).
# Only log job IDs, entity counts, modes, and structural metadata.

_PSEUDONYMIZER_TRACER = None


def _get_tracer():
    global _PSEUDONYMIZER_TRACER
    if _PSEUDONYMIZER_TRACER is None:
        _PSEUDONYMIZER_TRACER = init_tracer("phi-anonymizer")
    return _PSEUDONYMIZER_TRACER

# --- Environment Configuration ---
PHI_STRICT_MODE = os.getenv("PHI_STRICT_MODE", "false").lower() == "true"

_ERROR_CODE_BY_EXCEPTION: dict[str, str] = {
    "ValueError": "DEANONYMIZE_VALUE_ERROR",
    "TypeError": "DEANONYMIZE_TYPE_ERROR",
    "KeyError": "DEANONYMIZE_KEY_ERROR",
}

_ERROR_MESSAGE_BY_CODE: dict[str, str] = {
    "DEANONYMIZE_VALUE_ERROR": "Value error during deanonymization.",
    "DEANONYMIZE_TYPE_ERROR": "Type error during deanonymization.",
    "DEANONYMIZE_KEY_ERROR": "Key error during deanonymization.",
    "DEANONYMIZE_INTERNAL_ERROR": "Internal error during deanonymization.",
}


class AnonymizationResult(BaseModel):
    """Result of the anonymization process containing the safe text and the mapping table."""
    anonymized_text: str = Field(..., description="The medical text with PHI replaced by tokens like <NAME_1>.")
    mapping: dict[str, str] = Field(..., description="Mapping from tokens (e.g. '<NAME_1>') to original text.")


class DeanonymizeRequest(BaseModel):
    """Request to reverse the anonymization on an LLM output."""

    target_data: Any = Field(..., description="The target data containing tokens.")
    mapping: dict[str, str] = Field(..., description="The mapping dict to replace tokens with original PHI.")


def _redact_phi_from_exception(exc: Exception) -> tuple[str, str]:
    """SafeExceptionHandler: Map exceptions to fixed, PHI-free error codes.

    Zero-Trust requirement: The external error text MUST NOT contain any
    original PHI, mapping contents, or arbitrary exception messages.
    Only a stable error code and a short, generic description are returned.
    """
    exc_type = type(exc).__name__
    error_code = _ERROR_CODE_BY_EXCEPTION.get(exc_type, "DEANONYMIZE_INTERNAL_ERROR")
    safe_msg = _ERROR_MESSAGE_BY_CODE.get(
        error_code, _ERROR_MESSAGE_BY_CODE["DEANONYMIZE_INTERNAL_ERROR"]
    )
    return error_code, safe_msg


class LocalAnonymizer:
    """Zero-Trust Medical Data Anonymizer.

    Uses local spaCy NLP and Regex to strip PHI from German clinical text.

    BSI 200-2 Compliance:
        - STRICT_MODE (PHI_STRICT_MODE=true): Aborts if spaCy unavailable.
        - No PHI in logs, exceptions, or OTel spans.
        - Mapping data stored exclusively via S3 Claim-Check.
    """

    def __init__(self, spacy_model: str = "de_core_news_sm", require_nlp: bool = True):
        self.nlp = None
        self._anonymization_mode = "regex_only"
        self._spacy_model = spacy_model
        self._require_nlp = require_nlp
        self._nlp_attempted = False

        # For anonymization callers that require NLP at construction time (OCR worker),
        # we keep the original STRICT_MODE semantics.
        if self._require_nlp:
            self._ensure_nlp_loaded(strict=PHI_STRICT_MODE)

        # Custom regexes
        # KVNR: 1 Letter followed by 9 digits
        self.kvnr_pattern = re.compile(r"\b[A-Z]\d{9}\b")

        # German Date roughly: dd.mm.yyyy, d.m.yy, etc.
        self.date_pattern = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")

    def _ensure_nlp_loaded(self, strict: bool) -> None:
        """Lazy-load spaCy model with STRICT_MODE semantics for anonymization.

        This method is a no-op if loading has already been attempted.
        """
        if self._nlp_attempted:
            return

        self._nlp_attempted = True

        if not SPACY_AVAILABLE:
            if strict:
                logger.critical(
                    "STRICT_MODE: spacy package is not installed. "
                    "Aborting worker to prevent incomplete pseudonymization. "
                    "Run: pip install spacy",
                )
                sys.exit(1)
            logger.warning(
                "spacy is not installed. NLP features will be disabled. "
                "Run: pip install spacy",
            )
            return

        try:
            self.nlp = spacy.load(self._spacy_model)
            self._anonymization_mode = "spacy"
        except Exception:
            if strict:
                logger.critical(
                    "STRICT_MODE: SpaCy model '%s' could not be loaded. "
                    "Aborting worker to prevent incomplete pseudonymization. "
                    "Run: python -m spacy download %s",
                    self._spacy_model,
                    self._spacy_model,
                )
                sys.exit(1)
            logger.warning(
                "SpaCy model '%s' could not be loaded. "
                "Falling back to regex-only mode (reduced PHI coverage). "
                "Run: python -m spacy download %s",
                self._spacy_model,
                self._spacy_model,
            )
            self.nlp = None
            self._anonymization_mode = "regex_only"

    def anonymize(self, text: str) -> AnonymizationResult:
        """Anonymize PHI from clinical text using NLP + Regex.

        Returns an AnonymizationResult with the safe text and the mapping table.
        The mapping MUST be stored via S3 Claim-Check â€” never in logs or queues.
        """
        with _get_tracer().start_as_current_span("phi.anonymize") as span:
            # STRICT_MODE applies to anonymization only; deanonymization can
            # operate purely on mapping data without NLP.
            self._ensure_nlp_loaded(strict=PHI_STRICT_MODE)

            span.set_attribute("anonymization.mode", self._anonymization_mode)

            if not self.nlp:
                logger.info(
                    "NLP model not loaded â€” applying regex-only fallback "
                    "(KVNR + DATE patterns only)."
                )

            mapping: dict[str, str] = {}

            # DESIGN DECISION â€” Counter Determinism (ADR-011):
            # Counters reset per anonymize() call. Since each OCR job is an isolated
            # invocation (one call per RabbitMQ message), <NAME_1> always starts at 1
            # within a single job's scope. Cross-job determinism is NOT required because
            # the mapping is stored per-job in S3 (mappings/{job_id}.json).
            # This was reviewed and accepted as architecturally sound.
            counters: dict[str, int] = {
                "PER": 1, "LOC": 1, "ORG": 1, "MISC": 1, "KVNR": 1, "DATE": 1,
            }

            # 1. Regex replacements first (to avoid NLP splitting errors on dates/IDs)
            def replace_kvnr(match: re.Match[str]) -> str:
                token = f"<KVNR_{counters['KVNR']}>"
                counters["KVNR"] += 1
                mapping[token] = match.group(0)
                return token

            def replace_date(match: re.Match[str]) -> str:
                token = f"<DATE_{counters['DATE']}>"
                counters["DATE"] += 1
                mapping[token] = match.group(0)
                return token

            # Apply KVNR
            tmp_text = self.kvnr_pattern.sub(replace_kvnr, text)
            # Apply DATE
            tmp_text = self.date_pattern.sub(replace_date, tmp_text)

            if not self.nlp:
                span.set_attribute("anonymization.entity_count", len(mapping))
                return AnonymizationResult(anonymized_text=tmp_text, mapping=mapping)

            # 2. SpaCy NER replacements
            doc = self.nlp(tmp_text)

            # We need to replace from back to front to not mess up character indices
            entities = []
            for ent in doc.ents:
                # Include PER, LOC, ORG, and MISC for conservative PHI stripping.
                # MISC may contain institution-adjacent or medical context data.
                if ent.label_ in ("PER", "LOC", "ORG", "MISC"):
                    entities.append((ent.start_char, ent.end_char, ent.label_, ent.text))

            # Sort descending by start character
            entities.sort(key=lambda x: x[0], reverse=True)

            final_text = tmp_text
            for start_char, end_char, label, _val in entities:
                # Check if this substring overlaps with something already replaced via regex
                segment = final_text[start_char:end_char]
                if "<" in segment and ">" in segment:
                    continue

                # Convert spaCy labels to our labels (PER -> NAME)
                token_label = label
                if label == "PER":
                    token_label = "NAME"

                # Initialize counter for dynamically added labels if they aren't there
                if token_label not in counters:
                    counters[token_label] = 1

                token = f"<{token_label}_{counters[token_label]}>"
                counters[token_label] += 1
                mapping[token] = _val

                final_text = final_text[:start_char] + token + final_text[end_char:]

            # Span attributes: ONLY counters and metadata â€” NO PHI
            span.set_attribute("anonymization.entity_count", len(mapping))

            return AnonymizationResult(anonymized_text=final_text, mapping=mapping)

    def deanonymize(self, data: Any, mapping: dict[str, str]) -> Any:
        """Traverse the data (dict, list, string) and replace tokens with original values.

        SafeExceptionHandler: Any internal errors are caught, redacted of PHI,
        and re-raised to prevent mapping data from leaking in tracebacks.
        """
        with _get_tracer().start_as_current_span("phi.deanonymize") as span:
            span.set_attribute("deanonymization.token_count", len(mapping))

            try:
                return self._deanonymize_recursive(data, mapping)
            except Exception as exc:
                error_code, safe_msg = _redact_phi_from_exception(exc)
                mark_span_error(span, exc, error_code=error_code, component="phi-anonymizer")
                logger.error(
                    "Deanonymization failed (%s): %s",
                    error_code,
                    safe_msg,
                )
                raise RuntimeError(f"{error_code}: {safe_msg}") from None

    def _deanonymize_recursive(self, data: Any, mapping: dict[str, str]) -> Any:
        """Internal recursive traversal â€” separated for clean exception handling."""
        if isinstance(data, str):
            res = data
            for token, orig in mapping.items():
                res = res.replace(token, orig)
            return res
        elif isinstance(data, list):
            return [self._deanonymize_recursive(item, mapping) for item in data]
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                new_dict[k] = self._deanonymize_recursive(v, mapping)
            return new_dict
        elif isinstance(data, BaseModel):  # Pydantic model
            dump = data.model_dump()
            restored_dump = self._deanonymize_recursive(dump, mapping)
            return type(data).model_validate(restored_dump)
        else:
            return data


