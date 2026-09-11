#!/usr/bin/env python3
"""
Focused concurrency probe for POST /api/query.

Pre-seeds users (so the bcrypt register/login burst happens BEFORE the timed
window), then hammers /api/query at increasing concurrency, reporting
wall-clock percentiles. Useful to see server-side throughput independent of
registration cost and locust client overhead.

Usage:
    python probe_query.py [--users 60] [--duration 30] [--base http://localhost:8000]
"""

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.request


def http_json(url, data=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def seed_users(base, n):
    tokens = []
    for i in range(n):
        email = f"probe_{i}_{int(time.time())}@loadmailx.io"
        r = http_json(f"{base}/api/auth/register",
                      {"email": email, "password": "probepass1"})
        tokens.append(r["access_token"])
    return tokens


def pct(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, int(len(s) * p / 100))]


def hammer(base, token, chat_id, duration, stats):
    end = time.monotonic() + duration
    lat = []
    ok = 0
    err = 0
    while time.monotonic() < end:
        t0 = time.perf_counter()
        try:
            http_json(f"{base}/api/query",
                      {"conversation_id": str(chat_id), "query": "Detect water bodies", "image_ids": []},
                      token=token)
            ok += 1
            lat.append((time.perf_counter() - t0) * 1000)
        except Exception:
            err += 1
    stats["ok"] += ok
    stats["err"] += err
    stats["lat"].extend(lat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=60)
    ap.add_argument("--duration", type=int, default=25)
    ap.add_argument("--base", default="http://localhost:8000")
    args = ap.parse_args()

    print("seeding users...", flush=True)
    tokens = seed_users(args.base, args.users)
    token = tokens[0]
    r = http_json(f"{args.base}/api/chats", {"title": "probe"}, token=token)
    chat_id = r["id"]
    print(f"seeded {args.users} users, chat_id={chat_id}")

    for level in (1, 10, 25, 50, 100):
        results = {"ok": 0, "err": 0, "lat": []}
        start = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=level) as ex:
            futs = [
                ex.submit(hammer, args.base, tokens[i % args.users], chat_id,
                          args.duration, results)
                for i in range(level)
            ]
            for f in futs:
                f.result()
        dur = time.monotonic() - start
        lat = results["lat"]
        err_rate = results["err"] / max(1, results["ok"] + results["err"]) * 100
        print(
            f"conc={level:>4} ok={results['ok']:>6} err={results['err']:>4} "
            f"err%={err_rate:>5.2f} rps={results['ok']/dur:>7.1f} "
            f"p50={pct(lat,50):>7.1f}ms p95={pct(lat,95):>7.1f}ms p99={pct(lat,99):>7.1f}ms "
            f"max={max(lat):>7.1f}ms", flush=True
        )


if __name__ == "__main__":
    main()