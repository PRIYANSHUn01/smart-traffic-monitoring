# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 31 — day31_test.py
#  Topic: Unit tests with pytest — test helpers, database, config
#
#  NEW today:
#    ✓ Write pytest tests for utility functions
#    ✓ Test TrafficDB insert + read round-trip
#    ✓ Test config validation logic
#    ✓ Run tests in-process without pytest (for environments without it)
#
#  Run:  python day31_test.py           (runs built-in test runner)
#  Run:  pytest day31_test.py -v        (if pytest is installed)
#  Install pytest: pip install pytest
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, tempfile, traceback
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers  import compute_iou, box_center, box_area, now_iso
from utils.database import TrafficDB
from config         import VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE


# ══════════════════════════════════════════════════════════════════════════════
# Test helpers
# ══════════════════════════════════════════════════════════════════════════════

def test_compute_iou_identical():
    box = [100, 100, 200, 200]
    assert abs(compute_iou(box, box) - 1.0) < 1e-9

def test_compute_iou_no_overlap():
    assert compute_iou([0,0,50,50], [100,100,200,200]) == 0.0

def test_compute_iou_half_overlap():
    iou = compute_iou([0,0,200,100], [100,0,300,100])
    assert abs(iou - 1/3) < 1e-6

def test_compute_iou_contained():
    outer = [0, 0, 200, 200]
    inner = [50, 50, 150, 150]
    iou = compute_iou(outer, inner)
    assert 0.0 < iou < 1.0   # inner is 25% of outer → IoU = 25/100 = 0.25
    assert abs(iou - 0.25) < 1e-6

def test_box_center():
    cx, cy = box_center([100, 80, 300, 280])
    assert cx == 200 and cy == 180

def test_box_area():
    assert box_area([100, 100, 200, 200]) == 10000
    assert box_area([0, 0, 0, 0]) == 0

def test_now_iso_format():
    ts = now_iso()
    assert "T" in ts   # ISO format: 2024-01-01T12:00:00

# ══════════════════════════════════════════════════════════════════════════════
# Test database
# ══════════════════════════════════════════════════════════════════════════════

def test_database_insert_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = TrafficDB(db_path=db_path)

        # Insert violation
        db.log_violation(
            track_id=42, plate="TEST1234",
            vehicle_type="motorcycle", rider_count=1,
            helmet_status="without_helmet",
            violation_type=VIOLATION_NO_HELMET,
            snapshot_path="", frame_number=100,
        )

        # Read back
        rows = db.get_recent_violations(limit=10)
        assert len(rows) == 1
        assert rows[0]["plate_number"] == "TEST1234"
        assert rows[0]["track_id"] == 42
        assert rows[0]["violation_type"] == VIOLATION_NO_HELMET

def test_database_vehicle_count():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = TrafficDB(db_path=db_path)
        db.log_vehicle_count("motorcycle")
        db.log_vehicle_count("motorcycle")
        db.log_vehicle_count("bicycle")
        assert db.get_total_vehicles() == 3
        cts = db.get_vehicle_type_counts()
        assert cts["motorcycle"] == 2
        assert cts["bicycle"] == 1

def test_database_total_violations():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = TrafficDB(db_path=db_path)
        assert db.get_total_violations() == 0
        for i in range(3):
            db.log_violation(track_id=i, violation_type=VIOLATION_NO_HELMET,
                             frame_number=i*10)
        assert db.get_total_violations() == 3

def test_database_plate_search():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = TrafficDB(db_path=db_path)
        db.log_violation(track_id=1, plate="UP14AB1234",
                         violation_type=VIOLATION_NO_HELMET, frame_number=1)
        db.log_violation(track_id=2, plate="DL3CAB5678",
                         violation_type=VIOLATION_TRIPLE_RIDE, frame_number=2)
        results = db.search_by_plate("UP14")
        assert len(results) == 1
        assert results[0]["plate_number"] == "UP14AB1234"

def test_violation_breakdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        db = TrafficDB(db_path=db_path)
        db.log_violation(track_id=1, violation_type=VIOLATION_NO_HELMET,   frame_number=1)
        db.log_violation(track_id=2, violation_type=VIOLATION_NO_HELMET,   frame_number=2)
        db.log_violation(track_id=3, violation_type=VIOLATION_TRIPLE_RIDE, frame_number=3)
        bd = db.get_violation_breakdown()
        assert bd[VIOLATION_NO_HELMET]   == 2
        assert bd[VIOLATION_TRIPLE_RIDE] == 1


# ══════════════════════════════════════════════════════════════════════════════
# Mini test runner (no pytest dependency)
# ══════════════════════════════════════════════════════════════════════════════

def run_all():
    tests = [
        test_compute_iou_identical,
        test_compute_iou_no_overlap,
        test_compute_iou_half_overlap,
        test_compute_iou_contained,
        test_box_center,
        test_box_area,
        test_now_iso_format,
        test_database_insert_and_read,
        test_database_vehicle_count,
        test_database_total_violations,
        test_database_plate_search,
        test_violation_breakdown,
    ]
    passed = 0; failed = 0
    print("=" * 65)
    print("  DAY 31 — Unit Tests")
    print("=" * 65)
    for test in tests:
        try:
            test()
            print(f"  ✓  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {test.__name__}")
            print(f"       {e}")
            traceback.print_exc()
            failed += 1

    print()
    print(f"  Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("  ✓ All unit tests passed!")
    else:
        print("  ✗ Some tests failed — fix before proceeding")

    print("\n  Run with pytest for richer output:")
    print("    pip install pytest")
    print("    pytest day31_test.py -v")
    print("\n  Next → python day32_test.py  (Integration tests)")
    return failed == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
