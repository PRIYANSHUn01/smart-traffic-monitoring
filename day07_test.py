# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 7 — day07_test.py
#  Topics: test your trained helmet model locally after downloading from Colab
#  Run: python day07_test.py
#  Requires: models/helmet_detect.pt  (download from Colab after training)
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import os
import sys
import time
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import HELMET_MODEL, FALLBACK_MODEL

print("=" * 55)
print("  DAY 7 — Test Your Trained Helmet Model")
print("=" * 55)

# ── Check if custom model exists ──────────────────────────────────────────────
if os.path.exists(HELMET_MODEL):
    model_path = HELMET_MODEL
    print(f"\n  ✓ Custom helmet model found: {HELMET_MODEL}")
else:
    model_path = FALLBACK_MODEL
    print(f"\n  ⚠  Custom model not found at {HELMET_MODEL}")
    print(f"  Using pretrained {FALLBACK_MODEL} (helmet detection will be poor)")
    print(f"\n  To get a custom model:")
    print(f"  1. Train on Google Colab (see day07_train_colab_cells.txt)")
    print(f"  2. Download best.pt from Colab")
    print(f"  3. Move it to: {HELMET_MODEL}")

from ultralytics import YOLO
model = YOLO(model_path)
print(f"\n  Model classes: {model.names}")

# ── Colors ────────────────────────────────────────────────────────────────────
# Map class names to colors — green=helmet, red=no helmet
def get_color(cls_name):
    cn = cls_name.lower()
    if 'without' in cn or 'no' in cn or cn == '1':
        return (0, 0, 255), "NO HELMET ✗"   # red
    return (0, 200, 0), "HELMET OK ✓"        # green

# ── Open source ───────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--source", default="D:\\Traffic Monitoring System\\traffic_monitor\\data\\videos\\traffic.mp4")
args  = parser.parse_args()
src   = int(args.source) if args.source.isdigit() else args.source

cap = cv2.VideoCapture(src)
if not cap.isOpened():
    print(f"  ✗ Cannot open source: {src}")
    sys.exit(1)

print(f"\n  Running on: {src}")
print(f"  Press Q to quit | S to save snapshot")

start = time.time(); fps_t = start; fps_c = 0; fps = 0.0
snap_dir = "data/snapshots"; os.makedirs(snap_dir, exist_ok=True)

while True:
    fps_c += 1
    if time.time()-fps_t >= 1.0:
        fps=fps_c/(time.time()-fps_t); fps_c=0; fps_t=time.time()

    ret, frame = cap.read()
    if not ret:
        if src != 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
        break
    frame = cv2.resize(frame, (1280, 720))

    # Run helmet model
    results = model(frame, conf=0.40, verbose=False)[0]

    n_helmet = 0; n_nohelmet = 0
    for box in results.boxes:
        cls_id = int(box.cls[0])
        conf   = float(box.conf[0])
        cls_nm = model.names[cls_id]
        x1,y1,x2,y2 = map(int, box.xyxy[0].tolist())
        color, label = get_color(cls_nm)

        # Thick border for violations
        thick = 3 if 'no' in label.lower() or 'without' in cls_nm.lower() else 2
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,thick)
        if 'no' in label.lower() or 'without' in cls_nm.lower():
            cv2.rectangle(frame,(x1-2,y1-2),(x2+2,y2+2),(0,0,255),1)
            n_nohelmet += 1
        else:
            n_helmet += 1

        (tw,th),_ = cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.5,2)
        cv2.rectangle(frame,(x1,y1-th-8),(x1+tw+4,y1),color,-1)
        cv2.putText(frame,label,(x1+2,y1-4),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,255),2)

    # Stats overlay
    overlay = frame.copy()
    cv2.rectangle(overlay,(8,8),(250,100),(15,15,15),-1)
    cv2.addWeighted(overlay,0.65,frame,0.35,0,frame)
    for i,line in enumerate([
        f"FPS: {fps:.1f}",
        f"Helmet OK : {n_helmet}",
        f"NO HELMET : {n_nohelmet}",
    ]):
        cv2.putText(frame,line,(16,32+i*24),cv2.FONT_HERSHEY_SIMPLEX,0.6,(220,220,220),1)

    cv2.imshow("Day 7 — Helmet Detection (Q=quit S=snap)", frame)
    key = cv2.waitKey(1) & 0xFF
    if   key == ord('q'): break
    elif key == ord('s'):
        p = os.path.join(snap_dir,f"helmet_{int(time.time())}.jpg")
        cv2.imwrite(p, frame); print(f"  Saved: {p}")

cap.release(); cv2.destroyAllWindows()
print("\n  Day 7 test complete.")


# ═══════════════════════════════════════════════════════════════════════════════
# COLAB TRAINING CELLS — copy these into Google Colab to train your model
# (saved here for reference — not executed in this script)
# ═══════════════════════════════════════════════════════════════════════════════
COLAB_CELLS = """
# ── CELL 1: Verify GPU ───────────────────────────────────────────────────────
import torch
print("CUDA:", torch.cuda.is_available())
print("GPU: ", torch.cuda.get_device_name(0))

# ── CELL 2: Mount Google Drive ───────────────────────────────────────────────
from google.colab import drive
drive.mount('/content/drive')

# ── CELL 3: Install ultralytics ──────────────────────────────────────────────
!pip install ultralytics -q
from ultralytics import YOLO

# ── CELL 4: SET THESE (only change per model) ────────────────────────────────
DRIVE_ZIP  = '/content/drive/MyDrive/traffic_project/datasets/helmet_dataset.zip'
EXTRACT_TO = '/content/helmet_data'
NAME       = 'helmet_v1'
SAVE_PT    = '/content/drive/MyDrive/traffic_project/models/helmet_detect.pt'

# ── CELL 5: Copy and extract dataset ─────────────────────────────────────────
!cp "{DRIVE_ZIP}" /content/dataset.zip
!unzip -q /content/dataset.zip -d {EXTRACT_TO}
!ls {EXTRACT_TO}

# ── CELL 6: Fix data.yaml path ───────────────────────────────────────────────
import yaml
with open(f'{EXTRACT_TO}/data.yaml') as f: cfg = yaml.safe_load(f)
cfg['path'] = EXTRACT_TO
with open(f'{EXTRACT_TO}/data.yaml','w') as f: yaml.dump(cfg,f)
print(f"nc={cfg['nc']}  names={cfg['names']}")

# ── CELL 7: TRAIN ─────────────────────────────────────────────────────────────
model = YOLO('yolov8s.pt')
model.train(data=f'{EXTRACT_TO}/data.yaml', epochs=100, imgsz=640,
            batch=16, patience=20, device=0, save=True,
            save_period=10, project='/content/runs',
            name=NAME, exist_ok=True, plots=True)

# ── CELL 8: SAVE TO DRIVE (run immediately!) ──────────────────────────────────
import shutil
shutil.copy(f'/content/runs/{NAME}/weights/best.pt', SAVE_PT)
print(f"Saved: {SAVE_PT}")

# ── CELL 9: CHECK METRICS ─────────────────────────────────────────────────────
best = YOLO(f'/content/runs/{NAME}/weights/best.pt')
m = best.val(data=f'{EXTRACT_TO}/data.yaml', verbose=False)
print(f"mAP50={m.box.map50:.4f}  P={m.box.mp:.4f}  R={m.box.mr:.4f}")

# ── CELL 10: DOWNLOAD ────────────────────────────────────────────────────────
from google.colab import files
files.download(f'/content/runs/{NAME}/weights/best.pt')
"""
