# ═══════════════════════════════════════════════════════════════════════════════
#  DAY 37 — day37_test.py
#  Topic: API testing — test every endpoint with requests + assertions
#
#  NEW today:
#    ✓ Automated HTTP tests against the FastAPI server
#    ✓ Test: correct status codes, correct JSON structure
#    ✓ Test: search endpoint returns expected results
#    ✓ Load test: send 50 rapid requests and measure response time
#
#  Start the server first:  python day36_test.py
#  Then run:                python day37_test.py
#  Or run all-in-one:       python day37_test.py --selftest
# ═══════════════════════════════════════════════════════════════════════════════

import sys, os, time, argparse, threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from utils.database import TrafficDB
from utils.helpers  import get_logger
log = get_logger("day37")

BASE_URL = "http://localhost:8000"


# ── Test cases ────────────────────────────────────────────────────────────────

def test_health(base):
    r = requests.get(f"{base}/health", timeout=5) # type: ignore
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "db_exists" in data

def test_stats(base):
    r = requests.get(f"{base}/stats", timeout=5) # type: ignore
    assert r.status_code == 200
    data = r.json()
    assert "total_vehicles"   in data
    assert "total_violations" in data
    assert "breakdown"        in data

def test_violations_list(base):
    r = requests.get(f"{base}/violations?limit=5", timeout=5) # type: ignore
    assert r.status_code == 200
    data = r.json()
    assert "violations" in data
    assert len(data["violations"]) <= 5

def test_violations_search(base):
    r = requests.get(f"{base}/violations/search?plate=UP", timeout=5) # type: ignore
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert data["query"] == "UP"

def test_invalid_search_rejected(base):
    r = requests.get(f"{base}/violations/search?plate=X", timeout=5) # type: ignore
    assert r.status_code == 422   # FastAPI validation error for min_length=2

def test_hourly(base):
    r = requests.get(f"{base}/counts/hourly", timeout=5) # type: ignore
    assert r.status_code == 200
    data = r.json()
    assert "hourly" in data


# ── Load test ─────────────────────────────────────────────────────────────────

def load_test(base, n=50):
    print(f"\n  Load test: {n} rapid requests to /health and /stats")
    results = []

    def call(endpoint):
        t0 = time.perf_counter()
        try:
            r = requests.get(f"{base}{endpoint}", timeout=5) # type: ignore
            ok = r.status_code == 200
        except:
            ok = False
        results.append((ok, time.perf_counter() - t0))

    threads = [threading.Thread(target=call, args=(["/health","/stats"][i%2],))
               for i in range(n)]
    t_start = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    elapsed = time.time() - t_start

    success = sum(1 for ok, _ in results if ok)
    times_ms = [t * 1000 for _, t in results]
    avg_ms   = sum(times_ms) / len(times_ms)
    max_ms   = max(times_ms)

    print(f"  Requests: {n}  |  Success: {success}  |  "
          f"Avg: {avg_ms:.1f}ms  |  Max: {max_ms:.1f}ms  |  "
          f"Total: {elapsed:.2f}s  |  RPS: {n/elapsed:.1f}")
    return success == n


# ── Self-test mode: start server in background then test ──────────────────────

def selftest():
    try:
        from fastapi import FastAPI
        import uvicorn
    except ImportError:
        print("  pip install fastapi uvicorn requests")
        return

    from day36_test import build_app
    app = build_app()

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000,
                                           log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)   # wait for startup
    run_tests("http://127.0.0.1:8000")
    server.should_exit = True


# ── Main ──────────────────────────────────────────────────────────────────────

def run_tests(base):
    test_fns = [
        ("GET /health",                  test_health),
        ("GET /stats",                   test_stats),
        ("GET /violations?limit=5",      test_violations_list),
        ("GET /violations/search?plate", test_violations_search),
        ("search min_length validation", test_invalid_search_rejected),
        ("GET /counts/hourly",           test_hourly),
    ]
    print(f"\n  Testing API at {base}\n")
    passed = 0; failed = 0
    for name, fn in test_fns:
        try:
            fn(base)
            print(f"  ✓  {name}")
            passed += 1
        except Exception as e:
            print(f"  ✗  {name}  →  {e}")
            failed += 1

    load_ok = load_test(base)
    if load_ok: passed += 1
    else:        failed += 1

    print(f"\n  Results: {passed} passed, {failed} failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 37 — API Testing")
    parser.add_argument("--base",     default=BASE_URL)
    parser.add_argument("--selftest", action="store_true",
                        help="Start server in background and test")
    args = parser.parse_args()

    print("=" * 65)
    print("  DAY 37 — REST API Testing")
    print("=" * 65)

    if not HAS_REQUESTS:
        print("  pip install requests")
    elif args.selftest:
        selftest()
    else:
        try:
            requests.get(f"{args.base}/health", timeout=2) # type: ignore
            run_tests(args.base)
        except Exception:
            print(f"\n  Cannot reach {args.base}")
            print("  Start the server first:  python day36_test.py")
            print("  Or run:                  python day37_test.py --selftest")

    print("\n  Next → python day38_test.py  (Docker containerization)")
