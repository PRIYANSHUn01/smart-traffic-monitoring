# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 20 — day20_test.py
#  Topic: Live data pipeline → DB → Dashboard — wiring all three together
#
#  NEW today:
#    ✓ Run pipeline + dashboard simultaneously and watch data flow live
#    ✓ Understand how dashboard/app.py reads from SQLite in real-time
#    ✓ Insert synthetic test records to demo dashboard without a real camera
#    ✓ Verify dashboard metrics update correctly after each insert
#
#  Run:  python day20_test.py            (inject demo data, then view dashboard)
#  Run:  python day20_test.py --live     (real pipeline + DB writes)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, random, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
from config import (
    VIDEO_SOURCE, VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE,
    VIOLATION_DOUBLE_RIDE,
)

log = get_logger("day20")

SAMPLE_PLATES = [
    "UP14AB1234","DL3CAB5678","MH12AB3456","KA05MN7890",
    "TN09XY2345","GJ18CD6789","RJ14EF0123","WB23GH4567",
]
VEHICLE_TYPES = ["motorcycle", "motorcycle", "motorcycle", "bicycle"]
HELMET_STATUSES = ["with_helmet", "without_helmet", "unknown"]
VIOLATION_TYPES = [VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE, VIOLATION_DOUBLE_RIDE]


def inject_demo_data(db, n=20, delay=0.3):
    """Insert n synthetic violation records with a small delay between each."""
    print(f"\n  Injecting {n} demo records into DB (delay={delay}s each)…")
    print("  Open  http://localhost:8501  and watch the dashboard update live!")
    print("  (Start dashboard first:  streamlit run dashboard/app.py)\n")

    for i in range(n):
        plate   = random.choice(SAMPLE_PLATES)
        vtype   = random.choice(VEHICLE_TYPES)
        viol    = random.choice(VIOLATION_TYPES)
        helmet  = "without_helmet" if viol == VIOLATION_NO_HELMET else "with_helmet"
        riders  = 3 if viol == VIOLATION_TRIPLE_RIDE else (2 if viol == VIOLATION_DOUBLE_RIDE else 1)

        db.log_vehicle_count(vtype)
        db.log_violation(
            track_id     = i + 100,
            plate        = plate,
            vehicle_type = vtype,
            rider_count  = riders,
            helmet_status= helmet,
            violation_type=viol,
            snapshot_path= "",
            frame_number  = i * 30,
        )
        print(f"  [{i+1:2d}/{n}] {viol:<18s}  plate={plate:<12s}  type={vtype}")
        time.sleep(delay)

    print(f"\n  Done. DB now has {db.get_total_violations()} total violations.")
    print(f"  Vehicle types: {db.get_vehicle_type_counts()}")
    print(f"  Breakdown    : {db.get_violation_breakdown()}")


def run_live_pipeline(src):
    from modules.vehicle_detector import VehicleDetector
    from modules.helmet_detector  import HelmetDetector
    from modules.rider_counter    import RiderCounter
    from pipeline                 import TrafficPipeline

    print("\n  Starting live pipeline — watch dashboard at http://localhost:8501")
    pipe = TrafficPipeline(source=src, use_helmet=True, use_riders=True, use_plate=False)
    pipe.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 20 — Live Data Wiring")
    parser.add_argument("--live",   action="store_true", help="Run real pipeline")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    parser.add_argument("--n",      type=int, default=20, help="Demo records to inject")
    parser.add_argument("--delay",  type=float, default=0.5,
                        help="Seconds between injections (so you can watch dashboard)")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 20 — Live Data: Pipeline → DB → Dashboard")
    print("=" * 65)

    db = TrafficDB()

    if args.live:
        src = int(args.source) if str(args.source).isdigit() else args.source
        run_live_pipeline(src)
    else:
        inject_demo_data(db, n=args.n, delay=args.delay)
        print("\n  ── VERIFICATION ─────────────────────────────────────────────")
        print(f"  Hourly counts: {db.get_hourly_counts()}")
        print("\n  Tip: run with --live to use a real video source.")
        print("  Next → python day21_test.py  (Plotly chart deep dive)")
