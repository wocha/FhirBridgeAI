from pydantic import BaseModel, Field


class AnonymizationResult(BaseModel):
    """Result of the anonymization process containing the safe text and the mapping table."""
    anonymized_text: str = Field(..., description="The medical text with PHI replaced by tokens like [PER_1].")
    mapping: dict[str, str] = Field(..., description="Mapping from tokens (e.g. '[PER_1]') to original text.")

class DeanonymizeRequest(BaseModel):
    """Request to reverse the anonymization on an LLM output."""
    target_data: str | dict | list = Field(..., description="The target data containing tokens.")
    mapping: dict[str, str] = Field(..., description="The mapping dict to replace tokens with original PHI.")
