# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 2 — day02_practice.py
#  Topics: images as arrays, pixel manipulation, blur, threshold, Canny edges,
#          morphological operations — all used in helmet/plate preprocessing
#  Run: python day02_practice.py
# ═══════════════════════════════════════════════════════════════════════════════


import cv2
import numpy as np

print("=" * 55)
print("  DAY 2 — NumPy & Image Processing")
print("=" * 55)

# ── PART 1: Images ARE arrays ─────────────────────────────────────────────────
print("\n[Part 1] Image = NumPy array")

img = np.zeros((300, 400, 3), dtype=np.uint8)
print(f"  Shape : {img.shape}  (Height, Width, Channels)")
print(f"  Dtype : {img.dtype}  (uint8 = values 0-255)")

# Set regions by slicing — EXACTLY how helmet_detector.py crops head regions
img[50:150, 50:200]  = [0, 0, 255]    # red rectangle
img[50:150, 210:360] = [0, 255, 0]    # green rectangle
img[160:260, 50:200] = [255, 0, 0]    # blue rectangle

# Read a single pixel
print(f"  Pixel at (100,100): {img[100, 100]}  (B=0, G=0, R=255 = red)")

cv2.imshow("Day 2 Part 1 — Pixel array (press any key)", img)
cv2.waitKey(2000); cv2.destroyAllWindows()
print("  ✓ Array slicing = the same operation as helmet ROI cropping")

# ── PART 2: Gaussian blur ─────────────────────────────────────────────────────
print("\n[Part 2] Gaussian blur — removes noise before edge detection")

noisy = img.copy()
noise = np.random.randint(0, 35, img.shape, dtype=np.uint8)
noisy = cv2.add(noisy, noise)

blurred = cv2.GaussianBlur(noisy, (5, 5), 0)
cv2.imshow("Day 2 Part 2 — Noisy | Blurred (press any key)",
           np.hstack([noisy, blurred]))
cv2.waitKey(2000); cv2.destroyAllWindows()
print("  ✓ (5,5) kernel removes noise without losing shape detail")

# ── PART 3: Thresholding ──────────────────────────────────────────────────────
print("\n[Part 3] Otsu threshold — used in license plate OCR preprocessing")

gradient = np.tile(np.linspace(0, 255, 400, dtype=np.uint8), (200, 1))
_, binary = cv2.threshold(gradient, 127, 255, cv2.THRESH_BINARY)
ret, otsu = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
print(f"  Otsu auto-selected threshold: {ret}")

cv2.imshow("Day 2 Part 3 — Gradient | Binary | Otsu (press any key)",
           np.vstack([cv2.cvtColor(gradient, cv2.COLOR_GRAY2BGR),
                      cv2.cvtColor(binary,   cv2.COLOR_GRAY2BGR),
                      cv2.cvtColor(otsu,     cv2.COLOR_GRAY2BGR)]))
cv2.waitKey(2000); cv2.destroyAllWindows()
print("  ✓ Otsu threshold is used in plate_reader.py to isolate plate characters")

# ── PART 4: Canny edge detection ──────────────────────────────────────────────
print("\n[Part 4] Canny edges — finds object boundaries")

shapes = np.zeros((300, 500, 3), dtype=np.uint8)
cv2.rectangle(shapes, (50, 50), (200, 200), (180, 180, 180), -1)
cv2.circle(shapes, (370, 130), 80, (160, 160, 160), -1)

gray    = cv2.cvtColor(shapes, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edges   = cv2.Canny(blurred, 50, 150)

output = shapes.copy()
output[edges > 0] = [0, 255, 0]  # overlay edges in green

cv2.imshow("Day 2 Part 4 — Edges (press any key)", output)
cv2.waitKey(2000); cv2.destroyAllWindows()
print("  ✓ Canny edges used for license plate region detection")

# ── PART 5: Morphological operations ─────────────────────────────────────────
print("\n[Part 5] Morphology — clean binary masks")

mask = np.zeros((200, 400), dtype=np.uint8)
cv2.rectangle(mask, (50, 50), (200, 150), 255, -1)
np.random.seed(42)
npts = np.random.randint(0, 200, (30, 2))
for pt in npts:
    mask[pt[0] % 200, pt[1] % 400] = 255

kernel = np.ones((5, 5), np.uint8)
opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # removes noise dots
closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # fills gaps

cv2.imshow("Day 2 Part 5 — Original | Opened | Closed (press any key)",
           cv2.cvtColor(np.hstack([mask, opened, closed]), cv2.COLOR_GRAY2BGR))
cv2.waitKey(2000); cv2.destroyAllWindows()
print("  ✓ Opening removes noise, Closing fills gaps")

# ── PART 6: LIVE pipeline on webcam ──────────────────────────────────────────
print("\n[Part 6] Live pipeline: Gray → Blur → Threshold → Canny (Q to quit, 8s auto)")

cap = cv2.VideoCapture(0)
use_cam = cap.isOpened()
import time; start = time.time()

while True:
    if use_cam:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.resize(frame, (640, 480))
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        x = (int(time.time() * 60)) % 640
        cv2.rectangle(frame, (x-40, 160), (x+40, 320), (100, 100, 100), -1)

    gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur    = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thr  = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges   = cv2.Canny(blur, 50, 150)

    thr_3  = cv2.cvtColor(thr,   cv2.COLOR_GRAY2BGR)
    edge_3 = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    top    = np.hstack([frame, thr_3])
    bot    = np.hstack([edge_3, edge_3])
    grid   = cv2.resize(np.vstack([top, bot]), (1280, 720))

    for i, lbl in enumerate(["Original", "Otsu Thresh", "Canny Edges", "Canny Edges"]):
        r, c = divmod(i, 2)
        cv2.putText(grid, lbl, (c * 640 + 10, r * 360 + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow("Day 2 Part 6 — Live Pipeline (Q to quit)", grid)
    if cv2.waitKey(1) & 0xFF == ord('q') or time.time()-start > 8:
        break

cap.release(); cv2.destroyAllWindows()

print("\n" + "=" * 55)
print("  DAY 2 COMPLETE")
print("  ✓ Images are NumPy arrays — slicing = cropping")
print("  ✓ Blur → Threshold → Canny pipeline built")
print("  ✓ These operations used in helmet & plate modules")
print("  Next: python day03_practice.py")
print("=" * 55)
