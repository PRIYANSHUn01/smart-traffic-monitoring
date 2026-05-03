# utils/database.py  —  SQLite-based violation logging

import sqlite3
import csv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH, CSV_LOG_PATH
from utils.helpers import now_iso, get_logger

log = get_logger("database")

# ── Schema ────────────────────────────────────────────────────────────────────
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS violations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    track_id        INTEGER,
    plate_number    TEXT    DEFAULT 'UNKNOWN',
    vehicle_type    TEXT,
    rider_count     INTEGER DEFAULT 1,
    helmet_status   TEXT    DEFAULT 'unknown',
    violation_type  TEXT,
    snapshot_path   TEXT,
    frame_number    INTEGER
);
"""

CREATE_COUNTS_TABLE = """
CREATE TABLE IF NOT EXISTS vehicle_counts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    vehicle_type TEXT,
    count        INTEGER DEFAULT 1
);
"""


class TrafficDB:
    """
    Handles all database operations for the traffic monitoring system.
    Usage:
        db = TrafficDB()
        db.log_violation(track_id=1, plate="UP14AB1234", ...)
        rows = db.get_recent_violations(limit=20)
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # rows behave like dicts
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(CREATE_TABLE)
            conn.execute(CREATE_COUNTS_TABLE)
        log.info(f"Database ready: {self.db_path}")

    # ── Write operations ──────────────────────────────────────────────────────
    def log_violation(self, track_id, plate="UNKNOWN", vehicle_type="motorcycle",
                      rider_count=1, helmet_status="unknown",
                      violation_type="NO_HELMET", snapshot_path="",
                      frame_number=0):
        """Insert one violation record"""
        sql = """
            INSERT INTO violations
            (timestamp, track_id, plate_number, vehicle_type,
             rider_count, helmet_status, violation_type,
             snapshot_path, frame_number)
            VALUES (?,?,?,?,?,?,?,?,?)
        """
        params = (now_iso(), track_id, plate, vehicle_type,
                  rider_count, helmet_status, violation_type,
                  snapshot_path, frame_number)
        with self._connect() as conn:
            conn.execute(sql, params)
        log.info(f"Violation logged: {violation_type} | Plate:{plate} | ID:{track_id}")

        # Also append to CSV for easy export
        self._append_csv(params)

    def log_vehicle_count(self, vehicle_type: str):
        """Increment vehicle count (called when vehicle crosses count line)"""
        sql = "INSERT INTO vehicle_counts (timestamp, vehicle_type) VALUES (?,?)"
        with self._connect() as conn:
            conn.execute(sql, (now_iso(), vehicle_type))

    def _append_csv(self, params):
        """Keep a running CSV file in sync with DB"""
        write_header = not os.path.exists(CSV_LOG_PATH)
        with open(CSV_LOG_PATH, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "track_id", "plate",
                    "vehicle_type", "riders", "helmet",
                    "violation", "snapshot", "frame"
                ])
            writer.writerow(params)

    # ── Read operations ───────────────────────────────────────────────────────
    def get_recent_violations(self, limit=50):
        sql = """
            SELECT * FROM violations
            ORDER BY id DESC LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(sql, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_total_violations(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM violations"
            ).fetchone()[0]

    def get_violation_breakdown(self):
        """Returns dict: {violation_type: count}"""
        sql = """
            SELECT violation_type, COUNT(*) as cnt
            FROM violations GROUP BY violation_type
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return {r["violation_type"]: r["cnt"] for r in rows}

    def get_vehicle_type_counts(self):
        """Returns dict: {vehicle_type: count}"""
        sql = """
            SELECT vehicle_type, COUNT(*) as cnt
            FROM vehicle_counts GROUP BY vehicle_type
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return {r["vehicle_type"]: r["cnt"] for r in rows}

    def get_total_vehicles(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM vehicle_counts"
            ).fetchone()[0]

    def search_by_plate(self, plate: str):
        sql = """
            SELECT * FROM violations
            WHERE plate_number LIKE ? ORDER BY id DESC
        """
        with self._connect() as conn:
            rows = conn.execute(sql, (f"%{plate}%",)).fetchall()
        return [dict(r) for r in rows]

    def get_hourly_counts(self):
        """Returns list of (hour, count) for today's traffic chart"""
        sql = """
            SELECT strftime('%H:00', timestamp) as hour,
                   COUNT(*) as cnt
            FROM vehicle_counts
            WHERE date(timestamp) = date('now')
            GROUP BY hour ORDER BY hour
        """
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [(r["hour"], r["cnt"]) for r in rows]
