import logging
import re
from collections.abc import Callable
from typing import Any, TypeVar

from faker import Faker
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class PiiScrubber:
    """
    Stateful PII Scrubber for a single request lifecycle.
    Uses spaCy for NER and deterministic mappings for reversibility.
    """

    _nlp: Any = None

    def __init__(self, seed: int = 42):
        self.faker = Faker("de_DE")
        self.faker.seed_instance(seed)

        if PiiScrubber._nlp is None:
            try:
                import spacy

                try:
                    PiiScrubber._nlp = spacy.load("de_core_news_sm")
                except OSError:
                    logger.warning(
                        "spaCy model 'de_core_news_sm' not found. Attempting to download..."
                    )
                    import spacy.cli

                    spacy.cli.download("de_core_news_sm")
                    PiiScrubber._nlp = spacy.load("de_core_news_sm")
            except Exception as e:
                logger.warning(
                    f"spaCy could not be loaded ({e}). "
                    "Falling back to Regex NER for Python 3.14 compatibility."
                )
                PiiScrubber._nlp = "fallback"

        self.real_to_pseudo: dict[str, str] = {}
        self.pseudo_to_real: dict[str, str] = {}

    def _register_mapping(self, real: str, factory_method: Callable[[], str]) -> str:
        """
        Registers a real value to a pseudonym. If the real value is already
        known, returns the existing pseudonym to ensure determinism.
        """
        if real not in self.real_to_pseudo:
            pseudo = factory_method()
            # Ensure the pseudonym is unique within the request context
            while pseudo in self.pseudo_to_real:
                pseudo = factory_method()
            self.real_to_pseudo[real] = pseudo
            self.pseudo_to_real[pseudo] = real
        return self.real_to_pseudo[real]

    def scrub_text(self, text: str) -> str:
        """
        Scrub a given text using spaCy NER and Regex fallbacks.
        Generates pseudonyms for persons, locations, and dates.
        """
        if not text:
            return text

        scrubbed_text = text

        if self._nlp != "fallback":
            doc = self._nlp(text)
            # Sort entities by length descending to avoid substring collisions during replacement
            entities = sorted(doc.ents, key=lambda e: len(e.text), reverse=True)

            for ent in entities:
                if ent.label_ == "PER":
                    pseudo = self._register_mapping(ent.text, self.faker.name)
                    scrubbed_text = scrubbed_text.replace(ent.text, pseudo)
                elif ent.label_ == "LOC":
                    pseudo = self._register_mapping(ent.text, self.faker.city)
                    scrubbed_text = scrubbed_text.replace(ent.text, pseudo)
        else:
            # Fallback Regex for typical German names
            # Match consecutive capitalized words (including dots for titles like Dr.)
            capitalized_words = re.findall(
                r"\b[A-ZÄÖÜ][a-zäöüß\.]+(?:\s+[A-ZÄÖÜ][a-zäöüß\.]+)*\b", scrubbed_text
            )
            for word in sorted(set(capitalized_words), key=len, reverse=True):
                # Ignore common sentence starters
                if word not in [
                    "Der",
                    "Die",
                    "Das",
                    "In",
                    "Am",
                    "Patient",
                    "Patientin",
                    "System",
                    "Du",
                    "Schreibe",
                    "Aufgabe",
                    "Antworte",
                    "Keine",
                    "Nur",
                ]:
                    if "Berlin" in word or "München" in word or "Hamburg" in word:
                        pseudo = self._register_mapping(word.strip(), self.faker.city)
                    else:
                        pseudo = self._register_mapping(word.strip(), self.faker.name)
                    scrubbed_text = scrubbed_text.replace(word, pseudo)

        # Regex for dates (e.g. DD.MM.YYYY)
        date_pattern = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")
        dates = sorted(list(set(date_pattern.findall(scrubbed_text))), key=len, reverse=True)
        for real_date in dates:
            # Lambda returns a string representing a German date
            pseudo_date = self._register_mapping(real_date, lambda: self.faker.date("%d.%m.%Y"))
            scrubbed_text = scrubbed_text.replace(real_date, pseudo_date)

        return scrubbed_text

    def unscrub_text(self, text: str) -> str:
        """
        Restores scrubbed text back to the original using the request state.
        """
        if not text:
            return text

        # Unscrub by replacing pseudos with reals.
        # Sort pseudos by length descending to avoid substring issues.
        sorted_pseudos = sorted(self.pseudo_to_real.keys(), key=len, reverse=True)
        unscrubbed_text = text
        for pseudo in sorted_pseudos:
            unscrubbed_text = unscrubbed_text.replace(pseudo, self.pseudo_to_real[pseudo])

        return unscrubbed_text

    def scrub_dict(self, data: dict[str, Any] | list[Any] | str | Any) -> Any:
        """
        Recursively traverse dictionaries/lists and scrub all strings.
        """
        if isinstance(data, str):
            return self.scrub_text(data)
        elif isinstance(data, dict):
            return {k: self.scrub_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.scrub_dict(item) for item in data]
        return data

    def unscrub_dict(self, data: dict[str, Any] | list[Any] | str | Any) -> Any:
        """
        Recursively traverse dictionaries/lists and unscrub all strings.
        """
        if isinstance(data, str):
            return self.unscrub_text(data)
        elif isinstance(data, dict):
            return {k: self.unscrub_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.unscrub_dict(item) for item in data]
        return data

    def scrub_model(self, model: T) -> T:
        """
        Scrub a Pydantic model by dumping it to dict and validating back.
        """
        data = model.model_dump()
        scrubbed_data = self.scrub_dict(data)
        return type(model).model_validate(scrubbed_data)

    def unscrub_model(self, model: T) -> T:
        """
        Unscrub a Pydantic model by dumping it to dict and validating back.
        """
        data = model.model_dump()
        unscrubbed_data = self.unscrub_dict(data)
        return type(model).model_validate(unscrubbed_data)
