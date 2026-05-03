# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 24 — day24_test.py
#  Topic: CSV export + pandas analysis — reports and statistics
#
#  NEW today:
#    ✓ Export violations to CSV with proper headers
#    ✓ Pandas analysis: peak hour, top offending plates, violation rate
#    ✓ Generate a text summary report saved to logs/
#    ✓ Understand how the download button in dashboard/app.py works
#
#  Run:  python day24_test.py
#  Run:  python day24_test.py --report  (save report to logs/report.txt)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pandas as pd
except ImportError:
    print("  pip install pandas"); import sys; sys.exit(1)

from utils.database import TrafficDB
from config import DB_PATH, CSV_LOG_PATH, LOGS_DIR
import sqlite3
from datetime import datetime

os.makedirs(LOGS_DIR, exist_ok=True)


def load_dataframes(db_path):
    if not os.path.exists(db_path):
        return pd.DataFrame(), pd.DataFrame()
    conn = sqlite3.connect(db_path)
    viol_df  = pd.read_sql_query("SELECT * FROM violations ORDER BY id DESC", conn)
    count_df = pd.read_sql_query("SELECT * FROM vehicle_counts", conn)
    conn.close()
    return viol_df, count_df


def analyse(viol_df, count_df):
    if viol_df.empty:
        print("  No violation data in DB. Run the pipeline first or use day20_test.py --n 30")
        return {}

    viol_df["timestamp"] = pd.to_datetime(viol_df["timestamp"], errors="coerce")

    stats = {}
    stats["total_violations"]  = len(viol_df)
    stats["total_vehicles"]    = len(count_df) if not count_df.empty else 0
    stats["violation_rate"]    = (stats["total_violations"] / stats["total_vehicles"] * 100
                                   if stats["total_vehicles"] > 0 else 0)
    stats["breakdown"]         = viol_df["violation_type"].value_counts().to_dict()
    stats["top_plates"]        = (viol_df[viol_df["plate_number"] != "UNKNOWN"]
                                  ["plate_number"].value_counts().head(5).to_dict())

    if not viol_df["timestamp"].isna().all():
        viol_df["hour"] = viol_df["timestamp"].dt.hour
        peak = viol_df["hour"].value_counts().idxmax()
        stats["peak_hour"] = f"{peak:02d}:00 – {peak:02d}:59"

    stats["unique_plates"] = viol_df["plate_number"].nunique()
    if "vehicle_type" in viol_df.columns:
        stats["vehicle_breakdown"] = viol_df["vehicle_type"].value_counts().to_dict()

    return stats


def print_report(stats, save_path=None):
    lines = []
    lines.append("=" * 60)
    lines.append("  TRAFFIC VIOLATION REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append(f"  Total vehicles  : {stats.get('total_vehicles',0)}")
    lines.append(f"  Total violations: {stats.get('total_violations',0)}")
    lines.append(f"  Violation rate  : {stats.get('violation_rate',0):.1f}%")
    lines.append(f"  Unique plates   : {stats.get('unique_plates',0)}")
    if "peak_hour" in stats:
        lines.append(f"  Peak hour       : {stats['peak_hour']}")
    lines.append("")
    lines.append("  Violation Breakdown:")
    for vtype, cnt in stats.get("breakdown", {}).items():
        pct = cnt / stats["total_violations"] * 100 if stats["total_violations"] > 0 else 0
        bar = "█" * int(pct / 4)
        lines.append(f"    {vtype:<20s}: {cnt:4d}  ({pct:5.1f}%)  {bar}")
    lines.append("")
    lines.append("  Top Offending Plates:")
    for plate, cnt in list(stats.get("top_plates",{}).items())[:5]:
        lines.append(f"    {plate:<14s}: {cnt} violation(s)")
    lines.append("")
    lines.append("  Vehicle Type Breakdown:")
    for vtype, cnt in stats.get("vehicle_breakdown",{}).items():
        lines.append(f"    {vtype:<14s}: {cnt}")
    lines.append("=" * 60)

    for line in lines:
        print(line)

    if save_path:
        with open(save_path, "w") as f:
            f.write("\n".join(lines))
        print(f"\n  Report saved: {save_path}")


def export_csv(viol_df, out_path):
    if viol_df.empty:
        print("  No data to export")
        return
    viol_df.to_csv(out_path, index=False)
    size_kb = os.path.getsize(out_path) / 1024
    print(f"\n  CSV exported: {out_path}  ({size_kb:.1f} KB, {len(viol_df)} rows)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 24 — CSV Export & Analysis")
    parser.add_argument("--report", action="store_true", help="Save report to file")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 24 — CSV Export + Pandas Analysis")
    print("=" * 65)

    db = TrafficDB()
    viol_df, count_df = load_dataframes(db.db_path)

    stats = analyse(viol_df, count_df)
    if stats:
        report_path = os.path.join(LOGS_DIR, "report.txt") if args.report else None
        print_report(stats, save_path=report_path)

    # Export full CSV
    csv_out = os.path.join(LOGS_DIR, "violations_export.csv")
    export_csv(viol_df, csv_out)

    print("\n  ── HOW DASHBOARD CSV DOWNLOAD WORKS ───────────────────────")
    print("""
  In dashboard/app.py sidebar:
    if os.path.exists(CSV_LOG_PATH):
        with open(CSV_LOG_PATH, "rb") as f:
            st.download_button(
                label="📥 Download Violations CSV",
                data=f,
                file_name="violations_export.csv",
                mime="text/csv",
            )

  This reads the CSV that TrafficDB._append_csv() writes on every violation.
  No re-query needed — always up-to-date because it's written in real-time.
""")
    print("  Next → python day25_test.py  (Dashboard auto-refresh + real-time)")
