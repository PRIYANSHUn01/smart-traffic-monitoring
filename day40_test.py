# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 40 — day40_test.py
#  Topic: System monitoring — watchdog, auto-restart, metrics, alerts
#
#  NEW today:
#    ✓ Watchdog thread: detect pipeline crash and restart it
#    ✓ Metrics collector: FPS, queue depth, DB write rate
#    ✓ Prometheus-style text metrics export
#    ✓ Alert cooldown: don't spam email on repeated failures
#    ✓ Uptime tracker
#
#  Run:  python day40_test.py              (demo watchdog + metrics)
#  Run:  python day40_test.py --monitor    (live metrics loop)
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, threading, argparse, json
from collections import deque
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.database import TrafficDB
from utils.helpers  import get_logger
log = get_logger("day40")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Metrics ───────────────────────────────────────────────────────────────────

class MetricsCollector:
    """Rolling-window metrics for the pipeline."""

    def __init__(self, window=60):
        self.window       = window          # seconds
        self._fps_samples = deque()         # (timestamp, fps)
        self._db_writes   = deque()         # timestamps of DB writes
        self._errors      = deque()         # timestamps of errors
        self._start_time  = time.time()
        self._lock        = threading.Lock()

    def record_fps(self, fps):
        now = time.time()
        with self._lock:
            self._fps_samples.append((now, fps))
            self._trim(self._fps_samples)

    def record_db_write(self):
        now = time.time()
        with self._lock:
            self._db_writes.append(now)
            self._trim(self._db_writes)

    def record_error(self):
        now = time.time()
        with self._lock:
            self._errors.append(now)
            self._trim(self._errors)

    def _trim(self, q):
        cutoff = time.time() - self.window
        while q and q[0] if isinstance(q[0], float) else q[0][0] < cutoff:
            q.popleft()

    def _trim(self, q):
        cutoff = time.time() - self.window
        while q:
            first = q[0]
            ts = first if isinstance(first, float) else first[0]
            if ts < cutoff:
                q.popleft()
            else:
                break

    @property
    def avg_fps(self):
        with self._lock:
            if not self._fps_samples:
                return 0.0
            return sum(v for _, v in self._fps_samples) / len(self._fps_samples)

    @property
    def db_writes_per_min(self):
        with self._lock:
            cutoff = time.time() - 60
            return sum(1 for ts in self._db_writes if ts > cutoff)

    @property
    def errors_per_min(self):
        with self._lock:
            cutoff = time.time() - 60
            return sum(1 for ts in self._errors if ts > cutoff)

    @property
    def uptime_seconds(self):
        return int(time.time() - self._start_time)

    def snapshot(self):
        return {
            "uptime_s":        self.uptime_seconds,
            "avg_fps":         round(self.avg_fps, 1),
            "db_writes_per_min": self.db_writes_per_min,
            "errors_per_min":  self.errors_per_min,
            "timestamp":       datetime.now().isoformat(),
        }

    def to_prometheus(self):
        s = self.snapshot()
        lines = [
            "# HELP traffic_uptime_seconds Total uptime in seconds",
            "# TYPE traffic_uptime_seconds counter",
            f"traffic_uptime_seconds {s['uptime_s']}",
            "",
            "# HELP traffic_avg_fps Average pipeline FPS",
            "# TYPE traffic_avg_fps gauge",
            f"traffic_avg_fps {s['avg_fps']}",
            "",
            "# HELP traffic_db_writes_per_min DB write rate",
            "# TYPE traffic_db_writes_per_min gauge",
            f"traffic_db_writes_per_min {s['db_writes_per_min']}",
            "",
            "# HELP traffic_errors_per_min Error rate",
            "# TYPE traffic_errors_per_min gauge",
            f"traffic_errors_per_min {s['errors_per_min']}",
        ]
        return "\n".join(lines)


# ── Watchdog ──────────────────────────────────────────────────────────────────

class PipelineWatchdog:
    """Monitors a worker thread; restarts it if it dies."""

    def __init__(self, factory_fn, check_interval=5, max_restarts=5):
        self.factory_fn     = factory_fn
        self.check_interval = check_interval
        self.max_restarts   = max_restarts
        self._thread        = None
        self._restarts      = 0
        self._running       = False
        self._last_restart  = 0
        self._alert_cooldown = 60   # seconds between repeated alerts
        self._last_alert    = 0

    def start(self):
        self._running = True
        self._spawn()
        t = threading.Thread(target=self._watch, daemon=True)
        t.start()
        log.info("Watchdog started")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            log.info("Watchdog stopping worker…")

    def _spawn(self):
        self._thread = threading.Thread(target=self.factory_fn, daemon=True)
        self._thread.start()
        log.info(f"Worker spawned (restart #{self._restarts})")

    def _watch(self):
        while self._running:
            time.sleep(self.check_interval)
            if not self._thread.is_alive():
                if self._restarts >= self.max_restarts:
                    log.error("Max restarts reached — watchdog giving up")
                    self._maybe_alert("MAX RESTARTS REACHED")
                    self._running = False
                    return
                self._restarts += 1
                log.warning(f"Worker died — restarting ({self._restarts}/{self.max_restarts})")
                self._maybe_alert(f"Worker restarted (attempt {self._restarts})")
                self._spawn()

    def _maybe_alert(self, msg):
        now = time.time()
        if now - self._last_alert > self._alert_cooldown:
            log.error(f"WATCHDOG ALERT: {msg}")
            self._last_alert = now

    @property
    def restarts(self):
        return self._restarts

    @property
    def is_alive(self):
        return self._thread is not None and self._thread.is_alive()


