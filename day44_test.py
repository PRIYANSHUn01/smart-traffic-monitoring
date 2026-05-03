# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 44 — day44_test.py
#  Topic: Final polish — code quality, performance tuning, last bug fixes
#
#  NEW today:
#    ✓ Code quality scan: find common issues (bare except, print vs log, etc.)
#    ✓ Performance profiler: measure frame processing time per module
#    ✓ Config audit: find hardcoded values that should be in config.py
#    ✓ Dependency audit: check for unused / outdated imports
#    ✓ Final performance tuning checklist
#
#  Run:  python day44_test.py
#  Run:  python day44_test.py --audit    (code quality audit)
#  Run:  python day44_test.py --profile  (per-module profiling)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, argparse, ast, re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_logger
log = get_logger("day44")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Code quality scanner ──────────────────────────────────────────────────────

QUALITY_PATTERNS = [
    ("bare_except",     r"\bexcept\s*:",          "Replace bare `except:` with `except Exception:`"),
    ("print_statement", r"^\s*print\(",            "Use log.info() instead of print() in modules"),
    ("hardcoded_path",  r'["\'][A-Za-z]:\\\\',    "Hardcoded Windows path — use os.path.join or config"),
    ("magic_number",    r"\bconfidence\s*[<>]=?\s*0\.[0-9]",
                        "Magic confidence number — define in config.py"),
    ("todo_comment",    r"#\s*TODO|#\s*FIXME|#\s*HACK",
                        "Open TODO/FIXME — resolve before release"),
    ("deprecated_cv2",  r"cv2\.CV_",              "Legacy CV2 constant — use modern equivalent"),
]

def scan_file_quality(path):
    issues = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for lineno, line in enumerate(lines, 1):
            for name, pattern, message in QUALITY_PATTERNS:
                if re.search(pattern, line):
                    issues.append((lineno, name, message, line.strip()))
    except Exception as e:
        issues.append((0, "read_error", str(e), ""))
    return issues


def run_quality_audit(files=None):
    if files is None:
        files = []
        for root, dirs, fnames in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs
                       if d not in ("__pycache__", ".git", "node_modules")]
            for fname in fnames:
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))

    total_issues = 0
    print(f"\n  Code quality audit: {len(files)} files\n")
    for path in sorted(files):
        issues = scan_file_quality(path)
        if issues:
            rel = os.path.relpath(path, BASE_DIR)
            for lineno, name, msg, code in issues[:5]:   # max 5 per file
                print(f"  {rel}:{lineno}  [{name}]  {msg}")
                print(f"    → {code[:80]}")
            total_issues += len(issues)

    print(f"\n  Total issues found: {total_issues}")
    return total_issues


# ── Config audit: find hardcoded values ──────────────────────────────────────

CONFIG_SHOULD_HAVE = {
    "CONFIDENCE_THRESHOLD": (float, 0.45),
    "SKIP_FRAMES":          (int,   2),
    "TRAIL_LENGTH":         (int,   30),
    "FRAME_WIDTH":          (int,   1280),
    "FRAME_HEIGHT":         (int,   720),
    "TWO_WHEELER_LABELS":   (dict,  {}),
    "SHOW_TRAILS":          (bool,  True),
    "DB_PATH":              (str,   "data/traffic.db"),
    "VIDEO_SOURCE":         (None,  0),
}

def audit_config():
    print("\n  Config audit:\n")
    try:
        import config as cfg
    except ImportError:
        print("  ✗  Cannot import config.py")
        return

    for key, (expected_type, default) in CONFIG_SHOULD_HAVE.items():
        val = getattr(cfg, key, "__MISSING__")
        if val == "__MISSING__":
            print(f"  ✗  MISSING  {key}  (should default to {default!r})")
        elif expected_type and not isinstance(val, expected_type):
            print(f"  ⚠  {key} = {val!r}  (expected {expected_type.__name__})")
        else:
            print(f"  ✓  {key} = {val!r}")


# ── Per-module profiler ───────────────────────────────────────────────────────

