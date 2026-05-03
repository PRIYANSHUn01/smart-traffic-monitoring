# tests/test_setup.py — Run this to verify your full installation
# python tests/test_setup.py

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "="*60)
print("  Traffic Monitor — Setup Verification (Days 1-10)")
print("="*60 + "\n")

errors = []

def chk(n, label, fn):
    try:
        fn()
        print(f"  [{n:2d}] ✓  {label}")
    except Exception as e:
        errors.append(f"[{n}] {label}: {e}")
        print(f"  [{n:2d}] ✗  {label}  → {e}")

chk(1,  "Python 3.10+",        lambda: __import__('sys') and sys.version_info >= (3,10) or (_ for _ in ()).throw(Exception("Need 3.10+")))
chk(2,  "OpenCV",              lambda: __import__('cv2'))
chk(3,  "NumPy",               lambda: __import__('numpy'))
chk(4,  "Matplotlib",          lambda: __import__('matplotlib'))
chk(5,  "PyYAML",              lambda: __import__('yaml'))
chk(6,  "tqdm",                lambda: __import__('tqdm'))
chk(7,  "Ultralytics (YOLOv8)",lambda: __import__('ultralytics'))
chk(8,  "PyTorch + CUDA check",lambda: __import__('torch') and print(f"       CUDA: {__import__('torch').cuda.is_available()}") or True)
chk(9,  "EasyOCR",             lambda: __import__('easyocr'))
chk(10, "Streamlit",           lambda: __import__('streamlit'))
chk(11, "Plotly",              lambda: __import__('plotly'))
chk(12, "Pandas",              lambda: __import__('pandas'))
chk(13, "config.py imports",   lambda: __import__('config') and __import__('config').TWO_WHEELER_IDS == {1,3})
chk(14, "VehicleDetector import", lambda: __import__('modules.vehicle_detector', fromlist=['VehicleDetector']))
chk(15, "utils/helpers.py",    lambda: __import__('utils.helpers', fromlist=['compute_iou']))

print("\n" + "="*60)
if errors:
    print(f"  ✗ {len(errors)} issue(s) — fix before running practice files:\n")
    for e in errors: print(f"    {e}")
    print("\n  Install missing: pip install -r requirements.txt")
else:
    print("  ✓ All checks passed!  Run:")
    print("    python day01_practice.py    ← start here")
    print("    python day10_test.py        ← run everything")
print("="*60 + "\n")
