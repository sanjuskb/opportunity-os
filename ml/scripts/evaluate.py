"""
Opportunity OS - Model Evaluation & Benchmark Runner
Owner: Sanju (Frontend & ML Lead)
"""
import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Evaluate Opportunity OS models against target benchmarks")
    default_benchmarks = Path(__file__).parent.parent / "evaluation" / "benchmarks.json"
    parser.add_argument("--benchmarks", type=str, default=str(default_benchmarks), help="Path to benchmarks.json")
    args = parser.parse_args()

    print(f"[ML Evaluation] Loading benchmarks from {args.benchmarks}...")
    try:
        with open(args.benchmarks, "r", encoding="utf-8") as f:
            benchmarks = json.load(f)
    except FileNotFoundError:
        print(f"[ML Evaluation] Error: Benchmarks file {args.benchmarks} not found.")
        sys.exit(1)

    print("[ML Evaluation] Registered benchmarks:")
    for feature, details in benchmarks.get("benchmarks", {}).items():
        print(f"  - {feature}: Target {details['metric']} >= {details['target']} (Baseline: {details['baseline']})")
    
    print("[ML Evaluation] Evaluation harness ready for test runs on spare laptop.")

if __name__ == "__main__":
    main()
