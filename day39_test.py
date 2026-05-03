# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 39 — day39_test.py
#  Topic: Production configuration — env vars, secrets, multi-environment setup
#
#  NEW today:
#    ✓ Separate configs for dev / staging / production
#    ✓ Secrets management: never hardcode passwords or API keys
#    ✓ Health-check endpoint with detailed system info
#    ✓ Configuration validation with clear error messages
#    ✓ Graceful startup and shutdown sequence
#
#  Run:  python day39_test.py
#  Run:  python day39_test.py --env production
#  Run:  python day39_test.py --validate
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse, json, time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import get_logger
log = get_logger("day39")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Environment configurations ────────────────────────────────────────────────

ENV_CONFIGS = {
    "development": {
        "debug":           True,
        "log_level":       "DEBUG",
        "skip_frames":     2,
        "api_host":        "127.0.0.1",
        "api_port":        8000,
        "dashboard_port":  8501,
        "db_path":         "data/traffic_dev.db",
        "snapshot_dir":    "data/snapshots_dev",
        "max_workers":     2,
        "reload":          True,
    },
    "staging": {
        "debug":           False,
        "log_level":       "INFO",
        "skip_frames":     1,
        "api_host":        "0.0.0.0",
        "api_port":        8000,
        "dashboard_port":  8501,
        "db_path":         "data/traffic_staging.db",
        "snapshot_dir":    "data/snapshots_staging",
        "max_workers":     4,
        "reload":          False,
    },
    "production": {
        "debug":           False,
        "log_level":       "WARNING",
        "skip_frames":     1,
        "api_host":        "0.0.0.0",
        "api_port":        8000,
        "dashboard_port":  8501,
        "db_path":         "/data/traffic.db",
        "snapshot_dir":    "/data/snapshots",
        "max_workers":     8,
        "reload":          False,
    },
}

ENV_FILE_TEMPLATE = """\
# .env — Traffic Monitoring System
# Copy to .env and fill in your values. NEVER commit this file.

# Environment: development | staging | production
APP_ENV=development

# Database
DB_PATH=data/traffic.db

# API server
API_HOST=127.0.0.1
API_PORT=8000

# Alert emails (optional)
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=

# Video source (0=webcam, or path to file)
VIDEO_SOURCE=0

# Detection thresholds
CONFIDENCE_THRESHOLD=0.45
SKIP_FRAMES=2

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
"""


# ── Config loader ─────────────────────────────────────────────────────────────

class ProductionConfig:
    """Loads config from ENV_CONFIGS + .env overrides + environment variables."""

    def __init__(self, env="development"):
        if env not in ENV_CONFIGS:
            raise ValueError(f"Unknown env '{env}'. Choose: {list(ENV_CONFIGS)}")
        self.env = env
        self._cfg = dict(ENV_CONFIGS[env])
        self._load_env_file()
        self._apply_env_vars()

    def _load_env_file(self):
        env_path = os.path.join(BASE_DIR, ".env")
        if not os.path.exists(env_path):
            return
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if val:
                    self._cfg[key] = val

    def _apply_env_vars(self):
        mapping = {
            "APP_ENV":                "env",
            "DB_PATH":                "db_path",
            "API_HOST":               "api_host",
            "API_PORT":               "api_port",
            "LOG_LEVEL":              "log_level",
            "SKIP_FRAMES":            "skip_frames",
            "CONFIDENCE_THRESHOLD":   "confidence_threshold",
        }
        for env_var, cfg_key in mapping.items():
            val = os.environ.get(env_var)
            if val:
                self._cfg[cfg_key] = val

    def get(self, key, default=None):
        return self._cfg.get(key, default)

    def __repr__(self):
        safe = {k: v for k, v in self._cfg.items()
                if "pass" not in k.lower() and "secret" not in k.lower()}
        return f"ProductionConfig(env={self.env}, {safe})"


# ── Validation ────────────────────────────────────────────────────────────────

def validate_production_config(cfg):
    errors   = []
    warnings = []

    db_path = cfg.get("db_path", "")
    db_dir  = os.path.dirname(os.path.abspath(db_path))
    if not os.path.exists(db_dir):
        errors.append(f"DB directory does not exist: {db_dir}")

    snap_dir = cfg.get("snapshot_dir", "")
    if snap_dir and not os.path.exists(snap_dir):
        warnings.append(f"Snapshot dir missing (will create): {snap_dir}")

    port = cfg.get("api_port", 8000)
    try:
        port = int(port)
        if not (1024 <= port <= 65535):
            errors.append(f"api_port out of range: {port}")
    except (ValueError, TypeError):
        errors.append(f"api_port must be integer: {port}")

    skip = cfg.get("skip_frames", 2)
    try:
        skip = int(skip)
        if skip < 1:
            errors.append("skip_frames must be >= 1")
        elif skip > 10:
            warnings.append(f"skip_frames={skip} is high — detection may miss fast vehicles")
    except (ValueError, TypeError):
        errors.append(f"skip_frames must be integer: {skip}")

    if cfg.env == "production":
        if cfg.get("debug"):
            errors.append("debug=True in production — set to False")
        if cfg.get("reload"):
            warnings.append("reload=True in production — disable for performance")
        email_from = cfg.get("alert_email_from", "")
        if not email_from:
            warnings.append("ALERT_EMAIL_FROM not set — violation alerts disabled")

    return errors, warnings


