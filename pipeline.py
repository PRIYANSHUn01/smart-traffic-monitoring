# pipeline.py  —  Master pipeline: wires all modules together
# Run this file directly to start the detection system

import cv2
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import (
    VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE, VIOLATION_DOUBLE_RIDE,
    ENABLE_DOUBLE_WARNING, SAVE_FRAMES, SNAPSHOTS_DIR, ENABLE_EMAIL_ALERTS
)
from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector   import HelmetDetector
from modules.rider_counter     import RiderCounter
from modules.plate_reader      import PlateReader
from utils.database            import TrafficDB
from utils.helpers             import get_logger, put_stats_overlay, save_snapshot, now_str

log = get_logger("pipeline")


class TrafficPipeline:
    """
    Master pipeline that connects all 4 detection modules.

    Frame flow:
        VehicleDetector → RiderCounter → HelmetDetector → PlateReader
        → ViolationChecker → Database/Dashboard

    Usage:
        pipe = TrafficPipeline()
        pipe.run()           # blocking — runs until 'q' pressed
    """

    def __init__(self,
                 source=None,
                 use_helmet=True,
                 use_riders=True,
                 use_plate=True):
        log.info("Initializing Traffic Monitoring Pipeline…")

        self.source      = source or VIDEO_SOURCE
        self.use_helmet  = use_helmet
        self.use_riders  = use_riders
        self.use_plate   = use_plate

        # ── Load modules ──────────────────────────────────────────────────────
        self.vehicle_det = VehicleDetector()

        if use_riders:
            self.rider_ctr = RiderCounter(method="overlap")

        if use_helmet:
            self.helmet_det = HelmetDetector()

        if use_plate:
            self.plate_rdr = PlateReader()

        self.db = TrafficDB()

        # Runtime stats
        self.frame_num      = 0
        self.fps_counter    = 0
        self.fps            = 0.0
        self.fps_timer      = time.time()
        self.violation_ids  = set()   # track IDs already logged as violations

        log.info("Pipeline ready.")

    # ── Main run loop ─────────────────────────────────────────────────────────
    def run(self):
        """Open the video source and process frames in a loop"""
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            log.error(f"Cannot open source: {self.source}")
            return

        log.info(f"Source opened: {self.source}")
        log.info("Press 'q' to quit, 'r' to reset counters, 's' to save frame")

        while True:
            ret, frame = cap.read()
            if not ret:
                log.warning("End of stream or cannot read frame.")
                break

            self.frame_num += 1
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            # ── Process frame ─────────────────────────────────────────────────
            processed = self.process_frame(frame)

            # ── Update FPS ────────────────────────────────────────────────────
            self.fps_counter += 1
            elapsed = time.time() - self.fps_timer
            if elapsed >= 1.0:
                self.fps = self.fps_counter / elapsed
                self.fps_counter = 0
                self.fps_timer = time.time()

            # ── Draw stats overlay ────────────────────────────────────────────
            stats = {
                "FPS":        f"{self.fps:.1f}",
                "Frame":      self.frame_num,
                "Vehicles":   processed["total_counted"],
                "Violations": self.db.get_total_violations(),
            }
            put_stats_overlay(processed["frame"], stats)

            # ── Display ───────────────────────────────────────────────────────
            cv2.imshow("Traffic Monitor — press Q to quit", processed["frame"])

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('r'):
                self.vehicle_det.reset()
                log.info("Counters reset by user")
            elif key == ord('s'):
                path = os.path.join(SNAPSHOTS_DIR, f"manual_{now_str()}.jpg")
                cv2.imwrite(path, processed["frame"])
                log.info(f"Frame saved: {path}")

        cap.release()
        cv2.destroyAllWindows()
        log.info("Pipeline stopped.")

    # ── Per-frame processing ──────────────────────────────────────────────────
    def process_frame(self, frame):
        """
        Run the full detection pipeline on one frame.
        Returns dict with annotated frame and summary stats.
        """
        # ── Step 1: Vehicle detection & counting ──────────────────────────────
        veh_result = self.vehicle_det.process_frame(frame, self.frame_num)
        detections = veh_result["detections"]

        # Log newly counted vehicles to DB
        for tid in veh_result["newly_counted"]:
            vtype = self.vehicle_det.track_types.get(tid, "motorcycle")
            self.db.log_vehicle_count(vtype)

        # ── Step 2: Rider count ───────────────────────────────────────────────
        if self.use_riders and detections:
            detections = self.rider_ctr.count_all(frame, detections)

        # ── Step 3: Helmet detection ──────────────────────────────────────────
        if self.use_helmet and detections:
            detections = self.helmet_det.check_all(frame, detections)

        # ── Step 4: License plate OCR ─────────────────────────────────────────
        if self.use_plate and detections:
            for det in detections:
                plate_info = self.plate_rdr.read(
                    frame, det["box"], det["track_id"]
                )
                det["plate"]        = plate_info["plate"]
                det["plate_stable"] = plate_info["stable"]

        # ── Step 5: Violation detection & logging ─────────────────────────────
        for det in detections:
            self._check_and_log_violation(frame, det)

        # ── Step 6: Draw everything ───────────────────────────────────────────
        out = frame.copy()
        self.vehicle_det.draw(out, veh_result)

        if self.use_riders:
            self.rider_ctr.draw(out, detections)

        if self.use_helmet:
            self.helmet_det.draw(out, detections)

        if self.use_plate:
            self.plate_rdr.draw(out, detections)

        return {
            "frame":         out,
            "detections":    detections,
            "total_counted": veh_result["total_counted"],
        }

    # ── Violation checker ─────────────────────────────────────────────────────
    def _check_and_log_violation(self, frame, det):
        """Check one detection for violations and log if new"""
        tid = det["track_id"]
        if tid in self.violation_ids:
            return   # already logged this vehicle

        violations = []

        # Helmet violation
        if det.get("helmet_status") == "without_helmet":
            violations.append(VIOLATION_NO_HELMET)

        # Triple/double riding
        riders = det.get("rider_count", 1)
        if riders >= 3:
            violations.append(VIOLATION_TRIPLE_RIDE)
        elif riders == 2 and ENABLE_DOUBLE_WARNING:
            violations.append(VIOLATION_DOUBLE_RIDE)

        if not violations:
            return

        self.violation_ids.add(tid)
        vtype = det.get("vehicle_type", "motorcycle")
        plate = det.get("plate", "UNKNOWN")
        helmet = det.get("helmet_status", "unknown")

        snap_path = ""
        if SAVE_FRAMES:
            snap_path = save_snapshot(frame, tid,
                                      "+".join(violations), SNAPSHOTS_DIR)

        for viol in violations:
            self.db.log_violation(
                track_id     = tid,
                plate        = plate,
                vehicle_type = vtype,
                rider_count  = riders,
                helmet_status= helmet,
                violation_type=viol,
                snapshot_path= snap_path,
                frame_number  = self.frame_num,
            )
            log.warning(f"VIOLATION: {viol} | Plate:{plate} | ID:{tid}")

        if ENABLE_EMAIL_ALERTS:
            self._send_alert(plate, violations)

    def _send_alert(self, plate, violations):
        """Optional email alert for violations"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from config import EMAIL_SENDER, EMAIL_RECIPIENT, EMAIL_APP_PASSWORD
            if not EMAIL_APP_PASSWORD:
                return
            body = f"Traffic Violation Detected\nPlate: {plate}\nViolations: {', '.join(violations)}"
            msg = MIMEText(body)
            msg["Subject"] = f"[Traffic Alert] {plate}"
            msg["From"] = EMAIL_SENDER
            msg["To"]   = EMAIL_RECIPIENT
            with smtplib.SMTP("smtp.gmail.com", 587) as s:
                s.starttls()
                s.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                s.send_message(msg)
        except Exception as e:
            log.debug(f"Email alert failed: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Traffic Monitoring System")
    parser.add_argument("--source",    default=None,
                        help="Video source: 0=webcam, or path to video file")
    parser.add_argument("--no-helmet", action="store_true",
                        help="Disable helmet detection")
    parser.add_argument("--no-riders", action="store_true",
                        help="Disable rider counting")
    parser.add_argument("--no-plate",  action="store_true",
                        help="Disable license plate OCR")
    args = parser.parse_args()

    source = int(args.source) if args.source and args.source.isdigit() else args.source

    pipe = TrafficPipeline(
        source     = source,
        use_helmet = not args.no_helmet,
        use_riders = not args.no_riders,
        use_plate  = not args.no_plate,
    )
    pipe.run()
