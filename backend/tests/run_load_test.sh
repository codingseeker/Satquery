#!/usr/bin/env bash
#
# Progressive-concurrency load test for SatQuery.
#
# Tests 10, 25, 50, 100, 200 concurrent users against the running backend and
# writes per-level JSON results into backend/tests/results/.
#
# Usage:
#   backend/tests/run_load_test.sh [host]
#
#   host defaults to http://localhost:8000
#
set -euo pipefail

HOST="${1:-http://localhost:8000}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="${DIR}/results"
mkdir -p "${RESULTS}"

PYTHON="${PYTHON:-python3}"
which locust >/dev/null 2>&1 || { echo "locust not on PATH; install it (pip install locust)"; exit 1; }

RUNTIME=75
RAMP_UP=20

for USERS in 10 25 50 100 200; do
    echo "=== Running load test at ${USERS} concurrent users (host=${HOST}) ==="
    locust \
        -f "${DIR}/load_test.py" \
        --headless \
        -u "${USERS}" \
        -r "${USERS}" \
        --run-time "${RUNTIME}s" \
        --spawn-rate "${RAMP_UP}" \
        --host "${HOST}" \
        --json \
        --only-summary \
        > "${RESULTS}/users_${USERS}.json" 2> "${RESULTS}/users_${USERS}.log" || {
            echo "WARN: locust run for ${USERS} users exited nonzero; see ${RESULTS}/users_${USERS}.log"
        }
    echo "--- wrote ${RESULTS}/users_${USERS}.json"
done

echo "=== Load test complete. Results in ${RESULTS}/ ==="
ls -la "${RESULTS}"