# ── System health check ───────────────────────────────────────────────────────

def system_health_check(cfg):
    import platform
    checks = {}

    checks["python_version"] = platform.python_version()
    checks["platform"]       = platform.system()
    checks["env"]            = cfg.env

    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["ram_total_gb"]  = round(mem.total / 1024**3, 1)
        checks["ram_avail_gb"]  = round(mem.available / 1024**3, 1)
        checks["cpu_count"]     = psutil.cpu_count()
        checks["disk_free_gb"]  = round(
            psutil.disk_usage(BASE_DIR).free / 1024**3, 1)
    except ImportError:
        checks["psutil"] = "not installed"

    db_path = cfg.get("db_path", "data/traffic.db")
    checks["db_exists"] = os.path.exists(db_path)
    if checks["db_exists"]:
        checks["db_size_mb"] = round(os.path.getsize(db_path) / 1024**2, 2)

    for pkg, import_name in [
        ("ultralytics", "ultralytics"),
        ("fastapi",     "fastapi"),
        ("streamlit",   "streamlit"),
        ("cv2",         "cv2"),
        ("easyocr",     "easyocr"),
    ]:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "ok")
            checks[f"pkg_{pkg}"] = ver
        except ImportError:
            checks[f"pkg_{pkg}"] = "MISSING"

    return checks


# ── Startup/shutdown ──────────────────────────────────────────────────────────

def startup_sequence(cfg):
    print("\n  Running startup sequence…")
    steps = [
        ("Load config",       lambda: cfg.get("env")),
        ("Validate config",   lambda: validate_production_config(cfg)),
        ("Create directories", lambda: [
            os.makedirs(d, exist_ok=True)
            for d in [
                os.path.dirname(os.path.abspath(cfg.get("db_path", "data/traffic.db"))),
                cfg.get("snapshot_dir", "data/snapshots"),
                "logs",
            ]
        ]),
        ("Health check",      lambda: system_health_check(cfg)),
    ]
    for name, fn in steps:
        t0 = time.perf_counter()
        try:
            result = fn()
            ms = (time.perf_counter() - t0) * 1000
            if name == "Validate config":
                errors, warnings = result
                if errors:
                    for e in errors:
                        print(f"  ✗  {name}: {e}")
                    return False
                print(f"  ✓  {name} ({ms:.0f}ms)")
                for w in warnings:
                    print(f"       ⚠  {w}")
            else:
                print(f"  ✓  {name} ({ms:.0f}ms)")
        except Exception as e:
            print(f"  ✗  {name}: {e}")
            return False
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 39 — Production Configuration")
    parser.add_argument("--env",      default="development",
                        choices=["development", "staging", "production"])
    parser.add_argument("--validate", action="store_true",
                        help="Run config validation only")
    parser.add_argument("--health",   action="store_true",
                        help="Show system health check")
    parser.add_argument("--generate-env", action="store_true",
                        help="Generate .env.example file")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 39 — Production Configuration")
    print("=" * 65)

    if args.generate_env:
        path = os.path.join(BASE_DIR, ".env.example")
        with open(path, "w") as f:
            f.write(ENV_FILE_TEMPLATE)
        print(f"\n  Generated: {path}")
        print("  Copy to .env and fill in your values.")
        sys.exit(0)

    cfg = ProductionConfig(args.env)
    print(f"\n  Environment: {args.env}")
    print(f"  Config: {cfg}")

    if args.validate or args.env == "production":
        errors, warnings = validate_production_config(cfg)
        print(f"\n  Validation: {len(errors)} errors, {len(warnings)} warnings")
        for e in errors:
            print(f"  ✗  {e}")
        for w in warnings:
            print(f"  ⚠  {w}")
        if not errors:
            print("  ✓  Config is valid")

    if args.health:
        checks = system_health_check(cfg)
        print("\n  System Health:")
        for k, v in checks.items():
            status = "✓" if v != "MISSING" else "✗"
            print(f"  {status}  {k:<25s}: {v}")

    if not args.validate and not args.health:
        ok = startup_sequence(cfg)
        if ok:
            print("\n  ✓  Startup sequence complete — system ready")
        else:
            print("\n  ✗  Startup failed — fix errors above before deploying")

    print("\n  ── ENVIRONMENT CONFIGS ──────────────────────────────────────")
    for env_name, settings in ENV_CONFIGS.items():
        print(f"\n  [{env_name}]")
        for k, v in settings.items():
            print(f"    {k:<22s} = {v}")

    print("\n  ── SECRETS BEST PRACTICES ───────────────────────────────────")
    print("""
  1. Never hardcode passwords or API keys — use environment variables
  2. Add .env to .gitignore — only commit .env.example
  3. In production, use a secrets manager:
       AWS Secrets Manager / GCP Secret Manager / HashiCorp Vault
  4. Rotate credentials regularly
  5. Use different DB files per environment (dev/staging/prod)
""")
    print("  Next → python day40_test.py  (System monitoring and health checks)")
