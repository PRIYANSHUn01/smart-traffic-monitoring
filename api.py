"""
api.py — FastAPI REST API for Smart Traffic Monitoring System
Run: uvicorn api:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs

SECURITY:
  - Set API_KEY in your .env file (required for protected endpoints).
  - Set ALLOWED_ORIGINS as a comma-separated list of trusted origins.
  - Never expose this API publicly without an API key.
"""

import os
import time
from datetime import datetime

from fastapi import FastAPI, Query, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware

from utils.database import TrafficDB
from utils.helpers import get_logger

log = get_logger("api")
START_TIME = time.time()

# ── Security configuration ────────────────────────────────────────────────────

# Load from environment — never hardcode this value
API_KEY = os.getenv("API_KEY", "")

# Restrict to known origins only (comma-separated in env)
# Example: ALLOWED_ORIGINS=http://localhost:8501,https://yourdomain.com
_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:8501")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str = Security(api_key_header)):
    """Dependency: reject requests that do not carry a valid API key."""
    if not API_KEY:
        # Key not configured — warn but allow (dev mode safety net)
        log.warning("API_KEY is not set. Set it in .env to secure all endpoints.")
        return
    if key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Set X-API-Key header.",
        )


# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Smart Traffic Monitoring API",
    description="REST API for querying violations, vehicle counts, and system stats.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # VUL-2 FIX: no more wildcard "*"
    allow_methods=["GET"],
    allow_headers=["X-API-Key"],
)

db = TrafficDB()


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health():
    """Database status and API uptime (no auth required — public endpoint)."""
    uptime_sec = int(time.time() - START_TIME)
    try:
        total = db.get_total_violations()
        db_status = "ok"
    except Exception as e:
        # VUL-5 FIX: log the real error internally, return generic status to client
        log.error(f"DB health check failed: {e}")
        db_status = "error"
        total = None
    return {
        "status": "running",
        "db": db_status,
        "uptime_seconds": uptime_sec,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total_violations_in_db": total,
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

@app.get("/stats", tags=["Analytics"], dependencies=[Depends(require_api_key)])
def stats():
    """Summary counts: violations, vehicles, and breakdown by type."""
    return {
        "total_violations": db.get_total_violations(),
        "total_vehicles": db.get_total_vehicles(),
        "violation_breakdown": db.get_violation_breakdown(),
        "vehicle_type_counts": db.get_vehicle_type_counts(),
    }


# ── Violations ────────────────────────────────────────────────────────────────

@app.get("/violations", tags=["Violations"], dependencies=[Depends(require_api_key)])
def get_violations(limit: int = Query(default=20, ge=1, le=500)):
    """
    Return the most recent violations.
    - **limit**: number of records to return (1–500, default 20)
    """
    rows = db.get_recent_violations(limit=limit)
    return {"count": len(rows), "violations": rows}


@app.get("/violations/search", tags=["Violations"], dependencies=[Depends(require_api_key)])
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

@app.get("/counts/hourly", tags=["Analytics"], dependencies=[Depends(require_api_key)])
def hourly_counts():
    """Per-hour vehicle counts for today (for dashboard bar chart)."""
    data = db.get_hourly_counts()
    return {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "hourly": [{"hour": h, "count": c} for h, c in data],
    }
