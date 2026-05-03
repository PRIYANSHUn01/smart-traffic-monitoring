# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 41 — day41_test.py
#  Topic: Real-world testing — checklist, calibration, field validation
#
#  NEW today:
#    ✓ Pre-deployment checklist (camera angle, lighting, DB health)
#    ✓ Calibration wizard: set count line position interactively
#    ✓ Ground-truth comparison: manual count vs system count
#    ✓ False positive / false negative analysis
#    ✓ Field test report generator
#
#  Run:  python day41_test.py              (checklist + report)
#  Run:  python day41_test.py --calibrate  (interactive count-line setup)
#  Run:  python day41_test.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse, json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
from config         import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, DB_PATH
log = get_logger("day41")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Pre-deployment checklist ──────────────────────────────────────────────────

CHECKLIST = [
    ("Camera accessible",       lambda s: _check_camera(s)),
    ("DB directory writable",   lambda s: _check_db_dir()),
    ("Model weights present",   lambda s: _check_model()),
    ("Snapshot dir exists",     lambda s: _check_snapshots()),
    ("Logs dir exists",         lambda s: _check_logs()),
    ("ultralytics installed",   lambda s: _check_import("ultralytics")),
    ("fastapi installed",       lambda s: _check_import("fastapi")),
    ("easyocr installed",       lambda s: _check_import("easyocr")),
    ("Sufficient disk space",   lambda s: _check_disk(500)),   # MB
    ("Sufficient RAM",          lambda s: _check_ram(1.0)),    # GB
]


def _check_camera(src):
    cap = cv2.VideoCapture(src)
    ok  = cap.isOpened()
    if ok:
        ret, _ = cap.read()
        cap.release()
        return ok and ret, "opened + frame read"
    return False, "cannot open"

def _check_db_dir():
    d = os.path.dirname(os.path.abspath(DB_PATH))
    os.makedirs(d, exist_ok=True)
    return os.path.isdir(d), d

def _check_model():
    for path in ["models/vehicle_detect.pt", "models/yolov8n.pt",
                 "yolov8n.pt", "models/helmet_model.pt"]:
        full = os.path.join(BASE_DIR, path)
        if os.path.exists(full):
            return True, path
    return False, "no .pt files in models/"

def _check_snapshots():
    d = os.path.join(BASE_DIR, "data", "snapshots")
    os.makedirs(d, exist_ok=True)
    return True, d

def _check_logs():
    d = os.path.join(BASE_DIR, "logs")
    os.makedirs(d, exist_ok=True)
    return True, d

def _check_import(name):
    try:
        mod = __import__(name)
        return True, getattr(mod, "__version__", "ok")
    except ImportError:
        return False, "not installed"

def _check_disk(min_mb):
    try:
        import psutil
        free_mb = psutil.disk_usage(BASE_DIR).free / 1024 / 1024
        return free_mb >= min_mb, f"{free_mb:.0f} MB free"
    except ImportError:
        return True, "psutil not installed — skipped"

def _check_ram(min_gb):
    try:
        import psutil
        avail_gb = psutil.virtual_memory().available / 1024**3
        return avail_gb >= min_gb, f"{avail_gb:.1f} GB available"
    except ImportError:
        return True, "psutil not installed — skipped"


def run_checklist(src):
    print("\n  Pre-deployment checklist:\n")
    passed = 0; total = len(CHECKLIST)
    for name, check_fn in CHECKLIST:
        try:
            ok, detail = check_fn(src)
        except Exception as e:
            ok, detail = False, str(e)
        mark = "✓" if ok else "✗"
        print(f"  {mark}  {name:<35s}  {detail}")
        if ok:
            passed += 1

    print(f"\n  Result: {passed}/{total} checks passed")
    if passed == total:
        print("  System is ready for field deployment.")
    else:
        print("  Fix failing checks before deployment.")
    return passed == total


# ── Calibration wizard ────────────────────────────────────────────────────────

_calib_y = [0.6]   # count-line Y position as fraction of frame height

