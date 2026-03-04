import asyncio
import logging
from pydantic import BaseModel, Field
from fhirbridge.core.llm import LlmRetryClient, LlmConfig, LlmValidationError

logging.basicConfig(level=logging.INFO)

class TestSchema(BaseModel):
    hello: str = Field(..., description="Just a greeting")

async def test_tenacity():
    client = LlmRetryClient(LlmConfig(max_retries=3, initial_backoff_seconds=0.1, inference_engine="vllm"))

    attempts = 0
    async def mock_execute(*args, **kwargs):
        nonlocal attempts
        attempts += 1
        print(f"\n--- Mock execution attempt {attempts} called ---")
        return "invalid json output"
    
    client._execute_http_with_backoff = mock_execute

    try:
        await client.generate_structured("say hello", schema=TestSchema)
    except LlmValidationError as e:
        print("\n=== Caught LlmValidationError successfully! ===")
        print(f"Total attempts made: {attempts}")
        print("Error content:")
        # Show that the Prompt was updated correctly with the feedback chunk
        print(str(e))
        return

    print("\nTest failed: Should have raised LlmValidationError")

if __name__ == "__main__":
    asyncio.run(test_tenacity())
