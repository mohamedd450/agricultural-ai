# ─────────────────────────────────────────────────────────────
# Agricultural AI Platform – Data Pipeline Dockerfile
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL description="Agricultural AI Data Pipeline"

# Install system dependencies for OCR and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/data-pipeline

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline source code
COPY . .

# Default: run the ingestion script
ENTRYPOINT ["python", "scripts/ingest_all_data.py"]
CMD ["--help"]
