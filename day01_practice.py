# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 1 — day01_practice.py
#  Topics: Python setup, OpenCV install, read video, draw shapes, write text
#  Run: python day01_practice.py
# ═══════════════════════════════════════════════════════════════════════════════

import cv2
import numpy as np
import sys

print("=" * 55)
print("  DAY 1 — OpenCV Basics")
print("=" * 55)

# ── PART 1: Create a canvas and draw shapes ───────────────────────────────────
print("\n[Part 1] Drawing shapes on a blank canvas...")

canvas = np.zeros((480, 640, 3), dtype=np.uint8)

# Draw shapes — colours are BGR (Blue, Green, Red) NOT RGB
cv2.rectangle(canvas, (50, 50),  (200, 150), (0, 255, 0),   2)   # green rect
cv2.rectangle(canvas, (250, 50), (400, 150), (255, 100, 0), -1)  # filled blue
cv2.circle(canvas,   (320, 300), 80,         (0, 100, 255),  3)  # orange circle
cv2.line(canvas,     (0, 400),   (640, 400), (200, 200, 200), 1) # grey line
cv2.putText(canvas, "Day 1: OpenCV Basics",
            (60, 430), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

cv2.imshow("Day 1 Part 1 — Canvas (press any key)", canvas)
cv2.waitKey(2500)
cv2.destroyAllWindows()
print("  ✓ Canvas displayed — shapes drawn correctly")

# ── PART 2: Colour spaces ────────────────────────────────────────────────────
print("\n[Part 2] Colour space conversions...")

img = np.zeros((200, 400, 3), dtype=np.uint8)
img[:, :200]  = [0, 0, 255]   # red   (BGR)
img[:, 200:]  = [0, 255, 0]   # green (BGR)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

print(f"  Original shape : {img.shape}   (H, W, Channels)")
print(f"  Grayscale shape: {gray.shape}    (H, W — one channel)")
print(f"  HSV shape      : {hsv.shape}   (same size, different meaning)")

gray3 = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
combined = np.hstack([img, gray3])
cv2.imshow("Day 1 Part 2 — BGR vs Grayscale (press any key)", combined)
cv2.waitKey(2500)
cv2.destroyAllWindows()
print("  ✓ Colour conversions work")

# ── PART 3: Live video loop ───────────────────────────────────────────────────
print("\n[Part 3] Video capture loop — press Q to quit (auto-closes after 8s)...")

cap = cv2.VideoCapture(0)
use_cam = cap.isOpened()
if not use_cam:
    print("  ℹ  No webcam — using synthetic moving scene")

import time
frame_count = 0
start = time.time()

while True:
    frame_count += 1

    if use_cam:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x = (frame_count * 4) % 640
        cv2.circle(frame, (x, 240), 25, (0, 200, 255), -1)

    # Draw counting line — this exact pattern is used in Day 10!
    cv2.line(frame, (0, 280), (640, 280), (0, 0, 255), 2)
    cv2.putText(frame, "Count Line (used in Day 10)", (10, 268),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

    # Stats
    elapsed = time.time() - start
    fps = frame_count / elapsed if elapsed > 0 else 0
    cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Day 1 Part 3 — Video Loop (Q to quit)", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or elapsed > 8:
        break

cap.release()
cv2.destroyAllWindows()

print(f"  ✓ Video loop: {frame_count} frames at {fps:.1f} FPS") # type: ignore
print("\n" + "=" * 55)
print("  DAY 1 COMPLETE")
print("  ✓ Can draw shapes on frames")
print("  ✓ Can convert colour spaces")
print("  ✓ Can run a video capture loop")
print("  Next: python day02_practice.py")
print("=" * 55)
