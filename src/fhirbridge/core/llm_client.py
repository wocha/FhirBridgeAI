"""
LLM Client Facade for FhirBridgeAI.

Thin facade over the canonical ``LlmRetryClient`` that adds domain-specific
features for KDL document generation:
- PII scrubbing via ``PiiScrubber``
- Year-hallucination detection and self-correction
- ``DocumentContent``-bound type variable

All HTTP transport, retry logic, and exponential backoff are delegated to
``LlmRetryClient`` from the ``integrating-local-llms`` skill.
"""

import json
import logging
import re

# Canonical client import — single source of truth for Ollama interaction
import sys
from pathlib import Path
from typing import TypeVar

from fhirbridge.core.anonymizer import PiiScrubber
from fhirbridge.models.kdl_document import DocumentContent

_SKILL_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / ".agents"
    / "skills"
    / "integrating-local-llms"
    / "scripts"
)
if _SKILL_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SKILL_SCRIPTS_DIR)

from llm_retry_client import LlmConfig, LlmRetryClient, LlmValidationError  # noqa: E402

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DocumentContent)

# ---------------------------------------------------------------------------
# Pre-configured defaults for KDL generation
# ---------------------------------------------------------------------------

# Temperature 0.3 balances determinism with enough creativity for realistic
# medical prose.  num_predict 1200 covers a typical 1-page discharge brief.
_KDL_CONFIG = LlmConfig(temperature=0.3, max_tokens=1200)


class LlmClient:
    """Domain-specific facade for generating structured KDL documents.

    Preserves the original ``generate_structured_kdl()`` API so all existing
    callers (``synthea_bridge``, ``dispatch_documents``, ``generate_findings``,
    ``generate_synthetic_patients``) continue to work without code changes.
    """

    def __init__(
        self,
        config: LlmConfig | None = None,
    ) -> None:
        self._client = LlmRetryClient(config or _KDL_CONFIG)

    async def generate_structured_kdl(
        self,
        prompt: str,
        schema_class: type[T],
        context: str = "",
        target_date_str: str = "",
        max_retries: int = 3,
        use_anonymizer: bool = True,
    ) -> T:
        """Generate structured JSON matching a KDL Pydantic schema.

        Adds domain logic on top of the canonical retry client:
        1. Optional PII scrubbing before sending the prompt to the LLM.
        2. Year-hallucination detection after successful validation.

        Args:
            prompt: The clinical generation instruction.
            schema_class: A ``DocumentContent`` subclass.
            context: Patient demographics and clinical context.
            target_date_str: The target document date (DD.MM.YYYY).
            max_retries: Override for the retry count (default 3).
            use_anonymizer: Whether to scrub PII before generation.

        Returns:
            A validated instance of ``schema_class``.

        Raises:
            RuntimeError: If generation fails after all retries.
        """
        scrubber = PiiScrubber() if use_anonymizer else None

        if scrubber:
            prompt = scrubber.scrub_text(prompt)
            context = scrubber.scrub_text(context)

        # Build the allowed-years set for hallucination detection
        target_year = target_date_str.split(".")[-1] if "." in target_date_str else ""
        allowed_years = {
            "2000",
            "2005",
            "2010",
            "2015",
            "2016",
            "2017",
            "2018",
            "2019",
            "2020",
            "2021",
            "2022",
            "2023",
            "2024",
            "2025",
            "2026",
        }
        allowed_years.update(re.findall(r"\b(19\d{2}|20\d{2})\b", context))

        # Build system context with date constraint
        system_context = (
            f"HEUTIGES DATUM: {target_date_str}. "
            f"Erstelle den Text so, als wäre HEUTE dieser Tag.\n"
            f"Kontext: {context}"
        )

        # Use a temporary config with the caller's max_retries if different
        client = self._client
        if max_retries != client.config.max_retries:
            override_config = client.config.model_copy(update={"max_retries": max_retries})
            client = LlmRetryClient(override_config)


        try:
            parsed_obj = await client.generate_structured(
                prompt=prompt,
                schema=schema_class,
                system_context=system_context,
            )
        except LlmValidationError as exc:
            raise RuntimeError("LLM generation failed to meet schema constraints.") from exc

        # --- Post-processing: unscrub PII ---
        if scrubber:
            raw_dict = json.loads(parsed_obj.model_dump_json())
            unscrubbed_dict = scrubber.unscrub_dict(raw_dict)
            parsed_obj = schema_class.model_validate(unscrubbed_dict)

        # --- Post-processing: year hallucination check ---
        if hasattr(parsed_obj, "content_paragraphs"):
            all_text = " ".join(parsed_obj.content_paragraphs)
            found_years = re.findall(r"\b(19\d{2}|20\d{2})\b", all_text)
            hallucinated = [y for y in found_years if y not in allowed_years]
            if hallucinated and target_year not in hallucinated:
                logger.warning(
                    "Year hallucination detected (found %s, expected %s). "
                    "Attempting one correction pass.",
                    hallucinated,
                    target_year,
                )
                correction_prompt = (
                    f"WARNUNG: Du hast fälschlicherweise historische Jahre wie "
                    f"{hallucinated} erwähnt. Nutze AUSSCHLIESSLICH relevante "
                    f"Daten ({sorted(allowed_years)}).\n{prompt}"
                )

                try:
                    parsed_obj = await client.generate_structured(
                        prompt=correction_prompt,
                        schema=schema_class,
                        system_context=system_context,
                    )
                except LlmValidationError:
                    pass  # Keep the original parsed_obj

        return parsed_obj  # type: ignore[no-any-return]
