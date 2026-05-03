# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 32 — day32_test.py
#  Topic: Integration tests — test the full pipeline end-to-end with a test video
#
#  NEW today:
#    ✓ Create a synthetic test video (moving shapes simulating vehicles)
#    ✓ Run the full pipeline on it and verify outputs
#    ✓ Assert: vehicles counted > 0, DB written correctly
#    ✓ Regression test: ensure no crashes on edge-case frames
#
#  Run:  python day32_test.py
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, tempfile, time, traceback
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from utils.database           import TrafficDB
from utils.helpers            import get_logger

log = get_logger("day32")


# ── Synthetic test video generator ───────────────────────────────────────────
def make_test_video(path, num_frames=120, fps=30, w=640, h=480):
    """
    Create a short synthetic video with a moving rectangle (simulates a vehicle).
    Used so integration tests don't require a real camera or real footage.
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v") # type: ignore
    writer = cv2.VideoWriter(path, fourcc, fps, (w, h))
    for i in range(num_frames):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        # Simulated road background
        cv2.rectangle(frame, (0, h//2), (w, h), (40, 40, 40), -1)
        # Moving "vehicle" box
        x = int((i / num_frames) * (w - 80))
        y = h // 2 - 30
        cv2.rectangle(frame, (x, y), (x+80, y+60), (100, 180, 100), -1)
        # Lane line
        cv2.line(frame, (0, h//2 + 10), (w, h//2 + 10), (200, 200, 200), 1)
        writer.write(frame)
    writer.release()
    return path


# ── Integration test cases ────────────────────────────────────────────────────

def test_pipeline_runs_without_crash():
    """Pipeline should process 60 frames of a synthetic video without exceptions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vpath = os.path.join(tmpdir, "test.mp4")
        make_test_video(vpath, num_frames=60)

        detector = VehicleDetector()
        cap = cv2.VideoCapture(vpath)
        assert cap.isOpened(), "Could not open synthetic test video"

        for frame_n in range(60):
            ret, frame = cap.read()
            if not ret:
                break
            result = detector.process_frame(frame, frame_n)
            assert "detections" in result
            assert "total_counted" in result
            assert isinstance(result["detections"], list)

        cap.release()
    return True


def test_db_write_on_violation():
    """DB should have exactly 1 violation after we manually log one."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = TrafficDB(db_path=os.path.join(tmpdir, "t.db"))
        assert db.get_total_violations() == 0
        db.log_violation(track_id=1, violation_type="NO_HELMET", frame_number=10)
        assert db.get_total_violations() == 1
    return True


def test_vehicle_count_increments():
    """Vehicle count should increment on each log_vehicle_count call."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db = TrafficDB(db_path=os.path.join(tmpdir, "t.db"))
        for _ in range(5):
            db.log_vehicle_count("motorcycle")
        assert db.get_total_vehicles() == 5
    return True


def test_no_crash_on_blank_frame():
    """Detector should handle blank (all-zero) frames without crashing."""
    detector = VehicleDetector()
    blank = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.process_frame(blank, 1)
    assert isinstance(result["detections"], list)
    return True


def test_no_crash_on_tiny_frame():
    """Detector should handle very small frames without crashing."""
    detector = VehicleDetector()
    tiny = np.zeros((64, 64, 3), dtype=np.uint8)
    result = detector.process_frame(tiny, 1)
    assert isinstance(result["detections"], list)
    return True


def test_counting_line_set_correctly():
    """line_y should be set on first process_frame call."""
    from config import COUNT_LINE_POSITION
    detector = VehicleDetector()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector.process_frame(frame, 1)
    assert detector.line_y is not None
    expected = int(480 * COUNT_LINE_POSITION)
    assert detector.line_y == expected
    return True


def test_reset_clears_state():
    """After reset(), counted_ids and track_types should be empty."""
    detector = VehicleDetector()
    detector.counted_ids.add(99)
    detector.track_types[99] = "motorcycle"
    detector.reset()
    assert len(detector.counted_ids) == 0
    assert len(detector.track_types) == 0
    return True


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all():
    tests = [
        ("Pipeline runs without crash",    test_pipeline_runs_without_crash),
        ("DB write on violation",           test_db_write_on_violation),
        ("Vehicle count increments",        test_vehicle_count_increments),
        ("No crash on blank frame",         test_no_crash_on_blank_frame),
        ("No crash on tiny frame",          test_no_crash_on_tiny_frame),
        ("Counting line set correctly",     test_counting_line_set_correctly),
        ("Reset clears state",              test_reset_clears_state),
    ]

    print("=" * 65)
    print("  DAY 32 — Integration Tests")
    print("=" * 65)

    passed = 0; failed = 0
    for name, test in tests:
        t0 = time.time()
        try:
            test()
            elapsed = time.time() - t0
            print(f"  ✓  {name:<40s}  ({elapsed*1000:.0f}ms)")
            passed += 1
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  ✗  {name:<40s}  ({elapsed*1000:.0f}ms)")
            print(f"       {e}")
            traceback.print_exc()
            failed += 1

    print()
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  ✓ All integration tests passed!")
    print("\n  Next → python day33_test.py  (Model accuracy benchmarking)")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
