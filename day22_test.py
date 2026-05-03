# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 22 — day22_test.py
#  Topic: Dashboard filtering + plate search + violation detail view
#
#  NEW today:
#    ✓ Filter violations by type (NO_HELMET / TRIPLE_RIDING / DOUBLE_RIDING)
#    ✓ Search by plate number (partial match)
#    ✓ Date range filter (today / this week / custom)
#    ✓ Print a violation detail card to terminal
#    ✓ Understand how dashboard/app.py sidebar filters are wired
#
#  Run:  python day22_test.py
#  Run:  python day22_test.py --plate UP14  (search by partial plate)
#  Run:  python day22_test.py --type NO_HELMET
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from config import VIOLATION_NO_HELMET, VIOLATION_TRIPLE_RIDE, VIOLATION_DOUBLE_RIDE


def print_violation_card(v):
    """Pretty-print a single violation record."""
    border = "─" * 50
    print(f"\n  ┌{border}┐")
    print(f"  │  Violation #{v['id']:<44d}│")
    print(f"  ├{border}┤")
    print(f"  │  Time     : {str(v['timestamp']):<38s}│")
    print(f"  │  Type     : {str(v['violation_type']):<38s}│")
    print(f"  │  Plate    : {str(v['plate_number']):<38s}│")
    print(f"  │  Vehicle  : {str(v['vehicle_type']):<38s}│")
    print(f"  │  Riders   : {str(v['rider_count']):<38s}│")
    print(f"  │  Helmet   : {str(v['helmet_status']):<38s}│")
    print(f"  │  Frame    : {str(v['frame_number']):<38s}│")
    snap = str(v.get('snapshot_path', ''))
    snap_short = snap[-40:] if len(snap) > 40 else snap
    exists = "✓" if snap and os.path.exists(snap) else "✗"
    print(f"  │  Snapshot : {exists} {snap_short:<36s}│")
    print(f"  └{border}┘")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 22 — Dashboard Filters")
    parser.add_argument("--plate",  default="",         help="Partial plate search")
    parser.add_argument("--type",   default="",         help="Violation type filter")
    parser.add_argument("--limit",  type=int, default=10)
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 22 — Dashboard Filtering & Plate Search")
    print("=" * 65)

    db = TrafficDB()

    # 1. All recent violations
    all_viols = db.get_recent_violations(limit=args.limit)
    print(f"\n  Total in DB : {db.get_total_violations()}")
    print(f"  Showing last: {min(args.limit, len(all_viols))}")

    # 2. Filter by violation type
    if args.type:
        filtered = [v for v in all_viols if v["violation_type"] == args.type.upper()]
        print(f"\n  Filter --type={args.type.upper()} → {len(filtered)} matches")
        for v in filtered[:5]:
            print_violation_card(v)
    elif args.plate:
        # 3. Plate search
        results = db.search_by_plate(args.plate.upper())
        print(f"\n  Search plate='{args.plate.upper()}' → {len(results)} matches")
        for v in results[:5]:
            print_violation_card(v)
    else:
        # Show most recent
        print(f"\n  Most recent {min(3, len(all_viols))} violations:")
        for v in all_viols[:3]:
            print_violation_card(v)

    # 4. Summary by violation type
    print("\n  ── BREAKDOWN ──────────────────────────────────────────────")
    bd = db.get_violation_breakdown()
    total = db.get_total_violations()
    for vtype, count in sorted(bd.items(), key=lambda x: -x[1]):
        pct = count / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 4)
        print(f"  {vtype:<20s}: {count:4d}  ({pct:5.1f}%)  {bar}")

    # 5. Dashboard filter wiring explanation
    print("\n  ── HOW DASHBOARD FILTERS WORK ─────────────────────────────")
    print("""
  In dashboard/app.py (sidebar):
    viol_filter  = st.selectbox("Violation type", ["All","NO_HELMET",...])
    plate_search = st.text_input("Search by plate number", "")

  In the main section:
    if viol_filter != "All":
        viol_df = viol_df[viol_df["violation_type"] == viol_filter]
    if plate_search:
        viol_df = viol_df[viol_df["plate_number"].str.contains(plate_search)]

  This is pure pandas filtering — no extra DB query needed.
  The dashboard loads 200 rows at once and filters client-side.
""")
    print("  Next → python day23_test.py  (Snapshot gallery viewer)")
