# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

---

## GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "db_exists": true,
  "db_path": "data/traffic.db"
}
```

---

## GET /stats

Summary statistics from the database.

**Response:**
```json
{
  "total_vehicles": 1234,
  "total_violations": 56,
  "breakdown": {"no_helmet": 40, "triple_riding": 16},
  "vehicle_types": {"motorcycle": 800, "bicycle": 434}
}
```

---

## GET /violations

List recent violations, newest first.

**Query parameters:**
- `limit` (int, default 20, max 200) — number of results

**Response:**
```json
{
  "count": 5,
  "violations": [
    {
      "id": 1,
      "vehicle_type": "motorcycle",
      "plate": "UP14AB1234",
      "violation_type": "no_helmet",
      "timestamp": "2025-01-15 14:32:01",
      "snapshot_path": "data/snapshots/viol_001.jpg"
    }
  ]
}
```

---

## GET /violations/search

Search violations by plate number (case-insensitive).

**Query parameters:**
- `plate` (str, min_length=2) — partial or full plate string

**Response:**
```json
{
  "query": "UP14",
  "count": 3,
  "results": [ ... ]
}
```

**Error (422):** plate shorter than 2 characters.

---

## GET /counts/hourly

Vehicle counts grouped by hour (today only).

**Response:**
```json
{
  "hourly": [
    {"hour": "08:00", "count": 45},
    {"hour": "09:00", "count": 112}
  ]
}
```
