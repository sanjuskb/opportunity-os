"""
NexteRaS - Registered Benchmark Summary Inspector
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect NexteRaS ML benchmark summary register")
    default_benchmarks = Path(__file__).parent.parent / "evaluation" / "benchmarks.json"
    parser.add_argument("--benchmarks", type=str, default=str(default_benchmarks), help="Path to benchmarks.json")
    args = parser.parse_args()

    print(f"[ML Evaluation] Loading benchmarks from {args.benchmarks}...")
    try:
        benchmarks = json.loads(Path(args.benchmarks).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[ML Evaluation] Error: Benchmarks file {args.benchmarks} not found.")
        sys.exit(1)

    print("[ML Evaluation] Registered benchmarks:")
    for feature, details in benchmarks.get("benchmarks", {}).items():
        metric = details.get("metric", "n/a")
        status = details.get("status", "unknown")
        measured = (
            details.get("measured_synthetic")
            or details.get("measured_synthetic_baseline")
            or details.get("measured_synthetic_nli")
            or details.get("baseline")
            or {}
        )
        print(f"  - {feature}: metric={metric} | status={status} | measured={measured}")


if __name__ == "__main__":
    main()
