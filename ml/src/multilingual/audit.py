"""Language-by-language retrieval audit across all 7 Indian languages, English, and Hinglish."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from ml.src.evaluation.retrieval_metrics import compute_retrieval_summary, cosine_similarity_matrix
from ml.src.multilingual.service import MultilingualUnderstandingService


def evaluate_multilingual_corpus(
    service: MultilingualUnderstandingService,
    dataset_path: str | Path = "ml/datasets/synthetic/multilingual_eval_corpus.json",
    *,
    weak_recall_threshold: float = 0.65,
) -> dict[str, Any]:
    raw = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
    corpus = raw["corpus"]
    doc_ids = [c["doc_id"] for c in corpus]
    doc_texts = [c["doc_text"] for c in corpus]

    t0 = time.perf_counter()
    doc_embs = service.encode(doc_texts)

    by_lang: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for q in raw["queries"]:
        by_lang[q["language"]].append(q)

    per_language: dict[str, dict[str, Any]] = {}
    weak_languages: list[str] = []
    all_q_texts = [q["query_text"] for q in raw["queries"]]
    all_pos = [{q["target_doc_id"]} for q in raw["queries"]]
    all_q_embs = service.encode(all_q_texts)
    overall_sim = cosine_similarity_matrix(all_q_embs, doc_embs)
    overall_summary = compute_retrieval_summary(overall_sim, all_pos, doc_ids)

    for lang, q_rows in sorted(by_lang.items()):
        q_texts = [r["query_text"] for r in q_rows]
        pos_sets = [{r["target_doc_id"]} for r in q_rows]
        q_embs = service.encode(q_texts)
        sim = cosine_similarity_matrix(q_embs, doc_embs)
        summary = compute_retrieval_summary(sim, pos_sets, doc_ids)
        is_weak = summary["recall_at_1"] < weak_recall_threshold or summary["mean_pos_neg_margin"] < 0.02
        if is_weak:
            weak_languages.append(lang)
        per_language[lang] = {
            **summary,
            "adequate_without_translation_fallback": not is_weak,
        }

    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "dataset": raw["dataset_name"],
        "is_synthetic": raw["is_synthetic"],
        "model_id": service.model_id,
        "overall": overall_summary,
        "per_language": per_language,
        "weak_or_fallback_recommended_languages": weak_languages,
        "total_latency_ms": elapsed_ms,
    }
