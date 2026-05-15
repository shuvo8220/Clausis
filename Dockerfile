FROM python:3.12-slim

# System deps for PyMuPDF + Tesseract + Bengali language support
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ben \
    libgl1 \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install with increased timeout
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p data/sample_docs data/outputs data/chroma_db

EXPOSE 8000

# Initialize database and run server
CMD ["sh", "-c", "python -c 'from src.database.connection import init_db; init_db()' && uvicorn src.api:app --host 0.0.0.0 --port 8000"]
