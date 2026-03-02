import argparse
import sys
from pathlib import Path

import cv2
import fitz  # PyMuPDF
import numpy as np
import pytesseract

_SKILL_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent
    / "integrating-local-llms" / "scripts"
)
if _SKILL_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SKILL_SCRIPTS_DIR)
from llm_retry_client import LlmConfig, LlmRetryClient

# Config
MODEL_NAME = "mistral-nemo"

def preprocess_image_for_ocr(img_cv):
    """Applies basic computer vision techniques to improve OCR accuracy."""
    print("  -> Pre-processing image (Grayscale, Otsu)...")
    # 1. Grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # 2. Otsu's thresholding
    # Adding a slight Gaussian blur minimizes noise
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, processed_img = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return processed_img

def load_prompt_template():
    """Loads the mistral prompt template from the templates directory."""
    template_path = Path(__file__).parent.parent / "templates" / "ocr_cleanup_prompt.txt"
    try:
        with open(template_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Template not found at {template_path}")
        return "Bereinige den folgenden fehlerhaften OCR-Text eines Arztdokumentes. Output als reinen Text."

_OCR_CONFIG = LlmConfig(temperature=0.1, max_tokens=1500)

def cleanup_text_with_local_llm(raw_text):
    """Sends raw OCR text to local Mistral-NeMo for cleanup."""
    system_prompt = load_prompt_template()

    prompt = f"--- ROH-TEXT ANFANG ---\n{raw_text}\n--- ROH-TEXT ENDE ---\n\nBereinigter Text:"

    print(f"  -> Sending text to local {MODEL_NAME} for cleanup...")
    client = LlmRetryClient(_OCR_CONFIG)

    try:
        return client.generate_text(prompt=prompt, system_context=system_prompt)
    except Exception as e:
        print(f"  [!] Error calling local LLM: {e}")
        return f"[LLM CLEANUP FAILED] Original OCR Text Follows:\n\n{raw_text}"

def process_pdf(pdf_path):
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        print(f"Error: File '{pdf_path}' not found.")
        return

    print(f"--- Starting Local Extraction Pipeline for {pdf_path_obj.name} ---")

    print("1. Opening PDF with PyMuPDF...")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    complete_clean_text = []

    for page_num in range(len(doc)):
        print(f"\nProcessing Page {page_num + 1}/{len(doc)}")

        # Extract image from page using fitz
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)

        # Convert fitz pixmap to numpy array for OpenCV
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n == 4: # RGBA
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        elif pix.n == 3: # RGB
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        else: # Grayscale
            img_cv = cv2.cvtColor(img_np, cv2.COLOR_GRAY2BGR)

        # CV Preprocessing
        processed_img = preprocess_image_for_ocr(img_cv)

        # Tesseract
        print("  -> Running Tesseract OCR (German)...")
        try:
            raw_ocr = pytesseract.image_to_string(processed_img, lang='deu')
        except Exception as e:
            print(f"  [!] Tesseract Error: {e}. Ensure Tesseract is installed and in PATH.")
            continue

        if not raw_ocr.strip():
            print("  -> No text found on this page.")
            continue

        # LLM Cleanup
        clean_text = cleanup_text_with_local_llm(raw_ocr)
        complete_clean_text.append(f"--- SEITE {page_num + 1} ---\n{clean_text}")

    # Save output
    output_path = pdf_path_obj.with_suffix('.clean.txt')
    print(f"\n2. Saving unified clean output to: {output_path}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(complete_clean_text))

    print("--- Pipeline Finished Successfully ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Medical PDF OCR & LLM Cleanup Pipeline")
    parser.add_argument("pdf_path", help="Absolute or relative path to the PDF file to process.")
    args = parser.parse_args()

    process_pdf(args.pdf_path)
