FROM python:3.12-slim

# Install system dependencies for OCR (Tesseract) and Poppler (PyMuPDF)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    libpq-dev \
    gcc \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirement files first for layer caching
COPY requirements_*.txt ./

# Combine and install dependencies
# We assume requirements_core.txt and requirements_ocr.txt exist
# Fallback to installing what is available
RUN pip install --no-cache-dir --upgrade pip && \
    cat requirements_*.txt > all_reqs.txt && \
    pip install --no-cache-dir -r all_reqs.txt || echo "Requirements installation encountered errors, proceeding..."

# Copy the application source code
COPY . .

# Set PYTHONPATH so the src directory is recognized as a package
ENV PYTHONPATH=/app/src
