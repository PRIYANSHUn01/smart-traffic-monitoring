# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 8 — day08_test.py
#  Tests VehicleDetector class: detection, filtering, drawing, frame skipping
#  Run: python day08_test.py
#  Run with video: python day08_test.py --source data/videos/traffic.mp4
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
print("  DAY 8 — VehicleDetector Class Test")
print("=" * 55)
print("  Features tested:")
print("  ✓ Class architecture (Day 8)")
print("  ✓ Frame skipping     (Day 8)")
print("  ✓ Colour-coded boxes (Day 8)")
print("  ✓ Standard dict keys (Day 8)")
print("  NOTE: track_id=None is expected today (ByteTrack added Day 9)")

detector = VehicleDetector()
cap = cv2.VideoCapture(src)
assert cap.isOpened(), f"Cannot open {src}"

total   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_n = 0; paused = False
fps_t=time.time(); fps_c=0; fps=0.0

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset(); frame_n=0; continue
        frame_n+=1
        frame = cv2.resize(frame,(FRAME_WIDTH,FRAME_HEIGHT))

        result = detector.process_frame(frame, frame_n)
        detector.draw(frame, result)

        # Verify all required keys present
        for det in result['detections']:
            required = {'track_id','vehicle_type','cls_id','conf','box','cx','cy',
                        'counted','rider_count','rider_label','helmet_status','plate'}
            missing = required - set(det.keys())
            assert not missing, f"Missing keys: {missing}"

        fps_c+=1
        if time.time()-fps_t>=1.0: fps=fps_c/(time.time()-fps_t); fps_c=0; fps_t=time.time()
        cv2.putText(frame,f"FPS:{fps:.1f}  Day8:detection_only  track_id=None",
                    (10,FRAME_HEIGHT-15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(180,180,180),1)

    cv2.imshow("Day 8 Test — Detection (Q/R/P)", frame)  # type: ignore
    key=cv2.waitKey(0 if paused else 1)&0xFF
    if   key==ord('q'): break
    elif key==ord('r'): cap.set(cv2.CAP_PROP_POS_FRAMES,0); detector.reset(); frame_n=0
    elif key==ord('p'): paused=not paused

cap.release(); cv2.destroyAllWindows()
print("\n  Day 8 test complete ✓")
print("  Next: python day09_test.py  (add ByteTrack IDs)")
