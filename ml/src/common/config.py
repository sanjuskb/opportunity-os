"""Common ML configuration, seeding, and CPU execution helpers for NexteRaS."""

from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ML_ROOT = Path(__file__).resolve().parents[2]


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file safely."""
    path = Path(config_path)
    if not path.is_absolute():
        candidate = REPO_ROOT / path
        path = candidate if candidate.exists() else (ML_ROOT / path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in config YAML: {path}")
    return data


def resolve_repo_path(path_value: str | Path) -> Path:
    """Resolve a relative repo path against REPO_ROOT cleanly."""
    p = Path(path_value)
    return p if p.is_absolute() else (REPO_ROOT / p)


def seed_everything(seed: int = 42) -> None:
    """Set deterministic RNG seeds across Python, NumPy, and CPU PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def configure_cpu_runtime(num_threads: int = 6) -> dict[str, Any]:
    """Configure CPU-safe defaults (no CUDA, explicit PyTorch intra-op threads)."""
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    import torch

    max_threads = max(1, min(num_threads, os.cpu_count() or num_threads))
    torch.set_num_threads(max_threads)
    return {
        "torch_version": torch.__version__,
        "device": "cpu",
        "cuda_available": bool(torch.cuda.is_available()),
        "cpu_threads": max_threads,
        "logical_cores": os.cpu_count(),
    }
