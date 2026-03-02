"""
Patient State Updater for Clinical Scenarios.

Delegates to the canonical LlmRetryClient to generate the next MedicalEvent
based on the current PatientState and a prompt instruction.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure the canonical client is importable
_SKILL_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "integrating-local-llms" / "scripts"
)
if _SKILL_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SKILL_SCRIPTS_DIR)

from llm_retry_client import (  # noqa: E402
    LlmConfig,
    LlmConnectionError,
    LlmRetryClient,
    LlmValidationError,
)
from patient_state import MedicalEvent, PatientState  # noqa: E402

logger = logging.getLogger(__name__)

# Low temperature for deterministic state transitions;
# 800 tokens is sufficient for a single MedicalEvent JSON.
_STATE_CONFIG = LlmConfig(temperature=0.2, max_tokens=800)


def load_patient_state(file_path: Path) -> PatientState:
    """Loads the PatientState from a JSON file."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return PatientState.model_validate(data)


def save_patient_state(state: PatientState, file_path: Path) -> None:
    """Saves the PatientState to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(state.model_dump_json(indent=2))


def load_template(template_name: str) -> str:
    """Loads a prompt template from the templates/ directory."""
    template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.txt"
    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name} not found: {template_path}")
    with open(template_path, encoding="utf-8") as f:
        return f.read()


def generate_next_event(
    current_state: PatientState,
    prompt_instruction: str,
    client: LlmRetryClient | None = None,
) -> MedicalEvent | None:
    """Generate the next MedicalEvent using the canonical LlmRetryClient.

    Args:
        current_state: The current patient state.
        prompt_instruction: Instruction for what event to generate next.
        client: Optional pre-configured client instance (for testing/DI).

    Returns:
        A validated ``MedicalEvent`` or ``None`` on failure.
    """
    if client is None:
        client = LlmRetryClient(_STATE_CONFIG)

    schema_json = MedicalEvent.model_json_schema()
    state_json_str = current_state.model_dump_json(indent=2)

    template_content = load_template("state_transition")

    # Replace placeholders (simple string formatting, no magic numbers)
    system_prompt = template_content.replace("{{PATIENT_STATE}}", state_json_str)
    system_prompt = system_prompt.replace("{{PROMPT_INSTRUCTION}}", prompt_instruction)
    system_prompt = system_prompt.replace("{{JSON_SCHEMA}}", json.dumps(schema_json, indent=2))

    logger.info("Sending event generation request to local LLM...")

    try:
        new_event = client.generate_structured(
            prompt=system_prompt,
            schema=MedicalEvent,
        )
        logger.info(
            "New medical event generated: %s on %s",
            new_event.event_type,
            new_event.date,
        )
        return new_event

    except LlmValidationError as exc:
        logger.error("LLM output failed schema validation: %s", exc)
    except LlmConnectionError as exc:
        logger.error("Connection to Ollama failed: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)

    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patient State Management for Clinical Scenarios."
    )
    parser.add_argument(
        "--state-file", required=True, type=Path,
        help="Path to the PatientState JSON file",
    )
    parser.add_argument(
        "--instruction", required=True, type=str,
        help="Prompt for the next event (e.g. 'Generate the 2018 follow-up')",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if not args.state_file.exists():
        logger.error("State file not found: %s", args.state_file)
        return

    logger.info("Loading PatientState from %s", args.state_file)
    state = load_patient_state(args.state_file)

    new_event = generate_next_event(state, args.instruction)

    if new_event:
        state.add_event(new_event)
        save_patient_state(state, args.state_file)
        logger.info("State updated and saved to %s.", args.state_file)
    else:
        logger.error("Event generation failed. State was not updated.")


if __name__ == "__main__":
    main()
