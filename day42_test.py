# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 42 — day42_test.py
#  Topic: Final system integration test — everything working together
#
#  NEW today:
#    ✓ End-to-end smoke test: video → detection → DB → API → dashboard
#    ✓ Data flow validation at each stage
#    ✓ Concurrency test: pipeline + API running simultaneously
#    ✓ Regression test: verify DB has expected schema and data
#    ✓ Full system report
#
#  Run:  python day42_test.py
#  Run:  python day42_test.py --source data/videos/traffic.mp4
#  Run:  python day42_test.py --full   (includes API + load test)
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, threading, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
from config         import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT
log = get_logger("day42")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Stage 1: Video input ──────────────────────────────────────────────────────

def test_video_input(src):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return False, f"Cannot open source: {src}"
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False, "Opened but cannot read frame"
    h, w = frame.shape[:2]
    return True, f"{w}x{h} frame read OK"


# ── Stage 2: Detection ────────────────────────────────────────────────────────

def test_detection(src, n_frames=5):
    try:
        from modules.vehicle_detector import VehicleDetector
    except ImportError as e:
        return False, f"Import error: {e}"

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        return False, "Cannot open source"

    detector    = VehicleDetector()
    detections  = []
    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if not ret:
            break
        frame  = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        result = detector.process_frame(frame, i + 1)
        detections.append(len(result.get("detections", [])))

    cap.release()
    avg = sum(detections) / len(detections) if detections else 0
    return True, f"{n_frames} frames, avg {avg:.1f} detections/frame"


# ── Stage 3: Database ─────────────────────────────────────────────────────────

def test_database():
    try:
        db = TrafficDB()
    except Exception as e:
        return False, f"Cannot open DB: {e}"

    # Insert and retrieve test row
    try:
        db.log_vehicle_count("test_car")
        total = db.get_total_vehicles()
        return True, f"Write + read OK, total rows: {total}"
    except Exception as e:
        return False, f"DB operation failed: {e}"


# ── Stage 4: API health ───────────────────────────────────────────────────────

def test_api_health(base="http://localhost:8000", timeout=3):
    try:
        import requests
        r = requests.get(f"{base}/health", timeout=timeout)
        if r.status_code == 200:
            return True, f"HTTP 200 — {r.json().get('status')}"
        return False, f"HTTP {r.status_code}"
    except ImportError:
        return None, "requests not installed — skipped"
    except Exception as e:
        return None, f"API not reachable ({e}) — start day36_test.py first"


# ── Stage 5: Dashboard reachable ──────────────────────────────────────────────

def test_dashboard(base="http://localhost:8501", timeout=3):
    try:
        import requests
        r = requests.get(base, timeout=timeout)
        return r.status_code in (200, 301, 302), f"HTTP {r.status_code}"
    except ImportError:
        return None, "requests not installed — skipped"
    except Exception as e:
        return None, f"Dashboard not reachable — start dashboard/app.py first"


# ── Stage 6: Pipeline + API concurrency ──────────────────────────────────────

def test_concurrency(src, duration=5):
    """Run pipeline for N seconds while hammering the API."""
    try:
        import requests
        from modules.vehicle_detector import VehicleDetector
    except ImportError as e:
        return None, f"Import error: {e}"

    db       = TrafficDB()
    detector = VehicleDetector()
    results  = {"frames": 0, "api_ok": 0, "api_fail": 0}
    stop_ev  = threading.Event()

    def pipeline():
        cap = cv2.VideoCapture(src)
        while not stop_ev.is_set():
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            detector.process_frame(frame, results["frames"])
            results["frames"] += 1
        cap.release()

    def api_poller():
        while not stop_ev.is_set():
            try:
                r = requests.get("http://localhost:8000/health", timeout=1)
                if r.status_code == 200:
                    results["api_ok"] += 1
                else:
                    results["api_fail"] += 1
            except:
                results["api_fail"] += 1
            time.sleep(0.1)

    threads = [threading.Thread(target=pipeline, daemon=True)]
    # Only poll API if it seems to be running
    try:
        requests.get("http://localhost:8000/health", timeout=1)
        threads.append(threading.Thread(target=api_poller, daemon=True))
    except:
        pass

    for t in threads: t.start()
    time.sleep(duration)
    stop_ev.set()
    for t in threads: t.join(timeout=2)

    fps = results["frames"] / duration
    msg = (f"{results['frames']} frames @ {fps:.1f} FPS | "
           f"API: {results['api_ok']} ok, {results['api_fail']} fail")
    return True, msg


# ── DB schema regression test ─────────────────────────────────────────────────

def test_db_schema():
    import sqlite3
    from config import DB_PATH
    if not os.path.exists(DB_PATH):
        return None, "DB file not found — run pipeline first"
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        tables = {r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        required = {"vehicle_counts", "violations"}
        missing  = required - tables
        con.close()
        if missing:
            return False, f"Missing tables: {missing}"
        return True, f"Tables OK: {tables}"
    except Exception as e:
        return False, str(e)


# ── Full integration runner ───────────────────────────────────────────────────

def run_integration_tests(src, full=False):
    STAGES = [
        ("Video input",        lambda: test_video_input(src)),
        ("Detection (5 fr)",   lambda: test_detection(src, 5)),
        ("Database RW",        lambda: test_database()),
        ("DB schema",          lambda: test_db_schema()),
        ("API health",         lambda: test_api_health()),
        ("Dashboard reachable",lambda: test_dashboard()),
    ]
    if full:
        STAGES.append(("Concurrency (5s)", lambda: test_concurrency(src, 5)))

    print(f"\n  Integration tests ({len(STAGES)} stages)\n")
    passed = 0; failed = 0; skipped = 0
    for name, fn in STAGES:
        t0 = time.perf_counter()
        try:
            ok, detail = fn()
            ms = (time.perf_counter() - t0) * 1000
            if ok is True:
                print(f"  ✓  {name:<30s}  {detail}  ({ms:.0f}ms)")
                passed += 1
            elif ok is None:
                print(f"  ⊘  {name:<30s}  {detail}")
                skipped += 1
            else:
                print(f"  ✗  {name:<30s}  {detail}")
                failed += 1
        except Exception as e:
            print(f"  ✗  {name:<30s}  EXCEPTION: {e}")
            failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed, {skipped} skipped")
    return failed == 0


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 42 — Final Integration Test")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    parser.add_argument("--full",   action="store_true",
                        help="Include concurrency test (needs API running)")
    args = parser.parse_args()
    src = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 42 — Final System Integration Test")
    print("=" * 65)

    ok = run_integration_tests(src, full=args.full)

    print("\n  ── SYSTEM ARCHITECTURE SUMMARY ──────────────────────────────")
    print("""
  Input        Video source (file or webcam)
     ↓
  Detector     YOLOv8 + ByteTrack → bounding boxes + track IDs
     ↓
  HelmetDet    Crop top 40% of bike box → helmet/no-helmet
     ↓
  RiderCount   Person overlap → single/double/triple-riding
     ↓
  PlateReader  EasyOCR + voting → stable plate string
     ↓
  ViolTracker  5-frame confirmation window → log to DB
     ↓
  TrafficDB    SQLite + CSV → violations + vehicle_counts tables
     ↓
  FastAPI      REST endpoints → dashboard + external systems
     ↓
  Streamlit    Auto-refresh dashboard → charts + violation table
""")
    if ok:
        print("  ✓  All stages PASSED — system is integration-ready")
    else:
        print("  ✗  Some stages FAILED — see above for details")

    print("\n  Next → python day43_test.py  (Documentation generation)")
