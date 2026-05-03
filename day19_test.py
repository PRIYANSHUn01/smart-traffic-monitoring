# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 19 — day19_test.py
#  Topic: Streamlit dashboard intro — page layout, metrics, sidebar
#
#  Phase 3 starts here.  The detection engine is done; now we make it visible.
#
#  NEW today:
#    ✓ Understand Streamlit page structure (columns, sidebar, metrics)
#    ✓ Load violation data from TrafficDB into a DataFrame
#    ✓ Display summary KPI cards (total vehicles, violations, rate)
#    ✓ Run the dashboard alongside the pipeline in a separate terminal
#
#  To run the dashboard:
#      streamlit run dashboard/app.py
#
#  To run pipeline at the same time (separate terminal):
#      python pipeline.py --source data/videos/traffic.mp4
#
#  This script is a self-contained Streamlit demo that checks your
#  Streamlit installation and shows you the dashboard layout.
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── Check Streamlit is installed ──────────────────────────────────────────────
try:
    import streamlit as st
    print("  ✓ Streamlit installed:", st.__version__)
except ImportError:
    print("  ✗ Streamlit not found — install it:")
    print("    pip install streamlit plotly pandas Pillow")
    sys.exit(1)

try:
    import plotly.express as px
    print("  ✓ Plotly installed")
except ImportError:
    print("  ✗ Plotly not found: pip install plotly")

try:
    import pandas as pd
    print("  ✓ Pandas installed")
except ImportError:
    print("  ✗ Pandas not found: pip install pandas")

from utils.database import TrafficDB
from config import DB_PATH, CSV_LOG_PATH, SNAPSHOTS_DIR

# ── Quick terminal preview of what the dashboard will show ────────────────────
print("\n" + "=" * 65)
print("  DAY 19 — Dashboard Setup Check")
print("=" * 65)

db = TrafficDB()

total_v    = db.get_total_vehicles()
total_viol = db.get_total_violations()
breakdown  = db.get_violation_breakdown()
vtype_cts  = db.get_vehicle_type_counts()
recent     = db.get_recent_violations(limit=5)

print(f"\n  Database        : {DB_PATH}")
print(f"  Total vehicles  : {total_v}")
print(f"  Total violations: {total_viol}")
print(f"  Breakdown       : {breakdown}")
print(f"  Vehicle types   : {vtype_cts}")
print(f"\n  Recent violations (last 5):")
for r in recent:
    print(f"    [{r['id']:3d}] {r['timestamp']}  {r['violation_type']:<18s}  plate={r['plate_number']}")

print()
print("  Dashboard file  : dashboard/app.py")
print()
print("  ── HOW TO START THE DASHBOARD ──────────────────────────────")
print("  Terminal 1 (pipeline):   python pipeline.py")
print("  Terminal 2 (dashboard):  streamlit run dashboard/app.py")
print("  Then open               http://localhost:8501")
print()
print("  The dashboard auto-refreshes every 3 seconds.")
print("  You will see violations appear in real-time as the pipeline runs.")
print()
print("  ── STREAMLIT QUICK REFERENCE ───────────────────────────────")
print("""
  st.metric("label", value)           → KPI card
  st.columns([1,1,1])                 → side-by-side columns
  st.dataframe(df)                    → scrollable table
  st.plotly_chart(fig)                → interactive chart
  st.sidebar.checkbox("...")          → sidebar widget
  st.rerun()                          → refresh page
  @st.cache_resource                  → cache expensive objects
""")
print("  Next → python day20_test.py  (Live data + chart wiring)")
print("=" * 65)
