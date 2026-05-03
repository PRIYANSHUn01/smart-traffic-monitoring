# train_helmet.py — Run after downloading helmet dataset
# Usage: python train_helmet.py


from ultralytics import YOLO
import os

model = YOLO("yolov8s.pt")

results = model.train(
    data="data/datasets/helmet/data.yaml",
    epochs=50,
    imgsz=640,
    batch=8,
    name="helmet_v1",
    patience=15,     # stop early if no improvement after 15 epochs
    save=True,
    plots=True,      # saves training charts to runs/ folder
)

# Evaluate on validation set
metrics = model.val()
print(f"Validation mAP50: {metrics.box.map50:.4f}")
print(f"Precision:        {metrics.box.mp:.4f}")
print(f"Recall:           {metrics.box.mr:.4f}")

# Copy best model to models/ folder
import shutil
shutil.copy("runs/detect/helmet_v1/weights/best.pt",
            "models/helmet_detect.pt")
print("✓ Model saved to models/helmet_detect.pt")
