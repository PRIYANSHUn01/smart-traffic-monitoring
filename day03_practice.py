# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 3 — day03_practice.py  (FIXED)
#  Fix: yolo_to_pixel now uses round() instead of int()
#  Why: pixel_to_yolo stores h=0.416667 (rounded 6dp)
#       So (cy - h/2)*480 = 79.9999... and int() gives 79 (WRONG)
#       round() gives 80 (CORRECT)
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import numpy as np

print("=" * 55)
print("  DAY 3 — Detection Concepts: IoU, NMS, Confidence")
print("=" * 55)

# ═══════════════════════════════════════════════════════════════════════
# PART 1: Bounding box formats
# ═══════════════════════════════════════════════════════════════════════
print("\n[Part 1] Bounding box formats")

def pixel_to_yolo(x1, y1, x2, y2, img_w, img_h):
    """Convert pixel box to YOLO normalised format.
    Store full precision — do NOT round here.
    Rounding here causes tiny errors that int() amplifies in the reverse step."""
    cx = (x1 + x2) / 2 / img_w
    cy = (y1 + y2) / 2 / img_h
    w  = (x2 - x1) / img_w
    h  = (y2 - y1) / img_h
    return cx, cy, w, h

def yolo_to_pixel(cx, cy, w, h, img_w, img_h):
    """Convert YOLO normalised box to pixel coordinates.

    *** KEY FIX: use round(), NOT int() ***

    Why int() breaks:
      h exact  = 0.41666666...
      h stored = 0.416667  (Roboflow rounds to 6dp in .txt files)
      (cy - h/2) * 480 = 79.99992   <- slightly below 80
      int(79.99992) = 79             <- WRONG (truncates toward zero)
      round(79.99992) = 80           <- CORRECT (nearest integer)
    """
    x1 = round((cx - w / 2) * img_w)   # round(), NOT int()
    y1 = round((cy - h / 2) * img_h)   # round(), NOT int()
    x2 = round((cx + w / 2) * img_w)   # round(), NOT int()
    y2 = round((cy + h / 2) * img_h)   # round(), NOT int()
    return x1, y1, x2, y2

def box_center(box):
    x1, y1, x2, y2 = box
    return (x1 + x2) // 2, (y1 + y2) // 2

IMG_W, IMG_H = 640, 480

# Test round-trip
original = (150, 80, 350, 280)
yolo     = pixel_to_yolo(*original, IMG_W, IMG_H)
back     = yolo_to_pixel(*yolo, IMG_W, IMG_H)

print(f"  Original pixel : {original}")
print(f"  YOLO format    : ({yolo[0]:.6f}, {yolo[1]:.6f}, {yolo[2]:.6f}, {yolo[3]:.6f})")
print(f"  Back to pixel  : {back}")

# Show why the bug happens
h_exact  = (280 - 80) / IMG_H
h_6dp    = round(h_exact, 6)
y1_raw   = (yolo[1] - h_6dp / 2) * IMG_H
print(f"\n  [Why int() fails — the floating point story]")
print(f"  h exact       = {h_exact}")
print(f"  h stored(6dp) = {h_6dp}")
print(f"  y1 raw        = {y1_raw:.8f}  <- just below 80")
print(f"  int(y1 raw)   = {int(y1_raw)}     <- WRONG (truncation)")
print(f"  round(y1 raw) = {round(y1_raw)}    <- CORRECT")

assert back == original, f"Round-trip failed: got {back}, expected {original}"
print("\n  ✓ Round-trip correct with round()")

# ═══════════════════════════════════════════════════════════════════════
# PART 2: IoU
# ═══════════════════════════════════════════════════════════════════════
print("\n[Part 2] IoU — measures bounding box overlap (0.0 to 1.0)")

def compute_iou(box_a, box_b):
    """Intersection over Union of two [x1,y1,x2,y2] boxes."""
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    ix1 = max(ax1, bx1);  iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2);  iy2 = min(ay2, by2)
    inter  = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union  = area_a + area_b - inter
    return inter / union if union > 0 else 0.0

b = [100, 100, 300, 300]
print(f"  Identical boxes  : {compute_iou(b, b):.3f}   (expect 1.000)")
print(f"  No overlap       : {compute_iou([0,0,100,100],[200,200,300,300]):.3f}   (expect 0.000)")
print(f"  Half overlap     : {compute_iou([0,0,200,200],[100,0,300,200]):.3f}   (expect 0.333)")
print(f"  Rider on bike    : {compute_iou([100,80,280,260],[120,90,270,250]):.3f}   (Day 14 rider_counter.py)")

assert abs(compute_iou(b, b) - 1.0) < 1e-9
assert compute_iou([0,0,100,100],[200,200,300,300]) == 0.0
assert abs(compute_iou([0,0,200,200],[100,0,300,200]) - 1/3) < 1e-6
print("  ✓ All IoU values correct")

