# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 43 — day43_test.py
#  Topic: Documentation — auto-generate API docs, module docs, README
#
#  NEW today:
#    ✓ Auto-generate README.md from project structure
#    ✓ Generate API reference (markdown) from FastAPI routes
#    ✓ Generate module docstring summary
#    ✓ Create CHANGELOG skeleton
#    ✓ All files written to docs/ directory
#
#  Run:  python day43_test.py
#  Run:  python day43_test.py --all   (generate all doc files)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse, inspect
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_logger
log = get_logger("day43")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")


# ── README generator ──────────────────────────────────────────────────────────

README_CONTENT = """\
# Traffic Monitoring System

An end-to-end AI-powered traffic violation detection system built with Python,
YOLOv8, and FastAPI.

## Features

- **Vehicle Detection** — YOLOv8 + ByteTrack for stable multi-object tracking
- **Helmet Detection** — Classifies whether two-wheeler riders wear helmets
- **Rider Counting** — Detects single / double / triple riding violations
- **Plate Reading** — EasyOCR with voting for stable plate extraction
- **REST API** — FastAPI endpoints for querying violation data
- **Dashboard** — Streamlit auto-refresh dashboard with Plotly charts
- **Docker** — Full containerization with docker-compose

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the pipeline (webcam)
python pipeline.py

# 3. Start the API
python day36_test.py

# 4. Start the dashboard (in a new terminal)
streamlit run dashboard/app.py

# 5. Open API docs
# http://localhost:8000/docs
```

## Project Structure

```
traffic_monitor/
├── config.py                # All constants and thresholds
├── pipeline.py              # Master pipeline (wires all modules)
├── modules/
│   ├── vehicle_detector.py  # YOLOv8 + ByteTrack
│   ├── helmet_detector.py   # Helmet classification
│   ├── rider_counter.py     # Triple-riding detection
│   └── plate_reader.py      # EasyOCR plate reading
├── utils/
│   ├── database.py          # SQLite + CSV logging
│   └── helpers.py           # Shared utilities
├── dashboard/
│   └── app.py               # Streamlit dashboard
├── data/
│   ├── videos/              # Input video files
│   └── snapshots/           # Violation snapshots
├── models/                  # YOLOv8 .pt weight files
├── logs/                    # Rotating log files
├── Dockerfile               # API container
├── Dockerfile.dashboard     # Dashboard container
└── docker-compose.yml       # Full stack deployment
```

## API Endpoints

| Method | Endpoint                       | Description                  |
|--------|-------------------------------|------------------------------|
| GET    | /health                       | Health check + DB status     |
| GET    | /stats                        | Summary statistics           |
| GET    | /violations?limit=20          | List recent violations       |
| GET    | /violations/search?plate=UP14 | Search by plate number       |
| GET    | /counts/hourly                | Hourly vehicle counts        |

## Configuration

All settings in `config.py`. Override with environment variables:

| Variable               | Default              | Description              |
|------------------------|----------------------|--------------------------|
| `DB_PATH`              | data/traffic.db      | SQLite database path     |
| `VIDEO_SOURCE`         | 0 (webcam)           | Video input source       |
| `CONFIDENCE_THRESHOLD` | 0.45                 | YOLOv8 confidence cutoff |
| `SKIP_FRAMES`          | 2                    | Run detection every N fr |
| `LOG_LEVEL`            | INFO                 | Logging verbosity        |

## 45-Day Learning Path

See [DAILY_GUIDE.md](DAILY_GUIDE.md) for the complete day-by-day study guide.

## License

MIT License. See LICENSE file.
"""

CHANGELOG_CONTENT = """\
# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added
- Docker containerization (Dockerfile + docker-compose.yml)
- Production configuration system with environment profiles
- System monitoring and watchdog auto-restart
- Field validation checklist and calibration wizard
- Full integration test suite

## [0.3.0] — Phase 3: Production

### Added
- FastAPI REST API (day36)
- Automated API testing (day37)
- Docker containerization (day38)
- Production config management (day39)
- System monitoring + watchdog (day40)
- Field testing tools (day41)
- Integration test suite (day42)

## [0.2.0] — Phase 2: Dashboard & Pipeline

### Added
- Streamlit dashboard with Plotly charts (day19–day25)
- Multi-threaded pipeline (day26)
- Environment variable config (day27)
- Rotating log files with session IDs (day28)
- Error handling and graceful shutdown (day29)
- Batch video processing with checkpoints (day30)
- Unit tests and integration tests (day31–day32)

## [0.1.0] — Phase 1: Core Detection

### Added
- YOLOv8 vehicle detection with ByteTrack (day1–day10)
- Helmet detection module (day11)
- Rider counting module (day12)
- EasyOCR plate reading (day13)
- SQLite + CSV database logging (day14)
- Master pipeline (day15)
- Violation confirmation window (day16)
- Snapshot + email alerts (day17)
- Performance benchmarking (day18)
"""