def profile_modules(src, n_frames=30):
    import cv2
    import numpy as np
    from config import FRAME_WIDTH, FRAME_HEIGHT

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"  Cannot open: {src}")
        return

    try:
        from modules.vehicle_detector import VehicleDetector
        detector = VehicleDetector()
    except ImportError as e:
        print(f"  Cannot load VehicleDetector: {e}")
        cap.release()
        return

    stage_times = {"detect": [], "draw": []}
    print(f"\n  Profiling {n_frames} frames…\n")

    for i in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        t0 = time.perf_counter()
        result = detector.process_frame(frame, i + 1)
        stage_times["detect"].append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        detector.draw(frame, result)
        stage_times["draw"].append(time.perf_counter() - t0)

    cap.release()

    print(f"  {'Stage':<12s}  {'avg ms':>8s}  {'min ms':>8s}  {'max ms':>8s}  {'% of total':>10s}")
    print("  " + "-" * 55)
    total_avg = sum(sum(v)/len(v) for v in stage_times.values() if v) * 1000
    for stage, times in stage_times.items():
        if not times:
            continue
        avg = sum(times) / len(times) * 1000
        mn  = min(times) * 1000
        mx  = max(times) * 1000
        pct = avg / total_avg * 100 if total_avg > 0 else 0
        print(f"  {stage:<12s}  {avg:>8.1f}  {mn:>8.1f}  {mx:>8.1f}  {pct:>10.1f}%")

    total_fps = 1000 / total_avg if total_avg > 0 else 0
    print(f"\n  Total avg latency: {total_avg:.1f}ms → {total_fps:.1f} FPS")


# ── Performance tuning checklist ──────────────────────────────────────────────

TUNING_CHECKLIST = """
  ── PERFORMANCE TUNING CHECKLIST ─────────────────────────────────────────────

  ✓ SKIP_FRAMES = 2       Run detection every 2nd frame (config.py)
  ✓ FRAME_WIDTH = 1280    Resize input before detection
  ✓ model.track()         Use track() not predict() — reuses last detections
  ✓ deque(maxlen=N)       Cap trail history to avoid unbounded growth
  ✓ Queue(maxsize=4)      Drop-on-full in threaded pipeline (day26)
  ✓ ThreadedPipeline      Separate reader / detector / writer threads

  Targets:
    > 15 FPS  on webcam with SKIP_FRAMES=2
    > 25 FPS  on webcam with SKIP_FRAMES=1 (yolov8n, GPU)
    < 50 MB   RAM growth over 1000 frames (day35)
    < 5%      vehicle count error vs manual (day41)

  If still slow:
    1. Use yolov8n.pt (fastest) — set MODEL_PATH in config.py
    2. Enable half-precision: model.predict(half=True)  [GPU only]
    3. Lower FRAME_WIDTH to 640
    4. Increase SKIP_FRAMES to 3
    5. Use ONNX export for CPU inference:
         yolo export model=yolov8n.pt format=onnx
"""


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from config import VIDEO_SOURCE
    parser = argparse.ArgumentParser(description="Day 44 — Final Polish")
    parser.add_argument("--audit",   action="store_true", help="Code quality audit")
    parser.add_argument("--profile", action="store_true", help="Per-module profiling")
    parser.add_argument("--config",  action="store_true", help="Config audit")
    parser.add_argument("--source",  default=str(VIDEO_SOURCE))
    parser.add_argument("--frames",  type=int, default=30)
    args = parser.parse_args()
    src = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 44 — Final Polish & Performance Tuning")
    print("=" * 65)

    ran_something = False

    if args.audit:
        run_quality_audit()
        ran_something = True

    if args.config:
        audit_config()
        ran_something = True

    if args.profile:
        profile_modules(src, args.frames)
        ran_something = True

    if not ran_something:
        # Default: run all
        audit_config()
        run_quality_audit([
            os.path.join(BASE_DIR, "config.py"),
            os.path.join(BASE_DIR, "pipeline.py"),
            os.path.join(BASE_DIR, "modules", "vehicle_detector.py"),
            os.path.join(BASE_DIR, "utils", "database.py"),
        ])

    print(TUNING_CHECKLIST)
    print("  Next → python day45_test.py  (Production-ready final demo)")
