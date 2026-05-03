# 45-Day Traffic Monitoring System — Daily Study Guide

This guide tells you exactly what to study, what to run, and what you should
understand by the end of each day.

---

## PHASE 1: Core Detection (Days 1–18)

---

### Day 1 — Project Setup & First Detection

**What to study:** Python project structure, config files, importing modules, YOLOv8 basics  
**What to run:** `python day01_test.py`  
**What you learn:**
- How to structure a multi-file Python project
- How to load a YOLOv8 model with `YOLO("yolov8n.pt")`
- How to run inference on one frame: `model(frame)`
- What a detection result looks like: bounding box, class, confidence

**Key concepts:** `config.py`, `sys.path.append()`, YOLO class IDs (1=bicycle, 3=motorcycle)

---

### Day 2 — Live Video from Webcam

**What to study:** OpenCV video capture, frame loop, imshow  
**What to run:** `python day02_test.py`  
**What you learn:**
- `cv2.VideoCapture(0)` opens webcam; `cv2.VideoCapture("file.mp4")` opens file
- `cap.read()` returns `(ret, frame)` — always check `ret`
- `cv2.imshow()` + `cv2.waitKey(1)` for live display
- `cap.release()` + `cv2.destroyAllWindows()` for cleanup

**Key concepts:** Frame loop pattern, FPS calculation with `time.time()`

---

### Day 3 — Filtering Vehicle Classes

**What to study:** YOLO class filtering, bounding box extraction  
**What to run:** `python day03_test.py`  
**What you learn:**
- Filter detections to motorcycles/bicycles only: `classes=[1, 3]`
- Extract bounding box: `det.xyxy[0]` → `[x1, y1, x2, y2]`
- Draw boxes: `cv2.rectangle()` + `cv2.putText()`
- What `conf` (confidence score) means and when to filter it

**Key concepts:** `CONFIDENCE_THRESHOLD`, filtering with list comprehension

---

### Day 4 — ByteTrack Multi-Object Tracking

**What to study:** Object tracking vs detection, track IDs  
**What to run:** `python day04_test.py`  
**What you learn:**
- Why tracking matters: gives each vehicle a stable ID across frames
- `model.track(persist=True)` — enables ByteTrack
- Each detection now has `track_id` — same vehicle = same ID
- Difference between `predict()` and `track()`

**Key concepts:** ByteTrack, `persist=True`, track ID stability

---

### Day 5 — Motion Trails

**What to study:** `collections.deque`, drawing polylines  
**What to run:** `python day05_test.py`  
**What you learn:**
- `deque(maxlen=N)` — fixed-length queue, auto-drops oldest
- Store trail points: `trail_history[track_id].append(center)`
- Draw trail: `cv2.polylines()` over all stored points
- Why `maxlen` prevents memory growth

**Key concepts:** `deque`, `TRAIL_LENGTH`, `cv2.polylines()`

---

### Day 6 — Vehicle Counting Line

**What to study:** Line crossing detection, direction logic  
**What to run:** `python day06_test.py`  
**What you learn:**
- Count line = horizontal line at `COUNT_LINE_Y` pixels from top
- A vehicle "crosses" when its center moves from above to below the line
- Track previous positions: `prev_y[track_id]`
- Separate "up" and "down" counts for bidirectional roads

**Key concepts:** `COUNT_LINE_Y`, crossing detection with sign change

---

### Day 7 — Skip Frames for Speed

**What to study:** Performance optimization, SKIP_FRAMES  
**What to run:** `python day07_test.py`  
**What you learn:**
- Running YOLO on every frame is slow (8–15 FPS on CPU)
- Only detect every N frames; interpolate bounding boxes in between
- `SKIP_FRAMES = 2` → run detection on frames 1, 3, 5… — roughly 2× faster
- Trade-off: faster FPS vs potentially missing fast vehicles

**Key concepts:** `SKIP_FRAMES`, `frame_n % SKIP_FRAMES == 0`

