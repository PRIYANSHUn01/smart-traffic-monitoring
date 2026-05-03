# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 6 — day06_inspect.py
#  Topics: YOLO annotation format, dataset quality checks, visual inspection
#  Run: python day06_inspect.py
#  NOTE: This script checks datasets at data/datasets/ — download first from
#        roboflow.com (see README.md for instructions)
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import os
import sys
import glob
import yaml
import random
import numpy as np
from collections import Counter

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=" * 55)
print("  DAY 6 — Dataset Inspection & Quality Checks")
print("=" * 55)

# ══════════════════════════════════════════════════════════════════════════════
# PART 1: YOLO annotation format demo
# ══════════════════════════════════════════════════════════════════════════════
print("\n[Part 1] YOLO annotation format")

def pixel_to_yolo(x1, y1, x2, y2, img_w, img_h):
    cx = (x1+x2)/2/img_w;  cy = (y1+y2)/2/img_h
    w  = (x2-x1)/img_w;    h  = (y2-y1)/img_h
    return round(cx,6), round(cy,6), round(w,6), round(h,6)

def yolo_to_pixel(cx, cy, w, h, img_w, img_h):
    x1=int((cx-w/2)*img_w); y1=int((cy-h/2)*img_h)
    x2=int((cx+w/2)*img_w); y2=int((cy+h/2)*img_h)
    return x1,y1,x2,y2

# Demonstrate
IMG_W, IMG_H = 640, 480
box_px = (100, 80, 260, 200)
yolo   = pixel_to_yolo(*box_px, IMG_W, IMG_H)
back   = yolo_to_pixel(*yolo, IMG_W, IMG_H)
print(f"  Pixel box   : {box_px}")
print(f"  YOLO format : {yolo}  ← what .txt label files contain")
print(f"  Back to px  : {back}")
print("  Format: class_id  cx  cy  width  height  (all normalised 0-1)")
print("  ✓ Conversion functions work")

# ══════════════════════════════════════════════════════════════════════════════
# PART 2: Quality check functions
# ══════════════════════════════════════════════════════════════════════════════
print("\n[Part 2] Dataset quality check functions")

def check_counts(dataset_path):
    print(f"\n  Checking: {dataset_path}")
    for split in ['train','valid']:
        img_dir = os.path.join(dataset_path, split, 'images')
        lbl_dir = os.path.join(dataset_path, split, 'labels')
        if not os.path.exists(img_dir):
            print(f"  {split:6s}: folder not found — skip")
            continue
        imgs = glob.glob(f"{img_dir}/*.jpg") + glob.glob(f"{img_dir}/*.png")
        lbls = glob.glob(f"{lbl_dir}/*.txt")
        ok   = "✓" if len(imgs)==len(lbls) else "✗ MISMATCH"
        print(f"  {split:6s}: {len(imgs):5d} images  {len(lbls):5d} labels  {ok}")

def check_balance(labels_dir, class_names):
    counts = Counter()
    for fp in glob.glob(f"{labels_dir}/*.txt"):
        with open(fp) as f:
            for ln in f:
                if ln.strip(): counts[int(ln.split()[0])] += 1
    total = sum(counts.values())
    if total == 0:
        print("  No labels found")
        return
    print(f"  Class balance:")
    for cid, name in enumerate(class_names):
        n   = counts.get(cid, 0)
        pct = n/total*100 if total>0 else 0
        bar = "█" * int(pct/3)
        print(f"    cls {cid} ({name:<18s}): {n:6d}  {pct:5.1f}%  {bar}")
    vals = [v for v in counts.values() if v > 0]
    ratio = max(vals)/min(vals) if len(vals)>=2 else 1
    status = "✓ OK" if ratio < 5 else f"⚠  {ratio:.1f}x imbalance"
    print(f"  Balance ratio: {status}")

def check_images(img_dir, max_check=100):
    imgs = (glob.glob(f"{img_dir}/*.jpg") + glob.glob(f"{img_dir}/*.png"))[:max_check]
    bad  = [p for p in imgs if cv2.imread(p) is None]
    if bad:
        print(f"  ✗ {len(bad)} corrupt images found")
    else:
        print(f"  ✓ All {len(imgs)} sampled images readable")

