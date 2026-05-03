# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 36 — day36_test.py
#  Topic: REST API with FastAPI — expose violation data as HTTP endpoints
#
#  NEW today:
#    ✓ FastAPI app with GET /violations, GET /stats, GET /health
#    ✓ Run API server alongside the pipeline
#    ✓ Test endpoints with requests or browser
#
#  Run:  python day36_test.py           (starts API server)
#  Test: curl http://localhost:8000/health
#        curl http://localhost:8000/stats
#        curl http://localhost:8000/violations?limit=5
#  Install: pip install fastapi uvicorn
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
from config         import DB_PATH

log = get_logger("day36")

try:
    from fastapi import FastAPI, Query, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


def build_app():
    db  = TrafficDB()
    app = FastAPI(
        title="Traffic Monitoring API",
        description="Query violation data from the Traffic Monitoring System",
        version="1.0.0",
    )

    @app.get("/health")
    def health():
        """Health check — returns OK and DB status."""
        return {
            "status":   "ok",
            "db_exists": os.path.exists(DB_PATH),
            "db_path":   DB_PATH,
        }

    @app.get("/stats")
    def stats():
        """Summary statistics."""
        return {
            "total_vehicles":   db.get_total_vehicles(),
            "total_violations": db.get_total_violations(),
            "breakdown":        db.get_violation_breakdown(),
            "vehicle_types":    db.get_vehicle_type_counts(),
        }

    @app.get("/violations")
    def violations(limit: int = Query(default=20, le=200)):
        """List recent violations (newest first)."""
        rows = db.get_recent_violations(limit=limit)
        return {"count": len(rows), "violations": rows}

    @app.get("/violations/search")
    def search(plate: str = Query(..., min_length=2)):
        """Search violations by plate number."""
        rows = db.search_by_plate(plate.upper())
        return {"query": plate.upper(), "count": len(rows), "results": rows}

    @app.get("/counts/hourly")
    def hourly():
        """Vehicle counts grouped by hour (today)."""
        return {"hourly": db.get_hourly_counts()}

    return app


def demo_no_fastapi():
    """Show what the endpoints would return without starting a server."""
    db = TrafficDB()
    print("\n  ── SIMULATED API RESPONSES ──────────────────────────────────")
    import json

    endpoints = [
        ("GET /health",   {"status":"ok","db_exists": os.path.exists(DB_PATH)}),
        ("GET /stats",    {"total_vehicles": db.get_total_vehicles(),
                           "total_violations": db.get_total_violations(),
                           "breakdown": db.get_violation_breakdown()}),
        ("GET /violations?limit=3",
                          {"count": min(3, db.get_total_violations()),
                           "violations": db.get_recent_violations(limit=3)}),
    ]
    for path, data in endpoints:
        print(f"\n  {path}")
        print("  " + json.dumps(data, indent=4, default=str)[:300])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 36 — REST API")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 36 — REST API with FastAPI")
    print("=" * 65)

    if not HAS_FASTAPI:
        print("\n  FastAPI / uvicorn not installed.")
        print("  Install:  pip install fastapi uvicorn")
        print()
        print("  Showing demo output instead:\n")
        demo_no_fastapi()
        print("\n  Once installed, run:  python day36_test.py")
        print("  Then open:            http://localhost:8000/docs")
        print("  Next → python day37_test.py  (API testing)")
    else:
        app = build_app()
        print(f"\n  API server starting on http://{args.host}:{args.port}")
        print("  Endpoints:")
        print("    GET /health")
        print("    GET /stats")
        print("    GET /violations?limit=20")
        print("    GET /violations/search?plate=UP14")
        print("    GET /counts/hourly")
        print()
        print("  Interactive docs: http://localhost:8000/docs")
        print("  Press Ctrl+C to stop\n")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
