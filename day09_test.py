# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 9 — day09_test.py
#  Tests ByteTrack stable IDs, trail history, track_types dictionary
#  Run: python day09_test.py
#  Run with video: python day09_test.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.vehicle_detector import VehicleDetector
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT

parser = argparse.ArgumentParser()
parser.add_argument("--source", default=str(VIDEO_SOURCE))
args = parser.parse_args()
src  = int(args.source) if str(args.source).isdigit() else args.source

print("=" * 55)
print("  DAY 9 — ByteTrack Tracking Test")
print("=" * 55)
print("  Features tested:")
print("  ✓ model.track(persist=True)   (Day 9)")
print("  ✓ Stable track IDs across frames (Day 9)")
print("  ✓ track_types dictionary       (Day 9)")
print("  ✓ Trail history + draw_trails  (Day 9)")
print("  ✓ ID circle badge on each box  (Day 9)")

detector   = VehicleDetector()
cap        = cv2.VideoCapture(src)
assert cap.isOpened(), f"Cannot open {src}"

frame_n    = 0; paused = False; show_trails=True
fps_t=time.time(); fps_c=0; fps=0.0
all_ids    = set()
id_changes = 0; prev_ids=set()

print("\n  Frame  | IDs in frame | Total IDs seen")
print("  " + "-"*40)

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset()
            frame_n=0; all_ids.clear(); prev_ids.clear(); continue
        frame_n+=1
        frame=cv2.resize(frame,(FRAME_WIDTH,FRAME_HEIGHT))

        result   = detector.process_frame(frame,frame_n)
        dets     = result['detections']
        curr_ids = {d['track_id'] for d in dets if d['track_id'] is not None}
        all_ids |= curr_ids

        # Print terminal update every 10 frames
        if frame_n % 10 == 0:
            print(f"  {frame_n:5d}  | IDs:{sorted(curr_ids)}  | Total seen:{len(all_ids)}")

        # Check for None IDs (only allowed on first 3 frames)
        none_dets = [d for d in dets if d['track_id'] is None]
        if none_dets and frame_n > 5:
            print(f"  ⚠ Frame {frame_n}: {len(none_dets)} unmatched detections")

        prev_ids = curr_ids

        if show_trails: detector.draw_trails(frame)
        detector.draw(frame,result)

        fps_c+=1
        if time.time()-fps_t>=1.0: fps=fps_c/(time.time()-fps_t); fps_c=0; fps_t=time.time()

        # Extra info overlay
        overlay=frame.copy()
        cv2.rectangle(overlay,(8,FRAME_HEIGHT-80),(380,FRAME_HEIGHT-8),(15,15,15),-1)
        cv2.addWeighted(overlay,0.65,frame,0.35,0,frame)
        cv2.putText(frame,f"FPS:{fps:.1f}  Active IDs:{sorted(curr_ids)}",
                    (14,FRAME_HEIGHT-56),cv2.FONT_HERSHEY_SIMPLEX,0.52,(220,220,220),1)
        cv2.putText(frame,f"Total IDs seen: {len(all_ids)}  track_types: {len(detector.track_types)}",
                    (14,FRAME_HEIGHT-30),cv2.FONT_HERSHEY_SIMPLEX,0.52,(220,220,220),1)

    cv2.imshow("Day 9 Test — ByteTrack (Q/R/P/T)", frame) # type: ignore
    key=cv2.waitKey(0 if paused else 1)&0xFF
    if   key==ord('q'): break
    elif key==ord('r'): cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset(); frame_n=0; all_ids.clear()
    elif key==ord('p'): paused=not paused
    elif key==ord('t'): show_trails=not show_trails; print(f"  Trails: {'ON' if show_trails else 'OFF'}")

cap.release(); cv2.destroyAllWindows()
print(f"\n  Total unique vehicles tracked: {len(all_ids)}")
print(f"  track_types: {detector.track_types}")
print("\n  Day 9 test complete ✓")
print("  Next: python day10_test.py  (add counting line)")