---

### Day 8 — VehicleDetector Class

**What to study:** Object-oriented programming, encapsulation  
**What to run:** `python day08_test.py`  
**What you learn:**
- Wrap all detection logic into `class VehicleDetector`
- Public methods: `process_frame(frame, frame_n)`, `draw(frame, result)`, `draw_trails(frame)`
- `process_frame` returns a result dict: `{"detections": [...], "count": {...}}`
- Why a class is better than loose functions for a multi-day project

**Key concepts:** `__init__`, `self.trail_history`, result dict pattern

---

### Day 9 — Stats Overlay & FPS Display

**What to study:** `cv2.putText()`, overlay design  
**What to run:** `python day09_test.py`  
**What you learn:**
- `put_stats_overlay(frame, stats_dict)` — draw key-value pairs on frame
- Calculate real-time FPS: `fps_c / (time.time() - fps_t)`
- Overlay: total count, FPS, active tracks, violations
- Semi-transparent background behind text: `cv2.addWeighted()`

**Key concepts:** `put_stats_overlay()` in `utils/helpers.py`

---

### Day 10 — Database Logging (Introduction)

**What to study:** SQLite basics, `utils/database.py`  
**What to run:** `python day10_test.py`  
**What you learn:**
- SQLite = file-based database, no server needed
- `TrafficDB` class wraps all SQL so you don't write raw SQL everywhere
- Two tables: `vehicle_counts` and `violations`
- CSV export as backup alongside the SQLite file

**Key concepts:** `TrafficDB.log_vehicle_count()`, `TrafficDB.log_violation()`

---

### Day 11 — Helmet Detection

**What to study:** Crop-and-classify pattern, HelmetDetector  
**What to run:** `python day11_test.py`  
**What you learn:**
- Helmet detection = crop the TOP 40% of each motorcycle bounding box
- Feed that crop to a second YOLO model (helmet classifier)
- Result per detection: `helmet_status` = "helmet" or "no_helmet", `helmet_conf`
- Why we crop instead of running the full frame through the helmet model

**Key concepts:** `HelmetDetector.check_all()`, crop = `frame[y1:y1+h//2, x1:x2]`

---

### Day 12 — Rider Counting (Triple Riding)

**What to study:** IoU overlap, person detection  
**What to run:** `python day12_test.py`  
**What you learn:**
- Triple riding = 3 or more people on one motorcycle
- Method 1 (overlap): find person detections whose box overlaps with bike box
- `compute_iou(box_a, box_b)` returns overlap ratio (0–1)
- Method 2 (pose): YOLOv8-pose skeleton for more precision
- Result per detection: `rider_count`, `is_triple_viol`

**Key concepts:** `RiderCounter.count_all()`, IoU threshold, `--method pose`

---

### Day 13 — Plate Reading (EasyOCR)

**What to study:** OCR, voting system for stability  
**What to run:** `python day13_test.py` (takes ~5s to load EasyOCR)  
**What you learn:**
- EasyOCR = reads text from image regions
- Crop the bottom 30% of each bike box for the plate region
- Problem: OCR is inconsistent frame-to-frame ("UP14" vs "UPI4" vs "UP 14")
- Solution: vote over 10 readings, pick the most frequent
- Result: `plate` (string), `stable` (True when vote is confident)

**Key concepts:** `PlateReader.read()`, `_vote_history`, `stable=True`

---

### Day 14 — Database Deep Dive

**What to study:** All TrafficDB methods, SQL queries  
**What to run:** `python day14_test.py`  
**What you learn:**
- `log_violation()` — saves one confirmed violation to DB
- `get_recent_violations(limit)` — newest first
- `search_by_plate("UP14")` — partial plate search
- `get_violation_breakdown()` — counts by violation type
- `get_hourly_counts()` — vehicles per hour (for charts)

**Key concepts:** All 8 public methods of `TrafficDB`

