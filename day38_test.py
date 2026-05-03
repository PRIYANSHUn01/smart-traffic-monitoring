# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 38 — day38_test.py
#  Topic: Docker containerization — package the system into containers
#
#  NEW today:
#    ✓ Generate Dockerfile for the pipeline
#    ✓ Generate docker-compose.yml for pipeline + dashboard + API
#    ✓ Generate .dockerignore
#    ✓ Verify Docker is installed and show how to build/run
#
#  Run:  python day38_test.py              (generate Docker files)
#  Run:  python day38_test.py --check      (check Docker availability)
#  Run:  python day38_test.py --build      (attempt docker build)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse, subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_logger
log = get_logger("day38")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── File content templates ─────────────────────────────────────────────────────

DOCKERFILE = """\
# Traffic Monitoring System — Dockerfile
# Build:  docker build -t traffic-monitor .
# Run:    docker run --rm -v $(pwd)/data:/app/data traffic-monitor

FROM python:3.10-slim

# System dependencies for OpenCV + EasyOCR
RUN apt-get update && apt-get install -y --no-install-recommends \\
    libgl1-mesa-glx \\
    libglib2.0-0 \\
    libsm6 \\
    libxext6 \\
    libxrender-dev \\
    ffmpeg \\
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
"""

DOCKERFILE_DASHBOARD = """\
# Streamlit Dashboard — Dockerfile
# Build:  docker build -f Dockerfile.dashboard -t traffic-dashboard .
# Run:    docker run --rm -p 8501:8501 -v $(pwd)/data:/app/data traffic-dashboard

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", \\
     "--server.port=8501", "--server.address=0.0.0.0", \\
     "--server.headless=true"]
"""

DOCKER_COMPOSE = """\
# docker-compose.yml — Traffic Monitoring System
# Start all services: docker-compose up
# Stop:               docker-compose down

version: "3.9"

services:

  # ── REST API ──────────────────────────────────────────────────────────
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: traffic-monitor-api
    container_name: traffic_api
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./models:/app/models
    environment:
      - PYTHONUNBUFFERED=1
      - DB_PATH=/app/data/traffic.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ── Streamlit Dashboard ───────────────────────────────────────────────
  dashboard:
    build:
      context: .
      dockerfile: Dockerfile.dashboard
    image: traffic-monitor-dashboard
    container_name: traffic_dashboard
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DB_PATH=/app/data/traffic.db
    depends_on:
      - api
    restart: unless-stopped

volumes:
  data:
  logs:
"""

DOCKERIGNORE = """\
# .dockerignore — files excluded from Docker build context
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.env.*
*.egg-info/
dist/
build/
.git/
.gitignore
*.md
tests/
.pytest_cache/
.mypy_cache/

# Large data files — mount as volumes instead
data/videos/
data/snapshots/
*.db
*.sqlite

# Model weights — download at runtime or mount
models/*.pt

# Logs
logs/
*.log
"""

REQUIREMENTS = """\
# Core detection
ultralytics>=8.0.0
opencv-python-headless>=4.8.0

# API
fastapi>=0.100.0
uvicorn[standard]>=0.23.0

# Dashboard
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0

# OCR (optional — comment out if not needed)
easyocr>=1.7.0

# Utilities
requests>=2.31.0
psutil>=5.9.0
"""


# ── Generator ─────────────────────────────────────────────────────────────────

def generate_docker_files(out_dir):
    files = {
        "Dockerfile":            DOCKERFILE,
        "Dockerfile.dashboard":  DOCKERFILE_DASHBOARD,
        "docker-compose.yml":    DOCKER_COMPOSE,
        ".dockerignore":         DOCKERIGNORE,
    }

    req_path = os.path.join(out_dir, "requirements.txt")
    if not os.path.exists(req_path):
        files["requirements.txt"] = REQUIREMENTS

    created = []
    for fname, content in files.items():
        path = os.path.join(out_dir, fname)
        if os.path.exists(path):
            print(f"  ↷  {fname}  (already exists — skipping)")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓  {fname}")
        created.append(fname)

    return created


# ── Docker check ──────────────────────────────────────────────────────────────

def check_docker():
    print("\n  Checking Docker availability…\n")
    for cmd, label in [
        (["docker", "--version"],         "Docker CLI"),
        (["docker-compose", "--version"],  "docker-compose"),
        (["docker", "compose", "version"], "docker compose (plugin)"),
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                ver = r.stdout.strip().split("\n")[0]
                print(f"  ✓  {label}: {ver}")
            else:
                print(f"  ✗  {label}: not available")
        except FileNotFoundError:
            print(f"  ✗  {label}: not found in PATH")
        except Exception as e:
            print(f"  ✗  {label}: {e}")


def try_build(out_dir):
    print("\n  Attempting: docker build -t traffic-monitor .\n")
    try:
        result = subprocess.run(
            ["docker", "build", "-t", "traffic-monitor", "."],
            cwd=out_dir,
            timeout=300,
        )
        if result.returncode == 0:
            print("\n  ✓  Build succeeded — image: traffic-monitor")
            print("  Run:  docker run --rm -v $(pwd)/data:/app/data -p 8000:8000 traffic-monitor")
        else:
            print("\n  ✗  Build failed — see output above")
    except FileNotFoundError:
        print("  Docker not installed. Install from https://docs.docker.com/get-docker/")
    except subprocess.TimeoutExpired:
        print("  Build timed out (>5 min) — Docker may be pulling base image")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 38 — Docker Containerization")
    parser.add_argument("--check", action="store_true", help="Check Docker availability")
    parser.add_argument("--build", action="store_true", help="Run docker build")
    parser.add_argument("--outdir", default=BASE_DIR)
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 38 — Docker Containerization")
    print("=" * 65)

    print("\n  Generating Docker configuration files…\n")
    created = generate_docker_files(args.outdir)

    if created:
        print(f"\n  Created {len(created)} file(s) in: {args.outdir}")
    else:
        print("\n  All files already exist.")

    print("\n  ── HOW TO USE ───────────────────────────────────────────────")
    print("""
  1. Build the API image:
       docker build -t traffic-monitor .

  2. Build the dashboard image:
       docker build -f Dockerfile.dashboard -t traffic-dashboard .

  3. Start everything with docker-compose:
       docker-compose up

  4. Open in browser:
       API docs:  http://localhost:8000/docs
       Dashboard: http://localhost:8501

  5. Mount real video files:
       docker run --rm \\
         -v $(pwd)/data:/app/data \\
         -p 8000:8000 \\
         traffic-monitor

  6. Stop:
       docker-compose down
""")

    if args.check:
        check_docker()

    if args.build:
        try_build(args.outdir)

    print("  ── WHAT'S IN EACH FILE ──────────────────────────────────────")
    print("""
  Dockerfile            — API server (uvicorn, port 8000)
  Dockerfile.dashboard  — Streamlit dashboard (port 8501)
  docker-compose.yml    — Both services + shared volume mounts
  .dockerignore         — Excludes large files from build context
  requirements.txt      — All Python dependencies (created if missing)
""")
    print("  Next → python day39_test.py  (Production configuration)")