def check_label_values(labels_dir):
    bad = []
    for fp in glob.glob(f"{labels_dir}/*.txt"):
        with open(fp) as f:
            for i, ln in enumerate(f):
                parts = ln.strip().split()
                if not parts: continue
                try:
                    vals = [float(x) for x in parts[1:]]
                    if any(v < 0 or v > 1 for v in vals):
                        bad.append(f"{fp}:{i+1}")
                except ValueError:
                    bad.append(f"{fp}:{i+1} (parse error)")
    if bad: print(f"  ✗ {len(bad)} invalid label lines")
    else:   print(f"  ✓ All label coordinates valid (0.0–1.0)")

# ══════════════════════════════════════════════════════════════════════════════
# PART 3: Visual inspector
# ══════════════════════════════════════════════════════════════════════════════
def visualise_dataset(dataset_path, class_names, split='train', n=20):
    """Show annotated images — press any key to advance, Q to quit."""
    img_dir  = os.path.join(dataset_path, split, 'images')
    lbl_dir  = os.path.join(dataset_path, split, 'labels')
    imgs     = glob.glob(f"{img_dir}/*.jpg") + glob.glob(f"{img_dir}/*.png")
    if not imgs:
        print(f"  No images found at {img_dir}")
        return
    sample = random.sample(imgs, min(n, len(imgs)))
    COLORS = [(0,200,0),(0,0,255),(255,165,0),(200,0,200),(0,165,255)]
    shown  = 0
    for img_path in sample:
        img = cv2.imread(img_path)
        if img is None: continue
        h, w = img.shape[:2]
        lbl_path = os.path.join(lbl_dir,
                    os.path.splitext(os.path.basename(img_path))[0]+'.txt')
        count = 0
        if os.path.exists(lbl_path):
            with open(lbl_path) as f:
                for ln in f:
                    parts = ln.strip().split()
                    if not parts: continue
                    cid = int(parts[0])
                    cx,cy,bw,bh = (float(x) for x in parts[1:])
                    x1=int((cx-bw/2)*w); y1=int((cy-bh/2)*h)
                    x2=int((cx+bw/2)*w); y2=int((cy+bh/2)*h)
                    c = COLORS[cid % len(COLORS)]
                    cv2.rectangle(img,(x1,y1),(x2,y2),c,2)
                    nm = class_names[cid] if cid<len(class_names) else f"cls{cid}"
                    cv2.putText(img,nm,(x1,y1-5),cv2.FONT_HERSHEY_SIMPLEX,0.5,c,2)
                    count += 1
        cv2.putText(img,f"{os.path.basename(img_path)}  {count} annotations",
                    (6,22),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,0),2)
        cv2.imshow("Day 6 — Dataset Inspector (any key=next, Q=quit)", img)
        shown += 1
        if cv2.waitKey(0) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    print(f"  ✓ Inspected {shown} images")

# ══════════════════════════════════════════════════════════════════════════════
# PART 4: Run checks on downloaded datasets
# ══════════════════════════════════════════════════════════════════════════════
DATASETS = {
    'helmet':   {'path':'data/datasets/helmet',   'classes':['with_helmet','without_helmet']},
    'plates':   {'path':'data/datasets/plates',   'classes':['license_plate']},
    'vehicles': {'path':'data/datasets/vehicles', 'classes':['motorcycle','bicycle']},
}

print("\n[Part 3] Running quality checks on downloaded datasets...")
any_found = False
for name, cfg in DATASETS.items():
    path = cfg['path']
    if not os.path.exists(path):
        print(f"\n  '{name}' dataset not found at {path}")
        print(f"  → Download from roboflow.com and extract to {path}")
        continue
    any_found = True
    print(f"\n  ── {name.upper()} ──────────────────────────────")
    check_counts(path)
    train_lbl = os.path.join(path,'train','labels')
    train_img = os.path.join(path,'train','images')
    if os.path.exists(train_lbl):
        check_balance(train_lbl, cfg['classes'])
        check_label_values(train_lbl)
    if os.path.exists(train_img):
        check_images(train_img)
    # Visual inspection (optional — shows 10 images)
    if os.path.exists(os.path.join(path,'train','images')):
        print(f"  Running visual inspection (10 images)...")
        visualise_dataset(path, cfg['classes'], n=10)

if not any_found:
    print("\n  No datasets found yet.")
    print("  Download from roboflow.com and put them in data/datasets/")
    print("  See README.md → Dataset Setup for step-by-step instructions")

print("\n" + "=" * 55)
print("  DAY 6 COMPLETE")
print("  ✓ YOLO format: class cx cy w h (normalised)")
print("  ✓ Quality checks: counts, balance, corrupt files, coords")
print("  ✓ Visual inspector: see annotations on actual images")
print("  Next: Train on Google Colab — see day07_train_colab.py")
print("=" * 55)
