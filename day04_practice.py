# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 4 — day04_practice.py
#  Topics: install ultralytics, load YOLOv8, run on image and video,
#          read output (xyxy, conf, cls), filter two-wheelers
#  Run: python day04_practice.py
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import numpy as np
import time

print("=" * 55)
print("  DAY 4 — YOLOv8 First Run")
print("=" * 55)

# ── Load model ────────────────────────────────────────────────────────────────
print("\nLoading yolov8n.pt (downloads ~6MB on first run)...")
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print(f"  ✓ Model loaded — knows {len(model.names)} COCO classes")
print(f"  Relevant classes: person={0}, bicycle={1}, motorcycle={3}")

# ── PART 1: Detection on blank image ─────────────────────────────────────────
print("\n[Part 1] Detection on blank image (should find 0 objects)...")
dummy   = np.zeros((480, 640, 3), dtype=np.uint8)
results = model(dummy, verbose=False)
print(f"  Detections on blank: {len(results[0].boxes)}  (expected 0)")

# ── PART 2: Understand the output object ─────────────────────────────────────
print("\n[Part 2] YOLOv8 output structure")
print("""
  results            → list, one element per image
  results[0]         → Result object for the first image
  results[0].boxes   → all detected boxes
  
  For each box:
    box.xyxy[0]      → tensor [x1, y1, x2, y2] in pixels
    box.conf[0]      → confidence float 0.0–1.0
    box.cls[0]       → class ID integer
    box.id[0]        → track ID (None when using model(), filled when model.track())
  
  ALWAYS use int() or float() — these are PyTorch tensors, not plain numbers
  box.xyxy[0].tolist()  → converts tensor to Python list
""")

# ── PART 3: Live detection on webcam / video ──────────────────────────────────
print("[Part 3] Live detection — press Q to quit (auto 10s)...")

TWO_WHEELERS = [1, 3]   # bicycle=1, motorcycle=3
COLORS = {
    0: (0, 200, 0),    # person    → green
    1: (255, 165, 0),  # bicycle   → orange
    3: (0, 120, 255),  # motorcycle→ blue
}

cap     = cv2.VideoCapture(0)
use_cam = cap.isOpened()
if not use_cam:
    print("  ℹ  No webcam — using synthetic scene")

start = time.time(); fps_t = time.time(); fps_c = 0; fps = 0.0

while True:
    fps_c += 1
    if time.time() - fps_t >= 1.0:
        fps = fps_c / (time.time() - fps_t); fps_c = 0; fps_t = time.time()

    if use_cam:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x = (int(time.time() * 40)) % 600
        cv2.rectangle(frame, (x, 180), (x+80, 300), (60,60,60), -1)

    # ── Run detection ─────────────────────────────────────────────────────────
    results = model(frame, conf=0.45, verbose=False)

    # ── Draw ALL detections ───────────────────────────────────────────────────
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        label  = model.names[cls_id]
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        color  = COLORS.get(cls_id, (180,180,180))

        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.putText(frame, f"FPS: {fps:.1f}  Objects: {len(results[0].boxes)}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    cv2.imshow("Day 4 Part 3 — YOLOv8 All Classes (Q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q') or time.time()-start > 10:
        break

# ── PART 4: Filter two-wheelers only ─────────────────────────────────────────
print("[Part 4] Filter: show ONLY motorcycles and bicycles...")
start = time.time()

while True:
    if use_cam:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x = (int(time.time() * 40)) % 600
        cv2.rectangle(frame, (x, 180), (x+80, 300), (60,60,60), -1)

    # classes=[1,3] filters OUT cars, buses, trucks — only bikes shown
    results = model(frame, conf=0.45, classes=TWO_WHEELERS, verbose=False)

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        color  = COLORS.get(cls_id, (180,180,180))
        label  = "bicycle" if cls_id == 1 else "motorcycle"
        cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    cv2.putText(frame, f"TWO-WHEELERS ONLY: {len(results[0].boxes)}",
                (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
    cv2.putText(frame, "classes=[1,3] in config.py → TWO_WHEELER_IDS",
                (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180,180,180), 1)
    cv2.imshow("Day 4 Part 4 — Two-Wheelers Only (Q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord('q') or time.time()-start > 8:
        break

cap.release(); cv2.destroyAllWindows()

print("\n" + "=" * 55)
print("  DAY 4 COMPLETE")
print("  ✓ YOLOv8 installed and running")
print("  ✓ Output format: xyxy, conf, cls — all extracted correctly")
print("  ✓ classes=[1,3] filters two-wheelers — same as VehicleDetector")
print("  Next: python day05_practice.py")
print("=" * 55)
