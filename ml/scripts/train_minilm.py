"""CPU-friendly fine-tuning of sentence-transformers/all-MiniLM-L6-v2 for NexteRaS."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ML_PARENT = Path(__file__).resolve().parents[2]
if str(ML_PARENT) not in sys.path:
    sys.path.insert(0, str(ML_PARENT))

from ml.src.common.config import configure_cpu_runtime, load_yaml_config, resolve_repo_path, seed_everything
from ml.src.data.matching_dataset import write_processed_splits
from ml.src.evaluation.retrieval_metrics import evaluate_sentence_transformer


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune all-MiniLM-L6-v2 on CPU for NexteRaS")
    parser.add_argument(
        "--config",
        type=str,
        default="ml/model_configs/personal_minilm_cpu.yaml",
        help="Path to personal CPU training YAML configuration",
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

    print("=== NexteRaS Personal CPU Training Setup ===")
    print("Runtime:", json.dumps(runtime))
    print("Splits (zero leakage verified):", json.dumps(counts))
    print(f"Base Model: {cfg['model']['base_model_name']} | Loss: {cfg['training']['loss']}")
    print(
        f"CPU Schedule: epochs={cfg['training']['epochs']}, batch_size={cfg['training']['batch_size']}, "
        f"lr={cfg['training']['learning_rate']}"
    )

    if args.dry_run:
        print("[DRY RUN] Validation complete. Run without --dry-run to train on CPU (~1.5-4 min).")
        return

    from datasets import Dataset
    from sentence_transformers import (
        SentenceTransformer,
        SentenceTransformerTrainer,
        SentenceTransformerTrainingArguments,
    )
    from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss

    train_rows = _read_jsonl(resolve_repo_path(cfg["data"]["train_file"]))
    val_rows = _read_jsonl(resolve_repo_path(cfg["data"]["val_file"]))
    test_queries = _read_jsonl(resolve_repo_path(cfg["data"]["test_queries_file"]))
    test_corpus = _read_jsonl(resolve_repo_path(cfg["data"]["test_corpus_file"]))

    train_ds = Dataset.from_list([{"anchor": r["anchor"], "positive": r["positive"]} for r in train_rows])
    val_ds = Dataset.from_list([{"anchor": r["anchor"], "positive": r["positive"]} for r in val_rows])

    base_model_name = str(cfg["model"]["base_model_name"])
    print(f"\n[1/4] Loading pretrained model '{base_model_name}' on CPU...")
    model = SentenceTransformer(base_model_name, device="cpu")
    model.max_seq_length = int(cfg["model"].get("max_sequence_length", 256))

    print("[2/4] Measuring BASELINE metrics BEFORE fine-tuning on held-out test split...")
    baseline_metrics = evaluate_sentence_transformer(model, test_queries, test_corpus)
    print("Baseline:", json.dumps(baseline_metrics, indent=2))

    output_model_dir = resolve_repo_path(cfg["output"]["model_dir"])
    output_model_dir.mkdir(parents=True, exist_ok=True)
    report_dir = resolve_repo_path(cfg["output"]["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)

    training_args = SentenceTransformerTrainingArguments(
        output_dir=str(output_model_dir / "_trainer_tmp"),
        num_train_epochs=int(cfg["training"]["epochs"]),
        per_device_train_batch_size=int(cfg["training"]["batch_size"]),
        per_device_eval_batch_size=int(cfg["training"]["batch_size"]),
        learning_rate=float(cfg["training"]["learning_rate"]),
        warmup_ratio=float(cfg["training"].get("warmup_ratio", 0.1)),
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
    )

    print("\n[3/4] Running CPU fine-tuning with MultipleNegativesRankingLoss...")
    t0 = time.perf_counter()
    trainer.train()
    train_seconds = round(time.perf_counter() - t0, 2)
    model.save_pretrained(str(output_model_dir))
    print(f"Saved fine-tuned checkpoint to {output_model_dir} in {train_seconds}s")

    print("\n[4/4] Measuring FINE-TUNED metrics AFTER training on held-out test split...")
    finetuned_metrics = evaluate_sentence_transformer(model, test_queries, test_corpus)
    delta = {
        k: round(finetuned_metrics[k] - baseline_metrics[k], 4)
        for k in ("recall_at_1", "recall_at_3", "recall_at_5", "mrr_at_10", "ndcg_at_10", "mean_pos_neg_margin")
    }

    run_summary = {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "experiment_name": cfg["experiment_name"],
        "is_synthetic_data": True,
        "runtime": runtime,
        "split_counts": counts,
        "train_duration_seconds": train_seconds,
        "baseline_metrics": baseline_metrics,
        "finetuned_metrics": finetuned_metrics,
        "delta_metrics": delta,
        "log_history": trainer.state.log_history,
        "limitations": [
            "Trained on small synthetic starter pairs (is_synthetic=true); does not establish production portal generalization.",
            "Hard deterministic rules (CGPA, batch year, degree) remain mandatory outside embedding ranking.",
        ],
    }

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"{ts}_minilm_comparison.json"
    report_path.write_text(json.dumps(run_summary, indent=2), encoding="utf-8")

    print("\n=== Side-by-Side Comparison (Held-Out Test Split) ===")
    print("Baseline:  ", json.dumps(baseline_metrics))
    print("Fine-tuned:", json.dumps(finetuned_metrics))
    print("Delta:     ", json.dumps(delta))
    print(f"Comparison report written to: {report_path}")


if __name__ == "__main__":
    main()
