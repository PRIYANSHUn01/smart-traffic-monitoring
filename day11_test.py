# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 11 — day11_test.py
#  Topic: HelmetDetector — crop head region, run classification model
#
#  Builds on Day 10 (VehicleDetector).
#  NEW today:
#    ✓ HelmetDetector class loaded
#    ✓ Each bike box → head crop → helmet model → "with_helmet" / "without_helmet"
#    ✓ Green border = helmeted, RED border = violation
#
#  Run: python day11_test.py
#  Run with video: python day11_test.py --source data/videos/traffic.mp4
#
#  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR

def main():
    parser = argparse.ArgumentParser(description="Day 11 — Helmet Detection")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 11: HELMET DETECTION")
    print("=" * 65)
    print(f"  Source: {src}")
    print()
    print("  What is active:")
    print("  Days 1-10  ✓ Detection, tracking, counting line")
    print("  Day 11     ✓ HelmetDetector — head crop → classify")
    print()
    print("  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails")
    print("=" * 65)

    vehicle_det = VehicleDetector()
    helmet_det  = HelmetDetector()

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False; show_trails = True
    fps_t = time.time(); fps_c = 0; fps = 0.0

    helmet_ok_count    = 0
    no_helmet_count    = 0
    unknown_count      = 0

    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                if total_frames > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    vehicle_det.reset()
                    frame_n = 0
                    continue
                else:
                    break
            frame_n += 1
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # ── Day 10 pipeline ───────────────────────────────────────────────
            veh_result = vehicle_det.process_frame(frame, frame_n)
            detections = veh_result["detections"]

            # ── Day 11: helmet check for every detected bike ──────────────────
            detections = helmet_det.check_all(frame, detections)

            # Count helmet statuses this frame
            for det in detections:
                s = det.get("helmet_status", "unknown")
                if s == "with_helmet":    helmet_ok_count += 1
                elif s == "without_helmet": no_helmet_count += 1
                else:                      unknown_count += 1

            # ── Draw ──────────────────────────────────────────────────────────
            if show_trails:
                vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            helmet_det.draw(frame, detections)

            # Log violations to terminal
            for det in detections:
                if det.get("helmet_status") == "without_helmet":
                    tid = det["track_id"]
                    print(f"  ⚠  NO HELMET  ID={tid}  frame={frame_n}")

            # FPS
            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()
            cv2.putText(frame, f"FPS:{fps:.1f}",
                        (FRAME_WIDTH // 2 - 30, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Day 11 — Helmet Detection (Q/R/P/S/T)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF

        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset()
            frame_n = 0; fps_c = 0; fps_t = time.time()
            helmet_ok_count = no_helmet_count = unknown_count = 0
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")
        elif key == ord('s'):
            p = os.path.join(SNAPSHOTS_DIR, f"day11_snap_{int(time.time())}_f{frame_n}.jpg")
            cv2.imwrite(p, frame) # type: ignore
            print(f"  Snapshot: {p}")
        elif key == ord('t'):
            show_trails = not show_trails
            print(f"  Trails: {'ON' if show_trails else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 65)
    print("  DAY 11 SUMMARY")
    print("=" * 65)
    print(f"  Frames processed : {frame_n:,}")
    print(f"  Helmet OK        : {helmet_ok_count}")
    print(f"  NO HELMET        : {no_helmet_count}")
    print(f"  Unknown          : {unknown_count}")
    print()
    print("  ✓ HelmetDetector crops the top 40% of each bike box")
    print("  ✓ Runs classification model on head region crop")
    print("  ✓ Returns 'with_helmet' / 'without_helmet' / 'unknown'")
    print("  Next → python day12_test.py  (Rider counting)")
    print("=" * 65)

if __name__ == "__main__":
    main()