# ── Demo worker ───────────────────────────────────────────────────────────────

def _demo_worker(metrics, crash_after=None):
    """Fake pipeline worker that records metrics and optionally crashes."""
    frame = 0
    while True:
        time.sleep(0.05)   # simulate 20 FPS
        frame += 1
        metrics.record_fps(20.0)
        if frame % 10 == 0:
            metrics.record_db_write()
        if crash_after and frame >= crash_after:
            log.warning(f"Demo worker crashing at frame {frame}")
            metrics.record_error()
            raise RuntimeError("Simulated crash")


# ── Live monitor ──────────────────────────────────────────────────────────────

def live_monitor(metrics, db, interval=2, duration=30):
    print(f"\n  Live metrics (every {interval}s, {duration}s total). Ctrl+C to stop.\n")
    cols = ["uptime_s", "avg_fps", "db_writes_per_min", "errors_per_min"]
    header = f"  {'Uptime':>8s}  {'FPS':>6s}  {'DB/min':>7s}  {'Err/min':>7s}  {'DB rows':>8s}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    t_end = time.time() + duration
    try:
        while time.time() < t_end:
            s = metrics.snapshot()
            db_rows = db.get_total_vehicles()
            print(f"  {s['uptime_s']:>8d}  {s['avg_fps']:>6.1f}  "
                  f"{s['db_writes_per_min']:>7d}  {s['errors_per_min']:>7d}  {db_rows:>8d}")
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 40 — System Monitoring")
    parser.add_argument("--monitor",    action="store_true",
                        help="Live metrics loop")
    parser.add_argument("--watchdog",   action="store_true",
                        help="Demo watchdog (simulates crash + restart)")
    parser.add_argument("--prometheus", action="store_true",
                        help="Print Prometheus metrics text")
    parser.add_argument("--duration",   type=int, default=20)
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 40 — System Monitoring & Watchdog")
    print("=" * 65)

    metrics = MetricsCollector(window=60)
    db      = TrafficDB()

    if args.prometheus:
        # Simulate a few seconds of data first
        for _ in range(20):
            metrics.record_fps(18.5)
            metrics.record_db_write()
        print("\n  Prometheus metrics text format:\n")
        print(metrics.to_prometheus())
        sys.exit(0)

    if args.watchdog:
        print("\n  Demo: watchdog detects crash and restarts worker")
        print("  Worker will crash after 2 seconds…\n")

        crash_frame = 40   # at 20fps ≈ 2 seconds
        wd = PipelineWatchdog(
            factory_fn=lambda: _demo_worker(metrics, crash_after=crash_frame),
            check_interval=2,
            max_restarts=3,
        )
        wd.start()
        time.sleep(10)
        wd.stop()
        print(f"\n  Worker restarts: {wd.restarts}")
        print(f"  Metrics: {metrics.snapshot()}")
        sys.exit(0)

    if args.monitor:
        # Start a background worker that generates metrics
        t = threading.Thread(
            target=_demo_worker, args=(metrics,), daemon=True)
        t.start()
        live_monitor(metrics, db, interval=2, duration=args.duration)
        sys.exit(0)

    # Default: show snapshot + explain system
    print("\n  Running demo metrics collection (5 seconds)…")
    for _ in range(100):
        metrics.record_fps(19.0 + (os.getpid() % 3) * 0.1)
        if _ % 5 == 0:
            metrics.record_db_write()
        time.sleep(0.05)

    s = metrics.snapshot()
    print(f"\n  Metrics snapshot:")
    for k, v in s.items():
        print(f"    {k:<25s}: {v}")

    print("\n  ── MONITORING ARCHITECTURE ──────────────────────────────────")
    print("""
  Component          Purpose
  ────────────────── ─────────────────────────────────────────────────
  MetricsCollector   Rolling window stats (FPS, DB writes, errors)
  PipelineWatchdog   Restarts dead threads, alerts on repeated failure
  Prometheus export  /metrics endpoint for Grafana dashboards
  Alert cooldown     Prevents email spam during extended outages

  Run flags:
    --monitor      Live terminal metrics every 2s
    --watchdog     Demo crash-and-restart cycle
    --prometheus   Print metrics in Prometheus text format
""")

    print("  ── ADDING /metrics TO THE API (day36) ───────────────────────")
    print("""
  In day36_test.py, add inside build_app():

    _metrics = MetricsCollector()   # global

    @app.get("/metrics")
    def prometheus_metrics():
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(_metrics.to_prometheus())
""")
    print("  Next → python day41_test.py  (Real-world testing)")
