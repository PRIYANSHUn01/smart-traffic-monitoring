# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 17 — day17_test.py
#  Topic: Snapshot saver + optional email alert on violations
#
#  NEW today:
#    ✓ save_snapshot() called on every confirmed violation
#    ✓ Snapshot stored as  logs/snapshots/<timestamp>_id<N>_<type>.jpg
#    ✓ Optional Gmail email alert (ENABLE_EMAIL_ALERTS=True in config.py)
#    ✓ --show-snaps flag: pop up violation snapshot in a second window
#    ✓ Review mode: browse saved snapshots from past sessions
#
#  Run:  python day17_test.py
#  With video: python day17_test.py --source data/videos/traffic.mp4
#  Browse old snaps: python day17_test.py --review
#
#  Keys: Q=quit  R=reset  P=pause  S=force snapshot  T=trails
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse, smtplib, glob
from email.mime.text      import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image     import MIMEImage
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from modules.helmet_detector  import HelmetDetector
from modules.rider_counter    import RiderCounter
from utils.database           import TrafficDB
from utils.helpers            import get_logger, save_snapshot, put_stats_overlay
from config import (
    VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT, SNAPSHOTS_DIR,
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE,
    ENABLE_EMAIL_ALERTS, EMAIL_SENDER, EMAIL_RECIPIENT, EMAIL_APP_PASSWORD,
)

log = get_logger("day17")


# ── Email helper ──────────────────────────────────────────────────────────────
def send_violation_email(plate, viol_types, snap_path):
    """
    Send a Gmail alert with violation details and the snapshot image attached.
    Requires ENABLE_EMAIL_ALERTS=True and valid EMAIL_APP_PASSWORD in config.py.
    Gmail App Passwords: myaccount.google.com/apppasswords
    """
    if not ENABLE_EMAIL_ALERTS or not EMAIL_APP_PASSWORD:
        log.debug("Email alerts disabled or no password set — skip")
        return

    try:
        msg = MIMEMultipart()
        msg["Subject"] = f"[Traffic Alert] Violation detected — {plate}"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECIPIENT

        body = (
            f"Traffic Violation Detected\n\n"
            f"Plate     : {plate}\n"
            f"Violations: {', '.join(viol_types)}\n"
            f"Time      : {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Snapshot  : {snap_path}\n"
        )
        msg.attach(MIMEText(body))

        # Attach snapshot if it exists
        if snap_path and os.path.exists(snap_path):
            with open(snap_path, "rb") as f:
                img_data = f.read()
            img_part = MIMEImage(img_data, name=os.path.basename(snap_path))
            msg.attach(img_part)

        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            s.send_message(msg)
        log.info(f"Email sent to {EMAIL_RECIPIENT} for plate {plate}")

    except Exception as e:
        log.warning(f"Email send failed: {e}")


# ── Snapshot review mode ──────────────────────────────────────────────────────
def review_snapshots():
    """Browse all saved violation snapshots — any key to advance, Q to quit."""
    snaps = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.jpg")))
    if not snaps:
        print(f"\n  No snapshots found in {SNAPSHOTS_DIR}")
        print("  Run the pipeline first to generate violation snapshots.")
        return

    print(f"\n  Found {len(snaps)} snapshots — any key to advance, Q to quit\n")
    for i, path in enumerate(snaps):
        img = cv2.imread(path)
        if img is None:
            continue
        h, w = img.shape[:2]
        label = f"[{i+1}/{len(snaps)}]  {os.path.basename(path)}"
        cv2.putText(img, label, (10, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 255), 1)
        cv2.imshow("Day 17 — Snapshot Review (any key=next, Q=quit)", img)
        if cv2.waitKey(0) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
    print(f"  Review complete. {len(snaps)} snapshots total.")


