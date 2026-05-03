# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 28 — day28_test.py
#  Topic: Structured logging — rotating file logs, log levels, session IDs
#
#  NEW today:
#    ✓ RotatingFileHandler: log files that don't grow forever
#    ✓ Session ID: unique ID per pipeline run for traceability
#    ✓ Structured log format with timestamp, level, module, message
#    ✓ Separate log files: pipeline.log, violations.log, errors.log
#    ✓ Read and search logs programmatically
#
#  Run:  python day28_test.py
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, logging, uuid, time, argparse
from logging.handlers import RotatingFileHandler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import LOGS_DIR, LOG_LEVEL

os.makedirs(LOGS_DIR, exist_ok=True)

SESSION_ID = str(uuid.uuid4())[:8].upper()   # e.g. "A1B2C3D4"


# ── Logger factory ────────────────────────────────────────────────────────────
def make_file_logger(name, filename, level=logging.INFO, max_bytes=2_000_000, backups=3):
    """Create a logger that writes to a rotating file + stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        f"%(asctime)s | %(levelname)-8s | session={SESSION_ID} | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler (max 2 MB, keep 3 backups)
    fh = RotatingFileHandler(
        os.path.join(LOGS_DIR, filename),
        maxBytes=max_bytes, backupCount=backups,
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Also echo to stdout
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ── Three dedicated loggers ───────────────────────────────────────────────────
pipeline_log  = make_file_logger("pipeline",   "pipeline.log",   logging.INFO)
violation_log = make_file_logger("violations", "violations.log", logging.WARNING)
error_log     = make_file_logger("errors",     "errors.log",     logging.ERROR)


# ── Demo: write some log entries ──────────────────────────────────────────────
def demo_logging():
    pipeline_log.info("Pipeline started")
    pipeline_log.info("VehicleDetector loaded — yolov8n.pt")
    pipeline_log.info("HelmetDetector loaded — helmet_detect.pt (fallback)")
    pipeline_log.info("RiderCounter loaded — overlap method")
    pipeline_log.info("Processing source: webcam/0")

    for frame_n in range(1, 6):
        pipeline_log.debug(f"Frame {frame_n} processed")
        if frame_n == 2:
            violation_log.warning(
                f"VIOLATION | type=NO_HELMET | plate=UP14AB1234 | "
                f"track_id=7 | frame={frame_n} | session={SESSION_ID}"
            )
        if frame_n == 4:
            violation_log.warning(
                f"VIOLATION | type=TRIPLE_RIDING | plate=DL3CAB5678 | "
                f"track_id=12 | frame={frame_n} | session={SESSION_ID}"
            )
        if frame_n == 5:
            error_log.error(
                f"OCR timeout on track_id=15 — EasyOCR took >2s | frame={frame_n}"
            )
        time.sleep(0.05)

    pipeline_log.info(f"Session complete | violations=2 | vehicles=5 | session={SESSION_ID}")


# ── Log reader / searcher ─────────────────────────────────────────────────────
def search_log(filename, keyword, tail=20):
    path = os.path.join(LOGS_DIR, filename)
    if not os.path.exists(path):
        print(f"  Log not found: {path}")
        return []
    matches = []
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        if keyword.lower() in line.lower():
            matches.append(line.rstrip())
    return matches[-tail:]   # return last `tail` matching lines


if __name__ == "__main__":
    print("=" * 65)
    print("  DAY 28 — Structured Logging")
    print("=" * 65)
    print(f"\n  Session ID : {SESSION_ID}")
    print(f"  Logs dir   : {LOGS_DIR}")
    print()

    demo_logging()

    print("\n  ── LOG FILES CREATED ─────────────────────────────────────")
    for fname in ["pipeline.log", "violations.log", "errors.log"]:
        fpath = os.path.join(LOGS_DIR, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            with open(fpath) as f:
                lines = f.readlines()
            print(f"  {fname:<20s}: {len(lines):3d} lines  ({size:,} bytes)")

    print("\n  ── SEARCHING violations.log for 'NO_HELMET' ─────────────")
    for line in search_log("violations.log", "NO_HELMET"):
        print(f"  {line}")

    print("\n  ── LOG FILE ROTATION EXPLAINED ───────────────────────────")
    print("""
  RotatingFileHandler(maxBytes=2_000_000, backupCount=3)

  When pipeline.log reaches 2 MB:
    pipeline.log     → pipeline.log.1
    pipeline.log.1   → pipeline.log.2
    pipeline.log.2   → pipeline.log.3   (oldest, gets deleted)
    new pipeline.log starts fresh

  You always have at most 4 × 2 MB = 8 MB of logs.
  Use backupCount=5 and maxBytes=5_000_000 for longer retention.
""")
    print("  Next → python day29_test.py  (Error handling + edge cases)")
