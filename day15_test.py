# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 15 — day15_test.py
#  Topic: Full pipeline — all 4 modules wired together via TrafficPipeline
#
#  This is the first time all modules run together in one session:
#    VehicleDetector → RiderCounter → HelmetDetector → PlateReader
#    → ViolationChecker → TrafficDB
#
#  NEW today:
#    ✓ TrafficPipeline class (pipeline.py) called directly
#    ✓ All 4 modules active simultaneously
#    ✓ Violations logged to SQLite + CSV + snapshot saved
#    ✓ Session summary printed on exit
#
#  Run: python day15_test.py
#  Run with video: python day15_test.py --source data/videos/traffic.mp4
#  Disable modules: --no-helmet --no-riders --no-plate
#
#  Keys: Q=quit  R=reset  S=snapshot
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import TrafficPipeline
from config import VIDEO_SOURCE

def main():
    parser = argparse.ArgumentParser(description="Day 15 — Full Pipeline")
    parser.add_argument("--source",    default=str(VIDEO_SOURCE))
    parser.add_argument("--no-helmet", action="store_true")
    parser.add_argument("--no-riders", action="store_true")
    parser.add_argument("--no-plate",  action="store_true")
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 15: FULL PIPELINE")
    print("=" * 65)
    print(f"  Source    : {src}")
    print(f"  Helmet    : {'OFF' if args.no_helmet else 'ON'}")
    print(f"  Riders    : {'OFF' if args.no_riders else 'ON'}")
    print(f"  Plate OCR : {'OFF' if args.no_plate  else 'ON'}")
    print()
    print("  All modules active:")
    print("  ✓ VehicleDetector   (Days 8-10)")
    print("  ✓ HelmetDetector    (Day 11)")
    print("  ✓ RiderCounter      (Day 12)")
    print("  ✓ PlateReader       (Day 13)")
    print("  ✓ TrafficDB         (Day 14)")
    print("  ✓ Violation checker + snapshot saver")
    print()
    print("  Keys: Q=quit  R=reset  S=snapshot")
    print("  Dashboard: streamlit run dashboard/app.py")
    print("=" * 65)

    pipe = TrafficPipeline(
        source     = src,
        use_helmet = not args.no_helmet,
        use_riders = not args.no_riders,
        use_plate  = not args.no_plate,
    )
    pipe.run()

    print("\n" + "=" * 65)
    print("  DAY 15 COMPLETE — Full Pipeline")
    print("=" * 65)
    print("  ✓ All 4 detection modules ran together")
    print("  ✓ Violations saved to DB and CSV")
    print("  ✓ Snapshots saved for each violation")
    print(f"  Violations logged: {pipe.db.get_total_violations()}")
    print(f"  Vehicles counted:  {pipe.db.get_total_vehicles()}")
    print()
    print("  Next → python day16_test.py  (Violation logic deep dive)")
    print("=" * 65)

if __name__ == "__main__":
    main()
