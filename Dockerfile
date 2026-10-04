FROM python:3.11-slim

WORKDIR /app

# System deps for pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download embedding model at build time to avoid cold-start delay
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-large-en-v1.5')"

EXPOSE 8000 8501

# Default: start API. Override CMD to run Streamlit or pipeline.
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
