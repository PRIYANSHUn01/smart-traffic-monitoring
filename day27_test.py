# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 27 — day27_test.py
#  Topic: Config management + environment variables + .env file support
#
#  NEW today:
#    ✓ Override config.py values via environment variables at runtime
#    ✓ Load a .env file for sensitive values (email password, API keys)
#    ✓ Validate config at startup — catch bad values before they cause crashes
#    ✓ Print a config summary so you can see active settings at a glance
#
#  Run:  python day27_test.py
#  With overrides: SKIP_FRAMES=1 CONFIDENCE_THRESHOLD=0.5 python day27_test.py
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, argparse
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# ── .env loader (no dependency on python-dotenv) ──────────────────────────────
def load_dotenv(path=".env"):
    """Read a .env file and set environment variables (only if not already set)."""
    if not os.path.exists(path):
        return {}
    loaded = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip(); val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val
                loaded[key] = val
    return loaded


# ── Config override via environment variables ──────────────────────────────────
def apply_env_overrides():
    """
    Read environment variables and override config.py values.
    This lets you change settings without editing config.py.
    Example:
        set SKIP_FRAMES=1 && python day27_test.py
    """
    import config as cfg

    overrides = {}

    def _override(attr, env_key, cast=str):
        val = os.environ.get(env_key)
        if val is not None:
            try:
                setattr(cfg, attr, cast(val))
                overrides[env_key] = f"{val} ({cast.__name__})"
            except (ValueError, TypeError) as e:
                print(f"  ⚠  Bad value for {env_key}={val}: {e}")

    _override("SKIP_FRAMES",           "SKIP_FRAMES",           int) # type: ignore
    _override("CONFIDENCE_THRESHOLD",  "CONFIDENCE_THRESHOLD",  float) # type: ignore
    _override("COUNT_LINE_POSITION",   "COUNT_LINE_POSITION",   float) # pyright: ignore[reportArgumentType]
    _override("ENABLE_EMAIL_ALERTS",   "ENABLE_EMAIL_ALERTS",   lambda x: x.lower()=="true") # type: ignore
    _override("EMAIL_APP_PASSWORD",    "EMAIL_APP_PASSWORD",    str)
    _override("ENABLE_DOUBLE_WARNING", "ENABLE_DOUBLE_WARNING", lambda x: x.lower()=="true") # type: ignore
    _override("LOG_LEVEL",             "LOG_LEVEL",             str)

    return overrides


# ── Config validator ──────────────────────────────────────────────────────────
def validate_config():
    import config as cfg
    errors   = []
    warnings = []

    if not (0.1 <= cfg.CONFIDENCE_THRESHOLD <= 1.0):
        errors.append(f"CONFIDENCE_THRESHOLD={cfg.CONFIDENCE_THRESHOLD} must be 0.1–1.0")
    if not (0.0 < cfg.COUNT_LINE_POSITION < 1.0):
        errors.append(f"COUNT_LINE_POSITION={cfg.COUNT_LINE_POSITION} must be 0–1")
    if cfg.SKIP_FRAMES < 1:
        errors.append(f"SKIP_FRAMES={cfg.SKIP_FRAMES} must be >= 1")
    if cfg.SKIP_FRAMES > 5:
        warnings.append(f"SKIP_FRAMES={cfg.SKIP_FRAMES} is high — you may miss fast vehicles")
    if cfg.ENABLE_EMAIL_ALERTS and not cfg.EMAIL_APP_PASSWORD:
        warnings.append("ENABLE_EMAIL_ALERTS=True but EMAIL_APP_PASSWORD is empty")
    if not os.path.exists(cfg.MODELS_DIR):
        warnings.append(f"MODELS_DIR not found: {cfg.MODELS_DIR}")

    return errors, warnings


# ── Config summary printer ────────────────────────────────────────────────────
def print_config_summary():
    import config as cfg
    print("\n  ── ACTIVE CONFIGURATION ────────────────────────────────────")
    sections = {
        "Paths":       [("BASE_DIR",cfg.BASE_DIR),("DB_PATH",cfg.DB_PATH),
                        ("SNAPSHOTS_DIR",cfg.SNAPSHOTS_DIR)],
        "Detection":   [("CONFIDENCE_THRESHOLD",cfg.CONFIDENCE_THRESHOLD),
                        ("SKIP_FRAMES",cfg.SKIP_FRAMES),
                        ("INPUT_SIZE",cfg.INPUT_SIZE),
                        ("COUNT_LINE_POSITION",cfg.COUNT_LINE_POSITION)],
        "Violations":  [("ENABLE_DOUBLE_WARNING",cfg.ENABLE_DOUBLE_WARNING),
                        ("ENABLE_EMAIL_ALERTS",cfg.ENABLE_EMAIL_ALERTS)],
        "Display":     [("FRAME_WIDTH",cfg.FRAME_WIDTH),
                        ("FRAME_HEIGHT",cfg.FRAME_HEIGHT),
                        ("SHOW_TRAILS",cfg.SHOW_TRAILS),
                        ("TRAIL_LENGTH",cfg.TRAIL_LENGTH)],
        "Dashboard":   [("DASHBOARD_PORT",cfg.DASHBOARD_PORT),
                        ("REFRESH_RATE_MS",cfg.REFRESH_RATE_MS)],
    }
    for section, items in sections.items():
        print(f"\n  [{section}]")
        for key, val in items:
            print(f"    {key:<28s} = {val}")


if __name__ == "__main__":
    print("=" * 65)
    print("  DAY 27 — Config Management + Environment Variables")
    print("=" * 65)

    # Load .env if present
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    loaded_env = load_dotenv(env_path)
    if loaded_env:
        print(f"\n  Loaded {len(loaded_env)} variable(s) from .env:")
        for k, v in loaded_env.items():
            masked = v if "PASSWORD" not in k and "KEY" not in k else "***"
            print(f"    {k} = {masked}")
    else:
        print(f"\n  No .env file found at {env_path}  (optional)")

    # Apply env overrides
    overrides = apply_env_overrides()
    if overrides:
        print(f"\n  Applied {len(overrides)} env override(s):")
        for k, v in overrides.items():
            print(f"    {k} → {v}")

    # Validate
    errors, warnings = validate_config()
    if errors:
        print(f"\n  ✗ Config ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    {e}")
    if warnings:
        print(f"\n  ⚠  Config WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"    {w}")
    if not errors and not warnings:
        print("\n  ✓ Config validation passed — no errors or warnings")

    print_config_summary()

    # .env template
    print("\n  ── SAMPLE .env FILE ─────────────────────────────────────────")
    template = """\
# .env — override config.py without editing it
# Place this file next to config.py

SKIP_FRAMES=2
CONFIDENCE_THRESHOLD=0.45
COUNT_LINE_POSITION=0.55
ENABLE_EMAIL_ALERTS=false
EMAIL_APP_PASSWORD=your_gmail_app_password_here
LOG_LEVEL=INFO
"""
    env_sample = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env.example")
    with open(env_sample, "w") as f:
        f.write(template)
    print(f"  Sample written to: {env_sample}")
    print(f"  Rename to .env and fill in your values.\n")
    print("  Next → python day28_test.py  (Structured logging + log files)")