---

### Day 15 — Master Pipeline

**What to study:** `pipeline.py`, module wiring  
**What to run:** `python day15_test.py`  
**What you learn:**
- `TrafficPipeline` wires: VehicleDetector → HelmetDetector → RiderCounter → PlateReader → TrafficDB
- `pipeline.process_frame(frame, frame_n)` does everything in one call
- Session summary on exit: total vehicles, violations, FPS
- How to use `pipeline.py` in your own code

**Key concepts:** `TrafficPipeline`, composition pattern, session summary

---

### Day 16 — Violation Confirmation Window

**What to study:** State machine, `CONFIRM_FRAMES`  
**What to run:** `python day16_test.py`  
**What you learn:**
- Problem: single-frame detections create false positives
- Solution: only log a violation if we see it for 5 consecutive frames
- `ViolationTracker.update(track_id, violation_type)` returns `True` only on frame 5
- Resets if vehicle disappears from frame
- Why this matters: prevents log spam from wobbly detections

**Key concepts:** `CONFIRM_FRAMES = 5`, `consecutive_count[tid]`

---

### Day 17 — Snapshots & Email Alerts

**What to study:** `cv2.imwrite()`, SMTP email  
**What to run:** `python day17_test.py`  
**What you learn:**
- Save a JPEG snapshot when a violation is confirmed: `cv2.imwrite(path, frame)`
- `send_violation_email()` — sends Gmail with snapshot attached
- MIME multipart email: text body + JPEG attachment
- `--review` flag: browse saved snapshots with OpenCV window

**Key concepts:** `save_snapshot()`, `smtplib.SMTP_SSL`, MIME attachment

---

### Day 18 — Performance Benchmarking

**What to study:** `time.perf_counter()`, SKIP_FRAMES comparison  
**What to run:** `python day18_test.py`  
**What you learn:**
- Measure per-stage time: detect / draw / DB write / total
- `StageTimer` class wraps `perf_counter()` calls
- `--bench` flag: compare SKIP_FRAMES = 1, 2, 3, 4 — see FPS vs accuracy trade-off
- Live overlay: per-stage ms shown in stats panel each frame

**Key concepts:** `StageTimer`, `SKIP_FRAMES` impact table

---

## PHASE 2: Dashboard & Reliability (Days 19–32)

---

### Day 19 — Streamlit Dashboard Introduction

**What to study:** Streamlit basics, running dashboard alongside pipeline  
**What to run:** `python day19_test.py` then `streamlit run dashboard/app.py`  
**What you learn:**
- Streamlit = Python-first web dashboard, no HTML/JS needed
- `st.metric()`, `st.dataframe()`, `st.plotly_chart()` — one-line widgets
- `st.rerun()` — auto-refresh the dashboard every N seconds
- How to run the pipeline in one terminal and dashboard in another

**Key concepts:** `streamlit run`, `st.rerun()`, reading from `TrafficDB`

---

### Day 20 — Live Dashboard Demo

**What to study:** Injecting demo data, watching dashboard update  
**What to run:** `python day20_test.py` (inject data) + `streamlit run dashboard/app.py`  
**What you learn:**
- `inject_demo_data(db, n, delay)` — inserts violations with delay so dashboard updates live
- Watch metric counters increment in real time
- How `st.rerun()` with `time.sleep(REFRESH_INTERVAL)` creates auto-refresh
- `--live` flag: use real pipeline instead of demo data

**Key concepts:** `inject_demo_data()`, dashboard refresh loop

---

### Day 21 — HTML Charts Export

**What to study:** Plotly, saving charts to files  
**What to run:** `python day21_test.py --show`  
**What you learn:**
- Plotly = interactive charts (zoom, hover, export PNG)
- Four chart types: pie (vehicle types), bar (violations), line (hourly), heatmap (day×hour)
- `fig.write_html(path)` — save chart as standalone HTML file
- `--show` flag: open all 4 charts in browser

