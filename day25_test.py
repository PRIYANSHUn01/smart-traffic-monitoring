# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 25 — day25_test.py
#  Topic: Dashboard auto-refresh + real-time mode — st.rerun() and polling
#
#  NEW today:
#    ✓ Understand why st.rerun() makes the dashboard "live"
#    ✓ Measure dashboard latency (pipeline write → dashboard display)
#    ✓ Control refresh rate (REFRESH_RATE_MS in config.py)
#    ✓ Demo: write 1 violation per second, confirm dashboard updates
#    ✓ Phase 3 checkpoint: dashboard is fully wired and operational
#
#  Run:  python day25_test.py        (latency demo — inject + timestamp)
#  Open: streamlit run dashboard/app.py  (watch it update)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger, now_iso
from config import (
    VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE, REFRESH_RATE_MS,
    DB_PATH, DASHBOARD_PORT,
)

log = get_logger("day25")


def latency_demo(db, n=10, interval=2.0):
    """
    Write a violation every `interval` seconds.
    Measure the gap between the write time and when the dashboard WOULD refresh.
    Dashboard refresh cycle = REFRESH_RATE_MS / 1000 seconds.
    """
    refresh_s = REFRESH_RATE_MS / 1000
    print(f"\n  Dashboard refresh rate : {REFRESH_RATE_MS} ms  ({refresh_s:.1f}s)")
    print(f"  Write interval         : {interval}s")
    print(f"  Max latency (approx)   : {refresh_s:.1f}s")
    print()
    print("  ── INJECTING VIOLATIONS ─────────────────────────────────────")
    print("  Open  http://localhost:8501  and watch the KPI cards update\n")

    import random
    plates = ["UP14AB1234","DL3CAB5678","MH12NM3456","KA01AB9999"]

    for i in range(n):
        write_ts = time.time()
        plate    = random.choice(plates)
        viol     = random.choice([VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE])
        db.log_vehicle_count("motorcycle")
        db.log_violation(
            track_id      = 900 + i,
            plate         = plate,
            vehicle_type  = "motorcycle",
            rider_count   = 3 if viol == VIOLATION_TRIPLE_RIDE else 1,
            helmet_status = "without_helmet" if viol == VIOLATION_NO_HELMET else "with_helmet",
            violation_type= viol,
            snapshot_path = "",
            frame_number  = i * 60,
        )
        next_refresh = refresh_s - (time.time() - write_ts) % refresh_s
        print(f"  [{i+1:2d}] {now_iso()}  {viol:<18s}  "
              f"plate={plate}  dashboard update in ~{next_refresh:.1f}s")
        time.sleep(interval)

    print(f"\n  Done. Total violations in DB: {db.get_total_violations()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 25 — Dashboard Real-Time")
    parser.add_argument("--n",        type=int,   default=10)
    parser.add_argument("--interval", type=float, default=2.0,
                        help="Seconds between each injected violation")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 25 — Dashboard Auto-Refresh + Real-Time")
    print("=" * 65)
    print()
    print("  HOW st.rerun() WORKS:")
    print("""
  At the bottom of dashboard/app.py:
      if auto_refresh:
          time.sleep(3)
          st.rerun()

  This re-runs the entire Streamlit script every 3 seconds.
  Each re-run:
    1. Calls load_violations_df()  → fresh SQL query
    2. Calls load_vehicle_counts_df()
    3. Rebuilds all charts + tables with new data
    4. Renders updated metrics on screen

  The user sees new violations ~3 seconds after the pipeline writes them.
  To change the speed: edit REFRESH_RATE_MS in config.py  (default: 300 → 3s)
""")
    print(f"  Dashboard URL: http://localhost:{DASHBOARD_PORT}")
    print(f"  Start with:    streamlit run dashboard/app.py")
    print()

    db = TrafficDB()
    latency_demo(db, n=args.n, interval=args.interval)

    print("\n" + "=" * 65)
    print("  ── Phase 3 Dashboard Section Complete (Days 19–25) ────────")
    print("=" * 65)
    print("  Day 19 ✓ Streamlit setup + DB preview")
    print("  Day 20 ✓ Live data: pipeline → DB → dashboard")
    print("  Day 21 ✓ Plotly charts: pie, bar, line, heatmap")
    print("  Day 22 ✓ Filters: violation type, plate search")
    print("  Day 23 ✓ Snapshot gallery + contact sheet")
    print("  Day 24 ✓ CSV export + pandas report")
    print("  Day 25 ✓ Auto-refresh latency + real-time demo")
    print()
    print("  Next → python day26_test.py  (Multi-threading for performance)")
    print("=" * 65)
