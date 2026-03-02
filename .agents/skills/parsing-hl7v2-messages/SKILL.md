---
name: parsing-hl7v2-messages
description: Guides the agent to write robust, error-tolerant Python parsers for legacy HL7 v2 pipes. Use when mapping legacy hospital data to modern formats, debugging pipe-delimited text, or dealing with ADT/ORU messages.
---

# HL7v2 Parser Skill

You are an expert in legacy clinical data integration, specifically handling unstable, non-standard HL7v2 (Pipehat) messages. Your goal is to construct robust "Left Brain" Python code that extracts data from these messages safely, anticipating broken formatting, missing segments, and non-standard delimiters.

## Core Principles

1. **Never Trust the Sender**: Hospital HL7 streams are famously broken. Expect missing fields, extra delimiters, and trailing whitespace.
2. **Defensive Extraction**: Use `try/except` blocks and safe list indexing. Never do `segments[5]` without checking the length first.
3. **Regex vs. Libraries**: For simple extraction, standard string splitting (`line.split('|')`) or regex is often more durable than strict libraries (`hl7` or `python-hl7`) that crash on malformed MSH headers.

## Workflow: Building an HL7 Parser

1. **Analyze the Message Structure**: If the user provides a raw message or a file, you can execute `scripts/hl7_analyzer.py` to get a structured breakdown of segments and field counts.
2. **Identify Target Fields**: Clarify exactly which fields are needed (e.g., `PID-3` for ID, `PID-5.1` for Family Name).
3. **Write the Extractor**: Create a Python class or function that reads the string line by line.
   - Example safe extraction:

   ```python
   pid_segment = next((line for line in lines if line.startswith("PID|")), None)
   if pid_segment:
       fields = pid_segment.split("|")
       family_name = fields[5].split("^")[0] if len(fields) > 5 else None
   ```

4. **Return Clean Data**: Output a standard Python dictionary or a Pydantic model (`generating-fhir-models` skill) representing the extracted data.

## Utility Scripts

To understand file structures before parsing, use:

```bash
python .agents/skills/parsing-hl7v2-messages/scripts/hl7_analyzer.py <path_to_hl7_file>
```

*(If the user hasn't provided the script yet, you should help scaffold it!)*