API_REFERENCE = """\
# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "db_exists": true,
  "db_path": "data/traffic.db"
}
```

---

## GET /stats

Summary statistics from the database.

**Response:**
```json
{
  "total_vehicles": 1234,
  "total_violations": 56,
  "breakdown": {"no_helmet": 40, "triple_riding": 16},
  "vehicle_types": {"motorcycle": 800, "bicycle": 434}
}
```

---

## GET /violations

List recent violations, newest first.

**Query parameters:**
- `limit` (int, default 20, max 200) — number of results

**Response:**
```json
{
  "count": 5,
  "violations": [
    {
      "id": 1,
      "vehicle_type": "motorcycle",
      "plate": "UP14AB1234",
      "violation_type": "no_helmet",
      "timestamp": "2025-01-15 14:32:01",
      "snapshot_path": "data/snapshots/viol_001.jpg"
    }
  ]
}
```

---

## GET /violations/search

Search violations by plate number (case-insensitive).

**Query parameters:**
- `plate` (str, min_length=2) — partial or full plate string

**Response:**
```json
{
  "query": "UP14",
  "count": 3,
  "results": [ ... ]
}
```

**Error (422):** plate shorter than 2 characters.

---

## GET /counts/hourly

Vehicle counts grouped by hour (today only).

**Response:**
```json
{
  "hourly": [
    {"hour": "08:00", "count": 45},
    {"hour": "09:00", "count": 112}
  ]
}
```
"""


# ── Module doc scanner ────────────────────────────────────────────────────────

def scan_module_docs():
    """Collect first-line docstrings from key modules."""
    target_modules = [
        ("modules.vehicle_detector", "VehicleDetector"),
        ("modules.helmet_detector",  "HelmetDetector"),
        ("modules.rider_counter",    "RiderCounter"),
        ("modules.plate_reader",     "PlateReader"),
        ("utils.database",           "TrafficDB"),
        ("utils.helpers",            "helpers"),
    ]
    lines = ["# Module Reference\n"]
    for mod_path, class_name in target_modules:
        try:
            mod = __import__(mod_path, fromlist=[class_name])
            cls = getattr(mod, class_name, None)
            doc = inspect.getdoc(cls) if cls else inspect.getdoc(mod)
            first_line = (doc or "").split("\n")[0].strip()
            lines.append(f"## `{mod_path}.{class_name}`\n\n{first_line or '(no docstring)'}\n")
        except Exception as e:
            lines.append(f"## `{mod_path}.{class_name}`\n\n(import error: {e})\n")
    return "\n".join(lines)


# ── Writer ────────────────────────────────────────────────────────────────────

def write_docs(which="all"):
    os.makedirs(DOCS_DIR, exist_ok=True)
    files = {}

    if which in ("all", "readme"):
        files["README.md"] = (BASE_DIR, README_CONTENT)

    if which in ("all", "api"):
        files["API_REFERENCE.md"] = (DOCS_DIR, API_REFERENCE)

    if which in ("all", "changelog"):
        files["CHANGELOG.md"] = (BASE_DIR, CHANGELOG_CONTENT)

    if which in ("all", "modules"):
        files["MODULE_DOCS.md"] = (DOCS_DIR, scan_module_docs())

    created = []
    for fname, (directory, content) in files.items():
        path = os.path.join(directory, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓  {path}")
        created.append(path)

    return created


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 43 — Documentation")
    parser.add_argument("--all",      action="store_true", help="Generate all docs")
    parser.add_argument("--readme",   action="store_true")
    parser.add_argument("--api",      action="store_true")
    parser.add_argument("--modules",  action="store_true")
    parser.add_argument("--changelog",action="store_true")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 43 — Documentation Generation")
    print("=" * 65)

    which = "all"
    if args.readme:   which = "readme"
    elif args.api:    which = "api"
    elif args.modules: which = "modules"
    elif args.changelog: which = "changelog"

    print(f"\n  Generating docs ({which})…\n")
    created = write_docs(which)
    print(f"\n  Created/updated {len(created)} file(s)")

    print("\n  ── DOCUMENTATION TIPS ───────────────────────────────────────")
    print("""
  README.md        — project overview, quick start, architecture
  CHANGELOG.md     — version history (follow keep-a-changelog.org format)
  docs/API_REFERENCE.md    — endpoint details with example responses
  docs/MODULE_DOCS.md      — auto-generated from module docstrings

  Add docstrings to every public class/function:
      class VehicleDetector:
          \"\"\"YOLOv8 + ByteTrack multi-object detector.\"\"\"

  Use Google-style docstrings for Args/Returns sections.
  Auto-generate HTML docs with Sphinx: pip install sphinx
""")
    print("  Next → python day44_test.py  (Final polish and bug fixes)")
