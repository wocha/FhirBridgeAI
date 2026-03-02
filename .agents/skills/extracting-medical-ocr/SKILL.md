---
name: extracting-medical-ocr
description: Guides the agent to extract clean text from scanned medical PDFs. It forcefully delegates the extraction to a local script to preserve cloud context and reduce token costs.
---

# Medical OCR Extractor ("Gold Standard" Routing)

You are a Python Vision & Data Pipeline Engineer. Your objective is to extract clean, reliable text from scanned medical PDFs.

## 🚨 CORE DIRECTIVE: NEVER READ RAW PDFs YOURSELF 🚨

To conserve cloud resources and token limits, you must **NEVER** attempt to read or analyze raw OCR text yourself. You must **ALWAYS** delegate this task to the provided local extraction script.

Raw OCR data creates massive context windows, inflates token costs, and pushes non-essential execution into the cloud context.

## Workflow: Extracting Text

When the user asks you to extract text, process a PDF, or run an OCR pipeline, follow these exact steps:

1. **Locate the target PDF**: Ensure you have the absolute path to the PDF the user wants to process.
2. **Execute Local Delegation**: Run the following script using the project's virtual environment:

   ```bash
   python .agents/skills/extracting-medical-ocr/scripts/local_extract.py <path_to_pdf>
   ```

3. **Wait for output**: The script will handle all heavy lifting:
   - OpenCV Image Processing (Otsu thresholding, Grayscaling)
   - Tesseract OCR Extraction
   - **Local LLM cleanup** via Mistral NeMo running on `localhost:11434`
4. **Use Structured Output**: The script will generate a clean `.clean.txt` file next to the original PDF.
   - Use the `view_file` tool to read **this clean output file**, **NOT** the raw PDF.
   - You can then use the cleanly extracted text to build FHIR JSONs or write summaries as requested by the user.

## Architecture Context

- **Routing**: This `SKILL.md` acts as the brain, routing you to the correct tools.
- **Muscles**: The actual work is done by `scripts/local_extract.py` which runs locally on the user's machine.
- **Memory**: The prompt template used by the local LLM is stored in `templates/ocr_cleanup_prompt.txt`. You do not need to read it unless explicitly asked to modify it.
