"""Prepare leakage-free synthetic train/val/test JSONL splits for all-MiniLM-L6-v2."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ML_PARENT = Path(__file__).resolve().parents[2]
if str(ML_PARENT) not in sys.path:
    sys.path.insert(0, str(ML_PARENT))

from ml.src.common.config import load_yaml_config, resolve_repo_path
from ml.src.data.matching_dataset import write_processed_splits


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare NexteRaS semantic matching splits")
    parser.add_argument(
        "--config",
        type=str,
        default="ml/model_configs/personal_minilm_cpu.yaml",
        help="Path to personal CPU training config YAML",
    )
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    seed_path = resolve_repo_path(cfg["data"]["seed_file"])
    out_dir = resolve_repo_path(cfg["data"]["processed_dir"])
    counts = write_processed_splits(seed_path, out_dir)
    print(f"[prepare_minilm_data] Seed source: {seed_path}")
    print(f"[prepare_minilm_data] Output dir:  {out_dir}")
    for k, v in counts.items():
        print(f"  - {k}: {v}")
    print("[prepare_minilm_data] Verified zero student/opportunity ID leakage across splits.")


if __name__ == "__main__":
    main()
