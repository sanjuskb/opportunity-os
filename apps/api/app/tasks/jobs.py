"""Domain ARQ worker tasks for WS7 (resume processing, Olostep/Crustdata jobs, analytics)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.entities import (
    AnalyticsEvent,
    Application,
    Notification,
    Opportunity,
    Profile,
    Resume,
)
from app.repositories.resumes import ResumeRepository
from app.schemas.common import CompanyEnrichRequest, ResearchDiscoverRequest
from app.services.intelligence import IntelligenceService

logger = logging.getLogger("opportunity_os.tasks.jobs")


async def process_uploaded_resume(
    ctx: dict[str, Any],
    resume_id_str: str,
    user_id_str: str,
) -> dict[str, Any]:
    """Process an uploaded resume in background, compute student vector if encoder is available."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    resume_id = UUID(resume_id_str)
    user_id = UUID(user_id_str)

    async with session_factory() as session:
        repo = ResumeRepository(session)
        resume: Resume | None = await repo.get_for_user(resume_id, user_id)
        if resume is None:
            return {"status": "not_found", "resume_id": resume_id_str}

        content = dict(resume.master_content or {})
        skills = [str(s) for s in content.get("skills", []) if isinstance(s, str)]
        raw_text = str(
            content.get("rawText") or f"{content.get('summary', '')} {' '.join(skills)}".strip()
        )
        content["workerProcessed"] = True
        content["skillsCount"] = len(skills)
        resume.master_content = content

        adapter = ctx.get("embedding_adapter")
        embedded = False
        if adapter is not None and raw_text.strip():
            try:
                vector = adapter.encode_texts([raw_text])[0]
                from sqlalchemy.dialects.postgresql import insert as pg_insert

                from app.models.entities import StudentEmbedding

                stmt = (
                    pg_insert(StudentEmbedding)
                    .values(
                        user_id=user_id,
                        embedding_minilm_384=vector,
                        content_hash=resume.file_sha256,
                    )
                    .on_conflict_do_update(
                        index_elements=["user_id"],
                        set_={
                            "embedding_minilm_384": vector,
                            "content_hash": resume.file_sha256,
                            "updated_at": func.now(),
                        },
                    )
                )
                await session.execute(stmt)
                embedded = True
            except Exception as exc:
                logger.warning("Resume background embedding skipped (%s).", type(exc).__name__)

        await session.commit()
        return {
            "status": "processed",
            "resume_id": resume_id_str,
            "skills_count": len(skills),
            "student_embedded": embedded,
        }


async def run_olostep_research_job(
    ctx: dict[str, Any],
    user_id_str: str,
    query: str,
    location: str | None = None,
) -> dict[str, Any]:
    """Run Olostep external opportunity discovery job in background and notify the user."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    user_id = UUID(user_id_str)
    effective_query = f"{query} {location}".strip() if location else query

    async with session_factory() as session:
        res = await IntelligenceService(session).research_opportunities(
            user_id,
            ResearchDiscoverRequest(query=effective_query, enrich_companies=True),
        )
        session.add(
            Notification(
                user_id=user_id,
                title="Background Discovery Complete",
                message=(
                    f"Discovered {res.discovered_count} new and "
                    f"{res.deduplicated_count} deduplicated opportunities for '{query}'."
                ),
                type="opportunity_match",
            )
        )
        await session.commit()
        return {
            "status": "completed",
            "discovered": res.discovered_count,
            "deduplicated": res.deduplicated_count,
        }


async def sync_crustdata_company(
    ctx: dict[str, Any],
    domain: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    """Refresh organization firmographics and hiring velocity score via Crustdata."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    async with session_factory() as session:
        org = await IntelligenceService(session).enrich_company(
            CompanyEnrichRequest(domain=domain, company_name=company_name, force_refresh=True)
        )
        return {"status": "synced", "organization_id": str(org.id), "name": org.name}


async def aggregate_analytics_metrics(ctx: dict[str, Any]) -> dict[str, Any]:
    """Compute platform-wide funnel metrics into analytics_events for dashboards."""
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    async with session_factory() as session:
        users_count = int((await session.execute(select(func.count(Profile.id)))).scalar() or 0)
        opps_count = int((await session.execute(select(func.count(Opportunity.id)))).scalar() or 0)
        apps_count = int((await session.execute(select(func.count(Application.id)))).scalar() or 0)
        snapshot = {
            "total_users": users_count,
            "total_opportunities": opps_count,
            "total_applications": apps_count,
        }
        session.add(
            AnalyticsEvent(
                user_id=None,
                event_name="platform_metrics_snapshot",
                event_metadata=snapshot,
            )
        )
        await session.commit()
        return {"status": "aggregated", **snapshot}
