"""
Opportunity OS - Reproducible Model Training Script
Owner: Sanju (Frontend & ML Lead)
"""
import argparse
import sys
import yaml
from pathlib import Path

def set_seed(seed: int = 42):
    try:
        import random
        import numpy as np
        random.seed(seed)
        np.random.seed(seed)
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def main():
    parser = argparse.ArgumentParser(description="Train Opportunity OS matching models")
    default_config = Path(__file__).parent.parent / "model_configs" / "baseline_matching.yaml"
    parser.add_argument("--config", type=str, default=str(default_config), help="Path to config YAML")
    args = parser.parse_args()

    print(f"[ML Pipeline] Loading configuration from {args.config}...")
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"[ML Pipeline] Error: Config file {args.config} not found.")
        sys.exit(1)

    set_seed(config.get("seed", 42))
    print(f"[ML Pipeline] Initialized experiment: {config.get('experiment_name')}")
    print(f"[ML Pipeline] Base model: {config.get('model', {}).get('name')}")
    print("[ML Pipeline] Training pipeline scaffold ready for Phase 6 sprint experimentation.")

if __name__ == "__main__":
    main()
