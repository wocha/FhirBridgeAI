"""
extract_ocr.py — Tesseract OCR Pipeline for FhirBridgeAI
=========================================================
Reads scanned PDFs from data/inbound, applies image pre-processing
(grayscale, CLAHE contrast, Otsu threshold, deskew), extracts text
per page via Tesseract, and saves each page as a .txt file.

Usage:
    python scripts/extract_ocr.py
    python scripts/extract_ocr.py --input data/inbound --output data/ocr_output
"""

import argparse
import glob
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dependency checks — per skill requirement: "Solve, don't punt"
# ---------------------------------------------------------------------------

try:
    import numpy as np
except ImportError:
    logger.error("numpy is not installed. Run:  pip install -r scripts/requirements_ocr.txt")
    sys.exit(1)

try:
    import cv2
except ImportError:
    logger.error(
        "opencv-python is not installed. Run:  pip install -r scripts/requirements_ocr.txt"
    )
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    logger.error("Pillow is not installed. Run:  pip install -r scripts/requirements_ocr.txt")
    sys.exit(1)

try:
    from pdf2image import convert_from_path
    from pdf2image.exceptions import PDFInfoNotInstalledError
except ImportError:
    logger.error("pdf2image is not installed. Run:  pip install -r scripts/requirements_ocr.txt")
    sys.exit(1)

try:
    import pytesseract
except ImportError:
    logger.error("pytesseract is not installed. Run:  pip install -r scripts/requirements_ocr.txt")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Image pre-processing helpers
# ---------------------------------------------------------------------------


def to_grayscale(img: np.ndarray) -> np.ndarray:
    """Convert a BGR image to grayscale."""
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def apply_threshold(gray: np.ndarray) -> np.ndarray:
    """Binarize the image with Otsu's thresholding."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def deskew(img: np.ndarray) -> np.ndarray:
    """Detect skew angle from contours and correct it."""
    coords = np.column_stack(np.where(img > 0))
    if coords.shape[0] < 10:
        return img

    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    # Normalise angle to a small correction range
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Only correct if the skew is non-trivial but not insane
    if abs(angle) < 0.3 or abs(angle) > 15:
        return img

    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        img,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def preprocess_page(pil_image: Image.Image) -> np.ndarray:
    """Full pre-processing pipeline for a single page image.

    Steps:
        1. Convert to NumPy / BGR
        2. Grayscale
        3. CLAHE contrast enhancement
        4. Otsu threshold (binarisation)
        5. Deskew
    """
    cv_img = np.array(pil_image)
    if cv_img.ndim == 3 and cv_img.shape[2] == 4:  # RGBA
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGBA2BGR)
    elif cv_img.ndim == 3:
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)

    gray = to_grayscale(cv_img)
    contrasted = enhance_contrast(gray)
    binary = apply_threshold(contrasted)
    corrected = deskew(binary)
    return corrected


# ---------------------------------------------------------------------------
# OCR extraction
# ---------------------------------------------------------------------------


def extract_text(image: np.ndarray, lang: str = "deu") -> str:
    """Run Tesseract OCR on a pre-processed image."""
    try:
        text: str = pytesseract.image_to_string(image, lang=lang)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        logger.error(
            "Tesseract executable was not found on your PATH.\n"
            "  Windows : choco install tesseract   OR download from "
            "https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  Linux   : sudo apt-get install tesseract-ocr tesseract-ocr-deu\n"
            "Make sure the 'deu' (German) language pack is installed."
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


import asyncio

async def process_pdf(pdf_path: str, lang: str = "deu", dpi: int = 300) -> str:
    """Process a single PDF: convert pages → preprocess → OCR → return full text."""
    pdf_name = Path(pdf_path).stem

    logger.info(f"  Converting PDF to images at {dpi} DPI …")
    try:
        pages = await asyncio.to_thread(convert_from_path, pdf_path, dpi=dpi)
    except PDFInfoNotInstalledError:
        logger.error(
            "Poppler is not installed or not on PATH.\n"
            "  Windows : choco install poppler   OR download from "
            "https://github.com/oschwartz10612/poppler-windows/releases\n"
            "  Linux   : sudo apt-get install poppler-utils"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"  Failed to convert {pdf_path}: {e}")
        return ""

    logger.info(f"  {len(pages)} page(s) found.")

    full_text = []

    for page_num, page_img in enumerate(pages, start=1):
        logger.info(f"    Page {page_num}/{len(pages)} — preprocessing …")
        processed = await asyncio.to_thread(preprocess_page, page_img)

        logger.info(f"    Page {page_num}/{len(pages)} — running Tesseract OCR …")
        text = await asyncio.to_thread(extract_text, processed, lang=lang)
        full_text.append(text)

        char_count = len(text)
        preview = text[:80].replace("\n", " ") if text else "(leer)"
        logger.info(f"    → Page {page_num} OCR'd ({char_count} Zeichen)  {preview}…")

    logger.info(f"  ✓ Fertig: {pdf_name}")
    return "\n\n".join(full_text)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tesseract OCR Pipeline — extract text from scanned medical PDFs."
    )
    parser.add_argument(
        "--input",
        default="data/inbound",
        help="Directory containing PDF files (default: data/inbound)",
    )
    parser.add_argument(
        "--lang",
        default="deu",
        help="Tesseract language code (default: deu)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for PDF→image conversion (default: 300)",
    )
    args = parser.parse_args()

    # Validate input directory
    if not os.path.isdir(args.input):
        logger.error(
            f"Input directory not found: {args.input}\n" "Please provide a valid path with --input."
        )
        sys.exit(1)

    # Note: searching recursively into patient fallback folders
    pdf_files = sorted(glob.glob(os.path.join(args.input, "**", "*.pdf"), recursive=True))
    if not pdf_files:
        logger.error(f"No PDF files found in {args.input}")
        sys.exit(1)

    logger.info(f"Found {len(pdf_files)} PDF(s) in {args.input}")
    logger.info(f"Tesseract language: {args.lang} | DPI: {args.dpi}")
    logger.info("=" * 60)

    for i, pdf_path in enumerate(pdf_files, start=1):
        logger.info(f"[{i}/{len(pdf_files)}] {os.path.basename(pdf_path)}")
        text = await process_pdf(pdf_path, lang=args.lang, dpi=args.dpi)
        # Standalone wrapper just prints summary
        logger.info(f"Extracted {len(text)} characters total from {os.path.basename(pdf_path)}")

    logger.info("=" * 60)
    logger.info("Pipeline abgeschlossen.")


if __name__ == "__main__":
    asyncio.run(main())
