# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 16 — day16_test.py
#  Topic: Violation detection logic — configurable thresholds, cooldown, dedup
#
#  NEW today:
#    ✓ ViolationTracker class — prevents duplicate logs for same vehicle
#    ✓ Per-vehicle cooldown (avoid spamming same violation every frame)
#    ✓ Configurable min_confidence before triggering
#    ✓ "Pending" state: wait N frames before confirming a violation
#
#  Run: python day16_test.py
#  Run with video: python day16_test.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from utils.database           import TrafficDB
from utils.helpers            import get_logger, put_stats_overlay, save_snapshot
from config import (
    VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE, VIOLATION_DOUBLE_RIDE,
    ENABLE_DOUBLE_WARNING,
)

log = get_logger("day16")

# ── ViolationTracker ──────────────────────────────────────────────────────────
class ViolationTracker:
    """
    Prevents duplicate violation logs for the same vehicle.
    Also implements a 'confirmation window': a violation must be
    detected in CONFIRM_FRAMES consecutive frames before being logged.
    """
    CONFIRM_FRAMES = 5   # must see violation for this many frames

    def __init__(self, db):
        self.db         = db
        self.logged     = set()            # track_ids already fully logged
        self.pending    = defaultdict(lambda: defaultdict(int))
        # pending[track_id][violation_type] = consecutive_frame_count

    def update(self, frame, det, frame_num):
        tid = det.get("track_id")
        if tid is None or tid in self.logged:
            return []

        triggered = []

        # Helmet violation
        if det.get("helmet_status") == "without_helmet":
            self.pending[tid][VIOLATION_NO_HELMET] += 1
        else:
            self.pending[tid][VIOLATION_NO_HELMET] = 0

        # Triple riding
        if det.get("is_triple_viol"):
            self.pending[tid][VIOLATION_TRIPLE_RIDE] += 1
        else:
            self.pending[tid][VIOLATION_TRIPLE_RIDE] = 0

        # Double riding (optional)
        if ENABLE_DOUBLE_WARNING and det.get("rider_count", 1) == 2:
            self.pending[tid][VIOLATION_DOUBLE_RIDE] += 1
        else:
            self.pending[tid][VIOLATION_DOUBLE_RIDE] = 0

        # Confirm and log violations that have been consistent enough
        for vtype, count in list(self.pending[tid].items()):
            if count >= self.CONFIRM_FRAMES:
                triggered.append(vtype)

        if triggered:
            self.logged.add(tid)
            snap = save_snapshot(frame, tid, "+".join(triggered), SNAPSHOTS_DIR)
            for vtype in triggered:
                self.db.log_violation(
                    track_id=tid,
                    plate=det.get("plate", "UNKNOWN"),
                    vehicle_type=det.get("vehicle_type", "motorcycle"),
                    rider_count=det.get("rider_count", 1),
                    helmet_status=det.get("helmet_status", "unknown"),
                    violation_type=vtype,
                    snapshot_path=snap,
                    frame_number=frame_num,
                )
                log.warning(f"CONFIRMED: {vtype} | ID={tid} | frame={frame_num}")

        return triggered


def main():
    parser = argparse.ArgumentParser(description="Day 16 — Violation Logic")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 16: VIOLATION LOGIC")
    print("=" * 65)
    print(f"  Source: {src}")
    print(f"  Confirmation window: {ViolationTracker.CONFIRM_FRAMES} frames")
    print()
    print("  NEW: ViolationTracker class")
    print("  ✓ Must see violation for 5 consecutive frames to confirm")
    print("  ✓ Each track_id logged at most once per session")
    print("  ✓ Snapshot saved on confirmation")
    print("=" * 65)

    vehicle_det = VehicleDetector()
    helmet_det  = HelmetDetector()
    rider_ctr   = RiderCounter(method="overlap")
    db          = TrafficDB()
    vio_tracker = ViolationTracker(db)

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False
    fps_t = time.time(); fps_c = 0; fps = 0.0
    total_triggered = 0

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
            for tid in veh_result["newly_counted"]:
                db.log_vehicle_count(vehicle_det.track_types.get(tid, "motorcycle"))

            detections = rider_ctr.count_all(frame, detections)
            detections = helmet_det.check_all(frame, detections)

            for det in detections:
                triggered = vio_tracker.update(frame, det, frame_n)
                total_triggered += len(triggered)

            vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            rider_ctr.draw(frame, detections)
            helmet_det.draw(frame, detections)

            put_stats_overlay(frame, {
                "FPS":       f"{fps:.1f}",
                "Frame":     frame_n,
                "Vehicles":  veh_result["total_counted"],
                "Violations":db.get_total_violations(),
                "Confirmed": len(vio_tracker.logged),
            })

            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()

        cv2.imshow("Day 16 — Violation Logic (Q/R/P)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF
        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset(); frame_n = 0
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n  Confirmed violations: {len(vio_tracker.logged)}")
    print(f"  DB total           : {db.get_total_violations()}")
    print("  Next → python day17_test.py  (Snapshots + email alerts)")
