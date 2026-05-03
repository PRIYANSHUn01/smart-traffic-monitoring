# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 33 — day33_test.py
#  Topic: Model accuracy benchmarking — precision, recall, mAP basics
#
#  NEW today:
#    ✓ Run model.val() to get mAP50, precision, recall on a dataset
#    ✓ Confusion matrix: what the model gets right vs wrong
#    ✓ Speed benchmark: inference time vs accuracy tradeoff
#    ✓ Compare yolov8n vs yolov8s vs yolov8m for this task
#
#  Run:  python day33_test.py               (uses pretrained yolov8n)
#  Run:  python day33_test.py --val         (needs dataset in data/datasets/)
#  Run:  python day33_test.py --compare     (n vs s vs m speed comparison)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_logger
log = get_logger("day33")


def inference_speed_test(model_name, num_runs=50, input_size=640):
    """Measure average inference time for a model on a blank frame."""
    import numpy as np
    from ultralytics import YOLO
    print(f"\n  Loading {model_name}…", end=" ", flush=True)
    t0    = time.time()
    model = YOLO(model_name)
    print(f"loaded in {time.time()-t0:.1f}s")

    frame = (np.random.rand(input_size, input_size, 3) * 255).astype("uint8")

    # Warm-up
    for _ in range(3):
        model(frame, verbose=False, classes=[1, 3])

    times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        model(frame, verbose=False, classes=[1, 3])
        times.append(time.perf_counter() - t0)

    avg_ms  = sum(times) / len(times) * 1000
    min_ms  = min(times) * 1000
    max_ms  = max(times) * 1000
    fps     = 1000 / avg_ms
    return {"model": model_name, "avg_ms": avg_ms, "min_ms": min_ms,
            "max_ms": max_ms, "fps": fps}


def run_validation(model_path, data_yaml):
    """Run model.val() and print mAP metrics."""
    from ultralytics import YOLO
    if not os.path.exists(model_path):
        print(f"  Model not found: {model_path}")
        return
    if not os.path.exists(data_yaml):
        print(f"  Dataset YAML not found: {data_yaml}")
        print("  Download a dataset from roboflow.com first")
        return

    print(f"\n  Running validation: {model_path}")
    model   = YOLO(model_path)
    metrics = model.val(data=data_yaml, verbose=False)
    print(f"\n  mAP50    : {metrics.box.map50:.4f}")
    print(f"  mAP50-95 : {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall   : {metrics.box.mr:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Day 33 — Model Accuracy")
    parser.add_argument("--val",     action="store_true",
                        help="Run model.val() (needs dataset)")
    parser.add_argument("--compare", action="store_true",
                        help="Speed comparison: n vs s vs m")
    parser.add_argument("--model",   default="models/vehicle_detect.pt")
    parser.add_argument("--data",    default="data/datasets/vehicles/data.yaml")
    parser.add_argument("--runs",    type=int, default=30)
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 33 — Model Accuracy Benchmarking")
    print("=" * 65)

    if args.compare:
        print("\n  Speed comparison: yolov8n vs yolov8s vs yolov8m")
        print("  (downloads models on first run)")
        print(f"  Runs per model: {args.runs}\n")
        results = []
        for name in ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]:
            r = inference_speed_test(name, num_runs=args.runs)
            results.append(r)

        print("\n  ┌─────────────────────────────────────────────────────────┐")
        print("  │ Model      │ avg ms │ min ms │ max ms │  FPS   │ Size  │")
        print("  ├────────────┼────────┼────────┼────────┼────────┼───────┤")
        sizes = {"yolov8n.pt": "6 MB", "yolov8s.pt": "22 MB", "yolov8m.pt": "52 MB"}
        for r in results:
            nm = r["model"].replace(".pt","")
            sz = sizes.get(r["model"], "?")
            print(f"  │ {nm:<10s} │ {r['avg_ms']:6.1f} │ {r['min_ms']:6.1f} │"
                  f" {r['max_ms']:6.1f} │ {r['fps']:6.1f} │ {sz:<5s} │")
        print("  └─────────────────────────────────────────────────────────┘")
        print("\n  Recommendation:")
        print("  ├─ yolov8n: fastest, use when SKIP_FRAMES=1 needed")
        print("  ├─ yolov8s: good balance — recommended for this project")
        print("  └─ yolov8m: most accurate, use when FPS > 15 is acceptable")

    elif args.val:
        run_validation(args.model, args.data)

    else:
        # Default: single speed test + explanation
        r = inference_speed_test("yolov8n.pt", num_runs=args.runs)
        print(f"\n  yolov8n speed: {r['avg_ms']:.1f}ms avg  ({r['fps']:.1f} FPS)")

    print("\n  ── METRICS GLOSSARY ─────────────────────────────────────────")
    print("""
  Precision  = TP / (TP + FP)   → of all detections, how many were real?
  Recall     = TP / (TP + FN)   → of all real objects, how many did we find?
  mAP50      = mean Average Precision at IoU threshold 0.50
  mAP50-95   = mAP averaged over IoU thresholds 0.50 to 0.95 (stricter)

  For this project:
    Recall   > 0.85 is essential  (miss few real violations)
    Precision> 0.80 is good       (false positives annoy officers)
    mAP50    > 0.80 is production-ready
""")
    print("  Next → python day34_test.py  (Edge cases: night, rain, occlusion)")


if __name__ == "__main__":
    main()
