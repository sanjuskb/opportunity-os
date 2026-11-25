"""
CPU-friendly contrastive fine-tuning of sentence-transformers/all-MiniLM-L6-v2 for NexteRaS.

Implements:
- Leakage-verified synthetic splits (`matching_curriculum_v2.json` by default)
- Contrastive hard-negative triplet training (`anchor`, `positive`, `negative`) via MultipleNegativesRankingLoss
- Epoch-by-epoch validation retrieval checkpoint selection (test split kept 100% untouched until final eval)
- Versioned artifact export (`ml/artifacts/minilm-nexteras-v1`) without overwriting pretrained baseline
- Peak RSS memory & per-query CPU latency comparison across both untouched test splits
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import psutil

ML_PARENT = Path(__file__).resolve().parents[2]
if str(ML_PARENT) not in sys.path:
    sys.path.insert(0, str(ML_PARENT))

from ml.src.common.config import configure_cpu_runtime, load_yaml_config, resolve_repo_path, seed_everything
from ml.src.data.matching_dataset import write_processed_splits
from ml.src.evaluation.retrieval_metrics import evaluate_sentence_transformer


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mem_mb() -> float:
    return round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 1)


def _check_embeddings_integrity(model: Any, sample_texts: list[str]) -> dict[str, Any]:
    emb = model.encode(sample_texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(emb, axis=1)
    return {
        "embedding_dim": int(emb.shape[1]),
        "sample_count": int(emb.shape[0]),
        "min_l2_norm": round(float(np.min(norms)), 6),
        "max_l2_norm": round(float(np.max(norms)), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune all-MiniLM-L6-v2 on CPU for NexteRaS")
    parser.add_argument(
        "--config",
        type=str,
        default="ml/model_configs/minilm_cpu_finetune.yaml",
        help="Path to CPU training YAML configuration",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate splits, config, and CPU runtime without downloading weights or training",
    )
    args = parser.parse_args()

    cfg = load_yaml_config(args.config)
    seed = int(cfg.get("seed", 42))
    seed_everything(seed)
    runtime = configure_cpu_runtime(int(cfg["hardware"].get("cpu_threads", 6)))

    seed_path = resolve_repo_path(cfg["data"]["seed_file"])
    processed_dir = resolve_repo_path(cfg["data"]["processed_dir"])
    counts = write_processed_splits(seed_path, processed_dir)

    print("=== NexteRaS CPU Fine-Tuning Pipeline ===")
    print("Runtime:", json.dumps(runtime))
    print("Dataset Seed:", seed_path.name)
    print("Splits (zero leakage & false-negative check passed):", json.dumps(counts))
    print(f"Base Model: {cfg['model']['base_model_name']} | Loss: {cfg['training']['loss']}")
    print(
        f"CPU Schedule: epochs={cfg['training']['epochs']}, batch_size={cfg['training']['batch_size']}, "
        f"lr={cfg['training']['learning_rate']}"
    )

    if args.dry_run:
        print("[DRY RUN] Validation complete. Run without --dry-run to train on CPU.")
        return

    from datasets import Dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
        SentenceTransformerTrainingArguments,
    )
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
    from transformers import TrainerCallback

    train_rows = _read_jsonl(resolve_repo_path(cfg["data"]["train_file"]))
    val_pairs_key = "val_pairs_file" if "val_pairs_file" in cfg["data"] else "val_file"
    val_rows = _read_jsonl(resolve_repo_path(cfg["data"][val_pairs_key]))
    test_queries = _read_jsonl(resolve_repo_path(cfg["data"]["test_queries_file"]))
    test_corpus = _read_jsonl(resolve_repo_path(cfg["data"]["test_corpus_file"]))

    val_queries_path = resolve_repo_path(cfg["data"].get("val_queries_file", processed_dir / "val_queries.jsonl"))
    val_corpus_path = resolve_repo_path(cfg["data"].get("val_corpus_file", processed_dir / "val_corpus.jsonl"))
    val_queries = _read_jsonl(val_queries_path) if val_queries_path.exists() else []
    val_corpus = _read_jsonl(val_corpus_path) if val_corpus_path.exists() else []

    use_hn = bool(cfg["training"].get("use_hard_negatives", True)) and all("negative" in r for r in train_rows)
    if use_hn:
        train_ds = Dataset.from_list(
            [{"anchor": r["anchor"], "positive": r["positive"], "negative": r["negative"]} for r in train_rows]
        )
        val_ds = Dataset.from_list(
            [{"anchor": r["anchor"], "positive": r["positive"], "negative": r["negative"]} for r in val_rows]
            if all("negative" in r for r in val_rows)
            else [{"anchor": r["anchor"], "positive": r["positive"]} for r in val_rows]
        )
    else:
        train_ds = Dataset.from_list([{"anchor": r["anchor"], "positive": r["positive"]} for r in train_rows])
        val_ds = Dataset.from_list([{"anchor": r["anchor"], "positive": r["positive"]} for r in val_rows])

    output_model_dir = resolve_repo_path(cfg["output"]["model_dir"])
    best_tmp_dir = output_model_dir.parent / "_best_val_ckpt_tmp"
    trainer_tmp_dir = output_model_dir / "_trainer_tmp"
    report_dir = resolve_repo_path(cfg["output"]["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    if best_tmp_dir.exists():
        shutil.rmtree(best_tmp_dir, ignore_errors=True)
    if trainer_tmp_dir.exists():
        shutil.rmtree(trainer_tmp_dir, ignore_errors=True)

    base_model_name = str(cfg["model"]["base_model_name"])
    rss_start = _mem_mb()
    t_load0 = time.perf_counter()
    print(f"\n[1/5] Loading pretrained baseline '{base_model_name}' on CPU...")
    model = SentenceTransformer(base_model_name, device="cpu")
    model.max_seq_length = int(cfg["model"].get("max_sequence_length", 256))
    baseline_load_ms = round((time.perf_counter() - t_load0) * 1000.0, 2)

    print("[2/5] Measuring BASELINE metrics BEFORE fine-tuning (val + untouched test)...")
    baseline_val_metrics = (
        evaluate_sentence_transformer(model, val_queries, val_corpus) if val_queries and val_corpus else {}
    )
    baseline_test_metrics = evaluate_sentence_transformer(model, test_queries, test_corpus)
    baseline_integrity = _check_embeddings_integrity(model, [str(test_queries[0]["query_text"])])
    rss_baseline_peak = _mem_mb()

    # Track starter reference test split if configured
    starter_baseline_metrics: dict[str, Any] = {}
    if cfg["data"].get("starter_reference_seed_file"):
        starter_proc = processed_dir / "_starter_ref"
        write_processed_splits(resolve_repo_path(cfg["data"]["starter_reference_seed_file"]), starter_proc)
        sq = _read_jsonl(starter_proc / "test_queries.jsonl")
        sc = _read_jsonl(starter_proc / "test_corpus.jsonl")
        starter_baseline_metrics = evaluate_sentence_transformer(model, sq, sc)

    epoch_validation_history: list[dict[str, Any]] = []
    best_state = {
        "epoch": 0,
        "selection_score": (
            baseline_val_metrics.get("ndcg_at_10", 0.0) + 0.35 * baseline_val_metrics.get("mean_pos_neg_margin", 0.0)
            if baseline_val_metrics
            else -1.0
        ),
        "val_metrics": baseline_val_metrics,
    }
    if baseline_val_metrics:
        model.save_pretrained(str(best_tmp_dir))

    class _ValidationSelectionCallback(TrainerCallback):
        def on_epoch_end(self, cb_args: Any, state: Any, control: Any, **kwargs: Any) -> None:
            ep = round(float(state.epoch or 0.0), 2)
            if not (val_queries and val_corpus):
                return
            metrics = evaluate_sentence_transformer(model, val_queries, val_corpus)
            sel_score = round(metrics["ndcg_at_10"] + 0.35 * metrics["mean_pos_neg_margin"], 4)
            rec = {
                "epoch": ep,
                "selection_score": sel_score,
                **metrics,
            }
            epoch_validation_history.append(rec)
            print(
                f"  [Val Epoch {ep}] R@1={metrics['recall_at_1']:.4f} MRR@10={metrics['mrr_at_10']:.4f} "
                f"nDCG@10={metrics['ndcg_at_10']:.4f} margin={metrics['mean_pos_neg_margin']:+.4f} "
                f"(score={sel_score:.4f})"
            )
            if sel_score >= best_state["selection_score"]:
                best_state["epoch"] = ep
                best_state["selection_score"] = sel_score
                best_state["val_metrics"] = metrics
                model.save_pretrained(str(best_tmp_dir))

    training_args = SentenceTransformerTrainingArguments(
        output_dir=str(trainer_tmp_dir),
        num_train_epochs=int(cfg["training"]["epochs"]),
        per_device_train_batch_size=int(cfg["training"]["batch_size"]),
        per_device_eval_batch_size=int(cfg["training"]["batch_size"]),
        learning_rate=float(cfg["training"]["learning_rate"]),
        warmup_steps=float(cfg["training"].get("warmup_ratio", 0.1)),
        weight_decay=float(cfg["training"].get("weight_decay", 0.01)),
        fp16=False,
        bf16=False,
        use_cpu=True,
        eval_strategy="epoch",
        logging_strategy="epoch",
        save_strategy="no",
        report_to="none",
        seed=seed,
        data_seed=seed,
    )

    loss_fn = MultipleNegativesRankingLoss(model=model)
    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        loss=loss_fn,
        callbacks=[_ValidationSelectionCallback()],
    )

    print(
        f"\n[3/5] Running CPU fine-tuning ({len(train_ds)} training {'triplets' if use_hn else 'pairs'}, "
        f"{cfg['training']['epochs']} epochs)..."
    )
    t0 = time.perf_counter()
    trainer.train()
    train_seconds = round(time.perf_counter() - t0, 2)
    rss_train_peak = _mem_mb()

    # Promote best validation checkpoint to final versioned output directory
    output_model_dir.mkdir(parents=True, exist_ok=True)
    if trainer_tmp_dir.exists():
        shutil.rmtree(trainer_tmp_dir, ignore_errors=True)
    if best_tmp_dir.exists():
        best_model = SentenceTransformer(str(best_tmp_dir), device="cpu")
        best_model.save_pretrained(str(output_model_dir))
        shutil.rmtree(best_tmp_dir, ignore_errors=True)
    else:
        model.save_pretrained(str(output_model_dir))
    del model, trainer
    gc.collect()

    print(f"[4/5] Selected best validation epoch={best_state['epoch']} -> saved checkpoint to {output_model_dir}")

    # Load freshly saved checkpoint from disk to verify cold load, integrity, RAM, and untouched test performance
    t_ft_load0 = time.perf_counter()
    finetuned_model = SentenceTransformer(str(output_model_dir), device="cpu")
    finetuned_load_ms = round((time.perf_counter() - t_ft_load0) * 1000.0, 2)

    print("[5/5] Evaluating FINE-TUNED checkpoint on UNTOUCHED held-out test split...")
    finetuned_test_metrics = evaluate_sentence_transformer(finetuned_model, test_queries, test_corpus)
    finetuned_integrity = _check_embeddings_integrity(finetuned_model, [str(test_queries[0]["query_text"])])
    rss_eval_peak = _mem_mb()

    starter_finetuned_metrics: dict[str, Any] = {}
    if starter_baseline_metrics:
        starter_proc = processed_dir / "_starter_ref"
        sq = _read_jsonl(starter_proc / "test_queries.jsonl")
        sc = _read_jsonl(starter_proc / "test_corpus.jsonl")
        starter_finetuned_metrics = evaluate_sentence_transformer(finetuned_model, sq, sc)

    delta = {
        k: round(finetuned_test_metrics[k] - baseline_test_metrics[k], 4)
        for k in ("recall_at_1", "recall_at_3", "recall_at_5", "mrr_at_10", "ndcg_at_10", "mean_pos_neg_margin")
    }

    run_summary = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "experiment_name": cfg["experiment_name"],
        "base_model_name": base_model_name,
        "artifact_dir": str(output_model_dir.relative_to(ML_PARENT)),
        "is_synthetic_data": True,
        "used_hard_negatives_in_training": use_hn,
        "runtime": runtime,
        "split_counts": counts,
        "training_schedule": {
            "epochs": int(cfg["training"]["epochs"]),
            "batch_size": int(cfg["training"]["batch_size"]),
            "learning_rate": float(cfg["training"]["learning_rate"]),
            "warmup_ratio": float(cfg["training"].get("warmup_ratio", 0.1)),
            "weight_decay": float(cfg["training"].get("weight_decay", 0.01)),
            "loss": str(cfg["training"]["loss"]),
        },
        "train_duration_seconds": train_seconds,
        "best_validation_epoch": best_state["epoch"],
        "best_validation_selection_score": best_state["selection_score"],
        "epoch_validation_history": epoch_validation_history,
        "memory_profile_mb": {
            "rss_start_mb": rss_start,
            "rss_baseline_eval_mb": rss_baseline_peak,
            "rss_train_peak_mb": rss_train_peak,
            "rss_finetuned_eval_mb": rss_eval_peak,
            "baseline_model_load_ms": baseline_load_ms,
            "finetuned_model_load_ms": finetuned_load_ms,
        },
        "embedding_integrity": {
            "baseline": baseline_integrity,
            "finetuned": finetuned_integrity,
        },
        "baseline_val_metrics": baseline_val_metrics,
        "best_val_metrics": best_state["val_metrics"],
        "baseline_metrics": baseline_test_metrics,
        "finetuned_metrics": finetuned_test_metrics,
        "delta_metrics": delta,
        "starter_reference_regression": {
            "baseline": starter_baseline_metrics,
            "finetuned": starter_finetuned_metrics,
        },
        "limitations": [
            "Trained and evaluated on explicitly labeled synthetic pairs (`is_synthetic: true`), not real student/portal logs.",
            "Hard negatives use domain-disjoint keyword distractors to eliminate false negatives; fine-grained within-domain seniority nuances still require real interaction feedback.",
            "Hard deterministic rules (CGPA, batch year, degree, location, backlogs) remain mandatory outside dense cosine scoring.",
        ],
    }

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    stamped_path = report_dir / f"{ts}_minilm_comparison.json"
    latest_path = report_dir / "latest_minilm_training_report.json"
    payload_str = json.dumps(run_summary, indent=2, ensure_ascii=False)
    stamped_path.write_text(payload_str, encoding="utf-8")
    latest_path.write_text(payload_str, encoding="utf-8")

    print("\n=== Side-by-Side Comparison (Untouched Held-Out Test Split) ===")
    print("Baseline:  ", json.dumps(baseline_test_metrics))
    print("Fine-tuned:", json.dumps(finetuned_test_metrics))
    print("Delta:     ", json.dumps(delta))
    print("Starter Ref Regression:", json.dumps(run_summary["starter_reference_regression"]))
    print(f"Comparison report written to: {latest_path} & {stamped_path}")


if __name__ == "__main__":
    main()
