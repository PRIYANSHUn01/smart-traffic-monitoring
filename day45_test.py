# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 45 — day45_test.py
#  Topic: Production-ready final demo — everything running together
#
#  This is the capstone of the 45-day Traffic Monitoring System course.
#
#  What this file demonstrates:
#    ✓ Full pipeline: video → detect → log → API → dashboard
#    ✓ One-command startup: python day45_test.py --all
#    ✓ System status dashboard in the terminal
#    ✓ Graceful shutdown (Ctrl+C)
#    ✓ Final project summary and what to build next
#
#  Usage:
#    python day45_test.py              # terminal status + DB summary
#    python day45_test.py --all        # start pipeline + API together
#    python day45_test.py --summary    # print 45-day achievement summary
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, threading, argparse, signal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
from config         import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, DB_PATH
log = get_logger("day45")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_STOP = threading.Event()


# ── Signal handler ────────────────────────────────────────────────────────────

def _handle_sigint(sig, frame):
    print("\n\n  Ctrl+C received — shutting down…")
    _STOP.set()

signal.signal(signal.SIGINT, _handle_sigint)


# ── Pipeline thread ───────────────────────────────────────────────────────────

def run_pipeline_thread(src, stats):
    try:
        from modules.vehicle_detector import VehicleDetector
        from utils.database import TrafficDB
    except ImportError as e:
        log.error(f"Import failed: {e}")
        return

    detector = VehicleDetector()
    db       = TrafficDB()
    cap      = cv2.VideoCapture(src)
    if not cap.isOpened():
        log.error(f"Cannot open source: {src}")
        return

    frame_n = 0
    t_last  = time.time()
    fps_cnt = 0

    while not _STOP.is_set():
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        frame_n += 1
        fps_cnt += 1

        frame  = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
        result = detector.process_frame(frame, frame_n)
        detector.draw_trails(frame)
        detector.draw(frame, result)

        # Update FPS
        now = time.time()
        if now - t_last >= 1.0:
            stats["fps"]    = fps_cnt / (now - t_last)
            stats["frames"] = frame_n
            fps_cnt = 0
            t_last  = now

        stats["detections"] = len(result.get("detections", []))

        # Log to DB every 30 frames
        if frame_n % 30 == 0:
            for det in result.get("detections", []):
                db.log_vehicle_count(
                    det.get("label", "vehicle"),
                    det.get("plate", ""), # type: ignore
                    det.get("helmet_status", "unknown"),
                )

        cv2.imshow("Day 45 — Traffic Monitor (Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            _STOP.set()

    cap.release()
    cv2.destroyAllWindows()


# ── API thread ────────────────────────────────────────────────────────────────

def run_api_thread(port=8000):
    try:
        import uvicorn
        from day36_test import build_app
    except ImportError:
        log.warning("FastAPI/uvicorn not installed — API not started")
        return

    app    = build_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    def _stop_watcher():
        while not _STOP.is_set():
            time.sleep(0.5)
        server.should_exit = True

    threading.Thread(target=_stop_watcher, daemon=True).start()
    server.run()


# ── Terminal status display ───────────────────────────────────────────────────

def terminal_status(stats, db, refresh=2):
    print("\n  Live status (Ctrl+C to stop):\n")
    try:
        while not _STOP.is_set():
            total_v    = db.get_total_vehicles()
            total_viol = db.get_total_violations()
            breakdown  = db.get_violation_breakdown()

            os.system("cls" if os.name == "nt" else "clear")
            print("=" * 65)
            print("  DAY 45 — Traffic Monitoring System — LIVE")
            print("=" * 65)
            print(f"  FPS          : {stats.get('fps', 0):.1f}")
            print(f"  Frames       : {stats.get('frames', 0)}")
            print(f"  Detections   : {stats.get('detections', 0)}")
            print(f"  Vehicles DB  : {total_v}")
            print(f"  Violations   : {total_viol}")
            if breakdown:
                print("\n  Violation breakdown:")
                for k, v in breakdown.items():
                    bar = "█" * min(v, 30)
                    print(f"    {k:<20s}: {v:>4d}  {bar}")
            print("\n  API: http://127.0.0.1:8000/docs")
            print("  Dashboard: streamlit run dashboard/app.py")
            print("\n  Press Ctrl+C to stop")
            time.sleep(refresh)
    except KeyboardInterrupt:
        _STOP.set()


# ── DB summary ────────────────────────────────────────────────────────────────

def print_db_summary(db):
    print("\n  ── DATABASE SUMMARY ─────────────────────────────────────────")
    print(f"  DB path        : {DB_PATH}")
    print(f"  Total vehicles : {db.get_total_vehicles()}")
    print(f"  Total violations: {db.get_total_violations()}")
    breakdown = db.get_violation_breakdown()
    if breakdown:
        print("  Violation types:")
        for k, v in breakdown.items():
            print(f"    {k:<20s}: {v}")
    types = db.get_vehicle_type_counts()
    if types:
        print("  Vehicle types:")
        for k, v in types.items():
            print(f"    {k:<20s}: {v}")
    hourly = db.get_hourly_counts()
    if hourly:
        peak = max(hourly, key=lambda x: x.get("count", 0))
        print(f"  Peak hour today : {peak.get('hour', 'N/A')} "
              f"({peak.get('count', 0)} vehicles)")


# ── 45-day achievement summary ────────────────────────────────────────────────

ACHIEVEMENT_SUMMARY = """
╔═══════════════════════════════════════════════════════════════╗
║         45-DAY TRAFFIC MONITORING SYSTEM — COMPLETE          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  PHASE 1 (Days 1–18): Core Detection                         ║
║  ✓ YOLOv8 vehicle detection + ByteTrack                      ║
║  ✓ Helmet detection (crop + classify)                        ║
║  ✓ Rider counting (overlap / pose)                           ║
║  ✓ EasyOCR plate reading + voting                            ║
║  ✓ SQLite + CSV database logging                             ║
║  ✓ Master pipeline + violation confirmation                  ║
║  ✓ Snapshot + email alerts                                   ║
║  ✓ Performance benchmarking                                  ║
║                                                               ║
║  PHASE 2 (Days 19–32): Dashboard & Reliability               ║
║  ✓ Streamlit dashboard with Plotly charts                    ║
║  ✓ Multi-threaded pipeline (Producer/Detector/DBWriter)       ║
║  ✓ Environment variable config management                    ║
║  ✓ Rotating log files with session IDs                       ║
║  ✓ Error handling + graceful shutdown                        ║
║  ✓ Batch video processing with checkpoint/resume             ║
║  ✓ Unit tests + integration tests                            ║
║                                                               ║
║  PHASE 3 (Days 33–45): Production                            ║
║  ✓ Model accuracy benchmarking (mAP50, precision, recall)    ║
║  ✓ Edge case handling (night, rain, blur, glare)             ║
║  ✓ Memory + CPU profiling                                    ║
║  ✓ FastAPI REST API                                          ║
║  ✓ Automated API testing + load testing                      ║
║  ✓ Docker containerization                                   ║
║  ✓ Production configuration + secrets management            ║
║  ✓ System monitoring + watchdog auto-restart                 ║
║  ✓ Field validation + calibration wizard                     ║
║  ✓ Integration test suite                                    ║
║  ✓ Auto-generated documentation                              ║
║  ✓ Code quality audit + performance tuning                   ║
║                                                               ║
╠═══════════════════════════════════════════════════════════════╣
║  SKILLS GAINED                                               ║
║  Computer vision · Object tracking · OCR                     ║
║  SQLite · REST API · Streamlit · Docker                      ║
║  Multi-threading · Logging · Testing · Profiling             ║
╠═══════════════════════════════════════════════════════════════╣
║  WHAT TO BUILD NEXT                                          ║
║  → Add a mobile app (Flutter / React Native) for alerts      ║
║  → Train a custom helmet detection model on your own data    ║
║  → Add speed estimation (distance ÷ time between frames)     ║
║  → Add wrong-way driving detection                           ║
║  → Connect to a city traffic management API                  ║
║  → Add face-blur for privacy compliance                      ║
╚═══════════════════════════════════════════════════════════════╝
"""


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 45 — Final Demo")
    parser.add_argument("--source",  default=str(VIDEO_SOURCE))
    parser.add_argument("--all",     action="store_true",
                        help="Start pipeline + API together")
    parser.add_argument("--summary", action="store_true",
                        help="Print 45-day achievement summary")
    parser.add_argument("--port",    type=int, default=8000)
    args = parser.parse_args()
    src = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 45 — Production-Ready Traffic Monitoring System")
    print("=" * 65)

    db    = TrafficDB()
    stats = {"fps": 0, "frames": 0, "detections": 0}

    if args.summary:
        print(ACHIEVEMENT_SUMMARY)
        sys.exit(0)

    if args.all:
        print(f"\n  Starting: pipeline + API (port {args.port})")
        print("  Open dashboard: streamlit run dashboard/app.py")
        print("  API docs:       http://127.0.0.1:8000/docs\n")

        pipeline_t = threading.Thread(
            target=run_pipeline_thread, args=(src, stats), daemon=True)
        api_t = threading.Thread(
            target=run_api_thread, args=(args.port,), daemon=True)

        pipeline_t.start()
        time.sleep(0.5)
        api_t.start()
        time.sleep(0.5)

        terminal_status(stats, db, refresh=2)

        pipeline_t.join(timeout=3)
        api_t.join(timeout=3)

    else:
        # Default: show DB summary + achievement
        print_db_summary(db)
        print(ACHIEVEMENT_SUMMARY)
        print("  Run with --all to start the full system.")
        print("  Run with --summary to see the achievement board again.")
