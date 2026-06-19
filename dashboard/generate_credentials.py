#!/usr/bin/env python3
"""
dashboard/generate_credentials.py
──────────────────────────────────
Interactive helper that generates a bcrypt-hashed password and writes a
credentials.yml file for the Streamlit dashboard authentication.

Usage:
    python dashboard/generate_credentials.py

The script will prompt for a username, display name, and password, then
create (or overwrite) dashboard/credentials.yml with the hashed result.

SECURITY NOTES:
  - credentials.yml contains bcrypt hashes — safe to store, but keep private.
  - The cookie key (signature secret) is auto-generated with secrets.token_hex.
  - Never commit credentials.yml to version control (.gitignore already covers it).
"""

import sys
import os
import getpass
import secrets

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import bcrypt
except ImportError:
    print("ERROR: bcrypt is not installed.")
    print("       Run: pip install streamlit-authenticator==0.3.2")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml is not installed.")
    print("       Run: pip install pyyaml")
    sys.exit(1)

# ── Prompt for credentials ────────────────────────────────────────────────────
print("=" * 60)
print("  Traffic Monitoring Dashboard — Credential Setup")
print("=" * 60)
print()
print("This will create dashboard/credentials.yml")
print("You can run this script again to add more users.\n")

username = input("Enter username (e.g. admin): ").strip().lower()
if not username:
    print("ERROR: username cannot be empty.")
    sys.exit(1)

display_name = input(f"Enter display name for '{username}' (e.g. Administrator): ").strip()
if not display_name:
    display_name = username.capitalize()

email = input(f"Enter email for '{username}' (optional, press Enter to skip): ").strip()
if not email:
    email = f"{username}@localhost"

while True:
    password = getpass.getpass(f"Enter password for '{username}': ")
    if len(password) < 8:
        print("Password must be at least 8 characters. Try again.")
        continue
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match. Try again.")
        continue
    break

# ── Hash the password ─────────────────────────────────────────────────────────
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# ── Load existing credentials.yml or start fresh ──────────────────────────────
script_dir  = os.path.dirname(os.path.abspath(__file__))
creds_path  = os.path.join(script_dir, "credentials.yml")

if os.path.exists(creds_path):
    with open(creds_path) as f:
        config = yaml.safe_load(f) or {}
    print(f"\nUpdating existing {creds_path}")
else:
    config = {}
    print(f"\nCreating new {creds_path}")

# ── Merge user into config ────────────────────────────────────────────────────
config.setdefault("credentials", {}).setdefault("usernames", {})[username] = {
    "email":    email,
    "name":     display_name,
    "password": hashed,
}

# Keep existing cookie section if present, otherwise generate one
if "cookie" not in config:
    config["cookie"] = {
        "expiry_days": 1,
        "key":  secrets.token_hex(32),   # random signing secret
        "name": "traffic_monitor_auth",
    }

# ── Write file ────────────────────────────────────────────────────────────────
with open(creds_path, "w") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print(f"\n✅  credentials.yml written to: {creds_path}")
print(f"   User '{username}' ({display_name}) has been added.")
print()
print("REMINDER: Add credentials.yml to .gitignore if not already there.")
print("          Never commit this file to version control.")
print()
print("Start the dashboard:")
print("  streamlit run dashboard/app.py")
