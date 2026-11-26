"""
Master Reproducible ML Evaluation Suite for NexteRaS (`ml` branch).
Evaluates deterministic/offline components AND optional sequential pretrained Hugging Face models
one component at a time (protecting ~16 GB Windows laptop RAM via explicit cache clearing/unloading).

IMPORTANT: Never trains or overwrites Sanju's personal `all-MiniLM-L6-v2` fine-tuning checkpoint!
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ml.src.common.config import configure_cpu_runtime, resolve_repo_path
from ml.src.data.matching_dataset import write_processed_splits
from ml.src.eligibility.engine import DeterministicEligibilityEngine
from ml.src.evaluation.eligibility_eval import evaluate_eligibility_benchmark
from ml.src.evaluation.extraction_eval import evaluate_extraction_benchmark
from ml.src.evaluation.ranking_eval import evaluate_ranking_benchmark
from ml.src.evaluation.retrieval_metrics import evaluate_sentence_transformer
from ml.src.evaluation.verification_eval import evaluate_verification_benchmark
from ml.src.extraction.extractor import ResumeExtractionService
from ml.src.infrastructure.model_registry import ModelRegistry
from ml.src.infrastructure.runtime import GLOBAL_MODEL_CACHE
from ml.src.multilingual.audit import evaluate_multilingual_corpus
from ml.src.multilingual.service import MultilingualUnderstandingService
from ml.src.ranking.baseline_ranker import DeterministicOpportunityRanker
from ml.src.verification.verifier import EvidenceVerificationService


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _mem_mb() -> float:
    return round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NexteRaS ML subsystem evaluations")
    parser.add_argument(
        "--components",
        nargs="+",
        default=["extraction", "eligibility", "ranking", "semantic_baseline", "multilingual", "nli"],
        choices=["extraction", "eligibility", "ranking", "semantic_baseline", "multilingual", "nli_fallback", "nli"],
        help="Evaluation components to execute sequentially",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="ml/evaluation/latest_evaluation_report.json",
        help="Output JSON report path",
    )
    args = parser.parse_args()

    runtime = configure_cpu_runtime(6)
    vm = psutil.virtual_memory()
    registry = ModelRegistry()
    results: dict[str, Any] = {}

    if "extraction" in args.components:
        rss_before = _mem_mb()
        res = evaluate_extraction_benchmark(ResumeExtractionService())
        res["process_rss_mb_after"] = _mem_mb()
        res["rss_delta_mb"] = round(res["process_rss_mb_after"] - rss_before, 1)
        results["extraction"] = res

    if "eligibility" in args.components:
        rss_before = _mem_mb()
        res = evaluate_eligibility_benchmark(DeterministicEligibilityEngine())
        res["process_rss_mb_after"] = _mem_mb()
        res["rss_delta_mb"] = round(res["process_rss_mb_after"] - rss_before, 1)
        results["eligibility"] = res

    if "ranking" in args.components:
        rss_before = _mem_mb()
        res = evaluate_ranking_benchmark(DeterministicOpportunityRanker())
        res["process_rss_mb_after"] = _mem_mb()
        res["rss_delta_mb"] = round(res["process_rss_mb_after"] - rss_before, 1)
        results["ranking"] = res

    if "semantic_baseline" in args.components:
        from sentence_transformers import SentenceTransformer

        rss_before = _mem_mb()
        seed_path = resolve_repo_path("ml/datasets/synthetic/matching_curriculum_v2.json")
        proc_dir = resolve_repo_path("ml/datasets/processed_v2")
        counts = write_processed_splits(seed_path, proc_dir)
        test_q = _read_jsonl(proc_dir / "test_queries.jsonl")
        test_c = _read_jsonl(proc_dir / "test_corpus.jsonl")

        t0 = time.perf_counter()
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
        load_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        metrics = evaluate_sentence_transformer(model, test_q, test_c)
        rss_peak = _mem_mb()
        del model
        gc.collect()
        results["semantic_baseline_pretrained"] = {
            "model_id": "sentence-transformers/all-MiniLM-L6-v2",
            "status": "PRETRAINED_BASELINE_EVALUATED",
            "dataset": "matching_curriculum_v2",
            "split_counts": counts,
            "is_synthetic": True,
            "model_load_ms": load_ms,
            "peak_rss_mb": rss_peak,
            "rss_delta_mb": round(rss_peak - rss_before, 1),
            **metrics,
        }

        tuned_dir = resolve_repo_path("ml/artifacts/minilm-nexteras-v1")
        if tuned_dir.exists() and any(tuned_dir.iterdir()):
            rss_ft_before = _mem_mb()
            t1 = time.perf_counter()
            ft_model = SentenceTransformer(str(tuned_dir), device="cpu")
            ft_load_ms = round((time.perf_counter() - t1) * 1000.0, 2)
            ft_metrics = evaluate_sentence_transformer(ft_model, test_q, test_c)
            ft_peak = _mem_mb()
            del ft_model
            gc.collect()
            results["semantic_finetuned_minilm_v1"] = {
                "model_id": "ml/artifacts/minilm-nexteras-v1",
                "base_model": "sentence-transformers/all-MiniLM-L6-v2",
                "status": "FINE_TUNED_SYNTHETIC_CPU",
                "dataset": "matching_curriculum_v2",
                "is_synthetic": True,
                "model_load_ms": ft_load_ms,
                "peak_rss_mb": ft_peak,
                "rss_delta_mb": round(ft_peak - rss_ft_before, 1),
                **ft_metrics,
            }

    if "multilingual" in args.components:
        rss_before = _mem_mb()
        svc = MultilingualUnderstandingService(cache=GLOBAL_MODEL_CACHE)
        t0 = time.perf_counter()
        svc.encode(["warmup"])
        load_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        res = evaluate_multilingual_corpus(svc)
        rss_peak = _mem_mb()
        GLOBAL_MODEL_CACHE.clear()
        res["model_load_ms"] = load_ms
        res["peak_rss_mb"] = rss_peak
        res["rss_delta_mb"] = round(rss_peak - rss_before, 1)
        results["multilingual"] = res

    if "nli_fallback" in args.components:
        rss_before = _mem_mb()
        res = evaluate_verification_benchmark(EvidenceVerificationService(use_pretrained_nli=False))
        res["peak_rss_mb"] = _mem_mb()
        results["verification_lexical_fallback"] = res

    if "nli" in args.components:
        rss_before = _mem_mb()
        svc_nli = EvidenceVerificationService(use_pretrained_nli=True)
        res = evaluate_verification_benchmark(svc_nli)
        rss_peak = _mem_mb()
        GLOBAL_MODEL_CACHE.clear()
        res["peak_rss_mb"] = rss_peak
        res["rss_delta_mb"] = round(rss_peak - rss_before, 1)
        results["verification_pretrained_nli"] = res

    out_path = resolve_repo_path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Preserve existing sections when running a single component into the same report file cleanly
    existing: dict[str, Any] = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    merged_results = {**(existing.get("results") or {}), **results}
    tuned_exists = (resolve_repo_path("ml/artifacts/minilm-nexteras-v1") / "model.safetensors").exists()
    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "system_runtime": runtime,
        "system_memory_snapshot": {
            "total_gb": round(vm.total / 1e9, 2),
            "available_gb_at_start": round(vm.available / 1e9, 2),
        },
        "registered_models_summary": registry.summary(),
        "minilm_finetuning_status": (
            "COMPLETED_SYNTHETIC_CPU (ml/artifacts/minilm-nexteras-v1)"
            if tuned_exists
            else "CHECKPOINT_ABSENT (using pretrained fallback)"
        ),
        "results": merged_results,
    }
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote evaluation report to {out_path}")
    for key, val in results.items():
        print(f"  [{key}] done -> keys={list(val.keys())[:8]}")


if __name__ == "__main__":
    main()
