# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 30 — day30_test.py
#  Topic: Batch video processing — process multiple video files in sequence
#
#  NEW today:
#    ✓ Process a folder of video files automatically
#    ✓ Per-file summary report (vehicles, violations, duration, FPS)
#    ✓ Combined report across all files
#    ✓ Skip already-processed files (resume from checkpoint)
#    ✓ Headless mode (no display) for server deployment
#
#  Run:  python day30_test.py --folder data/videos
#  Run:  python day30_test.py --folder data/videos --headless
#  Run:  python day30_test.py --folder data/videos --resume
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, json, argparse, glob
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from utils.database           import TrafficDB
from utils.helpers            import get_logger, put_stats_overlay, save_snapshot
from config import (
    FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR, LOGS_DIR,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE,
)

log = get_logger("day30")
CHECKPOINT_FILE = os.path.join(LOGS_DIR, "batch_checkpoint.json")
os.makedirs(LOGS_DIR, exist_ok=True)


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE) as f:
            return json.load(f)
    return {"processed": []}


def save_checkpoint(cp):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(cp, f, indent=2)


def process_video(path, detector, helmet_det, rider_ctr, db, headless=False):
    """Process one video file. Returns per-file stats dict."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        log.warning(f"Cannot open: {path}")
        return None

    total_f   = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_src   = cap.get(cv2.CAP_PROP_FPS)
    duration  = total_f / fps_src if fps_src > 0 else 0

    log.info(f"Processing: {os.path.basename(path)}  ({total_f} frames, {duration:.1f}s)")

    frame_n      = 0
    violation_ids = set()
    t_start       = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_n += 1
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        veh  = detector.process_frame(frame, frame_n)
        dets = veh["detections"]

        for tid in veh["newly_counted"]:
            db.log_vehicle_count(detector.track_types.get(tid, "motorcycle"))

        if dets:
            dets = rider_ctr.count_all(frame, dets)
            dets = helmet_det.check_all(frame, dets)

        for det in dets:
            tid = det.get("track_id")
            if tid is None or tid in violation_ids:
                continue
            viols = []
            if det.get("helmet_status") == "without_helmet":
                viols.append(VIOLATION_NO_HELMET)
            if det.get("is_triple_viol"):
                viols.append(VIOLATION_TRIPLE_RIDE)
            if viols:
                violation_ids.add(tid)
                snap = save_snapshot(frame, tid, "+".join(viols), SNAPSHOTS_DIR)
                for v in viols:
                    db.log_violation(track_id=tid, plate="UNKNOWN",
                                     vehicle_type=det.get("vehicle_type","motorcycle"),
                                     rider_count=det.get("rider_count",1),
                                     helmet_status=det.get("helmet_status","unknown"),
                                     violation_type=v, snapshot_path=snap,
                                     frame_number=frame_n)

        if not headless:
            detector.draw_trails(frame)
            detector.draw(frame, veh)
            pct = frame_n / total_f * 100 if total_f > 0 else 0
            cv2.putText(frame, f"{os.path.basename(path)}  {pct:.0f}%",
                        (10, FRAME_HEIGHT - 15), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 220, 255), 1)
            cv2.imshow("Day 30 — Batch Processing (Q=skip file)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    elapsed = time.time() - t_start
    proc_fps = frame_n / elapsed if elapsed > 0 else 0

    stats = {
        "file":       os.path.basename(path),
        "frames":     frame_n,
        "duration_s": round(duration, 1),
        "proc_fps":   round(proc_fps, 1),
        "vehicles":   len(detector.counted_ids),
        "violations": len(violation_ids),
    }
    log.info(f"Done: {stats}")
    detector.reset()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Day 30 — Batch Processing")
    parser.add_argument("--folder",   default="data/videos",
                        help="Folder containing video files")
    parser.add_argument("--headless", action="store_true",
                        help="No display window (for server use)")
    parser.add_argument("--resume",   action="store_true",
                        help="Skip already-processed files")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 30 — Batch Video Processing")
    print("=" * 65)

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"\n  Folder not found: {folder}")
        print("  Put .mp4 / .avi files there and re-run.")
        print("  Example: data/videos/clip1.mp4  data/videos/clip2.mp4")
        print("\n  Next → python day31_test.py  (Unit tests with pytest)")
        return

    exts = ("*.mp4","*.avi","*.mov","*.mkv","*.MP4","*.AVI")
    files = []
    for ext in exts:
        files.extend(glob.glob(os.path.join(folder, ext)))
    files = sorted(files)

    if not files:
        print(f"\n  No video files found in {folder}")
        print("  Next → python day31_test.py")
        return

    cp = load_checkpoint() if args.resume else {"processed": []}
    todo = [f for f in files if os.path.basename(f) not in cp["processed"]]

    print(f"\n  Found   : {len(files)} video file(s)")
    print(f"  To do   : {len(todo)} (resume={args.resume})")
    print(f"  Headless: {args.headless}")

    detector   = VehicleDetector()
    helmet_det = HelmetDetector()
    rider_ctr  = RiderCounter(method="overlap")
    db         = TrafficDB()
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    all_stats = []
    for i, fpath in enumerate(todo):
        print(f"\n  [{i+1}/{len(todo)}] {os.path.basename(fpath)}")
        stats = process_video(fpath, detector, helmet_det, rider_ctr, db, args.headless)
        if stats:
            all_stats.append(stats)
            cp["processed"].append(os.path.basename(fpath))
            save_checkpoint(cp)

    if not args.headless:
        cv2.destroyAllWindows()

    # ── Combined report ───────────────────────────────────────────────────────
    if all_stats:
        print("\n" + "=" * 65)
        print("  BATCH REPORT")
        print("=" * 65)
        print(f"  {'File':<30s} {'Frames':>7} {'FPS':>6} {'Vehicles':>9} {'Violations':>11}")
        print("  " + "-" * 65)
        tot_v = tot_viol = 0
        for s in all_stats:
            print(f"  {s['file']:<30s} {s['frames']:>7,} {s['proc_fps']:>6.1f}"
                  f" {s['vehicles']:>9} {s['violations']:>11}")
            tot_v    += s["vehicles"]
            tot_viol += s["violations"]
        print("  " + "─" * 65)
        print(f"  {'TOTAL':<30s} {'':>7} {'':>6} {tot_v:>9} {tot_viol:>11}")
        print(f"\n  DB total violations : {db.get_total_violations()}")
        print(f"  Checkpoint saved    : {CHECKPOINT_FILE}")

    print("\n  Next → python day31_test.py  (Unit tests with pytest)")


if __name__ == "__main__":
    main()
