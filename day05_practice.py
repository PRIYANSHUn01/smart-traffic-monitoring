# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 5 — day05_practice.py
#  Topics: process video FILES (not webcam), frame count, FPS, timestamps,
#          detection statistics tracker, save annotated video, loop restart
#  Run: python day05_practice.py
#  Run with video: python day05_practice.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import numpy as np
import time
import argparse
import os
import sys
from collections import defaultdict, Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  DAY 5 — Video File Processing + Statistics")
print("=" * 55)

parser = argparse.ArgumentParser()
parser.add_argument("--source", default="D:\\Traffic Monitoring System\\traffic_monitor\\data\\videos\\4K Road traffic video for object detection and tracking - free download now.mp4")
args = parser.parse_args()
source = int(args.source) if args.source.isdigit() else args.source

# ── Load model ────────────────────────────────────────────────────────────────
from ultralytics import YOLO
model = YOLO("yolov8n.pt")

# ── Open video ────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(source)
if not cap.isOpened():
    print(f"✗ Cannot open source: {source}")
    sys.exit(1)

# ── Read video properties (Day 5 key skill) ───────────────────────────────────
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps_src      = cap.get(cv2.CAP_PROP_FPS)
width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
duration     = total_frames / fps_src if fps_src > 0 else 0

print(f"\n  Source  : {source}")
print(f"  Size    : {width}×{height}")
print(f"  FPS     : {fps_src:.1f}")
print(f"  Frames  : {total_frames}")
print(f"  Duration: {duration:.1f}s")

def frame_to_timestamp(n, fps):
    """Convert frame number to MM:SS.ms string — used in violation logs (Day 25)"""
    s = n / fps if fps > 0 else 0
    return f"{int(s//60):02d}:{s%60:05.2f}"

# ── Statistics tracker ────────────────────────────────────────────────────────
cls_counts     = defaultdict(int)
cls_conf_sums  = defaultdict(float)
frame_det_cts  = []

def print_progress(n, total, start_t):
    if total <= 0: return
    pct  = n/total
    fps_p = n/(time.time()-start_t) if (time.time()-start_t)>0 else 0
    eta  = (total-n)/fps_p if fps_p>0 else 0
    bar  = "█" * int(pct*25) + "░" * (25-int(pct*25))
    print(f"\r[{bar}] {pct*100:5.1f}%  {n}/{total}  {fps_p:.1f}fps  ETA:{eta:.0f}s",
          end="", flush=True)

# ── Main processing loop ─────────────────────────────────────────────────────
frame_n   = 0
start_t   = time.time()
last_dets = []
print("\n\nProcessing... (Q to quit, P to pause, R to restart)")
paused = False

while True:
    if not paused:
        ret, frame = cap.read()
        if not ret:
            if total_frames > 0:
                print(f"\n\n  Video ended — looping back")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_n = 0; start_t = time.time()
                continue
            else:
                break
        frame_n += 1
        frame = cv2.resize(frame, (1280, 720))

        # ── Detection every 2nd frame ─────────────────────────────────────────
        if frame_n % 2 == 0:
            results   = model(frame, conf=0.45, classes=[1,3], verbose=False)
            last_dets = []
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                x1,y1,x2,y2 = map(int, box.xyxy[0].tolist())
                last_dets.append({'cls':model.names[cls_id],'cls_id':cls_id,
                                   'conf':conf,'box':[x1,y1,x2,y2]})
                cls_counts[model.names[cls_id]] += 1
                cls_conf_sums[model.names[cls_id]] += conf
            frame_det_cts.append(len(last_dets))

        # ── Draw detections ───────────────────────────────────────────────────
        for det in last_dets:
            x1,y1,x2,y2 = det['box']
            c = (255,165,0) if det['cls_id']==1 else (0,120,255)
            cv2.rectangle(frame,(x1,y1),(x2,y2),c,2)
            cv2.putText(frame,f"{det['cls']} {det['conf']:.2f}",
                        (x1,y1-5),cv2.FONT_HERSHEY_SIMPLEX,0.5,c,2)

        # ── Progress overlay ──────────────────────────────────────────────────
        ts  = frame_to_timestamp(frame_n, fps_src)
        pct = frame_n/total_frames*100 if total_frames>0 else 0
        cv2.putText(frame,f"[{ts}]  {pct:.0f}%  vehicles:{len(last_dets)}",
                    (10,30),cv2.FONT_HERSHEY_SIMPLEX,0.65,(0,255,255),2)

        if frame_n % 15 == 0:
            print_progress(frame_n, total_frames, start_t)

    cv2.imshow("Day 5 — Video Processing (Q/P/R)", frame) # type: ignore
    key = cv2.waitKey(0 if paused else 1) & 0xFF
    if   key == ord('q'): break
    elif key == ord('p'): paused = not paused
    elif key == ord('r'):
        cap.set(cv2.CAP_PROP_POS_FRAMES,0); frame_n=0; start_t=time.time()

cap.release(); cv2.destroyAllWindows()


# ── Print report ─────────────────────────────────────────────────────────────
elapsed = time.time() - start_t
print(f"\n\n{'='*55}")
print("  DETECTION REPORT")
print(f"{'='*55}")
print(f"  Frames processed : {frame_n:,}")
print(f"  Processing speed : {frame_n/elapsed:.1f} fps")
for cls, cnt in sorted(cls_counts.items(), key=lambda x:-x[1]):
    avg = cls_conf_sums[cls]/cnt if cnt>0 else 0
    print(f"  {cls:<15s}: {cnt:5,} detections  avg_conf={avg:.3f}")
if frame_det_cts:
    bf_idx = frame_det_cts.index(max(frame_det_cts))
    print(f"  Busiest frame   : #{bf_idx}  ({max(frame_det_cts)} vehicles)")
print(f"{'='*55}")
print("  DAY 5 COMPLETE")
print("  Next: python day06_practice.py")
print(f"{'='*55}")
