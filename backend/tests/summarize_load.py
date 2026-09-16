#!/usr/bin/env python3
"""
Summarizes locust ``--json`` output files into a latency table.

For each level (10/25/50/100/200 users) prints the primary workload metric
and errors, computing p50/p95/p99 from the response-time histogram.

Usage:
    python backend/tests/summarize_load.py [results_dir]
"""

import json
import os
import sys


def percentile_from_hist(hist, p):
    total = sum(hist.values())
    if total == 0:
        return 0.0
    target = total * p / 100.0
    acc = 0.0
    for ms, count in sorted(hist.items(), key=lambda kv: int(kv[0])):
        acc += count
        if acc >= target:
            return float(ms)
    return float(max(hist.keys()))


def aggregate(d):
    primary = next(
        (s for s in d if s.get("name") == "POST /api/query"), None
    )

    reqs = sum(s["num_requests"] for s in d) if d else 0
    fails = sum(s["num_failures"] for s in d) if d else 0

    out = {"requests": reqs, "failures": fails}
    if reqs:
        out["error_rate"] = (fails / reqs) * 100.0

    if primary and primary["num_requests"]:
        hist = primary["response_times"]
        out["primary"] = {
            "requests": primary["num_requests"],
            "failures": primary["num_failures"],
            "p50": percentile_from_hist(hist, 50),
            "p95": percentile_from_hist(hist, 95),
            "p99": percentile_from_hist(hist, 99),
            "min": min(hist.keys()),
            "max": max(hist.keys()),
            "rps": (
                sum(primary["num_reqs_per_sec"].values())
                / max(1, len(primary["num_reqs_per_sec"]))
            ),
        }
        if primary["num_requests"]:
            out["primary"]["error_rate"] = (
                primary["num_failures"] / primary["num_requests"]
            ) * 100.0

    total_rps_values = []
    for s in d:
        total_rps_values.extend(s["num_reqs_per_sec"].values())
    out["total_rps"] = sum(total_rps_values) / max(1, len(total_rps_values))
    return out


def main():
    results_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "results"
    )

    levels = []
    for fname in sorted(os.listdir(results_dir)):
        if fname.startswith("users_") and fname.endswith(".json"):
            levels.append(fname)

    if not levels:
        print(f"No users_*.json files found in {results_dir}")
        return

    print(f"{'Users':>7} | {'All reqs':>9} | {'Fails':>6} | {'Err%':>6} | "
          f"{'Total RPS':>9} | {'q RPS':>6} | {'q p50':>7} | {'q p95':>7} | {'q p99':>7} | {'q min':>7} | {'q max':>7} | q fails")
    print("-" * 122)

    for fname in levels:
        import re
        m = re.match(r"users_(\d+)", fname)
        label = m.group(1) if m else "?"
        with open(os.path.join(results_dir, fname)) as f:
            d = json.load(f)
        a = aggregate(d)
        line = f"{int(label):>6} | {a['requests']:>9} | {a['failures']:>6} | {a.get('error_rate', -1):>6.2f} | {a['total_rps']:>9.1f} | "
        p = a.get("primary")
        if p:
            line += (f"{p['rps']:>6.1f} | {p['p50']:>7.1f} | {p['p95']:>7.1f} | {p['p99']:>7.1f} | "
                     f"{p['min']:>7} | {p['max']:>7} | {p['failures']} ({p['error_rate']:.2f}%)")
        else:
            line += "  -- no POST /api/query traffic --"
        print(line)


if __name__ == "__main__":
    main()