"""Unit and API tests for W1-D: Voice Sessions, Saved Opportunities, and Application Concurrency."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import get_db_session
from app.main import create_application
from app.models.entities import Application, ApprovalRequest, Opportunity, Profile, VoiceSession
from app.repositories.applications import ApplicationRepository
from app.repositories.opportunities import OpportunityRepository
from app.schemas.common import ApprovalDecisionRequest
from app.services import applications as applications_service_module
from app.services import approvals as approvals_service_module
from app.services import opportunities as opportunities_service_module
from app.services import voice_sessions as voice_sessions_service_module

TEST_SECRET = "test-super-secret-supabase-jwt-key-32-chars"
TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _make_token(user_id: UUID, *, role: str = "authenticated") -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "role": role,
            "email": f"{user_id}@iitb.ac.in",
        },
        TEST_SECRET,
        algorithm="HS256",
    )


class _TrackingSession:
    def __init__(self, *, fail_on_commit: bool = False) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.fail_on_commit = fail_on_commit

    async def commit(self) -> None:
        if self.fail_on_commit:
            raise OperationalError(
                "COMMIT",
                {},
                Exception("postgresql+asyncpg://postgres:secret-db-pass@db/postgres"),
            )
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        return None


# ---------------------------------------------------------------------------
# W1-D.1 — Voice Sessions
# ---------------------------------------------------------------------------


class _VoiceSessionStore:
    def __init__(self, profiles: set[UUID]) -> None:
        self.profiles = profiles
        self.sessions: list[VoiceSession] = []
        self.fail_db = False

    def make_profile_repo(self, _session: Any) -> Any:
        store = self

        class _FakeProfileRepo:
            async def get_by_user_id(self, user_id: UUID) -> Profile | None:
                if store.fail_db:
                    raise OperationalError(
                        "SELECT * FROM public.profiles",
                        {},
                        Exception("password=secret-db-pass"),
                    )
                if user_id not in store.profiles:
                    return None
                return Profile(id=user_id, email=f"{user_id}@iitb.ac.in")

        return _FakeProfileRepo()

    def make_voice_repo(self, _session: Any) -> Any:
        store = self

        class _FakeVoiceRepo:
            async def create_for_user(
                self,
                user_id: UUID,
                *,
                detected_language: str = "en",
                audio_duration_seconds: Decimal = Decimal("0"),
                transcript: str | None = None,
                status: str = "completed",
            ) -> VoiceSession:
                rec = VoiceSession(
                    id=uuid4(),
                    user_id=user_id,
                    detected_language=detected_language,
                    audio_duration_seconds=audio_duration_seconds,
                    transcript=transcript,
                    status=status,
                    created_at=datetime.now(UTC),
                )
                store.sessions.append(rec)
                return rec

        return _FakeVoiceRepo()


@contextmanager
def _voice_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    profiles: set[UUID],
    fail_on_commit: bool = False,
) -> Generator[tuple[TestClient, _VoiceSessionStore, _TrackingSession], None, None]:
    store = _VoiceSessionStore(profiles)
    fake_session = _TrackingSession(fail_on_commit=fail_on_commit)
    monkeypatch.setattr(voice_sessions_service_module, "ProfileRepository", store.make_profile_repo)
    monkeypatch.setattr(
        voice_sessions_service_module, "VoiceSessionRepository", store.make_voice_repo
    )

    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )

    async def _override_db() -> AsyncIterator[_TrackingSession]:
        yield fake_session

    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_db_session] = _override_db  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client, store, fake_session
    finally:
        app.dependency_overrides.clear()


def test_voice_session_create_auth_validation_and_db_error_safety(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    token = _make_token(user_id)

    with _voice_client(monkeypatch, profiles={user_id}) as (client, store, session):
        # Unauthenticated rejected
        assert (
            client.post("/api/v1/voice/sessions", json={"detectedLanguage": "en"}).status_code
            == 401
        )

        # Authenticated creation succeeds; userId from JWT; no ticket field exposed
        resp = client.post(
            "/api/v1/voice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "detectedLanguage": "hi",
                "audioDurationSeconds": "12.50",
                "transcript": "Find me AI internships",
                "status": "completed",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["userId"] == str(user_id)
        assert body["detectedLanguage"] == "hi"
        assert Decimal(str(body["audioDurationSeconds"])) == Decimal("12.50")
        assert body["transcript"] == "Find me AI internships"
        assert body["status"] == "completed"
        assert "id" in body and "createdAt" in body
        assert "ticket" not in body
        assert session.commits == 1
        assert len(store.sessions) == 1

        # Invalid payload rejected (extra userId, invalid language, negative duration)
        assert (
            client.post(
                "/api/v1/voice/sessions",
                headers={"Authorization": f"Bearer {token}"},
                json={"userId": str(uuid4())},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/voice/sessions",
                headers={"Authorization": f"Bearer {token}"},
                json={"detectedLanguage": "fr"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/voice/sessions",
                headers={"Authorization": f"Bearer {token}"},
                json={"audioDurationSeconds": -1},
            ).status_code
            == 422
        )

    # DB failure sanitized and rolled back
    with _voice_client(monkeypatch, profiles={user_id}, fail_on_commit=True) as (
        client,
        _,
        session,
    ):
        err_resp = client.post(
            "/api/v1/voice/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={"detectedLanguage": "en"},
        )
        assert err_resp.status_code == 503
        assert session.rollbacks == 1
        assert "secret-db-pass" not in err_resp.text
        assert "postgresql+asyncpg" not in err_resp.text


# ---------------------------------------------------------------------------
# W1-D.2 — Saved Opportunities
# ---------------------------------------------------------------------------


def test_saved_opportunities_list_isolation_pagination_and_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_a = uuid4()
    user_b = uuid4()
    token_a = _make_token(user_a)
    token_b = _make_token(user_b)

    opp1 = Opportunity(
        id=uuid4(),
        title="Backend Intern",
        organization="Acme",
        location="Remote",
        type="internship",
        description="Python",
        source_url="https://example.com/1",
        source_provider="manual",
        is_active=True,
    )
    opp2 = Opportunity(
        id=uuid4(),
        title="ML Fellowship",
        organization="Lab",
        location="Bengaluru",
        type="fellowship",
        description="ML",
        source_url="https://example.com/2",
        source_provider="manual",
        is_active=True,
    )
    opp3_b = Opportunity(
        id=uuid4(),
        title="User B Only",
        organization="OrgB",
        location="Delhi",
        type="job",
        description="Go",
        source_url="https://example.com/3",
        source_provider="manual",
        is_active=True,
    )
    saved_by_user: dict[UUID, list[Opportunity]] = {
        user_a: [opp1, opp2],
        user_b: [opp3_b],
    }

    class _FakeOppRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def list_saved_for_user(
            self,
            user_id: UUID,
            *,
            limit: int = 50,
            offset: int = 0,
            active_only: bool = True,
        ) -> list[Opportunity]:
            items = [o for o in saved_by_user.get(user_id, []) if (not active_only or o.is_active)]
            return items[offset : offset + limit]

    monkeypatch.setattr(opportunities_service_module, "OpportunityRepository", _FakeOppRepo)

    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )

    async def _override_db() -> AsyncIterator[_TrackingSession]:
        yield _TrackingSession()

    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_db_session] = _override_db  # type: ignore[assignment]

    try:
        with TestClient(app) as client:
            assert client.get("/api/v1/opportunities/saved").status_code == 401

            resp_a = client.get(
                "/api/v1/opportunities/saved",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert resp_a.status_code == 200
            ids_a = [item["id"] for item in resp_a.json()]
            assert ids_a == [str(opp1.id), str(opp2.id)]
            assert str(opp3_b.id) not in ids_a

            # Pagination
            page_2 = client.get(
                "/api/v1/opportunities/saved?limit=1&offset=1",
                headers={"Authorization": f"Bearer {token_a}"},
            )
            assert page_2.status_code == 200
            assert [item["id"] for item in page_2.json()] == [str(opp2.id)]

            # Empty list for user with no saved opportunities
            user_c_token = _make_token(uuid4())
            empty_resp = client.get(
                "/api/v1/opportunities/saved",
                headers={"Authorization": f"Bearer {user_c_token}"},
            )
            assert empty_resp.status_code == 200
            assert empty_resp.json() == []

            # Cross-user isolation
            resp_b = client.get(
                "/api/v1/opportunities/saved",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert [item["id"] for item in resp_b.json()] == [str(opp3_b.id)]

            # Invalid pagination rejected
            assert (
                client.get(
                    "/api/v1/opportunities/saved?limit=0",
                    headers={"Authorization": f"Bearer {token_a}"},
                ).status_code
                == 422
            )
            assert (
                client.get(
                    "/api/v1/opportunities/saved?limit=101",
                    headers={"Authorization": f"Bearer {token_a}"},
                ).status_code
                == 422
            )
            assert (
                client.get(
                    "/api/v1/opportunities/saved?offset=-1",
                    headers={"Authorization": f"Bearer {token_a}"},
                ).status_code
                == 422
            )
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_saved_opportunities_repository_sql_joins_and_filters() -> None:
    executed_sql: list[str] = []

    class _FakeScalarResult:
        def unique(self) -> _FakeScalarResult:
            return self

        def all(self) -> list[Any]:
            return []

    class _FakeResult:
        def scalars(self) -> _FakeScalarResult:
            return _FakeScalarResult()

    class _SpySession:
        async def execute(self, stmt: Any) -> _FakeResult:
            executed_sql.append(str(stmt.compile(dialect=postgresql.dialect())))
            return _FakeResult()

    repo = OpportunityRepository(_SpySession())  # type: ignore[arg-type]
    await repo.list_saved_for_user(uuid4(), limit=10, offset=5, active_only=True)
    sql = executed_sql[0]
    assert "JOIN public.saved_opportunities" in sql
    assert "saved_opportunities.user_id =" in sql
    assert "opportunities.is_active IS true" in sql
    assert "ORDER BY public.saved_opportunities.saved_at DESC" in sql
    assert "LIMIT" in sql and "OFFSET" in sql


# ---------------------------------------------------------------------------
# W1-D.3 — Atomic Application Status Transitions & Concurrency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_application_atomic_status_transition_and_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    app_id = uuid4()
    opp_id = uuid4()

    app_record = Application(
        id=app_id,
        user_id=user_id,
        opportunity_id=opp_id,
        status="drafting",
        submission_method="manual",
        created_at=datetime.now(UTC),
    )

    class _AtomicAppRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_for_user(self, aid: UUID, uid: UUID) -> Application | None:
            if aid == app_id and uid == user_id:
                return Application(
                    id=app_record.id,
                    user_id=app_record.user_id,
                    opportunity_id=app_record.opportunity_id,
                    status=app_record.status,
                    submission_method=app_record.submission_method,
                    created_at=app_record.created_at,
                )
            return None

        async def transition_status_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            expected_status: str,
            new_status: str,
        ) -> Application | None:
            # Yield once to force interleaving between concurrent tasks
            await asyncio.sleep(0)
            if aid != app_id or uid != user_id or app_record.status != expected_status:
                return None
            app_record.status = new_status
            return app_record

    monkeypatch.setattr(applications_service_module, "ApplicationRepository", _AtomicAppRepo)

    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    session = _TrackingSession()

    async def _override_db() -> AsyncIterator[_TrackingSession]:
        yield session

    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_db_session] = _override_db  # type: ignore[assignment]
    token = _make_token(user_id)

    try:
        with TestClient(app) as client:
            # Missing expectedStatus rejected (422)
            missing_expected = client.patch(
                f"/api/v1/applications/{app_id}/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "ready_for_review"},
            )
            assert missing_expected.status_code == 422

            # Foreign-owned application returns 404
            other_token = _make_token(uuid4())
            foreign = client.patch(
                f"/api/v1/applications/{app_id}/status",
                headers={"Authorization": f"Bearer {other_token}"},
                json={"status": "ready_for_review", "expectedStatus": "drafting"},
            )
            assert foreign.status_code == 404

            # Invalid transition rejected (422)
            bad = client.patch(
                f"/api/v1/applications/{app_id}/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "ineligible", "expectedStatus": "drafting"},
            )
            assert bad.status_code == 422

            # Stale expectedStatus rejected (409)
            stale = client.patch(
                f"/api/v1/applications/{app_id}/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "ready_for_review", "expectedStatus": "saved"},
            )
            assert stale.status_code == 409
            assert session.commits == 0

            # Valid expectedStatus permits transition and commits once
            ok = client.patch(
                f"/api/v1/applications/{app_id}/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "ready_for_review", "expectedStatus": "drafting"},
            )
            assert ok.status_code == 200
            assert ok.json()["status"] == "ready_for_review"
            assert session.commits == 1

            # Reset to drafting for concurrency race test
            app_record.status = "drafting"

            # Concurrent transitions from the same expectedStatus: only ONE can succeed
            from app.schemas.common import ApplicationStatusUpdateRequest
            from app.services.applications import ApplicationService

            s1 = _TrackingSession()
            s2 = _TrackingSession()
            svc1 = ApplicationService(s1)  # type: ignore[arg-type]
            svc2 = ApplicationService(s2)  # type: ignore[arg-type]

            results = await asyncio.gather(
                svc1.update_status_by_client(
                    app_id,
                    user_id,
                    ApplicationStatusUpdateRequest(
                        status="ready_for_review", expected_status="drafting"
                    ),
                ),
                svc2.update_status_by_client(
                    app_id,
                    user_id,
                    ApplicationStatusUpdateRequest(status="saved", expected_status="drafting"),
                ),
                return_exceptions=True,
            )
            successes = [r for r in results if not isinstance(r, Exception)]
            conflicts = [
                r for r in results if isinstance(r, ProblemDetailError) and r.status_code == 409
            ]
            assert len(successes) == 1
            assert len(conflicts) == 1
            assert s1.commits + s2.commits == 1
            assert s1.rollbacks + s2.rollbacks == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_application_repository_transition_sql_is_atomic() -> None:
    executed_sql: list[str] = []

    class _FakeResult:
        def scalar_one_or_none(self) -> None:
            return None

    class _SpySession:
        async def execute(self, stmt: Any) -> _FakeResult:
            executed_sql.append(str(stmt.compile(dialect=postgresql.dialect())))
            return _FakeResult()

    repo = ApplicationRepository(_SpySession())  # type: ignore[arg-type]
    await repo.transition_status_for_user(
        uuid4(),
        uuid4(),
        expected_status="drafting",
        new_status="ready_for_review",
    )
    sql = executed_sql[0]
    assert "UPDATE public.applications SET status=" in sql
    assert "applications.id =" in sql
    assert "applications.user_id =" in sql
    assert "applications.status =" in sql
    assert "RETURNING" in sql


@pytest.mark.asyncio
async def test_approval_decision_does_not_create_duplicate_notifications_on_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    approval_id = uuid4()
    opp_id = uuid4()
    notifications_created: list[str] = []
    approval_row = ApprovalRequest(
        id=approval_id,
        session_id=uuid4(),
        user_id=user_id,
        opportunity_id=opp_id,
        action_type="submit_application",
        payload_summary={},
        status="pending",
    )

    class _FakeApprovalRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_for_user(self, aid: UUID, uid: UUID) -> ApprovalRequest | None:
            if aid == approval_id and uid == user_id:
                return ApprovalRequest(
                    id=approval_row.id,
                    session_id=approval_row.session_id,
                    user_id=approval_row.user_id,
                    opportunity_id=approval_row.opportunity_id,
                    action_type=approval_row.action_type,
                    payload_summary=approval_row.payload_summary,
                    status=approval_row.status,
                )
            return None

        async def decide_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            approved: bool,
            rejection_reason: str | None = None,
        ) -> ApprovalRequest | None:
            await asyncio.sleep(0)
            if approval_row.status != "pending":
                return None
            approval_row.status = "approved" if approved else "rejected"
            approval_row.user_decision_at = datetime.now(UTC)
            return approval_row

    class _FakeNotifRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def create_for_user(self, uid: UUID, *, title: str, **_kwargs: Any) -> None:
            notifications_created.append(f"{uid}:{title}")

    class _FakeAppRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_user_and_opportunity(self, _uid: UUID, _oid: UUID) -> None:
            return None

    monkeypatch.setattr(approvals_service_module, "ApprovalRepository", _FakeApprovalRepo)
    monkeypatch.setattr(approvals_service_module, "NotificationRepository", _FakeNotifRepo)
    monkeypatch.setattr(approvals_service_module, "ApplicationRepository", _FakeAppRepo)

    from app.services.approvals import ApprovalService

    s1 = _TrackingSession()
    s2 = _TrackingSession()
    results = await asyncio.gather(
        ApprovalService(s1).decide_approval(  # type: ignore[arg-type]
            approval_id, user_id, ApprovalDecisionRequest(approved=True)
        ),
        ApprovalService(s2).decide_approval(  # type: ignore[arg-type]
            approval_id, user_id, ApprovalDecisionRequest(approved=True)
        ),
        return_exceptions=True,
    )
    assert sum(1 for r in results if not isinstance(r, Exception)) == 1
    assert (
        sum(1 for r in results if isinstance(r, ProblemDetailError) and r.status_code == 409) == 1
    )
    assert len(notifications_created) == 1


@pytest.mark.asyncio
async def test_approval_decision_rolls_back_when_linked_app_transition_conflicts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    approval_id = uuid4()
    opp_id = uuid4()
    app_id = uuid4()
    notifications_created: list[str] = []

    persisted_approval_status = "pending"
    competing_app_status = "submitted"

    class _FakeApprovalRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_for_user(self, aid: UUID, uid: UUID) -> ApprovalRequest | None:
            if aid == approval_id and uid == user_id:
                return ApprovalRequest(
                    id=approval_id,
                    session_id=uuid4(),
                    user_id=user_id,
                    opportunity_id=opp_id,
                    action_type="submit_application",
                    payload_summary={},
                    status=persisted_approval_status,
                )
            return None

        async def decide_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            approved: bool,
            rejection_reason: str | None = None,
        ) -> ApprovalRequest | None:
            return ApprovalRequest(
                id=approval_id,
                session_id=uuid4(),
                user_id=user_id,
                opportunity_id=opp_id,
                action_type="submit_application",
                payload_summary={},
                status="approved" if approved else "rejected",
                user_decision_at=datetime.now(UTC),
            )

    class _FakeAppRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_user_and_opportunity(self, uid: UUID, oid: UUID) -> Application | None:
            return Application(
                id=app_id,
                user_id=uid,
                opportunity_id=oid,
                status="ready_for_review",
                submission_method="manual",
            )

        async def transition_status_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            expected_status: str,
            new_status: str,
        ) -> Application | None:
            # Competing transaction already updated the application row
            return None

    class _FakeNotifRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def create_for_user(self, uid: UUID, *, title: str, **_kwargs: Any) -> None:
            notifications_created.append(f"{uid}:{title}")

    monkeypatch.setattr(approvals_service_module, "ApprovalRepository", _FakeApprovalRepo)
    monkeypatch.setattr(approvals_service_module, "ApplicationRepository", _FakeAppRepo)
    monkeypatch.setattr(approvals_service_module, "NotificationRepository", _FakeNotifRepo)

    from app.services.approvals import ApprovalService

    session = _TrackingSession()
    with pytest.raises(ProblemDetailError) as exc_info:
        await ApprovalService(session).decide_approval(  # type: ignore[arg-type]
            approval_id, user_id, ApprovalDecisionRequest(approved=True)
        )

    assert exc_info.value.status_code == 409
    assert session.rollbacks == 1
    assert session.commits == 0
    assert notifications_created == []
    assert persisted_approval_status == "pending"
    assert competing_app_status == "submitted"


@pytest.mark.asyncio
async def test_approval_decision_succeeds_with_linked_app_transition_and_single_notification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    approval_id = uuid4()
    opp_id = uuid4()
    app_id = uuid4()
    notifications_created: list[str] = []
    app_status = "ready_for_review"

    class _FakeApprovalRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_for_user(self, aid: UUID, uid: UUID) -> ApprovalRequest | None:
            return ApprovalRequest(
                id=approval_id,
                session_id=uuid4(),
                user_id=user_id,
                opportunity_id=opp_id,
                action_type="submit_application",
                payload_summary={},
                status="pending",
            )

        async def decide_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            approved: bool,
            rejection_reason: str | None = None,
        ) -> ApprovalRequest | None:
            return ApprovalRequest(
                id=approval_id,
                session_id=uuid4(),
                user_id=user_id,
                opportunity_id=opp_id,
                action_type="submit_application",
                payload_summary={},
                status="approved" if approved else "rejected",
                user_decision_at=datetime.now(UTC),
            )

    class _FakeAppRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def get_by_user_and_opportunity(self, uid: UUID, oid: UUID) -> Application | None:
            return Application(
                id=app_id,
                user_id=uid,
                opportunity_id=oid,
                status=app_status,
                submission_method="manual",
            )

        async def transition_status_for_user(
            self,
            aid: UUID,
            uid: UUID,
            *,
            expected_status: str,
            new_status: str,
        ) -> Application | None:
            nonlocal app_status
            if app_status != expected_status:
                return None
            app_status = new_status
            return Application(
                id=aid,
                user_id=uid,
                opportunity_id=opp_id,
                status=new_status,
                submission_method="manual",
            )

    class _FakeNotifRepo:
        def __init__(self, _session: Any) -> None:
            pass

        async def create_for_user(self, uid: UUID, *, title: str, **_kwargs: Any) -> None:
            notifications_created.append(f"{uid}:{title}")

    monkeypatch.setattr(approvals_service_module, "ApprovalRepository", _FakeApprovalRepo)
    monkeypatch.setattr(approvals_service_module, "ApplicationRepository", _FakeAppRepo)
    monkeypatch.setattr(approvals_service_module, "NotificationRepository", _FakeNotifRepo)

    from app.services.approvals import ApprovalService

    session = _TrackingSession()
    result = await ApprovalService(session).decide_approval(  # type: ignore[arg-type]
        approval_id, user_id, ApprovalDecisionRequest(approved=True)
    )

    assert result.status == "approved"
    assert app_status == "approved"
    assert session.commits == 1
    assert session.rollbacks == 0
    assert len(notifications_created) == 1
