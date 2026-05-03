# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 14 — day14_test.py
#  Topic: TrafficDB — SQLite violation logging, CSV export, dashboard queries
#
#  NEW today:
#    ✓ TrafficDB class: creates tables, inserts violations, reads back
#    ✓ log_violation() → saves to SQLite + CSV
#    ✓ log_vehicle_count() → tracks all vehicles that crossed line
#    ✓ get_recent_violations(), get_violation_breakdown()
#    ✓ Standalone DB demo (no video required) + live DB during pipeline
#
#  Run: python day14_test.py           (standalone DB demo)
#  Run: python day14_test.py --live    (with live video + DB writes)
#  Run: python day14_test.py --live --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from config import (
    VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT,
    SNAPSHOTS_DIR, DB_PATH, CSV_LOG_PATH,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE,
)

# ── Part 1: standalone DB demo ────────────────────────────────────────────────
def demo_database():
    print("=" * 65)
    print("  DAY 14 PART 1 — TrafficDB Standalone Demo")
    print("=" * 65)

    db = TrafficDB()
    print(f"\n  Database path: {DB_PATH}")

    # Insert test violations
    print("\n  Inserting test records…")
    db.log_violation(track_id=1,  plate="UP14AB1234", vehicle_type="motorcycle",
                     rider_count=1, helmet_status="without_helmet",
                     violation_type=VIOLATION_NO_HELMET,
                     snapshot_path="", frame_number=150)
    db.log_violation(track_id=2,  plate="DL3CAB5678", vehicle_type="motorcycle",
                     rider_count=3, helmet_status="with_helmet",
                     violation_type=VIOLATION_TRIPLE_RIDE,
                     snapshot_path="", frame_number=210)
    db.log_violation(track_id=3,  plate="UNKNOWN",    vehicle_type="bicycle",
                     rider_count=1, helmet_status="without_helmet",
                     violation_type=VIOLATION_NO_HELMET,
                     snapshot_path="", frame_number=320)
    db.log_vehicle_count("motorcycle")
    db.log_vehicle_count("motorcycle")
    db.log_vehicle_count("bicycle")

    # Read back
    print("\n  Recent violations:")
    for row in db.get_recent_violations(limit=10):
        print(f"    [{row['id']}] {row['timestamp']}  "
              f"plate={row['plate_number']:<12s}  "
              f"type={row['violation_type']}")

    print(f"\n  Total violations     : {db.get_total_violations()}")
    print(f"  Total vehicles       : {db.get_total_vehicles()}")
    print(f"  Breakdown            : {db.get_violation_breakdown()}")
    print(f"  Vehicle type counts  : {db.get_vehicle_type_counts()}")

    # Search by plate
    results = db.search_by_plate("UP14")
    print(f"\n  Search 'UP14' → {len(results)} result(s)")
    for r in results:
        print(f"    Plate={r['plate_number']}  viol={r['violation_type']}")

    print(f"\n  CSV log written to: {CSV_LOG_PATH}")
    print("\n  ✓ TrafficDB demo complete")


# ── Part 2: live video with DB writes ────────────────────────────────────────
def live_with_db(src):
    from modules.vehicle_detector import VehicleDetector
    from modules.helmet_detector  import HelmetDetector
    from modules.rider_counter    import RiderCounter
    from utils.helpers import save_snapshot

    print("\n" + "=" * 65)
    print("  DAY 14 PART 2 — Live Pipeline + Database Writes")
    print("=" * 65)

    vehicle_det  = VehicleDetector()
    helmet_det   = HelmetDetector()
    rider_ctr    = RiderCounter(method="overlap")
    db           = TrafficDB()

    violation_ids = set()

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False
    fps_t = time.time(); fps_c = 0; fps = 0.0
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                if total_frames > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    vehicle_det.reset(); frame_n = 0; continue
                else:
                    break
            frame_n += 1
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            veh_result = vehicle_det.process_frame(frame, frame_n)
            detections = veh_result["detections"]

            # Log newly counted vehicles
            for tid in veh_result["newly_counted"]:
                vtype = vehicle_det.track_types.get(tid, "motorcycle")
                db.log_vehicle_count(vtype)

            detections = rider_ctr.count_all(frame, detections)
            detections = helmet_det.check_all(frame, detections)

            # Log violations (once per track_id)
            for det in detections:
                tid = det.get("track_id")
                if tid is None or tid in violation_ids:
                    continue
                viols = []
                if det.get("helmet_status") == "without_helmet":
                    viols.append(VIOLATION_NO_HELMET)
                if det.get("is_triple_viol"):
                    viols.append(VIOLATION_TRIPLE_RIDE)

                if viols:
                    violation_ids.add(tid)
                    snap = save_snapshot(frame, tid, "+".join(viols), SNAPSHOTS_DIR)
                    for v in viols:
                        db.log_violation(
                            track_id=tid, plate=det.get("plate", "UNKNOWN"),
                            vehicle_type=det.get("vehicle_type", "motorcycle"),
                            rider_count=det.get("rider_count", 1),
                            helmet_status=det.get("helmet_status", "unknown"),
                            violation_type=v, snapshot_path=snap,
                            frame_number=frame_n,
                        )
                        print(f"  DB WRITE: {v}  ID={tid}  frame={frame_n}")

            # Draw
            vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            rider_ctr.draw(frame, detections)
            helmet_det.draw(frame, detections)

            # Live DB stats overlay
            total_v = db.get_total_violations()
            cv2.putText(frame, f"DB violations: {total_v}",
                        (8, FRAME_HEIGHT - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)

            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()
            cv2.putText(frame, f"FPS:{fps:.1f}",
                        (FRAME_WIDTH // 2 - 30, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Day 14 — Database Logging (Q/R/P)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF
        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset(); frame_n = 0
            violation_ids.clear()
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n  Session violations: {len(violation_ids)}")
    print(f"  Total DB violations: {db.get_total_violations()}")
    print(f"  CSV: {CSV_LOG_PATH}")
    print("  Next → python day15_test.py  (Full pipeline with all modules)")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 14 — Database Logging")
    parser.add_argument("--live",   action="store_true", help="Run live video + DB demo")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    demo_database()
    if args.live:
        live_with_db(src)
    else:
        print("\n  Tip: run with --live to also test DB writes during video")
        print("  Next → python day15_test.py")
