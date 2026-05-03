# utils/helpers.py  — Shared utility functions (Days 1-10 and beyond)

import cv2
import numpy as np
import os
import logging
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Logger ────────────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                            datefmt="%H:%M:%S")
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger


# ── Bounding box helpers (Day 3) ──────────────────────────────────────────────
def box_center(box):
    """Return (cx, cy) integer pixel centre of [x1,y1,x2,y2] box."""
    x1, y1, x2, y2 = box
    return int((x1+x2)/2), int((y1+y2)/2)

def box_area(box):
    x1, y1, x2, y2 = box
    return max(0, x2-x1) * max(0, y2-y1)

def compute_iou(box_a, box_b):
    """IoU of two [x1,y1,x2,y2] boxes. Returns float 0.0–1.0."""
    ax1,ay1,ax2,ay2 = box_a;  bx1,by1,bx2,by2 = box_b
    ix1=max(ax1,bx1); iy1=max(ay1,by1)
    ix2=min(ax2,bx2); iy2=min(ay2,by2)
    inter = max(0,ix2-ix1) * max(0,iy2-iy1)
    union = box_area(box_a) + box_area(box_b) - inter
    return inter/union if union > 0 else 0.0

def is_center_inside(small_box, big_box):
    """True if centre of small_box is inside big_box."""
    cx, cy = box_center(small_box)
    bx1,by1,bx2,by2 = big_box
    return bx1 < cx < bx2 and by1 < cy < by2

def pixel_to_yolo(x1, y1, x2, y2, img_w, img_h):
    """Convert pixel box to YOLO normalised (cx,cy,w,h) format."""
    cx=(x1+x2)/2/img_w; cy=(y1+y2)/2/img_h
    w=(x2-x1)/img_w;    h=(y2-y1)/img_h
    return round(cx,6),round(cy,6),round(w,6),round(h,6)

def yolo_to_pixel(cx, cy, w, h, img_w, img_h):
    """Convert YOLO normalised box to pixel (x1,y1,x2,y2) format."""
    x1=int((cx-w/2)*img_w); y1=int((cy-h/2)*img_h)
    x2=int((cx+w/2)*img_w); y2=int((cy+h/2)*img_h)
    return x1,y1,x2,y2


# ── Image helpers (Day 2) ─────────────────────────────────────────────────────
def crop_box(frame, box, pad=0):
    """Crop frame using [x1,y1,x2,y2] box with optional padding."""
    h, w = frame.shape[:2]
    x1,y1,x2,y2 = map(int, box)
    x1=max(0,x1-pad); y1=max(0,y1-pad)
    x2=min(w,x2+pad); y2=min(h,y2+pad)
    return frame[y1:y2, x1:x2]

def resize_frame(frame, width=640):
    h, w = frame.shape[:2]
    return cv2.resize(frame, (width, int(h*(width/w))))

def enhance_for_ocr(img):
    """Preprocess a license plate crop for OCR — used in plate_reader.py."""
    h, w = img.shape[:2]
    scale = 80/h
    img = cv2.resize(img, (int(w*scale), 80))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
    gray = clahe.apply(gray)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return thresh


# ── Drawing helpers (Days 1-10) ───────────────────────────────────────────────
def draw_label(frame, text, pos, color=(0,255,0), font_scale=0.55, thickness=2):
    """Draw text with filled background rectangle — used by all draw methods."""
    x, y = pos
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw,th), bl = cv2.getTextSize(text, font, font_scale, thickness)
    cv2.rectangle(frame, (x,y-th-bl-4), (x+tw+4,y+bl), color, -1)
    text_color = (0,0,0) if sum(color)>382 else (255,255,255)
    cv2.putText(frame, text, (x+2,y-2), font, font_scale, text_color, thickness)

def put_stats_overlay(frame, stats: dict, x=8, y=8, w=220):
    """Draw a semi-transparent stats panel (top-left)."""
    line_h  = 24
    panel_h = 14 + len(stats)*line_h + 8
    overlay = frame.copy()
    cv2.rectangle(overlay, (x,y), (x+w, y+panel_h), (15,15,15), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    for i, (key, val) in enumerate(stats.items()):
        cv2.putText(frame, f"{key}: {val}",
                    (x+10, y+16+i*line_h),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.56, (220,220,220), 1)


# ── Timestamp helpers (Day 5) ─────────────────────────────────────────────────
def now_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

def frame_to_timestamp(frame_num, fps):
    """Convert frame number to MM:SS.ms string."""
    s = frame_num/fps if fps > 0 else 0
    return f"{int(s//60):02d}:{s%60:05.2f}"


# ── Snapshot saver (Day 10) ───────────────────────────────────────────────────
def save_snapshot(frame, track_id, tag, snapshots_dir):
    """Save a frame crop as a JPG violation snapshot."""
    fname = f"{now_str()}_id{track_id}_{tag}.jpg"
    path  = os.path.join(snapshots_dir, fname)
    cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return path