**Key concepts:** `plotly.express`, `write_html()`, synthetic fallback data

---

### Day 22 — Dashboard Filters (CLI)

**What to study:** `argparse`, data filtering  
**What to run:** `python day22_test.py --type no_helmet --limit 5`  
**What you learn:**
- CLI flags mirror what a real dashboard filter UI would do
- `--type`, `--plate`, `--limit` — filter violations before display
- `print_violation_card(v)` — box-drawing terminal card per violation
- How to translate terminal filtering logic into Streamlit `st.selectbox()`

**Key concepts:** Filter pattern, `print_violation_card()`, argparse

---

### Day 23 — Snapshot Gallery

**What to study:** OpenCV image browser, contact sheets  
**What to run:** `python day23_test.py --generate` then `python day23_test.py`  
**What you learn:**
- `gallery_viewer()` — cycle through violation snapshots with keyboard: A/D to navigate, D to mark delete
- `make_contact_sheet()` — tile up to 12 thumbnails into one combined image
- `--generate` creates placeholder colored images if no real snapshots exist
- How to use `cv2.imread()` + `np.hstack/vstack` for image layout

**Key concepts:** `gallery_viewer()`, `make_contact_sheet()`, `cv2.imread()`

---

### Day 24 — Reports & CSV Export

**What to study:** Pandas analysis, report generation  
**What to run:** `python day24_test.py`  
**What you learn:**
- Load DB data into pandas: `pd.read_sql()`
- `analyse(viol_df, count_df)` — computes peak hour, top plates, violation rates
- `print_report(stats)` — formatted terminal report with box-drawing chars
- `export_csv(df, path)` — export filtered data as CSV for Excel

**Key concepts:** Pandas, `pd.read_sql()`, `export_csv()`

---

### Day 25 — Dashboard Latency & Refresh

**What to study:** `st.rerun()` timing, refresh interval tuning  
**What to run:** `python day25_test.py`  
**What you learn:**
- Why `REFRESH_INTERVAL` matters: too fast = CPU waste, too slow = stale data
- How `st.rerun()` after `time.sleep(N)` creates the auto-refresh loop
- Latency = time from violation event to dashboard showing it
- Measuring actual latency: write timestamp to DB, check when dashboard reads it

**Key concepts:** `REFRESH_INTERVAL`, `st.rerun()`, latency measurement

---

### Day 26 — Multi-Threaded Pipeline

**What to study:** Threading, `queue.Queue`, producer-consumer pattern  
**What to run:** `python day26_test.py`  
**What you learn:**
- Three threads: `_reader` (cap.read), `_detector` (YOLO), `_db_writer` (SQL)
- `queue.Queue(maxsize=4)` — blocks reader when detector is busy (backpressure)
- Drop-on-full strategy: if queue full, drop oldest frame (prevents memory growth)
- Why this is faster: reader and DB writer run while detector is computing

**Key concepts:** `ThreadedPipeline`, `Queue(maxsize=4)`, daemon threads

---

### Day 27 — Environment Variables & .env

**What to study:** `.env` files, os.environ, config overrides  
**What to run:** `python day27_test.py`  
**What you learn:**
- `load_dotenv(path)` — reads `KEY=value` lines from `.env` file
- `apply_env_overrides()` — maps env vars to `config.py` attributes
- `validate_config()` — checks for invalid values, returns error/warning lists
- Why you should never hardcode secrets — always use env vars

**Key concepts:** `.env`, `os.environ.get()`, config validation

---

### Day 28 — Rotating Log Files

**What to study:** Python logging, `RotatingFileHandler`  
**What to run:** `python day28_test.py`  
**What you learn:**
- `RotatingFileHandler(filename, maxBytes=2MB, backupCount=3)` — auto-rotates logs
- Three separate loggers: `pipeline.log`, `violations.log`, `errors.log`
- `SESSION_ID = uuid.uuid4()` — unique ID per run, appears in every log line
- `search_log(filename, keyword, tail=20)` — grep-like log searching

