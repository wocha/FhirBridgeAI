from unittest.mock import MagicMock, patch

from pydantic import BaseModel

from fhirbridge.core.anonymizer import PiiScrubber
from fhirbridge.core.llm_client import LlmClient


# 1. Klartext Scrub/Unscrub
def test_scrub_and_unscrub_text():
    scrubber = PiiScrubber(seed=42)
    original_text = "Der Patient Max Mustermann wurde am 15.08.1985 in Berlin geboren."

    scrubbed_text = scrubber.scrub_text(original_text)

    assert "Max Mustermann" not in scrubbed_text
    assert "Berlin" not in scrubbed_text
    assert "15.08.1985" not in scrubbed_text

    unscrubbed_text = scrubber.unscrub_text(scrubbed_text)
    assert unscrubbed_text == original_text


# 2. Pydantic Rekursion
class PatientState(BaseModel):
    name: str
    city: str
    birth_date: str
    details: dict
    tags: list


def test_scrub_and_unscrub_pydantic_model():
    scrubber = PiiScrubber(seed=123)
    patient = PatientState(
        name="Sabine Müller",
        city="München",
        birth_date="12.12.1990",
        details={"doctor": "Dr. Hans Meyer", "notes": "Behandelt in Hamburg"},
        tags=["Wichtig", "Hamburg", "12.12.1990"],
    )

    scrubbed_model = scrubber.scrub_model(patient)

    assert scrubbed_model.name != "Sabine Müller"
    assert scrubbed_model.city != "München"
    assert scrubbed_model.birth_date != "12.12.1990"
    assert scrubbed_model.details["doctor"] != "Dr. Hans Meyer"
    assert scrubbed_model.details["notes"] != "Behandelt in Hamburg"
    assert scrubbed_model.tags[1] != "Hamburg"
    assert scrubbed_model.tags[2] != "12.12.1990"

    unscrubbed_model = scrubber.unscrub_model(scrubbed_model)

    assert unscrubbed_model.name == "Sabine Müller"
    assert unscrubbed_model.city == "München"
    assert unscrubbed_model.birth_date == "12.12.1990"
    assert unscrubbed_model.details["doctor"] == "Dr. Hans Meyer"
    assert unscrubbed_model.details["notes"] == "Behandelt in Hamburg"
    assert unscrubbed_model.tags[1] == "Hamburg"
    assert unscrubbed_model.tags[2] == "12.12.1990"


# 3. LLM Client Mock Test
class SimpleSchema(BaseModel):
    extracted_name: str
    extracted_city: str


from unittest.mock import AsyncMock  # noqa: E402


@patch("llm_retry_client.httpx.AsyncClient")
def test_llm_client_interceptor(mock_client_cls):
    # Determine what pseudos will be generated for "Klaus Wowereit" and "Berlin"
    scrubber = PiiScrubber(seed=999)
    pseudo_name = scrubber._register_mapping("Klaus Wowereit", scrubber.faker.name)
    pseudo_city = scrubber._register_mapping("Berlin", scrubber.faker.city)

    mock_client = AsyncMock()
    mock_client.post.return_value = MagicMock(
        raise_for_status=MagicMock(),
        json=MagicMock(
            return_value={
                "response": (
                    f'{{"extracted_name": "{pseudo_name}",' f' "extracted_city": "{pseudo_city}"}}'
                )
            }
        ),
    )
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    client = LlmClient()
    prompt = "Extrahiere Name und Stadt."
    context = "Der Patient heißt Klaus Wowereit aus Berlin."

    with patch("fhirbridge.core.llm_client.PiiScrubber") as mock_scrubber_cls:
        mock_scrubber_cls.return_value = scrubber

        result = client.generate_structured_kdl(
            prompt=prompt,
            schema_class=SimpleSchema,
            context=context,
            target_date_str="01.01.2024",
            use_anonymizer=True,
        )

    # Check that requests.post was called with scrubbed context
    call_args = mock_client.post.call_args[1]
    system_instruction = call_args["json"]["prompt"]

    assert "Klaus Wowereit" not in system_instruction
    assert "Berlin" not in system_instruction
    assert pseudo_name in system_instruction
    assert pseudo_city in system_instruction

    # Check that the final result is unscrubbed
    assert result.extracted_name == "Klaus Wowereit"
    assert result.extracted_city == "Berlin"
