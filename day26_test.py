# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 26 — day26_test.py
#  Topic: Multi-threading — run detection + DB writes in parallel
#
#  NEW today:
#    ✓ Producer thread: reads frames and puts them in a Queue
#    ✓ Consumer thread: pulls frames from Queue, runs detection
#    ✓ DB writer thread: handles all database inserts without blocking detection
#    ✓ Measure FPS improvement with threading vs single-threaded
#
#  Run:  python day26_test.py
#  Run:  python day26_test.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, threading, queue, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from utils.database           import TrafficDB
from utils.helpers            import put_stats_overlay, get_logger
from config import (
    VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE,
)

log = get_logger("day26")


class ThreadedPipeline:
    """
    3-thread architecture:
      Thread 1 (reader)   : cap.read() → frame_queue
      Thread 2 (detector) : frame_queue → detection → result_queue
      Thread 3 (db_writer): result_queue → TrafficDB inserts
    Main thread displays the annotated frame from result_queue.
    """

    FRAME_Q_SIZE  = 4
    RESULT_Q_SIZE = 4

    def __init__(self, source):
        self.source     = source
        self.frame_q    = queue.Queue(maxsize=self.FRAME_Q_SIZE)
        self.result_q   = queue.Queue(maxsize=self.RESULT_Q_SIZE)
        self.stop_event = threading.Event()

        self.vehicle_det = VehicleDetector()
        self.helmet_det  = HelmetDetector()
        self.rider_ctr   = RiderCounter(method="overlap")
        self.db          = TrafficDB()

        self.violation_ids = set()
        self.fps           = 0.0
        self.frame_n       = 0

    # ── Thread 1: frame reader ────────────────────────────────────────────────
    def _reader(self):
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            log.error(f"Cannot open: {self.source}")
            self.stop_event.set(); return
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                if total > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                break
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
            try:
                self.frame_q.put(frame, timeout=1.0)
            except queue.Full:
                pass   # drop frame if detector is too slow
        cap.release()
        self.stop_event.set()

    # ── Thread 2: detector ────────────────────────────────────────────────────
    def _detector(self):
        fps_t = time.time(); fps_c = 0
        while not self.stop_event.is_set():
            try:
                frame = self.frame_q.get(timeout=1.0)
            except queue.Empty:
                continue
            self.frame_n += 1
            out   = frame.copy()

            veh   = self.vehicle_det.process_frame(out, self.frame_n)
            dets  = veh["detections"]
            if dets:
                dets = self.rider_ctr.count_all(out, dets)
                dets = self.helmet_det.check_all(out, dets)

            self.vehicle_det.draw_trails(out)
            self.vehicle_det.draw(out, veh)
            self.rider_ctr.draw(out, dets)
            self.helmet_det.draw(out, dets)

            fps_c += 1
            if time.time() - fps_t >= 1.0:
                self.fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()

            try:
                self.result_q.put((out, dets, veh), timeout=1.0)
            except queue.Full:
                pass

    # ── Thread 3: DB writer ───────────────────────────────────────────────────
    def _db_writer(self):
        from utils.helpers import save_snapshot
        while not self.stop_event.is_set():
            try:
                frame, dets, veh = self.result_q.get(timeout=1.0)
            except queue.Empty:
                continue
            for tid in veh.get("newly_counted", []):
                vtype = self.vehicle_det.track_types.get(tid, "motorcycle")
                self.db.log_vehicle_count(vtype)
            for det in dets:
                tid = det.get("track_id")
                if tid is None or tid in self.violation_ids:
                    continue
                viols = []
                if det.get("helmet_status") == "without_helmet":
                    viols.append(VIOLATION_NO_HELMET)
                if det.get("is_triple_viol"):
                    viols.append(VIOLATION_TRIPLE_RIDE)
                if viols:
                    self.violation_ids.add(tid)
                    snap = save_snapshot(frame, tid, "+".join(viols), SNAPSHOTS_DIR)
                    for v in viols:
                        self.db.log_violation(
                            track_id=tid, plate=det.get("plate","UNKNOWN"),
                            vehicle_type=det.get("vehicle_type","motorcycle"),
                            rider_count=det.get("rider_count",1),
                            helmet_status=det.get("helmet_status","unknown"),
                            violation_type=v, snapshot_path=snap,
                            frame_number=self.frame_n,
                        )

    def run(self):
        threads = [
            threading.Thread(target=self._reader,    daemon=True, name="Reader"),
            threading.Thread(target=self._detector,  daemon=True, name="Detector"),
            threading.Thread(target=self._db_writer, daemon=True, name="DBWriter"),
        ]
        for t in threads:
            t.start()
            log.info(f"Thread started: {t.name}")

        while not self.stop_event.is_set():
            try:
                frame, dets, veh = self.result_q.get(timeout=0.1)
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                # Show last frame while waiting
                try:
                    frame = getattr(self, "_last_frame", None)
                    if frame is None:
                        continue
                except:
                    continue

            self._last_frame = frame
            put_stats_overlay(frame, {
                "FPS":        f"{self.fps:.1f}",
                "Frame":      self.frame_n,
                "Vehicles":   veh.get("total_counted", 0), # type: ignore
                "Violations": len(self.violation_ids),
                "Q(frame)":   self.frame_q.qsize(),
                "Q(result)":  self.result_q.qsize(),
            })
            cv2.imshow("Day 26 — Threaded Pipeline (Q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop_event.set()

        for t in threads:
            t.join(timeout=3.0)
        cv2.destroyAllWindows()
        log.info(f"Violations logged: {len(self.violation_ids)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 26 — Multi-Threading")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 26 — Multi-Threading: Reader / Detector / DB Writer")
    print("=" * 65)
    print(f"  Source: {src}")
    print("  3 threads: Reader → Detector → DB Writer")
    print("  Main thread: display only (never blocks on I/O)")
    print("  Keys: Q=quit")
    print("=" * 65)

    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    pipeline = ThreadedPipeline(src)
    pipeline.run()
    print("\n  Next → python day27_test.py  (Config + environment variables)")
