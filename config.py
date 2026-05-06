# ─────────────────────────────────────────────────
# config.py  —  Central settings for entire project
# Change these values to match your setup
# ─────────────────────────────────────────────────

import os

# ── Paths ────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR     = os.path.join(BASE_DIR, "models")
DATA_DIR       = os.path.join(BASE_DIR, "data")
SNAPSHOTS_DIR  = os.path.join(DATA_DIR, "snapshots")
LOGS_DIR       = os.path.join(BASE_DIR, "logs")
DB_PATH        = os.path.join(LOGS_DIR, "traffic.db")
CSV_LOG_PATH   = os.path.join(LOGS_DIR, "violations.csv")

# ── Model Paths ──────────────────────────────────
# vehicle_detector.pt = custom-trained, class 0: "two-wheeler"
VEHICLE_MODEL    = os.path.join(MODELS_DIR, "vehicle_detector.pt")
HELMET_MODEL     = os.path.join(MODELS_DIR, "helmet_detect.pt")
PLATE_MODEL      = os.path.join(MODELS_DIR, "plate_detect.pt")

# If custom models not found, fallback to pretrained COCO
FALLBACK_MODEL   = "yolov8n.pt"    # downloads automatically

# ── Custom Model Flag ────────────────────────────
# True  → vehicle_detector.pt  (class 0 = "two-wheeler")
# False → COCO pretrained       (class 1 = bicycle, 3 = motorcycle)
USING_CUSTOM_VEHICLE_MODEL = os.path.exists(
    os.path.join(MODELS_DIR, "vehicle_detector.pt")
)

# ── Video Source ─────────────────────────────────
# 0 = webcam, or path to video file
# VIDEO_SOURCE     = 0
VIDEO_SOURCE   = "data/videos/traffic.mp4"

# ── Detection Settings ───────────────────────────
CONFIDENCE_THRESHOLD  = 0.45   # min confidence to accept detection
NMS_IOU_THRESHOLD     = 0.45   # overlap threshold for NMS
INPUT_SIZE            = 640    # YOLO input resolution (640 or 416)
SKIP_FRAMES           = 2      # run YOLO every N frames (1 = every frame)

# ── Counting Line ────────────────────────────────
# Horizontal line at this Y-position (fraction of frame height)
# 0.5 = middle of frame, 0.6 = slightly below middle
COUNT_LINE_POSITION   = 0.55   # fraction of frame height

# ── Vehicle Classes ───────────────────────────────
# Custom model:  class 0 = "two-wheeler"
# COCO fallback: class 1 = bicycle, class 3 = motorcycle
if USING_CUSTOM_VEHICLE_MODEL:
    VEHICLE_CLASS_IDS  = {0: "two-wheeler"}
    TWO_WHEELER_IDS    = [0]
    TWO_WHEELER_LABELS = {0: "two-wheeler"}
else:
    VEHICLE_CLASS_IDS  = {3: "motorcycle", 1: "bicycle"}
    TWO_WHEELER_IDS    = [1, 3]
    TWO_WHEELER_LABELS = {1: "bicycle", 3: "motorcycle"}

# ── Rider Detection ──────────────────────────────
RIDER_OVERLAP_THRESHOLD = 0.30  # person box must overlap bike box by this much
RIDER_LABELS = {
    0: "No rider",
    1: "Solo",
    2: "Double",
    3: "Triple+",
}
RIDER_COLORS = {
    1: (0, 200, 0),     # green — solo
    2: (0, 165, 255),   # orange — double
    3: (0, 0, 255),     # red — triple
}

# ── Helmet Detection ─────────────────────────────
HELMET_CLASS_NAMES = ["with_helmet", "without_helmet"]
HELMET_HEAD_CROP_RATIO = 0.40   # top 40% of bike box = head region
HELMET_CONFIDENCE     = 0.40

# ── OCR Settings ─────────────────────────────────
OCR_LANGUAGES       = ["en"]
OCR_MIN_CONFIDENCE  = 0.50
PLATE_VOTE_FRAMES   = 10        # collect this many readings before picking best

# ── Violation Types ──────────────────────────────
VIOLATION_NO_HELMET   = "NO_HELMET"
VIOLATION_TRIPLE_RIDE = "TRIPLE_RIDING"
VIOLATION_DOUBLE_RIDE = "DOUBLE_RIDING"   # optional — enable below
ENABLE_DOUBLE_WARNING = False             # set True to flag double riders too

# ── Display Settings ─────────────────────────────
SHOW_TRACK_IDS    = True
SHOW_CONFIDENCE   = True
SHOW_PLATE_TEXT   = True
SHOW_RIDER_COUNT  = True
SHOW_TRAILS       = True     # draw fading motion trails behind vehicles
SHOW_COUNT_LINE   = True     # draw the horizontal counting line
TRAIL_LENGTH      = 30       # max trail points kept per vehicle
FRAME_WIDTH       = 1280    # resize display window
FRAME_HEIGHT      = 720

# ── Dashboard ────────────────────────────────────
DASHBOARD_PORT    = 8501
DASHBOARD_TITLE   = "Traffic Monitoring System"
REFRESH_RATE_MS   = 300    # dashboard refresh interval

# ── Alerts (Email) ───────────────────────────────
ENABLE_EMAIL_ALERTS = False
EMAIL_SENDER        = "your_email@gmail.com"
EMAIL_RECIPIENT     = "officer@dept.gov.in"
EMAIL_APP_PASSWORD  = ""   # use Gmail App Password, NOT your real password

# ── Logging ──────────────────────────────────────
LOG_LEVEL    = "INFO"   # DEBUG / INFO / WARNING / ERROR
SAVE_FRAMES  = True     # save snapshot image on each violation


# ── Auto-create required directories ─────────────
VIDEOS_DIR = os.path.join(DATA_DIR, "videos")
for _dir in [MODELS_DIR, SNAPSHOTS_DIR, LOGS_DIR, VIDEOS_DIR]:
    os.makedirs(_dir, exist_ok=True)