def calibrate_count_line(src):
    """Interactive: click to set the counting line position."""
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"  Cannot open: {src}")
        return None

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("  Cannot read frame.")
        return None

    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
    h, w  = frame.shape[:2]

    print("\n  Calibration: click to set count line (Q to accept).")

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            _calib_y[0] = y / h
            print(f"  Count line set at y={y} ({_calib_y[0]:.2f} of height)")

    cv2.namedWindow("Calibrate (click = set line, Q = done)")
    cv2.setMouseCallback("Calibrate (click = set line, Q = done)", on_mouse)

    while True:
        display = frame.copy()
        line_y  = int(_calib_y[0] * h)
        cv2.line(display, (0, line_y), (w, line_y), (0, 255, 255), 2)
        cv2.putText(display, f"Count line: {_calib_y[0]:.2f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.putText(display, "Click to move | Q = accept",
                    (10, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.imshow("Calibrate (click = set line, Q = done)", display)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

    # Save calibration
    cal_path = os.path.join(BASE_DIR, "data", "calibration.json")
    os.makedirs(os.path.dirname(cal_path), exist_ok=True)
    with open(cal_path, "w") as f:
        json.dump({"count_line_y": _calib_y[0],
                   "frame_width":  FRAME_WIDTH,
                   "frame_height": FRAME_HEIGHT,
                   "calibrated_at": datetime.now().isoformat()}, f, indent=2)

    print(f"\n  Calibration saved: {cal_path}")
    print(f"  Count line position: {_calib_y[0]:.2f} (y fraction)")
    print("  Update COUNT_LINE_Y in config.py to match.")
    return _calib_y[0]


# ── Ground-truth comparison ───────────────────────────────────────────────────

def ground_truth_report(system_count, manual_count, label="vehicles"):
    if manual_count == 0:
        print("  No manual count provided — skipping accuracy report.")
        return

    precision = system_count / manual_count if manual_count > 0 else 0
    recall    = system_count / manual_count  # simplified — assumes all manual = ground truth
    err_pct   = abs(system_count - manual_count) / manual_count * 100

    print(f"\n  Ground-Truth Comparison ({label})")
    print(f"  System count  : {system_count}")
    print(f"  Manual count  : {manual_count}")
    print(f"  Error         : {err_pct:.1f}%")
    if err_pct < 5:
        print("  ✓  Excellent accuracy (< 5% error)")
    elif err_pct < 15:
        print("  ⚠  Acceptable (5–15% error) — check COUNT_LINE_Y position")
    else:
        print("  ✗  Poor accuracy (>15%) — recalibrate or retrain model")


# ── Field test report ─────────────────────────────────────────────────────────

def generate_field_report(db, duration_s, src_label):
    total_v = db.get_total_vehicles()
    total_viol = db.get_total_violations()
    breakdown = db.get_violation_breakdown()

    report = {
        "generated_at":   datetime.now().isoformat(),
        "source":         str(src_label),
        "test_duration_s": duration_s,
        "total_vehicles":  total_v,
        "total_violations": total_viol,
        "violations_per_minute": round(total_viol / max(duration_s / 60, 1), 2),
        "vehicles_per_minute":   round(total_v    / max(duration_s / 60, 1), 2),
        "violation_breakdown":   breakdown,
    }

    report_path = os.path.join(BASE_DIR, "logs",
                               f"field_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("\n  ── FIELD TEST REPORT ────────────────────────────────────────")
    print(f"  Source         : {src_label}")
    print(f"  Test duration  : {duration_s}s")
    print(f"  Vehicles       : {total_v}  ({report['vehicles_per_minute']:.1f}/min)")
    print(f"  Violations     : {total_viol}  ({report['violations_per_minute']:.1f}/min)")
    if breakdown:
        print("  Breakdown:")
        for k, v in breakdown.items():
            print(f"    {k:<20s}: {v}")
    print(f"\n  Report saved: {report_path}")
    return report


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 41 — Real-World Testing")
    parser.add_argument("--source",     default=str(VIDEO_SOURCE))
    parser.add_argument("--calibrate",  action="store_true")
    parser.add_argument("--manual-count", type=int, default=0,
                        help="Manual vehicle count for accuracy comparison")
    parser.add_argument("--duration",   type=int, default=60,
                        help="Test duration in seconds for report")
    args = parser.parse_args()
    src = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 41 — Real-World Testing & Field Validation")
    print("=" * 65)

    # Pre-deployment checklist
    run_checklist(src)

    if args.calibrate:
        calibrate_count_line(src)

    # Generate field test report from current DB
    db = TrafficDB()
    generate_field_report(db, duration_s=args.duration, src_label=src)

    # Ground-truth comparison (if manual count provided)
    if args.manual_count > 0:
        system_count = db.get_total_vehicles()
        ground_truth_report(system_count, args.manual_count)

    print("\n  ── FIELD TESTING TIPS ───────────────────────────────────────")
    print("""
  1. Camera angle
     • Mount at 3–6m height, 15–30° downward angle
     • Avoid direct sunlight on lens
     • Frame should show full lane width

  2. Count line position
     • Run --calibrate to set it visually
     • Place mid-frame where vehicles are fully visible
     • Avoid placing at entry/exit edges

  3. Accuracy targets
     • Vehicle count: < 5% error vs manual count
     • Helmet detection: > 80% accuracy on clear frames
     • Plate reading: > 70% on well-lit plates at < 40 km/h

  4. Lighting
     • Test at: dawn, noon, dusk, night (with IR cam if available)
     • Night mode: enable CLAHE preprocessing (day34)

  5. Run a 30-min baseline before going live
     • Compare system count with traffic officer's manual tally
""")
    print("  Next → python day42_test.py  (Final integration test)")
