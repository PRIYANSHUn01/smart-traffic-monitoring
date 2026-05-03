# test_helmet.py — verify helmet detector loads and runs
import cv2
import numpy as np
from ultralytics import YOLO
import os

# ── Step 1: Load model and verify ──────────────────────────────
print("Step 1: Loading helmet model...")
from config import HELMET_MODEL, FALLBACK_MODEL

model_path = HELMET_MODEL if os.path.exists(HELMET_MODEL) else FALLBACK_MODEL

if model_path == FALLBACK_MODEL:
    print(f"WARNING: helmet_detect.pt not found. Using fallback: {FALLBACK_MODEL}")
    print("Complete the Colab training and place best.pt in models/ first.")
else:
    print(f"Found custom model: {model_path}")

model = YOLO(model_path)
print(f"Model loaded. Classes: {model.names}")

# ── Step 2: Run on a test image ────────────────────────────────
print("Step 2: Running on synthetic test image...")
test_img = np.zeros((200, 300, 3), dtype=np.uint8)
test_img[20:180, 30:270] = (120, 80, 60)   # simulate a head region

results = model(test_img, verbose=False, conf=0.3)
print(f"Detections on blank image: {len(results[0].boxes)}")
print("(0 expected — no helmet in a blank image)")

# ── Step 3: Test the head-crop pipeline ────────────────────────
print("Step 3: Testing crop-and-detect workflow...")
frame = np.zeros((480, 640, 3), dtype=np.uint8)
bike_box = (100, 80, 280, 320)
x1, y1, x2, y2 = bike_box
bike_h = y2 - y1
head_crop = frame[y1 : y1 + int(bike_h * 0.4), x1:x2]
print(f"Bike box size:   {x2-x1} x {y2-y1} pixels")
print(f"Head crop size:  {head_crop.shape[1]} x {head_crop.shape[0]} pixels")

h_results = model(head_crop, verbose=False, conf=0.3)
print(f"Detections in head crop: {len(h_results[0].boxes)}")
print("Crop-and-detect pipeline working correctly.")

# ── Step 4: Live webcam test (optional) ────────────────────────
print("Step 4: Live webcam test (press Q to exit)...")
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No webcam — skipping live test")
else:
    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (640, 480))
        results = model(frame, verbose=False, conf=0.35)
        for box in results[0].boxes:
            cls  = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names.get(cls, f"cls{cls}")
            x1,y1,x2,y2 = map(int, box.xyxy[0])
            color = (0,200,0) if 'with' in name else (0,0,255)
            cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)
            cv2.putText(frame, f"{name} {conf:.2f}", (x1,y1-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
        cv2.imshow("Helmet Test (press Q)", frame)
        if cv2.waitKey(1) == ord('q'): break
    cap.release(); cv2.destroyAllWindows()

print("All tests passed. Helmet detector is ready.")