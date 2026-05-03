# reset_data.py
# One-command full data reset for the Smart Traffic Monitoring System.
# Clears: SQLite DB, CSV logs, snapshots, log files, batch checkpoints.

import os, sys, shutil, sqlite3, glob

sys.path.insert(0, os.path.dirname(__file__))
from config import DB_PATH, CSV_LOG_PATH, LOGS_DIR, SNAPSHOTS_DIR

SEPARATOR = "=" * 55

def confirm(msg):
    ans = input(f"\n{msg} [y/N]: ").strip().lower()
    return ans == "y"

def reset_database():
    if not os.path.exists(DB_PATH):
        print("  [DB] No database found — skipping.")
        return
    with sqlite3.connect(DB_PATH) as conn:
        violations = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
        counts     = conn.execute("SELECT COUNT(*) FROM vehicle_counts").fetchone()[0]
        conn.execute("DELETE FROM violations")
        conn.execute("DELETE FROM vehicle_counts")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('violations','vehicle_counts')")
        conn.commit()
    print(f"  [DB] Cleared {violations} violations, {counts} vehicle counts. IDs reset to 1.")

def reset_csv():
    cleared = 0
    for path in [CSV_LOG_PATH,
                 os.path.join(LOGS_DIR, "violations_export.csv")]:
        if os.path.exists(path):
            os.remove(path)
            print(f"  [CSV] Deleted: {os.path.basename(path)}")
            cleared += 1
    if cleared == 0:
        print("  [CSV] No CSV files found — skipping.")

def reset_snapshots():
    if not os.path.exists(SNAPSHOTS_DIR):
        print("  [Snapshots] Directory not found — skipping.")
        return
    files = glob.glob(os.path.join(SNAPSHOTS_DIR, "*.jpg")) + \
            glob.glob(os.path.join(SNAPSHOTS_DIR, "*.jpeg")) + \
            glob.glob(os.path.join(SNAPSHOTS_DIR, "*.png"))
    for f in files:
        os.remove(f)
    print(f"  [Snapshots] Deleted {len(files)} snapshot image(s).")

def reset_logs():
    patterns = ["*.log", "*.json", "batch_checkpoint.json", "field_report_*.json"]
    deleted = 0
    for pat in patterns:
        for f in glob.glob(os.path.join(LOGS_DIR, pat)):
            os.remove(f)
            deleted += 1
    print(f"  [Logs] Deleted {deleted} log/report file(s).")

def reset_charts():
    deleted = 0
    for f in glob.glob(os.path.join(LOGS_DIR, "chart_*.html")):
        os.remove(f)
        deleted += 1
    print(f"  [Charts] Deleted {deleted} chart HTML file(s).")


def main():
    print(SEPARATOR)
    print("  Smart Traffic Monitoring — Data Reset")
    print(SEPARATOR)
    print(f"\n  DB path       : {DB_PATH}")
    print(f"  Logs dir      : {LOGS_DIR}")
    print(f"  Snapshots dir : {SNAPSHOTS_DIR}")

    # Show current counts
    if os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            v = conn.execute("SELECT COUNT(*) FROM violations").fetchone()[0]
            c = conn.execute("SELECT COUNT(*) FROM vehicle_counts").fetchone()[0]
        print(f"\n  Current data  : {v} violations · {c} vehicle count records")
    else:
        print("\n  Current data  : No database found")

    print()
    print("  Choose reset mode:")
    print("  [1] Full reset   — DB + CSV + Snapshots + Logs + Charts")
    print("  [2] DB only      — Clear violations and vehicle counts")
    print("  [3] Logs only    — Delete log files and chart HTMLs")
    print("  [4] Cancel")
    print()

    choice = input("  Enter choice (1/2/3/4): ").strip()

    if choice == "4" or choice == "":
        print("\n  Cancelled. No data was changed.")
        return

    if choice == "1":
        if not confirm("  This will delete ALL data permanently. Are you sure?"):
            print("\n  Cancelled.")
            return
        print()
        reset_database()
        reset_csv()
        reset_snapshots()
        reset_logs()
        reset_charts()

    elif choice == "2":
        if not confirm("  Clear all violations and vehicle count records?"):
            print("\n  Cancelled.")
            return
        print()
        reset_database()
        reset_csv()

    elif choice == "3":
        if not confirm("  Delete all log files and chart HTMLs?"):
            print("\n  Cancelled.")
            return
        print()
        reset_logs()
        reset_charts()

    else:
        print("\n  Invalid choice. No data was changed.")
        return

    print()
    print(SEPARATOR)
    print("  RESET COMPLETE — System ready for fresh run.")
    print("  Run: python pipeline.py")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
