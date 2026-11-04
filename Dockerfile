# NewsLens — Minimal Python 3.12 Container
FROM python:3.12-slim

# Prevent Python from writing pyc files to disc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, model artifacts, and data
COPY src/ ./src/
COPY models/ ./models/
COPY data/ ./data/
COPY pyproject.toml .

# Install newslens package in editable/package mode
RUN pip install --no-cache-dir -e .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "src/newslens/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