**Key concepts:** `RotatingFileHandler`, `SESSION_ID`, log levels

---

### Day 29 — Error Handling & Graceful Shutdown

**What to study:** Exception handling, signal handling, frame validation  
**What to run:** `python day29_test.py`  
**What you learn:**
- `is_valid_frame(frame)` — rejects None, all-black, too-uniform frames
- `safe_process(detector, frame, timeout_s=2.0)` — timeout guard for stuck frames
- `signal.signal(signal.SIGINT, handler)` — catch Ctrl+C for clean shutdown
- Why never use bare `except:` — always catch `except Exception as e`

**Key concepts:** `SIGINT`, `threading.Timer` timeout, frame validation

---

### Day 30 — Batch Video Processing

**What to study:** Processing multiple files, checkpoints  
**What to run:** `python day30_test.py --headless`  
**What you learn:**
- `process_video(path)` — process one file, returns stats dict
- Checkpoint JSON: save progress so batch can resume if interrupted
- `--headless` flag: no `cv2.imshow()` for server/background processing
- Print per-file + combined summary table after batch completes

**Key concepts:** Checkpoint pattern, `--headless`, batch stats table

---

### Day 31 — Unit Tests

**What to study:** pytest, assert statements, test isolation  
**What to run:** `python day31_test.py` or `pytest day31_test.py`  
**What you learn:**
- `def test_*()` — pytest discovers functions starting with `test_`
- `assert compute_iou(boxA, boxB) == expected_value`
- Test TrafficDB: insert → query → assert result
- Why unit tests catch regressions: run them after every change

**Key concepts:** pytest, `assert`, `tmp_path` fixture

---

### Day 32 — Integration Tests with Synthetic Video

**What to study:** `cv2.VideoWriter`, end-to-end tests  
**What to run:** `python day32_test.py`  
**What you learn:**
- `make_test_video(path, num_frames=120)` — synthetic MP4 with moving rectangle
- Integration test = runs the real VehicleDetector on synthetic video
- Tests: no crash on blank frame, reset clears state, pipeline completes N frames
- Difference between unit test (test one function) and integration test (test pipeline)

**Key concepts:** `cv2.VideoWriter`, `test_pipeline_runs_without_crash`

---

## PHASE 3: Production (Days 33–45)

---

### Day 33 — Model Accuracy Benchmarking

**What to study:** mAP50, precision, recall, model comparison  
**What to run:** `python day33_test.py --compare`  
**What you learn:**
- Precision = of all my detections, what % were real vehicles?
- Recall = of all real vehicles, what % did I detect?
- mAP50 = mean Average Precision at IoU 0.50 threshold
- `--compare` shows yolov8n vs yolov8s vs yolov8m: speed vs accuracy table

**Key concepts:** `model.val()`, mAP50, precision/recall trade-off

---

### Day 34 — Edge Cases: Night, Rain, Blur

**What to study:** Image augmentation, CLAHE, denoising  
**What to run:** `python day34_test.py`  
**What you learn:**
- `augment_night()` — darken + blue tint to simulate low light
- `augment_rain()` — diagonal streaks + reduced contrast
- `preprocess_night()` — CLAHE equalizes brightness before detection
- `preprocess_rain()` — denoise + sharpen to remove rain streaks
- Side-by-side display: augmented vs preprocessed

**Key concepts:** CLAHE (`cv2.createCLAHE`), `fastNlMeansDenoisingColored`

---

### Day 35 — Memory & CPU Profiling

**What to study:** tracemalloc, psutil, memory leaks  
**What to run:** `python day35_test.py --frames 200`  
**What you learn:**
- `tracemalloc.start()` / `get_traced_memory()` — Python heap allocation
- `psutil.Process().memory_info().rss` — actual RAM usage
- RAM growth > 50 MB over 1000 frames = likely memory leak
- Common leaks: unbounded `trail_history`, accumulating `track_types`

