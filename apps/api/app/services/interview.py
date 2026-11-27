"""Shared Gemini-assisted and rubric-backed technical interview helpers."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.gemini import GeminiClient
from app.models.entities import InterviewSession

logger = logging.getLogger("opportunity_os.services.interview")


async def generate_interview_questions(
    target_role: str,
    language: str = "en",
    *,
    gemini_client: GeminiClient | None = None,
) -> list[dict[str, Any]]:
    """Generate 3 structured technical interview questions in the requested language."""
    client = gemini_client or GeminiClient()
    if client.configured:
        try:
            raw = await client.generate_text(
                prompt=(
                    f"Generate 3 technical mock interview questions for the role '{target_role}' "
                    f"in language code '{language}' (preserving technical terms in English). "
                    "Respond strictly as JSON array of objects with keys: "
                    "question (string), difficulty ('medium'|'hard'), idealPoints (array of 3 concise strings)."
                ),
                system_instruction="You are an Indian engineering technical interviewer. Return ONLY valid JSON.",
                temperature=0.3,
            )
            cleaned = (
                raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            )
            parsed = json.loads(cleaned)
            if isinstance(parsed, list) and len(parsed) >= 1:
                items = [
                    {
                        "question": str(item.get("question", "")),
                        "difficulty": str(item.get("difficulty", "medium")),
                        "idealPoints": [str(p) for p in item.get("idealPoints", [])[:4]],
                    }
                    for item in parsed[:3]
                    if isinstance(item, dict) and item.get("question")
                ]
                if items:
                    return items
        except Exception as exc:
            logger.info("Using structured interview question bank (%s).", type(exc).__name__)

    return [
        {
            "question": f"Design a scalable backend or ML pipeline relevant to a {target_role} internship in India.",
            "difficulty": "medium",
            "idealPoints": [
                "Clear problem decomposition and latency/cost tradeoffs",
                "PostgreSQL indexing, caching, and schema choices",
                "Failure handling and verification metrics",
            ],
        },
        {
            "question": f"Describe a concrete debugging or performance optimization from one of your projects relevant to {target_role}.",
            "difficulty": "medium",
            "idealPoints": [
                "Baseline metric before the fix",
                "Root-cause diagnostic methodology",
                "Measurable post-fix outcome",
            ],
        },
        {
            "question": "How do you validate data quality and prevent edge-case failures in production APIs?",
            "difficulty": "hard",
            "idealPoints": [
                "Strict input validation (Pydantic/TypeScript schemas)",
                "Automated unit and integration tests",
                "Graceful degradation and observability",
            ],
        },
    ]


async def evaluate_interview_answer(
    *,
    target_role: str,
    question: str,
    ideal_points: list[str],
    answer: str,
    language: str,
    gemini_client: GeminiClient | None = None,
) -> dict[str, Any]:
    """Evaluate a candidate answer using Gemini or deterministic rubric matching."""
    client = gemini_client or GeminiClient()
    if client.configured:
        try:
            raw = await client.generate_text(
                prompt=(
                    f"Role: {target_role}\nQuestion: {question}\n"
                    f"Ideal points: {ideal_points}\nCandidate answer ({language}): {answer}\n"
                    "Return JSON with keys: score (0-100 int), summary (concise feedback string), "
                    "strengths (array of strings), improvements (array of strings)."
                ),
                system_instruction="Be fair, constructive, and specific. Return ONLY valid JSON.",
                temperature=0.2,
            )
            cleaned = (
                raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            )
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "score" in parsed:
                return {
                    "score": max(0, min(100, int(parsed.get("score", 75)))),
                    "summary": str(parsed.get("summary", "Evaluated candidate answer cleanly.")),
                    "strengths": [str(x) for x in parsed.get("strengths", [])[:3]],
                    "improvements": [str(x) for x in parsed.get("improvements", [])[:3]],
                }
        except Exception as exc:
            logger.info("Using rubric interview evaluator (%s).", type(exc).__name__)

    words = answer.split()
    matched = [
        pt
        for pt in ideal_points
        if any(tok.lower() in answer.lower() for tok in pt.split() if len(tok) > 4)
    ]
    score = min(96, max(45, 55 + len(matched) * 12 + min(20, len(words) // 5)))
    return {
        "score": score,
        "summary": (
            f"Strong structure with {len(words)} words; addressed {len(matched)} of "
            f"{max(1, len(ideal_points))} key rubric points."
        ),
        "strengths": matched or ["Clear attempt at explaining technical reasoning."],
        "improvements": [pt for pt in ideal_points if pt not in matched][:2]
        or ["Add specific quantitative metrics from your project benchmarks."],
    }


async def create_starter_interview_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    target_role: str,
    language: str = "en",
) -> InterviewSession:
    """Create and flush a starter mock interview session for a target role."""
    questions = await generate_interview_questions(target_role, language)
    row = InterviewSession(
        user_id=user_id,
        target_role=target_role,
        language=language,
        questions=questions,
        responses=[],
        feedback=[],
        status="in_progress",
    )
    session.add(row)
    await session.flush()
    return row
