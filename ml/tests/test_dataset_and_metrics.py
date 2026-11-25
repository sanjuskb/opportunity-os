"""Unit tests for NexteRaS ML dataset validation, split isolation, and IR metrics."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.common.config import load_yaml_config
from ml.src.data.matching_dataset import (
    load_seed_records,
    validate_no_split_leakage,
    write_processed_splits,
)
from ml.src.evaluation.retrieval_metrics import (
    compute_retrieval_summary,
    cosine_similarity_matrix,
    score_ranked_ids,
)


def test_seed_dataset_schema_and_zero_leakage(tmp_path: Path) -> None:
    seed_path = REPO_ROOT / "ml" / "datasets" / "synthetic" / "matching_seed_examples.json"
    records = load_seed_records(seed_path)
    assert len(records) >= 30
    assert all(r.is_synthetic for r in records)

    # Raises if any student_id or opportunity_id leaks across train/val/test
    validate_no_split_leakage(records)

    counts = write_processed_splits(seed_path, tmp_path)
    assert counts["train_pairs"] >= 18
    assert counts["val_pairs"] >= 5
    assert counts["test_queries"] >= 6
    assert counts["test_corpus_docs"] > counts["test_queries"]


def test_personal_cpu_config_bounds() -> None:
    cfg = load_yaml_config("ml/model_configs/personal_minilm_cpu.yaml")
    assert cfg["hardware"]["device"] == "cpu"
    assert cfg["hardware"]["use_fp16"] is False
    assert cfg["model"]["base_model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
    assert cfg["training"]["batch_size"] <= 16


def test_retrieval_metrics_exactness() -> None:
    single = score_ranked_ids(["d2", "d1", "d3"], {"d1"})
    assert single["recall_at_1"] == 0.0
    assert single["recall_at_3"] == 1.0
    assert single["mrr_at_10"] == 0.5

    q = np.array([[1.0, 0.0], [0.0, 1.0]])
    d = np.array([[1.0, 0.0], [0.0, 1.0], [0.2, 0.2]])
    sim = cosine_similarity_matrix(q, d)
    summary = compute_retrieval_summary(sim, [{"a"}, {"b"}], ["a", "b", "c"])
    assert summary["recall_at_1"] == 1.0
    assert summary["mrr_at_10"] == 1.0
    assert summary["ndcg_at_10"] == 1.0
    assert summary["mean_pos_neg_margin"] > 0.0
