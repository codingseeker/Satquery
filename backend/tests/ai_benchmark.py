"""
AI inference benchmark for SatQuery.

Measures the AI/VLM inference path directly (in-process, no HTTP overhead).
This is intentionally separate from the normal API/database load test because
inference latency must NOT be conflated with normal request latency.

Current: AI_MODE=mock -> deterministic placeholder service (CPU, no model).
When AI_MODE=real with an actual VLM, this same script reports real figures.

Measured operations:
  * Single-image VQA           (query -> mock analyze)
  * Scene description          ("Describe this scene")
  * Bi-temporal change analysis ("Detect changes between these images")
  * Optical + SAR analysis     ("Analyze optical and SAR data")

Run:
  python backend/tests/ai_benchmark.py
"""

import statistics
import sys
import time
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ai_service.factory import get_ai_service

OPERATIONS = [
    ("Single-image VQA", "What is the water coverage in this image?"),
    ("Scene description", "Describe this scene in detail."),
    ("Bi-temporal analysis", "Detect changes between the two images."),
    ("Optical + SAR analysis", "Analyze optical and SAR data for built-up areas."),
]

N = 100


def percentiles(values, ps=(50, 95, 99)):
    sorted_v = sorted(values)
    out = {}
    for p in ps:
        idx = min(len(sorted_v) - 1, int(len(sorted_v) * p / 100))
        out[p] = round(sorted_v[idx], 3)
    return out


def main():
    service = get_ai_service()
    device = "CPU (mock, no model)" if os.environ.get("AI_MODE", "mock") == "mock" else "GPU/CPU (real model)"
    model = os.environ.get("MODEL_PATH", "mock") or "mock"
    image_size = "N/A (mock service; no image decoded)"

    header = f"{'Operation':<28} {'Model':<18} {'Image Size':<28} {'Device':<26} {'N':>4} {'Mean(ms)':>9} {'p50':>7} {'p95':>7} {'p99':>7}"
    print(header)
    print("-" * len(header))

    all_results = {}
    for name, query in OPERATIONS:
        latencies = []
        for _ in range(N):
            t0 = time.perf_counter()
            service.analyze("", query)
            latencies.append((time.perf_counter() - t0) * 1000)

        mean = statistics.fmean(latencies)
        p = percentiles(latencies)
        all_results[name] = {"mean_ms": mean, "percentiles": p, "min_ms": min(latencies), "max_ms": max(latencies)}
        print(
            f"{name:<28} {model:<18} {image_size:<28} {device:<26} {N:>4} {mean:>9.3f} "
            f"{p[50]:>7.3f} {p[95]:>7.3f} {p[99]:>7.3f}"
        )

    print()
    print("Notes:")
    print("  * Mock service does pure-Python keyword classification; sub-millisecond results")
    print("    are expected and represent NO real model inference.")
    print("  * Replace AI_MODE with 'real' + MODEL_PATH to benchmark an actual VLM.")
    print("  * For real VLM inference expect seconds-scale latency; GPU memory and")
    print("    concurrent-inference capacity must be measured on the target hardware.")


if __name__ == "__main__":
    main()