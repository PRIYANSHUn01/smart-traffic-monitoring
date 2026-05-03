# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 21 — day21_test.py
#  Topic: Plotly charts deep dive — pie, bar, time-series, heatmap
#
#  NEW today:
#    ✓ Pie chart: vehicle type breakdown
#    ✓ Bar chart: violations by type
#    ✓ Line chart: vehicles per hour (time series)
#    ✓ Heatmap: violations by hour and day of week
#    ✓ Export charts as PNG / HTML
#
#  Run:  python day21_test.py          (generates charts as HTML files)
#  Run:  python day21_test.py --show   (opens each chart in browser)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse, random
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
except ImportError:
    print("  Install: pip install plotly pandas")
    sys.exit(1)

from utils.database import TrafficDB
from config import LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)


def build_sample_df(n=80):
    """Generate a realistic-looking violation DataFrame for chart demos."""
    import random as rnd
    rows = []
    base = datetime.now() - timedelta(hours=10)
    for i in range(n):
        vtype  = rnd.choice(["motorcycle"]*7 + ["bicycle"]*3)
        viol   = rnd.choice(["NO_HELMET"]*6 + ["TRIPLE_RIDING"]*3 + ["DOUBLE_RIDING"]*1)
        ts     = base + timedelta(seconds=rnd.randint(0, 36000))
        rows.append({
            "id": i+1, "timestamp": ts.isoformat(),
            "vehicle_type": vtype, "violation_type": viol,
            "plate_number": f"XX{rnd.randint(10,99)}YY{rnd.randint(1000,9999)}",
            "rider_count": 3 if viol=="TRIPLE_RIDING" else (2 if viol=="DOUBLE_RIDING" else 1),
        })
    return pd.DataFrame(rows)


def make_charts(df, show, out_dir):
    charts = []

    # 1. Pie — vehicle type
    vtype = df["vehicle_type"].value_counts().reset_index()
    vtype.columns = ["Type","Count"]
    fig1 = px.pie(vtype, values="Count", names="Type",
                  title="Vehicle Type Breakdown",
                  color_discrete_sequence=["#185FA5","#0F6E56"])
    path1 = os.path.join(out_dir, "chart_vehicle_types.html")
    fig1.write_html(path1)
    charts.append(("Vehicle Type Pie", path1))

    # 2. Bar — violations by type
    vtypes = df["violation_type"].value_counts().reset_index()
    vtypes.columns = ["Violation","Count"]
    fig2 = px.bar(vtypes, x="Violation", y="Count", title="Violations by Type",
                  color="Violation",
                  color_discrete_map={"NO_HELMET":"#E24B4A",
                                      "TRIPLE_RIDING":"#854F0B",
                                      "DOUBLE_RIDING":"#BA7517"})
    fig2.update_layout(showlegend=False)
    path2 = os.path.join(out_dir, "chart_violations_bar.html")
    fig2.write_html(path2)
    charts.append(("Violations Bar", path2))

    # 3. Line — vehicles per hour
    df["hour"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.strftime("%H:00")
    hourly = df.groupby("hour").size().reset_index(name="count")
    fig3 = px.line(hourly, x="hour", y="count", title="Vehicles per Hour",
                   markers=True, line_shape="spline")
    fig3.update_traces(line_color="#185FA5")
    path3 = os.path.join(out_dir, "chart_hourly_trend.html")
    fig3.write_html(path3)
    charts.append(("Hourly Trend", path3))

    # 4. Heatmap — violation hour × day-of-week
    df_ts = df.copy()
    df_ts["dt"]  = pd.to_datetime(df_ts["timestamp"], errors="coerce")
    df_ts["dow"] = df_ts["dt"].dt.day_name()
    df_ts["hr"]  = df_ts["dt"].dt.hour
    heat = df_ts.groupby(["dow","hr"]).size().unstack(fill_value=0)
    days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    heat = heat.reindex([d for d in days_order if d in heat.index])
    fig4 = px.imshow(heat, title="Violations Heatmap (Day × Hour)",
                     labels={"x":"Hour","y":"Day","color":"Count"},
                     color_continuous_scale="Reds")
    path4 = os.path.join(out_dir, "chart_heatmap.html")
    fig4.write_html(path4)
    charts.append(("Heatmap", path4))

    return charts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 21 — Plotly Charts")
    parser.add_argument("--show", action="store_true", help="Open charts in browser")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 21 — Plotly Charts Deep Dive")
    print("=" * 65)

    db = TrafficDB()
    import sqlite3, pandas as pd
    if os.path.exists(db.db_path):
        conn = sqlite3.connect(db.db_path)
        df = pd.read_sql_query("SELECT * FROM violations", conn)
        conn.close()
    else:
        df = pd.DataFrame()

    if df.empty or len(df) < 5:
        print("  Not enough real data — using synthetic demo data")
        df = build_sample_df(80)
    else:
        print(f"  Using {len(df)} real violation records from DB")

    charts = make_charts(df, args.show, LOGS_DIR)

    print(f"\n  Generated {len(charts)} charts in {LOGS_DIR}")
    for name, path in charts:
        print(f"    {name:<22s} → {path}")
        if args.show:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(path)}")

    print("\n  These charts are the same ones shown in dashboard/app.py")
    print("  Next → python day22_test.py  (Dashboard filters + plate search)")
