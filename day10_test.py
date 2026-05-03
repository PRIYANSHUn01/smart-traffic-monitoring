# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 10 — day10_test.py  (MAIN TEST — DAYS 1 TO 10 ALL WORKING TOGETHER)
#  Topics: counting line, counted_ids set, live counter, session summary
#
#  Run: python day10_test.py
#  Run with video: python day10_test.py --source data/videos/traffic.mp4
#
#  Keys:
#    Q = quit
#    R = reset all counters and restart
#    P = pause / resume
#    S = save snapshot
#    T = toggle trails
#    I = print current state to terminal
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.vehicle_detector import VehicleDetector
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT

def main():
    parser = argparse.ArgumentParser(description="Traffic Monitor Days 1-10 Complete")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  TRAFFIC MONITOR — DAYS 1 TO 10 COMPLETE")
    print("=" * 65)
    print(f"  Source: {src}")
    print()
    print("  What is active:")
    print("  Day 1-2  ✓ Video loop, NumPy frames, drawing")
    print("  Day 3    ✓ IoU, NMS, confidence (inside YOLOv8)")
    print("  Day 4    ✓ YOLOv8 detection (classes=[1,3])")
    print("  Day 5    ✓ Video file processing, stats, FPS")
    print("  Day 6    ✓ COCO class IDs, TWO_WHEELER_IDS in config.py")
    print("  Day 7    ✓ Custom model loading with fallback")
    print("  Day 8    ✓ VehicleDetector class, dict, frame skip")
    print("  Day 9    ✓ ByteTrack stable IDs, trails, badges")
    print("  Day 10   ✓ Counting line, counted_ids set, TOTAL counter")
    print()
    print("  Keys: Q=quit  R=reset  P=pause  S=snapshot  T=trails  I=info")
    print("=" * 65)

    detector    = VehicleDetector()
    cap         = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        print("  → For webcam: --source 0")
        print("  → For video:  --source data/videos/traffic.mp4")
        return

    total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_src = cap.get(cv2.CAP_PROP_FPS)
    sw      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    sh      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"\n  Video: {sw}×{sh}  @{fps_src:.0f}fps  ({total} frames)\n")

    frame_n    = 0; paused=False; show_trails=True
    fps_t=time.time(); fps_c=0; fps=0.0
    snap_dir   = "data/snapshots"; os.makedirs(snap_dir,exist_ok=True)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                if total > 0:
                    print(f"\n  Video ended — counted {len(detector.counted_ids)} vehicles — looping")
                    cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset(); frame_n=0; continue
                else:
                    print("\n  Webcam disconnected"); break
            frame_n+=1
            frame=cv2.resize(frame,(FRAME_WIDTH,FRAME_HEIGHT))

            # ── THE FULL PIPELINE ─────────────────────────────────────────────
            result = detector.process_frame(frame, frame_n)

            if show_trails:
                detector.draw_trails(frame)   # Day 9: fading trails

            detector.draw(frame, result)       # Day 8+9+10: boxes+line+counter

            # ── FPS ───────────────────────────────────────────────────────────
            fps_c+=1
            if time.time()-fps_t>=1.0: fps=fps_c/(time.time()-fps_t); fps_c=0; fps_t=time.time()
            cv2.putText(frame,f"FPS:{fps:.1f}",
                        (FRAME_WIDTH//2-30,26),cv2.FONT_HERSHEY_SIMPLEX,0.6,(200,200,200),1)

            # ── Terminal log for each crossing ────────────────────────────────
            for tid in result['newly_counted']:
                vtype = detector.track_types.get(tid,'vehicle')
                print(f"  COUNTED  ID={tid:3d}  {vtype:<12s}"
                      f"  total={result['total_counted']:4d}"
                      f"  frame={frame_n:6d}")

        cv2.imshow("Traffic Monitor Days 1-10 (Q/R/P/S/T/I)", frame) # type: ignore
        key=cv2.waitKey(0 if paused else 1)&0xFF

        if   key==ord('q'): break
        elif key==ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset()
            frame_n=0; fps_c=0; fps_t=time.time()
            print("\n  ── RESET ── counters cleared\n")
        elif key==ord('p'):
            paused=not paused
            print(f"  {'PAUSED' if paused else 'RESUMED'}")
        elif key==ord('s'):
            p=os.path.join(snap_dir,f"snap_{int(time.time())}_fr{frame_n}.jpg")
            cv2.imwrite(p,frame); print(f"  Snapshot: {p}") # type: ignore
        elif key==ord('t'):
            show_trails=not show_trails
            print(f"  Trails: {'ON' if show_trails else 'OFF'}")
        elif key==ord('i'):
            print(f"\n  ── STATE INFO ──")
            print(f"  frame_n        : {frame_n}")
            print(f"  counted_ids    : {sorted(detector.counted_ids)}")
            print(f"  total counted  : {len(detector.counted_ids)}")
            print(f"  track_types    : {detector.track_types}")
            print(f"  trail entries  : {len(detector.trail_history)}")
            print()

    cap.release(); cv2.destroyAllWindows()

    # ── SESSION SUMMARY ───────────────────────────────────────────────────────
    from collections import Counter
    print("\n" + "=" * 65)
    print("  SESSION SUMMARY — Days 1-10")
    print("=" * 65)
    print(f"  Frames processed     : {frame_n:,}")
    print(f"  Unique vehicles seen : {len(detector.track_types):,}")
    print(f"  Unique vehicles COUNTED (crossed line): {len(detector.counted_ids):,}")
    if detector.track_types:
        type_counts = Counter(detector.track_types.values())
        for vtype, cnt in sorted(type_counts.items()):
            counted_of_type = sum(1 for tid,vt in detector.track_types.items()
                                  if vt==vtype and tid in detector.counted_ids)
            print(f"    {vtype:<15s}: {cnt} tracked  {counted_of_type} counted")
    print("=" * 65)
    print("  PHASE 1 (Days 1-7) + PHASE 2 START (Days 8-10) COMPLETE")
    print("  Next step → Day 11: Helmet detection module")
    print("=" * 65)

if __name__ == "__main__":
    main()
