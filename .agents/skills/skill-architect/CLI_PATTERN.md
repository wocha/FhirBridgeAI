# Robust CLI Script Pattern

When writing utility scripts forFhirBridgeAI, especially those interacting with the host system or requiring heavy dependencies (like OCR, computer vision, or local models), always follow this architectural pattern.

## 1. The "Solve, Don't Punt" Principle

Scripts must handle missing dependencies explicitly instead of crashing and leaving the AI or user to figure out the fix.

Use declarative `try/except ImportError` blocks at the top of the file that print **copy-pasteable installation instructions** for both Windows and Linux.

### Example: Import Handling

```python
import sys
import logging

try:
    import pytesseract
except ImportError:
    logging.error(
        "pytesseract is not installed.\n"
        "  Windows: choco install tesseract\n"
        "  Linux: sudo apt-get install tesseract-ocr tesseract-ocr-deu\n"
        "Run: pip install pytesseract"
    )
    sys.exit(1)
```

## 2. Environment Context (Virtual Environments)

Never assume the script will run globally.

- **Windows**: When executing scripts or pip commands, always look for `.venv` and use the direct executable path: `.venv\Scripts\python.exe` or `.venv\Scripts\pip.exe`.
- **Linux/Mac**: Use `.venv/bin/python` or `.venv/bin/pip`.
Do not rely on the `python` or `pip` aliases working correctly in a sub-shell spawned by the AI.

## 3. Architecture Rules

1. **Use `argparse`**: Always provide a CLI interface. Hardcoded paths should only exist as `default="data/inbound"` arguments.
2. **Use Structured Logging**: Use Python's `logging` module configured with timestamps instead of raw `print()` statements.
3. **No Magic Numbers**: Document the reason behind specific values (e.g., `dpi=300` for OCR, or `clipLimit=2.0` for CLAHE).