**Key concepts:** `tracemalloc`, `psutil`, ASCII RAM chart

---

### Day 36 — REST API with FastAPI

**What to study:** FastAPI, uvicorn, HTTP endpoints  
**What to run:** `python day36_test.py` then open `http://localhost:8000/docs`  
**What you learn:**
- FastAPI creates REST endpoints with one decorator: `@app.get("/endpoint")`
- `Query(default=20, le=200)` — validates query parameters automatically
- Interactive API docs at `/docs` — generated automatically from code
- Five endpoints: `/health`, `/stats`, `/violations`, `/violations/search`, `/counts/hourly`

**Key concepts:** FastAPI, `@app.get()`, `Query()`, uvicorn

---

### Day 37 — API Testing

**What to study:** `requests` library, assertions, load testing  
**What to run:** `python day37_test.py --selftest`  
**What you learn:**
- `requests.get(url, timeout=5)` — make HTTP GET request
- `assert r.status_code == 200` — verify correct response
- `assert "key" in r.json()` — verify JSON structure
- `load_test(base, n=50)` — 50 concurrent requests, measure success rate + avg/max latency
- `--selftest` starts server + runs all tests automatically

**Key concepts:** `requests`, assert pattern, threaded load test

---

### Day 38 — Docker Containerization

**What to study:** Dockerfile, docker-compose, containers  
**What to run:** `python day38_test.py` then `docker-compose up`  
**What you learn:**
- `Dockerfile` = recipe to build a container image (FROM → RUN → COPY → CMD)
- `docker-compose.yml` = define multiple services (API + dashboard) with shared volumes
- `.dockerignore` = exclude large files from build context
- Volume mounts: `./data:/app/data` — share data between host and container
- `docker build -t traffic-monitor .` + `docker run ...`

**Key concepts:** Dockerfile, `docker-compose up`, volume mounts

---

### Day 39 — Production Configuration

**What to study:** Multi-environment config, secrets management  
**What to run:** `python day39_test.py --env production --validate`  
**What you learn:**
- Separate configs: development / staging / production
- `ProductionConfig` class loads from: base config → `.env` file → environment variables
- `validate_production_config()` — catches config errors before startup
- `startup_sequence()` — validates, creates directories, health-checks in order
- Why never commit `.env` — only commit `.env.example`

**Key concepts:** Multi-env config, config validation, `startup_sequence()`

---

### Day 40 — System Monitoring & Watchdog

**What to study:** Metrics, watchdog pattern, Prometheus format  
**What to run:** `python day40_test.py --monitor`  
**What you learn:**
- `MetricsCollector` — rolling-window FPS, DB write rate, error rate
- `PipelineWatchdog` — detects dead threads, restarts them, alerts with cooldown
- Prometheus text format: `metric_name value` lines that Grafana can scrape
- Alert cooldown: prevents spam when system is repeatedly failing

**Key concepts:** `MetricsCollector`, `PipelineWatchdog`, Prometheus format

---

### Day 41 — Real-World Field Testing

**What to study:** Deployment checklist, calibration, accuracy validation  
**What to run:** `python day41_test.py --calibrate`  
**What you learn:**
- Pre-deployment checklist: camera, DB, model, disk, RAM, dependencies
- `calibrate_count_line()` — click to set count line position visually
- Ground-truth comparison: system count vs manual tally → error %
- `generate_field_report()` — saves JSON report with violations/min, vehicles/min
- Camera angle tips: 3–6m height, 15–30° downward, avoid sun glare

**Key concepts:** Deployment checklist, `calibrate_count_line()`, ground-truth

---

### Day 42 — Final Integration Test

