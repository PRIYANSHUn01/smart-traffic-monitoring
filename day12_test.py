# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 12 — day12_test.py
#  Topic: RiderCounter — count persons on each detected bike (Solo/Double/Triple+)
#
#  Builds on Day 11 (VehicleDetector + HelmetDetector).
#  NEW today:
#    ✓ RiderCounter class loaded (overlap method)
#    ✓ Detects persons in frame, overlaps with each bike box
#    ✓ Solo=green, Double=orange, Triple+=RED (violation)
#    ✓ Terminal alert when 3+ riders detected
#
#  Run: python day12_test.py
#  Run with video: python day12_test.py --source data/videos/traffic.mp4
#  Use pose model: python day12_test.py --method pose
#
#  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR

def main():
    parser = argparse.ArgumentParser(description="Day 12 — Rider Counting")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    parser.add_argument("--method", default="overlap", choices=["overlap", "pose"],
                        help="overlap=person box IoU, pose=skeleton keypoints")
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 12: RIDER COUNTING")
    print("=" * 65)
    print(f"  Source  : {src}")
    print(f"  Method  : {args.method}")
    print()
    print("  What is active:")
    print("  Days 1-11  ✓ Detection, tracking, counting, helmet")
    print("  Day 12     ✓ RiderCounter — solo / double / triple+")
    print()
    print("  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails")
    print("=" * 65)

    vehicle_det = VehicleDetector()
    helmet_det  = HelmetDetector()
    rider_ctr   = RiderCounter(method=args.method)

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False; show_trails = True
    fps_t = time.time(); fps_c = 0; fps = 0.0

    triple_events = []   # list of (frame_n, track_id)

    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                if total_frames > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    vehicle_det.reset()
                    frame_n = 0; continue
                else:
                    break
            frame_n += 1
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # ── Full pipeline ─────────────────────────────────────────────────
            veh_result = vehicle_det.process_frame(frame, frame_n)
            detections = veh_result["detections"]

            # Day 12: count riders
            detections = rider_ctr.count_all(frame, detections)

            # Day 11: helmet check
            detections = helmet_det.check_all(frame, detections)

            # ── Detect triple-riding violations ───────────────────────────────
            for det in detections:
                if det.get("is_triple_viol"):
                    tid = det["track_id"]
                    triple_events.append((frame_n, tid))
                    print(f"  🚨 TRIPLE RIDING  ID={tid}  riders={det['rider_count']}  frame={frame_n}")

            # ── Draw ──────────────────────────────────────────────────────────
            if show_trails:
                vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            rider_ctr.draw(frame, detections)
            helmet_det.draw(frame, detections)

            # FPS
            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()
            cv2.putText(frame, f"FPS:{fps:.1f}  Method:{args.method}",
                        (FRAME_WIDTH // 2 - 80, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        cv2.imshow("Day 12 — Rider Counting (Q/R/P/S/T)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF

        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset(); frame_n = 0
            triple_events.clear()
            fps_c = 0; fps_t = time.time()
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")
        elif key == ord('s'):
            p = os.path.join(SNAPSHOTS_DIR, f"day12_snap_{int(time.time())}.jpg")
            cv2.imwrite(p, frame) # type: ignore
            print(f"  Snapshot: {p}")
        elif key == ord('t'):
            show_trails = not show_trails
            print(f"  Trails: {'ON' if show_trails else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 65)
    print("  DAY 12 SUMMARY")
    print("=" * 65)
    print(f"  Frames processed      : {frame_n:,}")
    print(f"  Triple-riding events  : {len(triple_events)}")
    for fn, tid in triple_events[:10]:
        print(f"    frame {fn:6d}  ID={tid}")
    print()
    print("  ✓ RiderCounter counts persons overlapping each bike box")
    print("  ✓ Solo=1, Double=2, Triple+=3 (is_triple_viol=True)")
    print("  ✓ Color: green=solo, orange=double, red=triple+")
    print("  Next → python day13_test.py  (License plate OCR)")
    print("=" * 65)

if __name__ == "__main__":
    main()
