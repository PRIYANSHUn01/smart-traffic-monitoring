<div align="center">

# 🚦 Smart Traffic Monitoring System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://ultralytics.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-Academic-orange?style=for-the-badge)](#license)

<br/>

**M.Sc. Computer Science Dissertation Project**

*Priyanshu Negi · Roll No. 2250121750007 · 3rd Semester*  
*D.S.B. Campus, Kumaun University, Nainital*  
*Supervisor: Dr. Ashish Mehta · May 2026*

<br/>

> An end-to-end AI-powered traffic violation detection system that detects **helmet violations**, **triple-riding**, and **reads number plates** — all in real-time from any video feed using YOLOv8, ByteTrack, FastAPI, and Streamlit.

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ System Architecture](#️-system-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [📁 Project Structure](#-project-structure)
- [⚙️ Installation](#️-installation)
- [🚀 Quick Start](#-quick-start)
- [🐳 Docker Deployment](#-docker-deployment)
- [🌐 REST API Reference](#-rest-api-reference)
- [📊 Dashboard](#-dashboard)
- [📈 Performance Benchmarks](#-performance-benchmarks)
- [🔐 Security](#-security)
- [🧪 Testing](#-testing)
- [📅 Development Journey](#-development-journey)
- [♻️ Data Reset](#️-data-reset)
- [📄 License](#-license)

---

## ✨ Features

| Module | Description | Status |
|--------|-------------|--------|
| 🚗 **Vehicle Detection** | Custom YOLOv8 model (`vehicle_detector.pt`) + ByteTrack for stable multi-object tracking | ✅ |
| ⛑️ **Helmet Detection** | Crop-and-classify pipeline — flags every rider without a helmet | ✅ |
| 👥 **Triple-Riding Detection** | IoU-based person-overlap counting per bike, configurable thresholds | ✅ |
| 🔢 **Number Plate OCR** | EasyOCR + 10-frame voting buffer for stable, noise-resistant plate reads | ✅ |
| 🗄️ **Violation Database** | SQLite with timestamped JPEG snapshots + parallel CSV export | ✅ |
| 🌐 **REST API** | FastAPI with 5 authenticated endpoints + Swagger `/docs` | ✅ |
| 📊 **Live Dashboard** | Streamlit + Plotly real-time auto-refresh dashboard | ✅ |
| 🐳 **Docker** | Full containerisation with `docker-compose` — one command deploy | ✅ |
| 🔐 **Security Hardened** | API key auth, env-based secrets, non-root Docker, pinned deps | ✅ |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VIDEO SOURCE                             │
│                 (Webcam / MP4 / RTSP Stream)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE  (pipeline.py)                       │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   Vehicle    │───▶│    Rider     │───▶│     Helmet       │   │
│  │  Detector   │    │   Counter    │    │    Detector      │   │
│  │ YOLOv8 +    │    │ (IoU-based)  │    │  (Crop+Classify) │   │
│  │  ByteTrack  │    └──────────────┘    └──────────────────┘   │
│  └──────────────┘                                ▼              │
│                                       ┌──────────────────┐      │
│                                       │   Plate Reader   │      │
│                                       │ EasyOCR + Voting │      │
│                                       └─────────┬────────┘      │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                             ┌────────────────────▼──────────────────┐
                             │         VIOLATION ENGINE               │
                             │  (Checks: NO_HELMET / TRIPLE_RIDING)  │
                             └────────────┬──────────────────────────┘
                                          │
                    ┌─────────────────────▼──────────────────────────┐
                    │                  STORAGE                        │
                    │   SQLite DB  │  CSV Export  │  JPEG Snapshots   │
                    └─────────────────────┬──────────────────────────┘
                                          │
                 ┌────────────────────────┴───────────────────────────┐
                 │                                                     │
          ┌──────▼──────┐                                    ┌────────▼──────┐
          │  FastAPI     │                                    │  Streamlit    │
          │  REST API    │                                    │  Dashboard    │
          │ :8000/docs   │                                    │    :8501      │
          └─────────────┘                                    └───────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Detection** | YOLOv8 (Ultralytics) | Real-time object detection |
| **Tracking** | ByteTrack (`model.track`) | Stable multi-object tracking with IDs |
| **Vision** | OpenCV 4.9 | Video I/O, frame preprocessing, drawing |
| **OCR** | EasyOCR 1.7 | License plate text extraction |
| **Database** | SQLite 3 | Violation & count storage |
| **API** | FastAPI 0.111 + Uvicorn | High-performance REST API |
| **Dashboard** | Streamlit 1.35 + Plotly | Interactive live analytics |
| **Containers** | Docker + docker-compose | Reproducible deployment |
| **Language** | Python 3.11 | Core runtime |

---

## 📁 Project Structure

```
traffic_monitor/
│
├── 📄 config.py                 # Central config — paths, thresholds, flags, env-vars
├── 📄 pipeline.py               # Master video processing pipeline (entry point)
├── 📄 api.py                    # FastAPI REST API — 5 authenticated endpoints
├── 📄 reset_data.py             # One-command interactive data reset utility
│
├── 📂 modules/                  # AI detection modules
│   ├── vehicle_detector.py      # YOLOv8 + ByteTrack detection & counting line
│   ├── helmet_detector.py       # Helmet violation detection (crop-classify)
│   ├── rider_counter.py         # Triple-riding IoU-overlap detection
│   └── plate_reader.py          # EasyOCR + 10-frame voting buffer
│
├── 📂 dashboard/
│   └── app.py                   # Streamlit live dashboard + snapshot viewer
│
├── 📂 utils/
│   ├── database.py              # SQLite + CSV logging (TrafficDB class)
│   ├── helpers.py               # Shared utilities (logging, drawing, OCR, bbox)
│   └── vehicle_record.py        # VehicleRecord dataclass
│
├── 📂 data/
│   ├── videos/                  # Input video files (place .mp4 here)
│   └── snapshots/               # Auto-saved JPEG violation snapshots
│
├── 📂 models/                   # Pre-trained model weights
│   ├── vehicle_detector.pt      # Custom YOLOv8 two-wheeler detector
│   ├── helmet_detect.pt         # Custom helmet classifier
│   └── plate_detect.pt          # License plate detector
│
├── 📂 logs/                     # Runtime logs & CSV exports (auto-created)
│
├── 🐳 Dockerfile                # API container (non-root, uvicorn)
├── 🐳 Dockerfile.dashboard      # Dashboard container (non-root, streamlit)
├── 🐳 docker-compose.yml        # Orchestration (api + dashboard services)
│
├── 📄 requirements.txt          # Pinned Python dependencies
├── 📄 .env.example              # Environment variable template (copy → .env)
└── 📄 README.md                 # This file
```

---

## ⚙️ Installation

### Prerequisites

- Python **3.10+**
- `pip` package manager
- Git
- *(Optional)* Docker + docker-compose for containerised deployment
- *(Optional)* NVIDIA GPU + CUDA for faster inference

### 1. Clone the repository

```bash
git clone https://github.com/PRIYANSHUn01/smart-traffic-monitoring.git
cd smart-traffic-monitoring
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the template
cp .env.example .env

# Open .env and fill in your values:
#   API_KEY          → generate with: python -c "import secrets; print(secrets.token_hex(32))"
#   ALLOWED_ORIGINS  → your dashboard URL (e.g. http://localhost:8501)
#   EMAIL_*          → optional email alert credentials
```

### 5. Place your model files

```
models/
├── vehicle_detector.pt   ← custom YOLOv8 two-wheeler model
├── helmet_detect.pt      ← custom helmet classifier
└── plate_detect.pt       ← license plate detector
```

> **Note:** If models are not present, the system automatically falls back to the pretrained `yolov8n.pt` COCO model (downloads on first run).

---

## 🚀 Quick Start

### Run the full pipeline (video / webcam)

```bash
# Default video source (set in .env or config.py)
python pipeline.py

# Specify a video file
python pipeline.py --source data/videos/traffic.mp4

# Use webcam
python pipeline.py --source 0

# Disable individual modules
python pipeline.py --no-plate        # skip OCR
python pipeline.py --no-helmet       # skip helmet detection
python pipeline.py --no-riders       # skip rider counting
```

**Keyboard shortcuts while running:**

| Key | Action |
|-----|--------|
| `Q` | Quit the pipeline |
| `R` | Reset vehicle counters |
| `S` | Save current frame manually |

### Start the REST API

```bash
uvicorn api:app --reload --port 8000

# Interactive docs:
# → http://localhost:8000/docs   (Swagger UI)
# → http://localhost:8000/redoc  (ReDoc)
```

### Start the live dashboard

```bash
streamlit run dashboard/app.py
# → http://localhost:8501
```

---

## 🐳 Docker Deployment

### One-command start

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API_KEY and settings

# Start all services
docker-compose up -d

# Services:
#   API       → http://localhost:8000
#   Dashboard → http://localhost:8501
```

### Individual containers

```bash
# Build and run API only
docker build -t traffic-monitor-api .
docker run -d -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  traffic-monitor-api

# Build and run Dashboard only
docker build -f Dockerfile.dashboard -t traffic-dashboard .
docker run -d -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  traffic-dashboard
```

### Stop services

```bash
docker-compose down
```

---

## 🌐 REST API Reference

> **Authentication:** All data endpoints require an `X-API-Key` header.  
> Set `API_KEY` in your `.env` file. The `/health` endpoint is public.

### Base URL: `http://localhost:8000`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health` | ❌ Public | Database status + API uptime |
| `GET` | `/stats` | ✅ Required | Total counts + violation breakdown |
| `GET` | `/violations` | ✅ Required | Recent violations (`?limit=20`, max 500) |
| `GET` | `/violations/search` | ✅ Required | Search by plate (`?plate=UP14`) |
| `GET` | `/counts/hourly` | ✅ Required | Per-hour vehicle counts for today |

### Example requests

```bash
# Health check (no auth)
curl http://localhost:8000/health

# Get recent violations (with API key)
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:8000/violations?limit=10

# Search by plate number
curl -H "X-API-Key: your_api_key_here" \
     "http://localhost:8000/violations/search?plate=UP14"

# Summary stats
curl -H "X-API-Key: your_api_key_here" \
     http://localhost:8000/stats
```

### Sample response — `/violations`

```json
{
  "count": 2,
  "violations": [
    {
      "id": 42,
      "timestamp": "2026-05-25T14:30:00",
      "track_id": 7,
      "plate_number": "UP14AB1234",
      "vehicle_type": "two-wheeler",
      "rider_count": 3,
      "helmet_status": "without_helmet",
      "violation_type": "TRIPLE_RIDING",
      "snapshot_path": "data/snapshots/20260525_143000_id7_TRIPLE_RIDING.jpg",
      "frame_number": 1024
    }
  ]
}
```

---

## 📊 Dashboard

The Streamlit dashboard auto-refreshes every **3 seconds** and provides:

- 📈 **KPI Metrics** — Total vehicles, violations, helmet violations, triple riding count, violation rate
- 🥧 **Vehicle Type Breakdown** — Pie chart (motorcycle / bicycle / two-wheeler)
- 📊 **Violation Type Chart** — Bar chart by violation category
- 🪖 **Helmet Status** — Donut chart (with / without / unknown)
- 🏍️ **Rider Distribution** — Solo / Double / Triple+ bar chart
- 🔢 **Number Plate Log** — Most recent plate detections table
- ⏰ **Hourly Traffic Count** — Today's vehicle count per hour
- 📸 **Violation Snapshots** — Auto-saved JPEG thumbnails
- 🔍 **Filter & Search** — Filter by violation type, search by plate
- 📥 **CSV Export** — Download full violation log

**Access:** `http://localhost:8501`

---

## 📈 Performance Benchmarks

> Tested on: Intel Core i5 11th Gen · 8 GB RAM · No dedicated GPU (CPU only)

| Metric | Result |
|--------|--------|
| 🎞️ Average FPS (CPU) | **24 fps** — YOLOv8n, skip_frames=2 |
| 🎯 Vehicle Detection mAP50 | **91.2%** |
| ⛑️ Helmet Detection Precision | **88.1%** |
| 🔢 Plate OCR Accuracy | **84.3%** (with 10-frame voting) |
| ⚡ API Throughput | **52 req/s** (50 concurrent threads, 0 errors) |
| 💾 Peak RAM Usage | **1.2 GB** |
| 📦 Model Size (vehicle_detector.pt) | **6.5 MB** (YOLOv8n) |

---

## 🔐 Security

This project has been hardened against **12 security vulnerabilities** identified in a full codebase audit:

| # | Issue | Severity | Fix Applied |
|---|-------|----------|-------------|
| 1 | Hardcoded email credentials | 🔴 HIGH | Moved to `.env` / `os.getenv()` |
| 2 | Wildcard CORS (`allow_origins=["*"]`) | 🔴 HIGH | Restricted via `ALLOWED_ORIGINS` env var |
| 3 | No API authentication | 🔴 HIGH | `X-API-Key` header auth on all data endpoints |
| 4 | Error details leaked in `/health` | 🟠 MED | Generic error returned; details logged server-side |
| 5 | Absolute DB path exposed in UI | 🟠 MED | Only filename shown (`os.path.basename`) |
| 6 | Docker containers running as root | 🟠 MED | Non-root `appuser` added to both Dockerfiles |
| 7 | Dockerfile CMD ran a test script | 🟠 MED | Fixed to `uvicorn api:app` |
| 8 | Unbounded in-memory set (DoS risk) | 🟡 LOW | Bounded `OrderedDict` (max 50,000 entries) |
| 9 | Logger ignored `LOG_LEVEL` config | 🟡 LOW | Logger reads `LOG_LEVEL` from config/env |
| 10 | Unpinned dependencies | 🟡 LOW | All deps pinned to exact versions |
| 11 | ReDoS via unsanitised plate search | 🟡 LOW | `re.escape()` applied before `str.contains()` |
| 12 | Malformed `.gitignore` glob | 🟡 LOW | Broken brace-expression removed |

### Setup security (required)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate a strong API key
python -c "import secrets; print(secrets.token_hex(32))"

# 3. Edit .env — set API_KEY, ALLOWED_ORIGINS, and email credentials
```

---

## 🧪 Testing

The project includes **45 structured test/practice scripts** covering every module:

```bash
# Core module unit tests (24 test cases)
python day31_test.py

# Full integration test suite (6 stages)
python day42_test.py

# API load test (52 req/s benchmark)
python day40_test.py

# Helmet detection edge cases
python day35_test.py

# Security & configuration validation
python day39_test.py
```

### Test coverage areas

| Test File | Coverage Area |
|-----------|--------------|
| `day07–day15` | Vehicle detection, tracking, counting |
| `day16–day22` | Helmet, rider, plate detection modules |
| `day23–day31` | Dashboard, CSV, multi-threading, unit tests |
| `day32–day40` | Benchmarking, CLAHE, FastAPI, load testing |
| `day41–day45` | Integration tests, security, final validation |

---

## 📅 Development Journey

Built over **45 structured days** following a day-by-day learning progression:

| Phase | Days | Topics |
|-------|------|--------|
| **Foundation** | 1–7 | Python, OpenCV, frame capture, basic YOLO inference |
| **Detection Core** | 8–18 | YOLOv8 classes, ByteTrack, counting line, helmet & rider modules, plate OCR |
| **Data & Dashboard** | 19–28 | SQLite, CSV, Streamlit dashboard, Plotly charts, email alerts, config management |
| **Reliability** | 29–35 | Multi-threading, unit tests, snapshot CLAHE edge cases |
| **Production** | 36–45 | FastAPI, Swagger, Docker, benchmarking, security hardening, integration tests |

---

## ♻️ Data Reset

```bash
python reset_data.py
```

Interactive menu with three options:

```
[1] Full reset   — DB + CSV + Snapshots + Logs + Charts
[2] DB only      — Clear violations and vehicle counts
[3] Logs only    — Delete log files and chart HTMLs
[4] Cancel
```

---

## 📄 License

This project was developed as an **M.Sc. Computer Science dissertation** at Kumaun University, Nainital and is intended for **academic and educational use**.

---

<div align="center">

**Smart Traffic Monitoring System**  
*Priyanshu Negi · D.S.B. Campus, Kumaun University, Nainital · 2026*

[![GitHub](https://img.shields.io/badge/GitHub-PRIYANSHUn01-181717?style=flat-square&logo=github)](https://github.com/PRIYANSHUn01/smart-traffic-monitoring)

</div>
