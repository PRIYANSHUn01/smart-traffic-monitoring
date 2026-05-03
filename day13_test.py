# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 13 — day13_test.py
#  Topic: PlateReader — detect plate region, OCR with EasyOCR, voting system
#
#  Builds on Day 12.
#  NEW today:
#    ✓ PlateReader class with EasyOCR
#    ✓ Detects plate region in lower half of bike box
#    ✓ Voting system: collects 10 readings, picks most consistent
#    ✓ Plate text shown below each bike box when stable
#
#  Run: python day13_test.py
#  Run with video: python day13_test.py --source data/videos/traffic.mp4
#
#  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from modules.plate_reader     import PlateReader
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR

def main():
    parser = argparse.ArgumentParser(description="Day 13 — License Plate OCR")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 13: LICENSE PLATE OCR")
    print("=" * 65)
    print(f"  Source: {src}")
    print()
    print("  What is active:")
    print("  Days 1-12  ✓ Detection, tracking, helmet, riders")
    print("  Day 13     ✓ PlateReader — OCR via EasyOCR + voting")
    print()
    print("  NOTE: EasyOCR loads in ~5 seconds on first run")
    print("  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails")
    print("=" * 65)

    vehicle_det = VehicleDetector()
    helmet_det  = HelmetDetector()
    rider_ctr   = RiderCounter(method="overlap")
    plate_rdr   = PlateReader()

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False; show_trails = True
    fps_t = time.time(); fps_c = 0; fps = 0.0

    stable_plates = {}   # {track_id: plate_str}

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
            detections = rider_ctr.count_all(frame, detections)
            detections = helmet_det.check_all(frame, detections)

            # Day 13: plate OCR
            for det in detections:
                tid = det.get("track_id")
                if tid is None:
                    continue
                plate_info = plate_rdr.read(frame, det["box"], tid)
                det["plate"]        = plate_info["plate"]
                det["plate_stable"] = plate_info["stable"]

                if plate_info["stable"] and tid not in stable_plates:
                    stable_plates[tid] = plate_info["plate"]
                    print(f"  📋 Plate STABLE  ID={tid}  plate={plate_info['plate']}"
                          f"  frame={frame_n}")

            # ── Draw ──────────────────────────────────────────────────────────
            if show_trails:
                vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            rider_ctr.draw(frame, detections)
            helmet_det.draw(frame, detections)
            plate_rdr.draw(frame, detections)

            # Stable plate count overlay
            cv2.putText(frame, f"Plates: {len(stable_plates)}",
                        (FRAME_WIDTH - 180, FRAME_HEIGHT - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)

            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()
            cv2.putText(frame, f"FPS:{fps:.1f}",
                        (FRAME_WIDTH // 2 - 30, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Day 13 — Plate OCR (Q/R/P/S/T)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF

        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset(); frame_n = 0
            stable_plates.clear()
            fps_c = 0; fps_t = time.time()
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")
        elif key == ord('s'):
            p = os.path.join(SNAPSHOTS_DIR, f"day13_snap_{int(time.time())}.jpg")
            cv2.imwrite(p, frame) # type: ignore
            print(f"  Snapshot: {p}")
        elif key == ord('t'):
            show_trails = not show_trails
            print(f"  Trails: {'ON' if show_trails else 'OFF'}")

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 65)
    print("  DAY 13 SUMMARY")
    print("=" * 65)
    print(f"  Frames processed   : {frame_n:,}")
    print(f"  Stable plates read : {len(stable_plates)}")
    for tid, plate in list(stable_plates.items())[:10]:
        print(f"    ID={tid:3d}  →  {plate}")
    print()
    print("  ✓ PlateReader finds plate region in lower bike half")
    print("  ✓ EasyOCR reads text with confidence filtering")
    print("  ✓ Voting system picks most-seen plate after 10 reads")
    print("  Next → python day14_test.py  (Database logging)")
    print("=" * 65)

if __name__ == "__main__":
    main()
