# Handling Temporary Files and Outputs

## Context & Problem

During the development and testing of components, especially for generating synthetic documents (like the MedicalPdfEngine), temporary artifact dumps such as QR codes, barcodes, curves, and test PDF files were often written directly to the project root directory. Additionally, outputs were sometimes placed in unstructured flat folders like `data/fhir_output` without a defined cleanup process.
This led to severe clutter in the codebase, posing a risk that generated or corrupted files might accidentally be checked into version control or interfere with production runs.

## Architectural Rule

1. **NO Temporary Files in Project Root:** You are forbidden from writing any generated temporary files (e.g., intermediate images, test texts, logs) directly to `<project-root>` or any source folder.
2. **Use the `tempfile` Standard Library:** When creating temporary assets needed only for the duration of a process (e.g., generating a barcode image to embed in a PDF), you MUST use Python's built-in `tempfile` module.
    - Prefer `tempfile.TemporaryDirectory()` when multiple files are needed.
    - Prefer `tempfile.NamedTemporaryFile()` for single files.
    - Always rely on context managers (`with tempfile.TemporaryDirectory() as tmpdirname:`) or explicit cleanup/`__del__` methods to ensure destruction of files even if a script crashes or an exception is raised in the middle of processing.
3. **Structured Output Storage:** Persistent generated artifacts must go into specific, dedicated data subfolders (e.g., `data/inbound/<patient_id>/<encounter_id>/`) rather than flat dumps, mirroring the design defined in the dispatcher and pipeline workflows.

## Examples

### Negative Example (Anti-Pattern)

```python
# Bad: Writing directly to the project directory or unmanaged local paths.
# If an exception occurs on line 3, 'temp.png' is forever left on the disk.
temp_png_path = "temp_barcode.png"
make_barcode(temp_png_path) 
embed_barcode()
os.remove(temp_png_path)
```

### Positive Example (Best Practice)

```python
import tempfile
from pathlib import Path

class PdfEngine:
    def __init__(self):
        # Good: The OS manages cleanup if the object is garbage collected or specifically cleaned
        self._temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self._temp_dir_obj.name)

    def cleanup(self):
        if hasattr(self, '_temp_dir_obj') and self._temp_dir_obj:
             self._temp_dir_obj.cleanup()
             self._temp_dir_obj = None

    def __del__(self):
        self.cleanup()
        
    def add_barcode(self):
        # File is written to the managed OS temp directory natively, not the project tree.
        temp_file = str(self.temp_dir / "barcode.png")
        make_barcode(temp_file)
        embed_barcode()
```
