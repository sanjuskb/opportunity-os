"""Compare original pretrained all-MiniLM-L6-v2 vs fine-tuned NexteRaS checkpoint cleanly."""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from pathlib import Path

import psutil

ML_PARENT = Path(__file__).resolve().parents[2]
if str(ML_PARENT) not in sys.path:
    sys.path.insert(0, str(ML_PARENT))

from ml.src.common.config import configure_cpu_runtime, load_yaml_config, resolve_repo_path
from ml.src.evaluation.retrieval_metrics import evaluate_sentence_transformer
from ml.src.infrastructure.runtime import ResourceManagedModelCache
from ml.src.matching.semantic_matcher import SemanticMatcher


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mem_mb() -> float:
    return round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate base vs fine-tuned all-MiniLM-L6-v2")
    parser.add_argument("--config", type=str, default="ml/model_configs/minilm_cpu_finetune.yaml")
    parser.add_argument("--tuned-model", type=str, default=None, help="Optional path to fine-tuned model folder")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    runtime = configure_cpu_runtime(int(cfg["hardware"].get("cpu_threads", 6)))
    print("Runtime:", json.dumps(runtime))

    test_queries = _read_jsonl(resolve_repo_path(cfg["data"]["test_queries_file"]))
    test_corpus = _read_jsonl(resolve_repo_path(cfg["data"]["test_corpus_file"]))

    cache = ResourceManagedModelCache(max_loaded_models=1, cpu_threads=int(cfg["hardware"].get("cpu_threads", 6)))
    base_matcher = SemanticMatcher(cfg["model"]["base_model_name"], device="cpu", cache=cache)
    t0 = time.perf_counter()
    base_model = base_matcher._get_model()
    base_load_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    base_metrics = evaluate_sentence_transformer(base_model, test_queries, test_corpus)
    base_metrics["model_load_ms"] = base_load_ms
    base_metrics["peak_rss_mb"] = _mem_mb()
    cache.clear()
    gc.collect()

    print("\nPretrained Base Metrics:")
    print(json.dumps(base_metrics, indent=2))

    tuned_path = resolve_repo_path(args.tuned_model or cfg["output"]["model_dir"])
    if tuned_path.exists() and any(tuned_path.iterdir()):
        tuned_matcher = SemanticMatcher(tuned_path, device="cpu", cache=cache)
        t1 = time.perf_counter()
        tuned_model = tuned_matcher._get_model()
        tuned_load_ms = round((time.perf_counter() - t1) * 1000.0, 2)
        tuned_metrics = evaluate_sentence_transformer(tuned_model, test_queries, test_corpus)
        tuned_metrics["model_load_ms"] = tuned_load_ms
        tuned_metrics["peak_rss_mb"] = _mem_mb()
        delta = {
            k: round(tuned_metrics[k] - base_metrics[k], 4)
            for k in ("recall_at_1", "recall_at_3", "recall_at_5", "mrr_at_10", "ndcg_at_10", "mean_pos_neg_margin")
        }
        print(f"\nFine-Tuned Checkpoint Metrics ({tuned_path}):")
        print(json.dumps(tuned_metrics, indent=2))
        print("\nDelta (Fine-Tuned - Base):")
        print(json.dumps(delta, indent=2))
        cache.clear()
    else:
        print(f"\nNo fine-tuned checkpoint found at {tuned_path}. Run train_minilm.py first to compare.")


if __name__ == "__main__":
    main()
