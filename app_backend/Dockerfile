FROM python:3.12-slim

WORKDIR /service

# Install system dependencies for PDF processing and chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application source into an 'app_backend' subdirectory so imports work
COPY . ./app_backend

# Persist ChromaDB data as a volume
VOLUME ["/service/app_backend/chroma_db"]

# Expose FastAPI port
EXPOSE 8000

CMD ["uvicorn", "app_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