# ── Live pipeline ─────────────────────────────────────────────────────────────
def run_live(src, show_snaps):
    print("=" * 65)
    print("  TRAFFIC MONITOR — DAY 17: SNAPSHOTS + EMAIL ALERTS")
    print("=" * 65)
    print(f"  Source        : {src}")
    print(f"  Snapshots dir : {SNAPSHOTS_DIR}")
    print(f"  Email alerts  : {'ON' if ENABLE_EMAIL_ALERTS else 'OFF (set ENABLE_EMAIL_ALERTS=True in config.py)'}")
    print(f"  Popup snaps   : {'ON' if show_snaps else 'OFF'}")
    print()
    print("  Keys: Q=quit  R=reset  P=pause  S=force snapshot  T=trails")
    print("=" * 65)

    vehicle_det   = VehicleDetector()
    helmet_det    = HelmetDetector()
    rider_ctr     = RiderCounter(method="overlap")
    db            = TrafficDB()
    violation_ids = set()

    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"\n  ✗ Cannot open: {src}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_n = 0; paused = False; show_trails = True
    fps_t = time.time(); fps_c = 0; fps = 0.0
    snap_count = 0

    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                if total_frames > 0:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    vehicle_det.reset(); frame_n = 0; continue
                else:
                    break
            frame_n += 1
            frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

            veh_result = vehicle_det.process_frame(frame, frame_n)
            detections = veh_result["detections"]
            for tid in veh_result["newly_counted"]:
                db.log_vehicle_count(vehicle_det.track_types.get(tid, "motorcycle"))

            detections = rider_ctr.count_all(frame, detections)
            detections = helmet_det.check_all(frame, detections)

            # ── Violation + snapshot + email ──────────────────────────────────
            for det in detections:
                tid = det.get("track_id")
                if tid is None or tid in violation_ids:
                    continue

                viols = []
                if det.get("helmet_status") == "without_helmet":
                    viols.append(VIOLATION_NO_HELMET)
                if det.get("is_triple_viol"):
                    viols.append(VIOLATION_TRIPLE_RIDE)

                if not viols:
                    continue

                violation_ids.add(tid)
                plate     = det.get("plate", "UNKNOWN")
                snap_path = save_snapshot(frame, tid, "+".join(viols), SNAPSHOTS_DIR)
                snap_count += 1

                log.warning(f"VIOLATION: {viols}  plate={plate}  snap={snap_path}")

                for v in viols:
                    db.log_violation(
                        track_id=tid, plate=plate,
                        vehicle_type=det.get("vehicle_type", "motorcycle"),
                        rider_count=det.get("rider_count", 1),
                        helmet_status=det.get("helmet_status", "unknown"),
                        violation_type=v, snapshot_path=snap_path,
                        frame_number=frame_n,
                    )

                # Email alert (if configured)
                send_violation_email(plate, viols, snap_path)

                # Pop-up snapshot window
                if show_snaps and os.path.exists(snap_path):
                    snap_img = cv2.imread(snap_path)
                    if snap_img is not None:
                        cv2.imshow(f"VIOLATION ID={tid}", snap_img)
                        cv2.waitKey(800)
                        cv2.destroyWindow(f"VIOLATION ID={tid}")

            # ── Draw ──────────────────────────────────────────────────────────
            if show_trails:
                vehicle_det.draw_trails(frame)
            vehicle_det.draw(frame, veh_result)
            rider_ctr.draw(frame, detections)
            helmet_det.draw(frame, detections)

            put_stats_overlay(frame, {
                "FPS":       f"{fps:.1f}",
                "Frame":     frame_n,
                "Vehicles":  veh_result["total_counted"],
                "Violations":len(violation_ids),
                "Snapshots": snap_count,
            })

            fps_c += 1
            if time.time() - fps_t >= 1.0:
                fps = fps_c / (time.time() - fps_t)
                fps_c = 0; fps_t = time.time()

        cv2.imshow("Day 17 — Snapshots + Alerts (Q/R/P/S/T)", frame) # type: ignore
        key = cv2.waitKey(0 if paused else 1) & 0xFF

        if   key == ord('q'): break
        elif key == ord('r'):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            vehicle_det.reset(); frame_n = 0
            violation_ids.clear(); snap_count = 0
            print("\n  ── RESET ──\n")
        elif key == ord('p'):
            paused = not paused
        elif key == ord('s'):
            p = save_snapshot(frame, 0, "manual", SNAPSHOTS_DIR) # type: ignore
            snap_count += 1
            print(f"  Manual snapshot: {p}")
        elif key == ord('t'):
            show_trails = not show_trails

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n  Snapshots saved : {snap_count}")
    print(f"  Located at      : {SNAPSHOTS_DIR}")
    print(f"  Violations in DB: {db.get_total_violations()}")
    print("  Next → python day18_test.py  (Performance benchmarking)")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 17 — Snapshots + Email Alerts")
    parser.add_argument("--source",     default=str(VIDEO_SOURCE))
    parser.add_argument("--show-snaps", action="store_true",
                        help="Pop up a window briefly when a snapshot is saved")
    parser.add_argument("--review",     action="store_true",
                        help="Browse previously saved snapshots and exit")
    args = parser.parse_args()

    if args.review:
        review_snapshots()
    else:
        src = int(args.source) if str(args.source).isdigit() else args.source
        run_live(src, args.show_snaps)
