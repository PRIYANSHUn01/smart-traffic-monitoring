# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 23 — day23_test.py
#  Topic: Snapshot gallery — browse, label, and export violation images
#
#  NEW today:
#    ✓ OpenCV gallery viewer: scroll through saved violation snapshots
#    ✓ Overlay violation metadata (plate, type, timestamp) on each image
#    ✓ Export contact sheet: combine multiple snapshots into one image
#    ✓ Link snapshot files back to their DB record
#
#  Run:  python day23_test.py            (gallery viewer)
#  Run:  python day23_test.py --sheet    (generate contact sheet PNG)
#  Run:  python day23_test.py --generate (create dummy snapshots for demo)
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, glob, argparse
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import draw_label
from config import SNAPSHOTS_DIR, LOGS_DIR

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)


def generate_dummy_snapshots(n=6):
    """Create coloured placeholder images so the gallery works without a camera."""
    colours = [(0,0,180),(0,120,0),(130,0,130),(0,100,100),(100,60,0),(60,0,180)]
    labels  = ["NO_HELMET","TRIPLE_RIDING","NO_HELMET","DOUBLE_RIDING","NO_HELMET","TRIPLE_RIDING"]
    paths   = []
    for i in range(n):
        img = np.full((240,320,3), colours[i%len(colours)], dtype=np.uint8)
        cv2.putText(img, f"Demo snap #{i+1}", (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
        cv2.putText(img, labels[i], (20,130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,0), 2)
        cv2.putText(img, f"UP14AB{1000+i*111}", (20,170),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,0), 1)
        p = os.path.join(SNAPSHOTS_DIR, f"dummy_snap_{i+1:02d}_{labels[i]}.jpg")
        cv2.imwrite(p, img)
        paths.append(p)
    print(f"  Created {n} dummy snapshots in {SNAPSHOTS_DIR}")
    return paths


def annotate_snapshot(img, meta):
    """Overlay plate + violation type on a snapshot."""
    h, w = img.shape[:2]
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h-60), (w, h), (0,0,0), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)
    cv2.putText(img, meta.get("plate",""), (8, h-36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,200,0), 1)
    vtype = meta.get("violation_type","")
    col   = (0,0,255) if "HELMET" in vtype else (0,100,255)
    cv2.putText(img, vtype, (8, h-12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1)
    return img


def gallery_viewer(snap_paths, meta_map):
    if not snap_paths:
        print("  No snapshots found — run with --generate first")
        return
    print(f"\n  Gallery: {len(snap_paths)} images  (any key=next, Q=quit, D=delete)\n")
    deleted = []
    for i, path in enumerate(snap_paths):
        img = cv2.imread(path)
        if img is None:
            continue
        img = cv2.resize(img, (640, 400))
        meta = meta_map.get(os.path.basename(path), {})
        img = annotate_snapshot(img, meta)
        cv2.putText(img, f"[{i+1}/{len(snap_paths)}] {os.path.basename(path)}",
                    (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200,200,200), 1)
        cv2.imshow("Day 23 — Snapshot Gallery (any key=next, Q=quit)", img)
        key = cv2.waitKey(0) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            deleted.append(path)
            print(f"  Marked for deletion: {os.path.basename(path)}")
    cv2.destroyAllWindows()
    if deleted:
        print(f"\n  {len(deleted)} image(s) marked for deletion.")
        print("  (Files not actually deleted — implement confirmation before removing)")


def make_contact_sheet(snap_paths, cols=3, thumb_size=(320,200)):
    if not snap_paths:
        return None
    thumbs = []
    for p in snap_paths[:12]:
        img = cv2.imread(p)
        if img is not None:
            thumbs.append(cv2.resize(img, thumb_size))
    if not thumbs:
        return None
    while len(thumbs) % cols != 0:
        thumbs.append(np.zeros((*thumb_size[::-1], 3), dtype=np.uint8))
    rows = [np.hstack(thumbs[i:i+cols]) for i in range(0, len(thumbs), cols)]
    sheet = np.vstack(rows)
    out_path = os.path.join(LOGS_DIR, "contact_sheet.jpg")
    cv2.imwrite(out_path, sheet)
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 23 — Snapshot Gallery")
    parser.add_argument("--sheet",    action="store_true", help="Generate contact sheet")
    parser.add_argument("--generate", action="store_true", help="Create dummy snapshots")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 23 — Snapshot Gallery Viewer")
    print("=" * 65)

    if args.generate:
        generate_dummy_snapshots(6)

    db = TrafficDB()
    violations = db.get_recent_violations(limit=200)
    meta_map   = {os.path.basename(v["snapshot_path"]): v
                  for v in violations if v.get("snapshot_path")}

    snap_paths = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.jpg")))
    print(f"\n  Found {len(snap_paths)} snapshots in {SNAPSHOTS_DIR}")
    print(f"  Matched {len(meta_map)} to DB records")

    if args.sheet:
        path = make_contact_sheet(snap_paths)
        if path:
            print(f"\n  Contact sheet saved: {path}")
            img = cv2.imread(path)
            if img is not None:
                cv2.imshow("Contact Sheet (any key to close)", img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
    else:
        gallery_viewer(snap_paths, meta_map)

    print("\n  Next → python day24_test.py  (CSV export + pandas analysis)")
