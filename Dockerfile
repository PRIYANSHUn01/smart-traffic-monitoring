# Traffic Monitoring System — Dockerfile
# Build:  docker build -t traffic-monitor .
# Run:    docker run --rm -v $(pwd)/data:/app/data traffic-monitor

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

# Default: run the API server (headless — no cv2.imshow)
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["python", "day36_test.py", "--host", "0.0.0.0", "--port", "8000"]
