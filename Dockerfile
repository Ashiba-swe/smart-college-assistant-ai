FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Seed database and build initial vector store
RUN python scripts/generate_sample_docs.py && \
    python scripts/seed_database.py

ENV PORT=5000
ENV FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "app:create_app('production')", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
