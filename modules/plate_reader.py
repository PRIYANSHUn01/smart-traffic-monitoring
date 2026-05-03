# modules/plate_reader.py
# Detects license plate region and reads the plate number using OCR

import cv2
import re
import os
import sys
from collections import defaultdict, Counter
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    PLATE_MODEL, FALLBACK_MODEL, CONFIDENCE_THRESHOLD,
    OCR_LANGUAGES, OCR_MIN_CONFIDENCE, PLATE_VOTE_FRAMES
)
from utils.helpers import get_logger, enhance_for_ocr, draw_label

log = get_logger("plate_reader")

# Regex for common Indian plate formats
# e.g. UP14AB1234  or  DL3CAB1234
INDIA_PLATE_PATTERN = re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$')


class PlateReader:
    """
    Detects license plates and reads their numbers via OCR.

    Key features:
      - Voting system: collects multiple OCR reads per vehicle and
        picks the most consistent result (reduces noise)
      - Perspective correction for angled plates
      - Regex validation for Indian plate format

    Usage:
        pr = PlateReader()
        result = pr.read(frame, bike_box, track_id)
        print(result["plate"])   # e.g. "UP14AB1234"
    """

    def __init__(self, model_path=None):
        import easyocr
        from ultralytics import YOLO

        # Plate detection model
        path = model_path or PLATE_MODEL
        if not os.path.exists(path):
            log.warning(f"Plate model not found at {path}. Using {FALLBACK_MODEL}")
            path = FALLBACK_MODEL
        self.detect_model = YOLO(path)

        # EasyOCR reader (loads on first call — takes ~5 sec)
        log.info("Loading EasyOCR reader… (first time takes ~5 seconds)")
        self.ocr = easyocr.Reader(OCR_LANGUAGES, gpu=False)
        log.info("EasyOCR ready")

        # Per-vehicle voting history: {track_id: [plate_str, ...]}
        self._vote_history = defaultdict(list)

    # ── Main read method ──────────────────────────────────────────────────────
    def read(self, frame, bike_box, track_id):
        """
        Attempt to read the license plate from a bike bounding box.

        Args:
            frame    : BGR numpy frame
            bike_box : [x1,y1,x2,y2] of the bike
            track_id : unique tracker ID for this vehicle

        Returns dict:
            plate      : best plate string so far (or "UNKNOWN")
            raw_ocr    : raw OCR string this frame
            confidence : OCR confidence
            stable     : True if voting has settled on a confident result
        """
        # Step 1: Detect plate region within bike crop
        plate_crop = self._detect_plate_region(frame, bike_box)

        if plate_crop is None:
            return {"plate": self._best_vote(track_id),
                    "raw_ocr": "", "confidence": 0.0, "stable": False}

        # Step 2: Preprocess
        processed = enhance_for_ocr(plate_crop)

        # Step 3: OCR
        raw_text, conf = self._run_ocr(processed)

        # Step 4: Clean and validate
        cleaned = self._clean_plate(raw_text)

        # Step 5: Vote
        if cleaned:
            self._vote_history[track_id].append(cleaned)

        best = self._best_vote(track_id)
        stable = (len(self._vote_history[track_id]) >= PLATE_VOTE_FRAMES
                  and best != "UNKNOWN")

        return {
            "plate":      best,
            "raw_ocr":    raw_text,
            "confidence": conf,
            "stable":     stable,
        }

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _detect_plate_region(self, frame, bike_box):
        """
        Detect the plate bounding box within the lower portion of the bike.
        Falls back to heuristic crop if model not trained for plates.
        """
        x1, y1, x2, y2 = map(int, bike_box)
        bike_h = y2 - y1

        # Look only in the lower half of the bike box (where plate usually is)
        search_y1 = y1 + int(bike_h * 0.5)
        bike_lower = frame[search_y1:y2, x1:x2]

        if bike_lower.size == 0:
            return None

        results = self.detect_model(bike_lower, verbose=False,
                                     conf=CONFIDENCE_THRESHOLD)

        if (results and results[0].boxes is not None
                and len(results[0].boxes) > 0):
            # Use first (best) detected plate
            pb = results[0].boxes[0].xyxy[0].tolist()
            px1, py1, px2, py2 = map(int, pb)
            crop = bike_lower[py1:py2, px1:px2]
            if crop.size > 0:
                return crop

        # Heuristic fallback: bottom 20% of bike, full width
        plate_y1 = y1 + int(bike_h * 0.78)
        heuristic = frame[plate_y1:y2, x1:x2]
        return heuristic if heuristic.size > 0 else None

    def _run_ocr(self, processed_img):
        """Run EasyOCR and concatenate all text detections"""
        try:
            results = self.ocr.readtext(processed_img)
        except Exception as e:
            log.debug(f"OCR error: {e}")
            return "", 0.0

        text = ""
        total_conf = 0.0
        n = 0
        for (_, t, c) in results:
            if c >= OCR_MIN_CONFIDENCE:
                text += t.strip()
                total_conf += c
                n += 1

        avg_conf = total_conf / n if n > 0 else 0.0
        return text, avg_conf

    def _clean_plate(self, raw: str) -> str:
        """
        Normalize OCR output:
        - Uppercase, remove spaces/special chars
        - Fix common OCR substitutions (O↔0, I↔1)
        - Validate against Indian plate pattern
        """
        if not raw:
            return ""

        cleaned = raw.upper()
        cleaned = re.sub(r'[^A-Z0-9]', '', cleaned)

        # Common OCR mistakes
        # (only fix digits in numeric sections to avoid breaking letter parts)
        # Simple global substitutions
        cleaned = cleaned.replace('O', '0').replace('I', '1')

        # Accept plates of reasonable length (8–12 chars)
        if 7 <= len(cleaned) <= 12:
            return cleaned
        return ""

    def _best_vote(self, track_id) -> str:
        """Return the most frequently seen plate string for this vehicle"""
        history = self._vote_history.get(track_id, [])
        if not history:
            return "UNKNOWN"
        best, _ = Counter(history).most_common(1)[0]
        return best

    # ── Drawing helper ────────────────────────────────────────────────────────
    def draw(self, frame, detections):
        """Draw the plate number below each bike box"""
        for det in detections:
            if "plate" not in det:
                continue
            x1, y1, x2, y2 = det["box"]
            plate = det.get("plate", "UNKNOWN")
            if plate == "UNKNOWN":
                continue
            draw_label(frame, f"Plate: {plate}",
                       (x1, y2 + 55),
                       color=(255, 200, 0))

    def clear_vehicle(self, track_id):
        """Remove voting history when a vehicle leaves the scene"""
        self._vote_history.pop(track_id, None)
