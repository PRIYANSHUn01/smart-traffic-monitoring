# Smart Traffic Monitoring System

**M.Sc. Computer Science Dissertation Project**
Priyanshu Negi | Roll No. 2250121750007 | 3rd Semester
D.S.B. Campus, Kumaun University, Nainital
Supervisor: Dr. Ashish Mehta | May 2026

---

An end-to-end AI-powered traffic violation detection system built with YOLOv8, ByteTrack, FastAPI, and Streamlit. Detects helmet violations, triple-riding, and reads number plates — all in real-time from a video feed.

## Features

| Module | Description |
|--------|-------------|
| **Vehicle Detection** | Custom YOLOv8 model (`vehicle_detector.pt`) + ByteTrack for stable multi-object tracking |
| **Helmet Detection** | Crop-and-classify pipeline — flags riders without helmets |
| **Triple-Riding Detection** | IoU-based person-overlap counting per bike |
| **Number Plate OCR** | EasyOCR + 10-frame voting buffer for stable plate reads |
| **Violation Database** | SQLite with timestamped JPEG snapshots |
| **REST API** | FastAPI with 5 endpoints + Swagger `/docs` |
| **Live Dashboard** | Streamlit + Plotly auto-refresh dashboard |
| **Docker** | Full containerisation with `docker-compose` |

## Tech Stack

- **Python 3.11**
- **YOLOv8** (Ultralytics) — object detection
- **ByteTrack** — multi-object tracking (`model.track(persist=True)`)
- **OpenCV** — video I/O and frame processing
- **EasyOCR** — number plate text extraction
- **SQLite** — violation storage
- **FastAPI + Uvicorn** — REST API
- **Streamlit + Plotly** — live dashboard
- **Docker + docker-compose** — containerised deployment

## Project Structure

```
traffic_monitor/
├── config.py                 # Central config — model paths, thresholds, flags
├── pipeline.py               # Main video processing pipeline
├── api.py                    # FastAPI REST API (5 endpoints)
├── modules/
│   ├── vehicle_detector.py   # YOLOv8 + ByteTrack detection & counting
│   ├── helmet_detector.py    # Helmet violation detection
│   ├── rider_counter.py      # Triple-riding IoU detection
│   └── plate_reader.py       # EasyOCR + voting buffer
├── dashboard/
│   └── app.py                # Streamlit dashboard
├── utils/
│   ├── database.py           # SQLite + CSV logging
│   └── helpers.py            # Shared utilities
├── data/
│   ├── videos/               # Input video files
│   └── snapshots/            # Violation snapshots
├── models/
│   ├── vehicle_detector.pt   # Custom-trained two-wheeler detector
│   └── helmet_detect.pt      # Custom helmet classifier
├── reset_data.py             # One-command data reset utility
├── Dockerfile
├── Dockerfile.dashboard
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/PRIYANSHUn01/smart-traffic-monitoring.git
cd smart-traffic-monitoring

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the pipeline (webcam or video file)
python pipeline.py
# or: python pipeline.py --source path/to/video.mp4

# 4. Start the REST API
uvicorn api:app --reload --port 8000
# Swagger docs: http://localhost:8000/docs

# 5. Start the dashboard (new terminal)
streamlit run dashboard/app.py
# Dashboard: http://localhost:8501
```

## Docker (One Command)

```bash
docker-compose up
# API       → http://localhost:8000
# Dashboard → http://localhost:8501
```

## Performance (Intel i5 11th Gen, 8 GB RAM, No GPU)

| Metric | Result |
|--------|--------|
| Average FPS (CPU) | **24 fps** (YOLOv8n) |
| Vehicle Detection mAP50 | **91.2%** |
| Helmet Detection Precision | **88.1%** |
| Plate OCR Accuracy | **84.3%** (with voting) |
| API Throughput | **52 req/s** (50 threads, 0 errors) |
| Peak RAM | **1.2 GB** |

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | DB status + uptime |
| GET | `/stats` | Total counts breakdown |
| GET | `/violations` | `?limit=20` recent violations |
| GET | `/violations/search` | `?plate=UP14` fuzzy search |
| GET | `/counts/hourly` | Per-hour vehicle counts |

## Reset Data

```bash
python reset_data.py
# Options: Full reset / DB only / Logs only
```

## Development Journey

This project was built over **45 structured days**:

- **Days 1–18** — Core detection: OpenCV, YOLOv8, ByteTrack, counting line, helmet/rider/plate modules
- **Days 19–32** — Dashboard, reliability: Streamlit, Plotly, CSV logs, multi-threading, unit tests
- **Days 33–45** — Production: benchmarking, CLAHE edge cases, FastAPI, Docker, integration tests

## Testing

```bash
# Unit tests (24 test cases)
python day31_test.py

# Integration test suite (6 stages)
python day42_test.py
```

## License

This project was developed as an M.Sc. dissertation and is for academic use.

---

*Smart Traffic Monitoring System — Priyanshu Negi, Kumaun University, 2026*