**What to study:** End-to-end testing, concurrency testing  
**What to run:** `python day42_test.py`  
**What you learn:**
- 6-stage integration test: video → detection → DB → schema → API → dashboard
- Each stage returns `(ok, detail)` — skipped if dependency unavailable
- `test_db_schema()` — verify table names haven't changed
- `test_concurrency()` — run pipeline + API poller simultaneously for 5s
- System architecture diagram printed at end

**Key concepts:** Stage-by-stage integration test, `test_db_schema()`

---

### Day 43 — Documentation

**What to study:** README, API docs, CHANGELOG format  
**What to run:** `python day43_test.py --all`  
**What you learn:**
- Auto-generate `README.md` with architecture, quick start, API table
- `CHANGELOG.md` — keep-a-changelog.org format: Unreleased → versions
- `docs/API_REFERENCE.md` — endpoint docs with example JSON responses
- `docs/MODULE_DOCS.md` — auto-scanned from module `__doc__` strings
- Good documentation habit: write it on Day 43, not after shipping

**Key concepts:** `README.md`, `CHANGELOG.md`, `inspect.getdoc()`

---

### Day 44 — Final Polish & Performance Tuning

**What to study:** Code quality, profiling, tuning checklist  
**What to run:** `python day44_test.py --audit --config`  
**What you learn:**
- Code quality scan: bare `except:`, `print()` in modules, hardcoded paths, TODO comments
- `audit_config()` — verify all required constants exist in `config.py`
- `profile_modules()` — per-stage ms breakdown: detect / draw / total
- Performance targets: > 15 FPS, < 50 MB RAM growth, < 5% count error
- Speed tricks: `yolov8n.pt`, ONNX export, `SKIP_FRAMES=2`, lower resolution

**Key concepts:** Code quality scan, per-stage profiler, performance targets

---

### Day 45 — Production-Ready Final Demo

**What to study:** Everything working together, what to build next  
**What to run:** `python day45_test.py --all`  
**What you learn:**
- `--all` flag: starts pipeline + API simultaneously, shows live terminal status
- Terminal status: FPS, frame count, detections, DB rows, violation breakdown — refreshing every 2s
- `--summary` flag: prints full 45-day achievement board
- Graceful shutdown: `signal.SIGINT` handler sets `_STOP` event, all threads exit cleanly
- What to build next: speed estimation, mobile alerts, custom model training

**Key concepts:** Full system startup, `_STOP` event, achievement summary

---

## Quick Reference

### Run Order (Phase 1)
```
day01 → day02 → day03 → day04 → day05 → day06 → day07 → day08
→ day09 → day10 → day11 → day12 → day13 → day14 → day15
→ day16 → day17 → day18
```

### Run Order (Phase 2)
```
day19 → day20 → day21 → day22 → day23 → day24 → day25
→ day26 → day27 → day28 → day29 → day30 → day31 → day32
```

### Run Order (Phase 3)
```
day33 → day34 → day35 → day36 → day37 → day38 → day39
→ day40 → day41 → day42 → day43 → day44 → day45
```

### Common Flags
| Flag | Used In | Purpose |
|------|---------|---------|
| `--source` | most files | Video source (0=webcam, or path) |
| `--headless` | day30 | No cv2.imshow (server mode) |
| `--selftest` | day37 | Start server + test in one command |
| `--all` | day45 | Start everything together |
| `--compare` | day33 | Compare yolov8n/s/m |
| `--calibrate` | day41 | Interactive count-line setup |
| `--summary` | day45 | Print achievement board |

### Key Files
| File | Purpose |
|------|---------|
| `config.py` | All constants — change settings here |
| `pipeline.py` | Master pipeline — wires all modules |
| `modules/vehicle_detector.py` | YOLOv8 + ByteTrack |
| `utils/database.py` | SQLite + CSV logging |
| `utils/helpers.py` | Shared utilities |
| `dashboard/app.py` | Streamlit dashboard |
| `day36_test.py` | FastAPI server |
| `day45_test.py` | Final production demo |
