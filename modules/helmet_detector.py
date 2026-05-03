# modules/helmet_detector.py
# Detects helmet / no-helmet for each rider using a cropped head region

import cv2
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    HELMET_MODEL, FALLBACK_MODEL,
    HELMET_HEAD_CROP_RATIO, HELMET_CONFIDENCE,
    HELMET_CLASS_NAMES
)
from utils.helpers import get_logger, crop_box

log = get_logger("helmet_detector")

# Colors for drawing
COLOR_HELMET    = (0, 200, 0)     # green
COLOR_NO_HELMET = (0, 0, 255)     # red


class HelmetDetector:
    """
    Detects whether each rider on a detected bike is wearing a helmet.

    Strategy:
      1. Receive the bike bounding box from VehicleDetector.
      2. Crop the top HELMET_HEAD_CROP_RATIO of the bike box → head region.
      3. Run the helmet classification model on that crop.
      4. Return "with_helmet" or "without_helmet".

    Usage:
        hdet = HelmetDetector()
        status, conf = hdet.check(frame, bike_box)
        # status = "with_helmet" or "without_helmet"
    """

    def __init__(self, model_path=None):
        from ultralytics import YOLO

        path = model_path or HELMET_MODEL
        if not os.path.exists(path):
            log.warning(
                f"Helmet model not found at {path}. "
                f"Falling back to {FALLBACK_MODEL} (accuracy will be low!)"
            )
            path = FALLBACK_MODEL

        self.model = YOLO(path)
        log.info(f"Helmet model loaded: {path}")

    # ── Core check ────────────────────────────────────────────────────────────
    def check(self, frame, bike_box):
        """
        Check helmet status for ONE bike.

        Args:
            frame    : full video frame (BGR numpy array)
            bike_box : [x1, y1, x2, y2] of the detected bike

        Returns:
            status : "with_helmet" | "without_helmet" | "unknown"
            conf   : float confidence score
        """
        x1, y1, x2, y2 = map(int, bike_box)
        bike_h = y2 - y1

        # Crop top portion as head region
        head_y2 = y1 + int(bike_h * HELMET_HEAD_CROP_RATIO)
        head_crop = frame[y1:head_y2, x1:x2]

        # Guard: if crop is too small, skip
        if head_crop.size == 0 or head_crop.shape[0] < 10 or head_crop.shape[1] < 10:
            return "unknown", 0.0

        results = self.model(head_crop, verbose=False, conf=HELMET_CONFIDENCE)

        if not results or results[0].boxes is None or len(results[0].boxes) == 0:
            # No detection in head region — assume unknown
            return "unknown", 0.0

        # Take highest-confidence detection
        best_box  = max(results[0].boxes, key=lambda b: float(b.conf[0]))
        cls_id    = int(best_box.cls[0])
        conf      = float(best_box.conf[0])

        # Map class id to name
        if cls_id < len(HELMET_CLASS_NAMES):
            status = HELMET_CLASS_NAMES[cls_id]
        else:
            status = "with_helmet" if cls_id == 0 else "without_helmet"

        return status, conf

    def check_all(self, frame, bike_detections):
        """
        Check helmet status for every bike in the detections list.

        Args:
            frame          : full BGR frame
            bike_detections: list of detection dicts from VehicleDetector

        Returns:
            list of same dicts with added keys: helmet_status, helmet_conf
        """
        updated = []
        for det in bike_detections:
            status, conf = self.check(frame, det["box"])
            det["helmet_status"] = status
            det["helmet_conf"]   = conf
            updated.append(det)
        return updated

    # ── Drawing helper ────────────────────────────────────────────────────────
    def draw(self, frame, detections):
        """
        Overlay helmet status on each vehicle box.
        Green border = helmeted, Red = no helmet.
        """
        for det in detections:
            if "helmet_status" not in det:
                continue
            x1, y1, x2, y2 = det["box"]
            status = det["helmet_status"]

            if status == "with_helmet":
                color = COLOR_HELMET
                label = "Helmet OK"
            elif status == "without_helmet":
                color = COLOR_NO_HELMET
                label = "NO HELMET!"
                # Draw thick red border to make it stand out
                cv2.rectangle(frame, (x1-3,y1-3), (x2+3,y2+3), color, 3)
            else:
                color = (150, 150, 150)
                label = "?"

            # Small label below the box
            cv2.putText(frame, label,
                        (x1, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)
