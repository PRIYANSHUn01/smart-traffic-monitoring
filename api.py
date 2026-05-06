"""
api.py — FastAPI REST API for Smart Traffic Monitoring System
Run: uvicorn api:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs
"""

import time
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from utils.database import TrafficDB

START_TIME = time.time()

app = FastAPI(
    title="Smart Traffic Monitoring API",
    description="REST API for querying violations, vehicle counts, and system stats.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

db = TrafficDB()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Database status and API uptime."""
    uptime_sec = int(time.time() - START_TIME)
    try:
        total = db.get_total_violations()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
        total = None
    return {
        "status": "running",
        "db": db_status,
        "uptime_seconds": uptime_sec,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_violations_in_db": total,
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Analytics"])
def stats():
    """Summary counts: violations, vehicles, and breakdown by type."""
    return {
        "total_violations": db.get_total_violations(),
        "total_vehicles": db.get_total_vehicles(),
        "violation_breakdown": db.get_violation_breakdown(),
        "vehicle_type_counts": db.get_vehicle_type_counts(),
    }


# ── Violations ────────────────────────────────────────────────────────────────

@app.get("/violations", tags=["Violations"])
def get_violations(limit: int = Query(default=20, ge=1, le=500)):
    """
    Return the most recent violations.
    - **limit**: number of records to return (1–500, default 20)
    """
    rows = db.get_recent_violations(limit=limit)
    return {"count": len(rows), "violations": rows}


@app.get("/violations/search", tags=["Violations"])
def search_violations(plate: str = Query(..., min_length=2, description="Partial plate number")):
    """
    Search violations by plate number (partial match).
    Example: `/violations/search?plate=UP14`
    """
    rows = db.search_by_plate(plate)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No violations found for plate: {plate}")
    return {"count": len(rows), "plate_query": plate, "violations": rows}


# ── Counts ────────────────────────────────────────────────────────────────────

@app.get("/counts/hourly", tags=["Analytics"])
def hourly_counts():
    """Per-hour vehicle counts for today (for dashboard bar chart)."""
    data = db.get_hourly_counts()
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "hourly": [{"hour": h, "count": c} for h, c in data],
    }
