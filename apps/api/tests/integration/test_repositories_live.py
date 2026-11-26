"""Live PostgreSQL 17 integration tests for DatabaseManager, ORM models, and repositories."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings, settings
from app.db.session import DatabaseManager, check_db_health
from app.models.entities import Notification, Opportunity, OpportunityEmbedding
from app.repositories import (
    ApplicationRepository,
    ApprovalRepository,
    CareerPassportRepository,
    NotificationRepository,
    OpportunityRepository,
    ProfileRepository,
    ResumeRepository,
    StudentProfileRepository,
)


async def _make_live_db() -> DatabaseManager:
    dsn = os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)
    db = DatabaseManager(Settings(DATABASE_URL=dsn))
    if not await check_db_health(db):
        await db.dispose()
        pytest.skip("Live PostgreSQL instance unavailable for repository integration tests")
    return db


@pytest.mark.asyncio
async def test_database_manager_lifecycle_and_rollback() -> None:
    db = await _make_live_db()
    try:
        assert await check_db_health(db) is True
        async with db.session_factory() as session:
            val = await session.scalar(text("SELECT 1"))
            assert val == 1
            await session.rollback()
    finally:
        await db.dispose()


@pytest.mark.asyncio
async def test_repositories_crud_isolation_pagination_and_constraints() -> None:
    db = await _make_live_db()
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    opp_ids = [uuid.uuid4() for _ in range(3)]
    session_id = uuid.uuid4()
    approval_id = uuid.uuid4()

    try:
        async with db.session_factory() as session, session.begin():
                # Provision two users in auth.users (triggers public.profiles via handle_new_user)
                await session.execute(
                    text("INSERT INTO auth.users (id, email) VALUES (:ua, :ea), (:ub, :eb)"),
                    {
                        "ua": user_a,
                        "ea": f"repo-a-{user_a.hex[:6]}@example.com",
                        "ub": user_b,
                        "eb": f"repo-b-{user_b.hex[:6]}@example.com",
                    },
                )

                # 1. ProfileRepository
                prof_repo = ProfileRepository(session)
                prof_a = await prof_repo.get_by_user_id(user_a)
                assert prof_a is not None
                updated_prof = await prof_repo.update_by_user_id(
                    user_a, full_name="Sanjeeth A", preferred_language="te"
                )
                assert updated_prof is not None
                assert updated_prof.full_name == "Sanjeeth A"
                assert updated_prof.preferred_language == "te"
                assert await prof_repo.get_by_user_id(uuid.uuid4()) is None

                # 2. StudentProfileRepository & CareerPassportRepository
                sp_repo = StudentProfileRepository(session)
                sp_a = await sp_repo.upsert_for_user(
                    user_a,
                    college_name="IIT Hyderabad",
                    degree="B.Tech",
                    branch="CSE",
                    graduation_year=2027,
                    cgpa=Decimal("8.95"),
                    state="Telangana",
                )
                assert sp_a.college_name == "IIT Hyderabad"
                edu = await sp_repo.add_education_for_user(
                    user_a,
                    institution="IIT Hyderabad",
                    degree="B.Tech",
                    field_of_study="Computer Science",
                    start_year=2023,
                    end_year=2027,
                    score="8.95 CGPA",
                )
                assert edu is not None

                cp_repo = CareerPassportRepository(session)
                cp_a = await cp_repo.upsert_for_user(
                    user_a,
                    projects=[{"title": "Opportunity OS", "verified": True}],
                )
                assert cp_a is not None
                assert await cp_repo.get_by_user_id(user_b) is None

                # 3. OpportunityRepository: cursor pagination & vector similarity interface
                base_ts = datetime.now(UTC)
                for idx, oid in enumerate(opp_ids):
                    session.add(
                        Opportunity(
                            id=oid,
                            title=f"Backend Intern #{idx}",
                            organization="NexteRaS Labs",
                            location="Bengaluru",
                            type="internship",
                            description="FastAPI & PostgreSQL internship",
                            source_url=f"https://example.com/jobs/{idx}",
                            source_provider="olostep",
                            is_active=True,
                            created_at=base_ts + timedelta(seconds=idx),
                        )
                    )
                await session.flush()

                # Add one 384-dim test vector for similarity query verification
                vec_384 = [0.0] * 384
                vec_384[0] = 1.0
                session.add(
                    OpportunityEmbedding(
                        opportunity_id=opp_ids[0],
                        embedding_minilm_384=vec_384,
                        embedding_status="ready",
                    )
                )
                await session.flush()

                opp_repo = OpportunityRepository(session)
                page_1 = await opp_repo.list_paginated(
                    limit=2, opp_type="internship", search_query="Backend Intern"
                )
                assert len(page_1.items) == 2
                assert page_1.has_more is True
                assert page_1.next_cursor is not None

                page_2 = await opp_repo.list_paginated(
                    cursor=page_1.next_cursor,
                    limit=2,
                    opp_type="internship",
                    search_query="Backend Intern",
                )
                assert len(page_2.items) == 1
                assert page_2.has_more is False
                assert {o.id for o in page_1.items + page_2.items} == set(opp_ids)

                sim_results = await opp_repo.search_similar_by_vector(vec_384, limit=5)
                assert any(opp.id == opp_ids[0] and score > 0.99 for opp, score in sim_results)

                # 4. ApplicationRepository: duplicate prevention & cross-user isolation
                app_repo = ApplicationRepository(session)
                app_a = await app_repo.create_draft(user_a, opp_ids[0])
                assert app_a.user_id == user_a
                assert await app_repo.get_for_user(app_a.id, user_b) is None
                assert await app_repo.delete_draft_for_user(app_a.id, user_b) is False

                with pytest.raises(IntegrityError):
                    async with session.begin_nested():
                        await app_repo.create_draft(user_a, opp_ids[0])

                # 5. ApprovalRepository: ownership & atomic pending transition
                await session.execute(
                    text(
                        "INSERT INTO public.agent_sessions (id, user_id, agent_type) VALUES (:sid, :uid, 'application')"
                    ),
                    {"sid": session_id, "uid": user_a},
                )
                await session.execute(
                    text(
                        """
                        INSERT INTO public.approval_requests (
                            id, session_id, user_id, opportunity_id, action_type, payload_summary
                        ) VALUES (:aid, :sid, :uid, :oid, 'form_submission', '{}'::jsonb)
                        """
                    ),
                    {"aid": approval_id, "sid": session_id, "uid": user_a, "oid": opp_ids[0]},
                )
                appr_repo = ApprovalRepository(session)
                assert await appr_repo.decide_for_user(approval_id, user_b, approved=True) is None
                decided = await appr_repo.decide_for_user(approval_id, user_a, approved=True)
                assert decided is not None
                assert decided.status == "approved"
                # Cannot re-decide once no longer pending
                assert await appr_repo.decide_for_user(approval_id, user_a, approved=False) is None

                # 6. NotificationRepository & ResumeRepository: isolation
                notif = Notification(
                    id=uuid.uuid4(),
                    user_id=user_a,
                    title="New Match",
                    message="You matched an internship.",
                )
                session.add(notif)
                await session.flush()

                notif_repo = NotificationRepository(session)
                assert await notif_repo.mark_read_for_user(notif.id, user_b) is None
                read_notif = await notif_repo.mark_read_for_user(notif.id, user_a)
                assert read_notif is not None and read_notif.is_read is True

                res_repo = ResumeRepository(session)
                res_a = await res_repo.create_for_user(
                    user_a, title="SDE Master", master_content={"sections": []}
                )
                assert await res_repo.get_for_user(res_a.id, user_b) is None
                assert await res_repo.delete_for_user(res_a.id, user_b) is False
                assert await res_repo.delete_for_user(res_a.id, user_a) is True

                # Roll back outer transaction cleanly so DB remains pristine
                await session.rollback()
    finally:
        await db.dispose()
