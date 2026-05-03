# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 34 — day34_test.py
#  Topic: Edge cases — night video, rain/blur, heavy occlusion, crowd scenes
#
#  NEW today:
#    ✓ Simulate challenging conditions with OpenCV transforms
#    ✓ Test detection in low-light, rainy, and blurry conditions
#    ✓ Measure detection drop-off under each condition
#    ✓ Adaptive preprocessing: CLAHE, denoise for poor conditions
#
#  Run:  python day34_test.py
#  Run:  python day34_test.py --source data/videos/traffic.mp4
# ═══════════════════════════════════════════════════════════════════════════════

import cv2, sys, os, time, argparse
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.vehicle_detector import VehicleDetector
from utils.helpers            import put_stats_overlay
from config import VIDEO_SOURCE, FRAME_WIDTH, FRAME_HEIGHT


# ── Augmentation functions (simulate bad conditions) ─────────────────────────

def augment_night(frame, brightness=0.25):
    """Simulate night-time: darken + add slight blue tint."""
    dark = (frame.astype(np.float32) * brightness).clip(0, 255).astype(np.uint8)
    dark[:, :, 0] = np.clip(dark[:, :, 0].astype(int) + 15, 0, 255)  # blue channel
    return dark

def augment_rain(frame, intensity=0.4):
    """Simulate rain: diagonal streaks + reduced contrast."""
    result = frame.copy()
    h, w   = frame.shape[:2]
    for _ in range(int(intensity * 200)):
        x1 = np.random.randint(0, w)
        y1 = np.random.randint(0, h)
        length = np.random.randint(10, 30)
        x2 = min(x1 + length // 3, w - 1)
        y2 = min(y1 + length, h - 1)
        cv2.line(result, (x1, y1), (x2, y2), (200, 200, 210), 1)
    result = cv2.addWeighted(result, 0.85, np.full_like(result, 180), 0.15, 0)
    return result

def augment_blur(frame, ksize=21):
    """Simulate motion blur or foggy lens."""
    return cv2.GaussianBlur(frame, (ksize, ksize), 0)

def augment_glare(frame):
    """Simulate headlight glare: bright horizontal band."""
    result = frame.copy()
    h, w   = frame.shape[:2]
    y_c    = h // 2
    for dy in range(-30, 30):
        y = y_c + dy
        if 0 <= y < h:
            alpha = max(0, 1.0 - abs(dy) / 30.0) * 0.7
            cv2.line(result, (0, y), (w, y), (255, 255, 200), 1)
    result = cv2.addWeighted(result, 1 - 0.3, frame, 0.3, 0)
    return result


# ── Adaptive preprocessing ────────────────────────────────────────────────────

def preprocess_night(frame):
    """Enhance dark frames with CLAHE before detection."""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

def preprocess_rain(frame):
    """Denoise and sharpen rain-affected frames."""
    denoised = cv2.fastNlMeansDenoisingColored(frame, h=10, hColor=10)
    kernel   = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return cv2.filter2D(denoised, -1, kernel)


# ── Test runner ───────────────────────────────────────────────────────────────

CONDITIONS = [
    ("Normal",   lambda f: f,               None),
    ("Night",    augment_night,             preprocess_night),
    ("Rain",     augment_rain,              preprocess_rain),
    ("Blur",     augment_blur,              None),
    ("Glare",    augment_glare,             None),
]


def run_condition_test(src):
    detector = VehicleDetector()
    cap      = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"  ✗ Cannot open: {src}")
        return

    total      = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cond_idx   = 0
    frame_n    = 0
    cond_name, aug_fn, pre_fn = CONDITIONS[cond_idx]
    det_counts = {c[0]: [] for c in CONDITIONS}
    frames_per_cond = max(30, total // len(CONDITIONS))

    print("  Switching condition every ~30 frames. Watch detection change.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0); frame_n = 0; continue
        frame_n += 1
        frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))

        # Switch condition
        if frame_n % frames_per_cond == 1:
            cond_idx = (frame_n // frames_per_cond) % len(CONDITIONS)
            cond_name, aug_fn, pre_fn = CONDITIONS[cond_idx]

        # Apply augmentation
        aug_frame = aug_fn(frame)

        # Apply preprocessing (if available)
        proc_frame = pre_fn(aug_frame) if pre_fn else aug_frame

        result = detector.process_frame(proc_frame, frame_n)
        n_dets = len(result["detections"])
        det_counts[cond_name].append(n_dets)

        # Show both: augmented (left) and processed (right)
        side_by_side = np.hstack([
            cv2.resize(aug_frame,  (FRAME_WIDTH // 2, FRAME_HEIGHT)),
            cv2.resize(proc_frame, (FRAME_WIDTH // 2, FRAME_HEIGHT)),
        ])
        cv2.putText(side_by_side, f"Condition: {cond_name}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2)
        cv2.putText(side_by_side, f"Detections: {n_dets}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
        cv2.putText(side_by_side, "Augmented",
                    (10, FRAME_HEIGHT - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        cv2.putText(side_by_side, "Preprocessed",
                    (FRAME_WIDTH // 2 + 10, FRAME_HEIGHT - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        cv2.imshow("Day 34 — Edge Cases (Q to quit)", side_by_side)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release(); cv2.destroyAllWindows()

    print("\n  ── DETECTION DROP-OFF BY CONDITION ─────────────────────────")
    baseline = sum(det_counts["Normal"]) / max(1, len(det_counts["Normal"]))
    for cname, counts in det_counts.items():
        if not counts:
            continue
        avg = sum(counts) / len(counts)
        drop = (1 - avg / baseline) * 100 if baseline > 0 else 0
        bar  = "▓" * int(avg * 2)
        sign = "-" if drop > 0 else "+"
        print(f"  {cname:<10s}: avg={avg:.1f} dets  "
              f"({sign}{abs(drop):.0f}% vs normal)  {bar}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 34 — Edge Cases")
    parser.add_argument("--source", default=str(VIDEO_SOURCE))
    args = parser.parse_args()
    src  = int(args.source) if str(args.source).isdigit() else args.source

    print("=" * 65)
    print("  DAY 34 — Edge Cases: Night / Rain / Blur / Glare")
    print("=" * 65)
    print(f"  Source: {src}")
    print("  Left half: augmented condition | Right half: preprocessed")
    print("  Keys: Q=quit")
    print("=" * 65)
    run_condition_test(src)
    print("\n  Next → python day35_test.py  (Memory + CPU profiling)")
