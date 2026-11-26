"""Retrieval and semantic ranking metrics (Recall@K, MRR@K, nDCG@K) for NexteRaS."""

from __future__ import annotations

import math
import time
from typing import Any, Iterable

import numpy as np


def cosine_similarity_matrix(queries: np.ndarray, docs: np.ndarray) -> np.ndarray:
    """Compute exact L2-normalized cosine similarity matrix [Q, D]."""
    q_norm = queries / np.clip(np.linalg.norm(queries, axis=1, keepdims=True), 1e-12, None)
    d_norm = docs / np.clip(np.linalg.norm(docs, axis=1, keepdims=True), 1e-12, None)
    return q_norm @ d_norm.T


def score_ranked_ids(ranked_doc_ids: list[str], positive_doc_ids: set[str]) -> dict[str, float]:
    """Compute per-query single-or-multi relevant IR metrics."""
    rr = 0.0
    for rank, doc_id in enumerate(ranked_doc_ids[:10], start=1):
        if doc_id in positive_doc_ids:
            rr = 1.0 / rank
            break

    dcg = 0.0
    for rank, doc_id in enumerate(ranked_doc_ids[:10], start=1):
        if doc_id in positive_doc_ids:
            dcg += 1.0 / math.log2(rank + 1)

    ideal_hits = min(10, len(positive_doc_ids))
    idcg = sum(1.0 / math.log2(r + 1) for r in range(1, ideal_hits + 1)) or 1.0
    ndcg_10 = dcg / idcg

    return {
        "recall_at_1": 1.0 if any(d in positive_doc_ids for d in ranked_doc_ids[:1]) else 0.0,
        "recall_at_3": 1.0 if any(d in positive_doc_ids for d in ranked_doc_ids[:3]) else 0.0,
        "recall_at_5": 1.0 if any(d in positive_doc_ids for d in ranked_doc_ids[:5]) else 0.0,
        "mrr_at_10": rr,
        "ndcg_at_10": ndcg_10,
    }


def compute_retrieval_summary(
    sim_matrix: np.ndarray,
    query_positives: list[set[str]],
    corpus_doc_ids: list[str],
) -> dict[str, float]:
    """Aggregate mean IR metrics + positive-vs-best-negative similarity margin."""
    if sim_matrix.shape[0] != len(query_positives):
        raise ValueError("Mismatch between similarity rows and queries count.")
    per_query: list[dict[str, float]] = []
    margins: list[float] = []

    for qi, pos_set in enumerate(query_positives):
        scores = sim_matrix[qi]
        order = np.argsort(-scores)
        ranked_ids = [corpus_doc_ids[int(idx)] for idx in order]
        per_query.append(score_ranked_ids(ranked_ids, pos_set))

        pos_scores = [float(scores[j]) for j, d in enumerate(corpus_doc_ids) if d in pos_set]
        neg_scores = [float(scores[j]) for j, d in enumerate(corpus_doc_ids) if d not in pos_set]
        if pos_scores and neg_scores:
            margins.append(max(pos_scores) - max(neg_scores))

    keys = ("recall_at_1", "recall_at_3", "recall_at_5", "mrr_at_10", "ndcg_at_10")
    summary: dict[str, float] = {
        k: round(float(np.mean([row[k] for row in per_query])), 4) for k in keys
    }
    summary["mean_pos_neg_margin"] = round(float(np.mean(margins)) if margins else 0.0, 4)
    summary["num_queries"] = float(len(query_positives))
    summary["corpus_size"] = float(len(corpus_doc_ids))
    return summary


def evaluate_sentence_transformer(
    model: Any,
    queries: Iterable[dict[str, Any]],
    corpus: Iterable[dict[str, Any]],
) -> dict[str, float]:
    """Encode queries and corpus using SentenceTransformer and return retrieval metrics."""
    q_list = list(queries)
    c_list = list(corpus)
    q_texts = [str(q["query_text"]) for q in q_list]
    c_texts = [str(c["doc_text"]) for c in c_list]
    c_ids = [str(c["doc_id"]) for c in c_list]
    positives = [{str(q["positive_doc_id"])} for q in q_list]

    t0 = time.perf_counter()
    q_emb = model.encode(q_texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    c_emb = model.encode(c_texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    sim = cosine_similarity_matrix(q_emb, c_emb)
    metrics = compute_retrieval_summary(sim, positives, c_ids)
    metrics["encode_latency_total_ms"] = round(elapsed_ms, 2)
    metrics["encode_latency_per_query_ms"] = round(elapsed_ms / max(1, len(q_list)), 2)
    return metrics
