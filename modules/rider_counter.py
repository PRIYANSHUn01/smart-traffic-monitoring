# modules/rider_counter.py
# Counts how many people are on each detected bike (Solo / Double / Triple+)

import cv2
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    FALLBACK_MODEL, CONFIDENCE_THRESHOLD,
    RIDER_OVERLAP_THRESHOLD, RIDER_LABELS, RIDER_COLORS
)
from utils.helpers import get_logger, compute_iou, box_center

log = get_logger("rider_counter")

# Person class ID in COCO (used by pretrained model)
PERSON_CLASS_ID = 0


class RiderCounter:
    """
    Counts the number of riders on each detected bike.

    Two methods available:
      - method="overlap"  → counts COCO 'person' boxes overlapping bike box
      - method="pose"     → uses YOLOv8-pose skeleton keypoints (more accurate)

    Usage:
        rc = RiderCounter(method="overlap")
        detections = rc.count_all(frame, bike_detections)
        # Each det now has: rider_count, rider_label, is_violation
    """

    def __init__(self, method="overlap"):
        from ultralytics import YOLO

        self.method = method

        if method == "pose":
            self.model = YOLO("yolov8n-pose.pt")
            log.info("Rider counter: YOLOv8-pose loaded")
        else:
            # Use a standard model to detect persons
            self.model = YOLO(FALLBACK_MODEL)
            log.info("Rider counter: overlap method (person detection)")

    # ── Public API ────────────────────────────────────────────────────────────
    def count_all(self, frame, bike_detections):
        """
        Add rider_count and rider_label to each detection dict.

        Args:
            frame           : BGR numpy frame
            bike_detections : list of dicts from VehicleDetector

        Returns:
            same list with added keys:
                rider_count   : int (1, 2, 3, ...)
                rider_label   : str ("Solo", "Double", "Triple+")
                is_triple_viol: bool
        """
        if self.method == "pose":
            return self._count_pose(frame, bike_detections)
        else:
            return self._count_overlap(frame, bike_detections)

    # ── Method 1: Person box overlap ─────────────────────────────────────────
    def _count_overlap(self, frame, bike_detections):
        """
        Detect all persons in the frame, then check how many
        person boxes overlap with each bike box.
        """
        # Detect persons only
        results = self.model(frame, verbose=False,
                             conf=CONFIDENCE_THRESHOLD,
                             classes=[PERSON_CLASS_ID])

        person_boxes = []
        if results and results[0].boxes is not None:
            for box in results[0].boxes:
                person_boxes.append(box.xyxy[0].tolist())

        updated = []
        for det in bike_detections:
            bike_box = det["box"]
            count = self._count_persons_on_bike(bike_box, person_boxes)
            count = max(count, 1)  # at least 1 rider assumed if bike detected

            det["rider_count"]    = count
            det["rider_label"]    = RIDER_LABELS.get(count, "Triple+")
            det["is_triple_viol"] = count >= 3
            updated.append(det)

        return updated

    def _count_persons_on_bike(self, bike_box, person_boxes):
        """Count how many person boxes significantly overlap with the bike box"""
        count = 0
        for pb in person_boxes:
            iou = compute_iou(bike_box, pb)
            if iou >= RIDER_OVERLAP_THRESHOLD:
                count += 1
            else:
                # Also check if person CENTER is inside bike box
                pcx, pcy = box_center(pb)
                bx1,by1,bx2,by2 = map(int, bike_box)
                if bx1 < pcx < bx2 and by1 < pcy < by2:
                    count += 1
        return count

    # ── Method 2: Pose / Skeleton ─────────────────────────────────────────────
    def _count_pose(self, frame, bike_detections):
        """
        Use YOLOv8-pose to count skeletons inside each bike box.
        Each complete skeleton = one rider.
        Keypoint 5 = left shoulder (torso anchor).
        """
        results = self.model(frame, verbose=False)

        skeleton_anchors = []  # list of (sx, sy) for each detected person
        if results and results[0].keypoints is not None:
            kpts = results[0].keypoints.xy
            for skeleton in kpts:
                # Use left shoulder (idx 5) as anchor
                if len(skeleton) > 5:
                    sx, sy = float(skeleton[5][0]), float(skeleton[5][1])
                    if sx > 0 and sy > 0:
                        skeleton_anchors.append((sx, sy))

        updated = []
        for det in bike_detections:
            bx1,by1,bx2,by2 = det["box"]
            count = sum(
                1 for (sx,sy) in skeleton_anchors
                if bx1 < sx < bx2 and by1 < sy < by2
            )
            count = max(count, 1)

            det["rider_count"]    = count
            det["rider_label"]    = RIDER_LABELS.get(count, "Triple+")
            det["is_triple_viol"] = count >= 3
            updated.append(det)

        return updated

    # ── Drawing helper ─────────────────────────────────────────────────────────
    def draw(self, frame, detections):
        """
        Draw rider count badge on each bike.
        Color: green=solo, orange=double, red=triple+
        """
        for det in detections:
            if "rider_count" not in det:
                continue
            x1, y1, x2, y2 = det["box"]
            count = det["rider_count"]
            label = det.get("rider_label", str(count))
            color = RIDER_COLORS.get(min(count, 3), (0, 0, 255))

            # Badge background at top-right of box
            badge_x = x2 - 80
            badge_y = y1 - 10
            cv2.rectangle(frame,
                          (badge_x, badge_y - 18),
                          (x2, badge_y + 4),
                          color, -1)
            cv2.putText(frame, label,
                        (badge_x + 4, badge_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (255, 255, 255), 1)

            # If triple — draw a thick warning border
            if count >= 3:
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,0,255), 4)
                cv2.putText(frame, "TRIPLE!",
                            (x1, y2 + 35),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 0, 255), 2)
