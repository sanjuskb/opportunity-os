"""Schema validation, text formatting, and leakage-free splitting for matching data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class StudentProfileRecord(BaseModel):
    student_id: str
    education_year: str
    branch: str
    skills: list[str] = Field(min_length=1)
    career_interest: str
    profile_summary: str
    preferred_languages: list[str] = Field(default_factory=lambda: ["en"])


class OpportunityRecord(BaseModel):
    opportunity_id: str
    title: str
    organization: str
    domain_family: str
    description: str
    required_skills: list[str] = Field(min_length=1)
    eligible_years: list[str] = Field(min_length=1)


class MatchingPairRecord(BaseModel):
    pair_id: str
    split: Literal["train", "val", "test"]
    relevance_label: Literal[0, 1]
    is_synthetic: bool = True
    student: StudentProfileRecord
    opportunity: OpportunityRecord
    hard_negative_opportunity: OpportunityRecord | None = None

    @model_validator(mode="after")
    def validate_synthetic_flag(self) -> "MatchingPairRecord":
        if not self.is_synthetic:
            raise ValueError("Starter pipeline expects explicit provenance tagging.")
        return self


def format_student_text(student: StudentProfileRecord) -> str:
    """Serialize a student profile into bi-encoder query text."""
    return (
        f"Student Profile | Education: {student.education_year} ({student.branch}) | "
        f"Career Interest: {student.career_interest} | "
        f"Skills: {', '.join(student.skills)} | "
        f"Summary: {student.profile_summary}"
    )


def format_opportunity_text(opp: OpportunityRecord) -> str:
    """Serialize an opportunity into bi-encoder passage text."""
    return (
        f"Opportunity: {opp.title} at {opp.organization} | "
        f"Domain: {opp.domain_family} | "
        f"Eligible: {', '.join(opp.eligible_years)} | "
        f"Required Skills: {', '.join(opp.required_skills)} | "
        f"Description: {opp.description}"
    )


def load_seed_records(seed_path: Path) -> list[MatchingPairRecord]:
    """Load and Pydantic-validate synthetic starter pairs from JSON."""
    raw = json.loads(seed_path.read_text(encoding="utf-8"))
    if not raw.get("is_synthetic", False):
        raise ValueError(f"Seed file missing top-level is_synthetic=true marker: {seed_path}")
    return [MatchingPairRecord.model_validate(item) for item in raw["records"]]


def validate_no_split_leakage(records: list[MatchingPairRecord]) -> None:
    """Guarantee zero student_id or positive opportunity_id overlap across train/val/test."""
    students_by_split: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    opps_by_split: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    for rec in records:
        students_by_split[rec.split].add(rec.student.student_id)
        opps_by_split[rec.split].add(rec.opportunity.opportunity_id)

    for a, b in [("train", "val"), ("train", "test"), ("val", "test")]:
        shared_s = students_by_split[a] & students_by_split[b]
        shared_o = opps_by_split[a] & opps_by_split[b]
        if shared_s or shared_o:
            raise ValueError(
                f"Data leakage detected between '{a}' and '{b}': "
                f"students={sorted(shared_s)}, opps={sorted(shared_o)}"
            )


def write_processed_splits(seed_path: Path, out_dir: Path) -> dict[str, int]:
    """Create processed train/val JSONL files + test retrieval query/corpus JSONLs."""
    records = load_seed_records(seed_path)
    validate_no_split_leakage(records)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_rows: list[dict[str, object]] = []
    val_rows: list[dict[str, object]] = []
    test_queries: list[dict[str, object]] = []
    test_corpus_map: dict[str, dict[str, object]] = {}

    for rec in records:
        anchor_txt = format_student_text(rec.student)
        pos_txt = format_opportunity_text(rec.opportunity)
        row: dict[str, object] = {
            "pair_id": rec.pair_id,
            "student_id": rec.student.student_id,
            "opportunity_id": rec.opportunity.opportunity_id,
            "anchor": anchor_txt,
            "positive": pos_txt,
            "label": rec.relevance_label,
            "is_synthetic": rec.is_synthetic,
        }
        if rec.hard_negative_opportunity is not None:
            row["hard_negative"] = format_opportunity_text(rec.hard_negative_opportunity)
            row["hard_negative_id"] = rec.hard_negative_opportunity.opportunity_id

        if rec.split == "train" and rec.relevance_label == 1:
            train_rows.append(row)
        elif rec.split == "val" and rec.relevance_label == 1:
            val_rows.append(row)
        elif rec.split == "test" and rec.relevance_label == 1:
            test_queries.append(
                {
                    "query_id": rec.student.student_id,
                    "query_text": anchor_txt,
                    "positive_doc_id": rec.opportunity.opportunity_id,
                    "domain_family": rec.opportunity.domain_family,
                    "is_synthetic": True,
                }
            )
            test_corpus_map[rec.opportunity.opportunity_id] = {
                "doc_id": rec.opportunity.opportunity_id,
                "title": rec.opportunity.title,
                "doc_text": pos_txt,
                "domain_family": rec.opportunity.domain_family,
                "is_synthetic": True,
            }
            if rec.hard_negative_opportunity is not None:
                neg = rec.hard_negative_opportunity
                test_corpus_map.setdefault(
                    neg.opportunity_id,
                    {
                        "doc_id": neg.opportunity_id,
                        "title": neg.title,
                        "doc_text": format_opportunity_text(neg),
                        "domain_family": neg.domain_family,
                        "is_synthetic": True,
                    },
                )

    def _dump_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
        path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    _dump_jsonl(out_dir / "train_pairs.jsonl", train_rows)
    _dump_jsonl(out_dir / "val_pairs.jsonl", val_rows)
    _dump_jsonl(out_dir / "test_queries.jsonl", test_queries)
    _dump_jsonl(out_dir / "test_corpus.jsonl", list(test_corpus_map.values()))

    return {
        "train_pairs": len(train_rows),
        "val_pairs": len(val_rows),
        "test_queries": len(test_queries),
        "test_corpus_docs": len(test_corpus_map),
    }
