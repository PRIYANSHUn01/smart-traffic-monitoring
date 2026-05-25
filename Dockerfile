# Traffic Monitoring System — Dockerfile (API)
# Build:  docker build -t traffic-monitor-api .
# Run:    docker run --rm -p 8000:8000 -v $(pwd)/data:/app/data traffic-monitor-api

FROM python:3.10-slim

# System dependencies for OpenCV + EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data/videos data/snapshots logs models

# VUL-7 FIX: run as a non-root user for container security hardening
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# VUL-8 FIX: was pointing to day36_test.py — now correctly runs the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