# Visualise
canvas = np.ones((400, 640, 3), dtype=np.uint8) * 235
ba=(80,80,280,280); bb=(180,180,380,380)
ix1=max(ba[0],bb[0]); iy1=max(ba[1],bb[1])
ix2=min(ba[2],bb[2]); iy2=min(ba[3],bb[3])
ov=canvas.copy()
cv2.rectangle(ov,(ix1,iy1),(ix2,iy2),(100,200,100),-1)
cv2.addWeighted(ov,0.35,canvas,0.65,0,canvas)
cv2.rectangle(canvas,ba[:2],ba[2:],(0,100,200),2)
cv2.rectangle(canvas,bb[:2],bb[2:],(200,0,0),2)
iou_val=compute_iou(ba,bb)
cv2.putText(canvas,f"IoU = {iou_val:.3f}  (green = intersection)",
            (90,390),cv2.FONT_HERSHEY_SIMPLEX,0.8,(30,30,30),2)
cv2.imshow("Day 3 Part 2 — IoU (press any key)",canvas)
cv2.waitKey(2500); cv2.destroyAllWindows()

# ═══════════════════════════════════════════════════════════════════════
# PART 3: NMS
# ═══════════════════════════════════════════════════════════════════════
print("\n[Part 3] NMS — collapse duplicate detections of the same vehicle")

def non_max_suppression(boxes, scores, iou_threshold=0.45):
    if not boxes: return []
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    keep  = []
    while order:
        best = order[0]; keep.append(best)
        order = [i for i in order[1:]
                 if compute_iou(boxes[best], boxes[i]) < iou_threshold]
    return keep

boxes  = [[100,80,280,240],[108,85,288,248],[95,75,275,235],
          [420,90,580,230],[415,85,575,225]]
scores = [0.92, 0.85, 0.71, 0.88, 0.64]
kept   = non_max_suppression(boxes, scores)

print(f"  Before NMS : {len(boxes)} detections")
print(f"  After  NMS : {len(kept)} detections  (indices {kept})")
assert len(kept) == 2
print("  ✓ NMS collapsed 5 duplicates → 2 unique vehicles")

before=np.ones((300,640,3),dtype=np.uint8)*230
after =np.ones((300,640,3),dtype=np.uint8)*230
colors=[(0,0,200),(0,80,180),(0,120,150),(200,80,0),(0,150,200)]
for i,(bx,sc) in enumerate(zip(boxes,scores)):
    cv2.rectangle(before,bx[:2],bx[2:],colors[i],2)
    cv2.putText(before,f"{sc:.2f}",(bx[0]+3,bx[1]+18),cv2.FONT_HERSHEY_SIMPLEX,0.5,colors[i],1)
for i in kept:
    cv2.rectangle(after,boxes[i][:2],boxes[i][2:],(0,160,0),3)
    cv2.putText(after,f"KEPT {scores[i]:.2f}",(boxes[i][0]+3,boxes[i][1]+18),
                cv2.FONT_HERSHEY_SIMPLEX,0.52,(0,120,0),2)
cv2.putText(before,"Before NMS — 5 boxes",(10,285),cv2.FONT_HERSHEY_SIMPLEX,0.6,(50,50,50),1)
cv2.putText(after, "After  NMS — 2 boxes",(10,285),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,120,0),1)
cv2.imshow("Day 3 Part 3 — NMS (press any key)",np.hstack([before,after]))
cv2.waitKey(2500); cv2.destroyAllWindows()

# ═══════════════════════════════════════════════════════════════════════
# PART 4: Confidence filter
# ═══════════════════════════════════════════════════════════════════════
print("\n[Part 4] Confidence threshold — remove weak detections")

def filter_by_conf(detections, threshold=0.45):
    return [d for d in detections if d['conf'] >= threshold]

test_dets = [
    {'cls':'motorcycle','conf':0.92,'box':[100,80,280,240]},
    {'cls':'bicycle',   'conf':0.31,'box':[300,90,450,220]},
    {'cls':'motorcycle','conf':0.78,'box':[480,60,600,200]},
    {'cls':'motorcycle','conf':0.18,'box':[200,10,300,80]},
]
kept_dets = filter_by_conf(test_dets, 0.45)
print(f"  Before: {len(test_dets)}  After: {len(kept_dets)}  (conf >= 0.45)")
for d in kept_dets:
    print(f"    {d['cls']:12s}  conf={d['conf']:.2f}  ✓")
assert len(kept_dets) == 2
print("  ✓ Confidence filter correct — CONFIDENCE_THRESHOLD=0.45 in config.py")

# ═══════════════════════════════════════════════════════════════════════
# PART 5: COCO class IDs
# ═══════════════════════════════════════════════════════════════════════
print("\n[Part 5] COCO class IDs — memorise these three")
print("""
  0  = person       ← rider_counter.py (Day 14)
  1  = bicycle      ← TWO_WHEELER_IDS = {1, 3}  in config.py
  3  = motorcycle   ← TWO_WHEELER_IDS = {1, 3}  in config.py
                       (scooters are classified here by COCO — acceptable)

  vehicle_detector.py passes:  classes=[1, 3]
  This drops persons(0), cars(2), buses(5), trucks(7) automatically.
""")


print("=" * 55)
print("  DAY 3 COMPLETE — all assertions passed")
print("  THE FIX: yolo_to_pixel uses round() not int()")
print("  ✓ compute_iou      → utils/helpers.py")
print("  ✓ NMS              → done inside YOLOv8 automatically")
print("  ✓ confidence filter→ via conf=0.45 in model.track()")
print("  ✓ COCO IDs 0,1,3   → config.py TWO_WHEELER_IDS={1,3}")
print("  Next: python day04_practice.py")
print("=" * 55)
