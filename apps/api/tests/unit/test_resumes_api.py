"""Unit and API tests for W1-C Resume CRUD endpoints, ownership, validation, and error safety."""

from __future__ import annotations

from collections.abc import AsyncIterator, Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.core.security import SupabaseJWTVerifier, get_jwt_verifier
from app.db.session import get_db_session
from app.main import create_application
from app.models.entities import Profile, Resume
from app.repositories.profiles import ProfileRepository
from app.repositories.resumes import ResumeRepository
from app.services import resumes as resumes_service_module

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


class _TrackingAsyncSession:
    def __init__(self, *, fail_on_commit: bool = False) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.fail_on_commit = fail_on_commit

    async def commit(self) -> None:
        if self.fail_on_commit:
            raise OperationalError(
                "COMMIT",
                {},
                Exception("postgresql+asyncpg://postgres:super-secret-db-pass@db/postgres"),
            )
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        return None


class _InMemoryResumeStore:
    def __init__(self, existing_profiles: set[UUID]) -> None:
        self.profiles = existing_profiles
        self.resumes: dict[UUID, Resume] = {}
        self.fail_reads = False

    def make_profile_repo(self, _session: Any) -> Any:
        store = self

        class _FakeProfileRepo:
            async def get_by_user_id(self, user_id: UUID) -> Profile | None:
                if store.fail_reads:
                    raise OperationalError(
                        "SELECT * FROM public.profiles",
                        {},
                        Exception("password=super-secret-db-pass"),
                    )
                if user_id not in store.profiles:
                    return None
                return Profile(id=user_id, email=f"{user_id}@iitb.ac.in", full_name="Student")

        return _FakeProfileRepo()

    def make_resume_repo(self, _session: Any) -> Any:
        store = self

        class _FakeResumeRepo:
            async def list_for_user(
                self, user_id: UUID, *, limit: int = 50, offset: int = 0
            ) -> list[Resume]:
                if store.fail_reads:
                    raise OperationalError(
                        "SELECT * FROM public.resumes",
                        {},
                        Exception("password=super-secret-db-pass"),
                    )
                owned = [r for r in store.resumes.values() if r.user_id == user_id]
                owned.sort(
                    key=lambda r: (r.created_at or datetime.min.replace(tzinfo=UTC), str(r.id)),
                    reverse=True,
                )
                return owned[offset : offset + limit]

            async def get_for_user(self, resume_id: UUID, user_id: UUID) -> Resume | None:
                if store.fail_reads:
                    raise OperationalError(
                        "SELECT * FROM public.resumes",
                        {},
                        Exception("password=super-secret-db-pass"),
                    )
                rec = store.resumes.get(resume_id)
                if rec is None or rec.user_id != user_id:
                    return None
                return rec

            async def create_for_user(
                self, user_id: UUID, *, title: str, master_content: dict[str, Any]
            ) -> Resume:
                rec = Resume(
                    id=uuid4(),
                    user_id=user_id,
                    title=title,
                    master_content=dict(master_content),
                    created_at=datetime.now(UTC),
                )
                store.resumes[rec.id] = rec
                return rec

            async def delete_for_user(self, resume_id: UUID, user_id: UUID) -> bool:
                if store.fail_reads:
                    raise OperationalError(
                        "DELETE FROM public.resumes",
                        {},
                        Exception("password=super-secret-db-pass"),
                    )
                rec = store.resumes.get(resume_id)
                if rec is None or rec.user_id != user_id:
                    return False
                del store.resumes[resume_id]
                return True

        return _FakeResumeRepo()


@contextmanager
def _resume_test_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    profiles: set[UUID],
    fail_on_commit: bool = False,
) -> Generator[tuple[TestClient, _InMemoryResumeStore, _TrackingAsyncSession], None, None]:
    store = _InMemoryResumeStore(existing_profiles=profiles)
    fake_session = _TrackingAsyncSession(fail_on_commit=fail_on_commit)

    monkeypatch.setattr(resumes_service_module, "ProfileRepository", store.make_profile_repo)
    monkeypatch.setattr(resumes_service_module, "ResumeRepository", store.make_resume_repo)

    app = create_application(Settings(ENVIRONMENT="development", REDIS_URL=""))
    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=TEST_SECRET,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )

    async def _override_db() -> AsyncIterator[_TrackingAsyncSession]:
        yield fake_session

    app.dependency_overrides[get_jwt_verifier] = lambda: verifier
    app.dependency_overrides[get_db_session] = _override_db  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client, store, fake_session
    finally:
        app.dependency_overrides.clear()


def test_authenticated_user_can_create_list_get_and_delete_own_resume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_a = uuid4()
    user_b = uuid4()
    token_a = _make_token(user_a)
    token_b = _make_token(user_b)

    with _resume_test_client(monkeypatch, profiles={user_a, user_b}) as (client, _, session):
        create_a1 = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "title": "  Backend Engineer Resume  ",
                "masterContent": {"summary": "FastAPI and PostgreSQL", "skills": ["Python"]},
            },
        )
        assert create_a1.status_code == 201
        body_a1 = create_a1.json()
        assert body_a1["userId"] == str(user_a)
        assert body_a1["title"] == "Backend Engineer Resume"
        assert body_a1["masterContent"] == {
            "summary": "FastAPI and PostgreSQL",
            "skills": ["Python"],
        }
        assert session.commits == 1
        resume_a1_id = body_a1["id"]

        create_b1 = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "title": "ML Researcher Resume",
                "masterContent": {"skills": ["PyTorch"]},
            },
        )
        assert create_b1.status_code == 201
        resume_b1_id = create_b1.json()["id"]

        list_a = client.get(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_a.status_code == 200
        items_a = list_a.json()
        assert len(items_a) == 1
        assert items_a[0]["id"] == resume_a1_id
        assert items_a[0]["userId"] == str(user_a)

        get_a = client.get(
            f"/api/v1/resumes/{resume_a1_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert get_a.status_code == 200
        assert get_a.json()["id"] == resume_a1_id

        # Cross-user GET must return 404
        cross_get = client.get(
            f"/api/v1/resumes/{resume_a1_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert cross_get.status_code == 404

        # Cross-user DELETE must return 404 and preserve user A's resume
        cross_del = client.delete(
            f"/api/v1/resumes/{resume_a1_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert cross_del.status_code == 404
        assert (
            client.get(
                f"/api/v1/resumes/{resume_a1_id}",
                headers={"Authorization": f"Bearer {token_a}"},
            ).status_code
            == 200
        )

        # Owner DELETE succeeds with 204 and subsequent GET returns 404
        del_a = client.delete(
            f"/api/v1/resumes/{resume_a1_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert del_a.status_code == 204
        assert del_a.content == b""
        assert (
            client.get(
                f"/api/v1/resumes/{resume_a1_id}",
                headers={"Authorization": f"Bearer {token_a}"},
            ).status_code
            == 404
        )
        # User B's resume remains intact
        assert (
            client.get(
                f"/api/v1/resumes/{resume_b1_id}",
                headers={"Authorization": f"Bearer {token_b}"},
            ).status_code
            == 200
        )


def test_missing_resume_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    token = _make_token(user_id)
    missing_id = uuid4()

    with _resume_test_client(monkeypatch, profiles={user_id}) as (client, _, _):
        get_resp = client.get(
            f"/api/v1/resumes/{missing_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_resp.status_code == 404
        assert get_resp.headers["content-type"].startswith("application/problem+json")

        del_resp = client.delete(
            f"/api/v1/resumes/{missing_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert del_resp.status_code == 404


def test_unauthenticated_requests_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_id = uuid4()
    with _resume_test_client(monkeypatch, profiles=set()) as (client, _, _):
        assert client.get("/api/v1/resumes").status_code == 401
        assert (
            client.post("/api/v1/resumes", json={"title": "Test", "masterContent": {}}).status_code
            == 401
        )
        assert client.get(f"/api/v1/resumes/{sample_id}").status_code == 401
        assert client.delete(f"/api/v1/resumes/{sample_id}").status_code == 401


def test_invalid_resume_requests_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    token = _make_token(user_id)

    with _resume_test_client(monkeypatch, profiles={user_id}) as (client, _, _):
        # Blank/whitespace title
        blank_title = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "   ", "masterContent": {}},
        )
        assert blank_title.status_code == 422

        # Missing masterContent
        missing_content = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Valid Title"},
        )
        assert missing_content.status_code == 422

        # Extra forbidden field (StrictCamelModel)
        extra_field = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Valid Title", "masterContent": {}, "userId": str(uuid4())},
        )
        assert extra_field.status_code == 422

        # Invalid UUID path parameter
        bad_uuid = client.get(
            "/api/v1/resumes/not-a-uuid",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bad_uuid.status_code == 422


def test_database_errors_do_not_leak_internal_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id = uuid4()
    token = _make_token(user_id)

    with _resume_test_client(monkeypatch, profiles={user_id}) as (client, store, _):
        store.fail_reads = True
        resp = client.get("/api/v1/resumes", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 503
        assert "super-secret-db-pass" not in resp.text
        assert "SELECT" not in resp.text
        assert "public.resumes" not in resp.text

    with _resume_test_client(monkeypatch, profiles={user_id}, fail_on_commit=True) as (
        client,
        _,
        session,
    ):
        resp = client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "My Resume", "masterContent": {"skills": []}},
        )
        assert resp.status_code == 503
        assert session.rollbacks == 1
        assert "super-secret-db-pass" not in resp.text
        assert "postgresql+asyncpg" not in resp.text


@pytest.mark.asyncio
async def test_resume_repository_queries_enforce_user_scoping() -> None:
    executed_sql: list[str] = []

    class _FakeScalarResult:
        def all(self) -> list[Any]:
            return []

    class _FakeResult:
        rowcount = 0

        def scalars(self) -> _FakeScalarResult:
            return _FakeScalarResult()

        def scalar_one_or_none(self) -> None:
            return None

    class _SpySession:
        async def execute(self, stmt: Any) -> _FakeResult:
            compiled = str(stmt.compile(dialect=postgresql.dialect()))
            executed_sql.append(compiled)
            return _FakeResult()

    repo = ResumeRepository(_SpySession())  # type: ignore[arg-type]
    uid = uuid4()
    rid = uuid4()

    await repo.list_for_user(uid, limit=10, offset=5)
    await repo.get_for_user(rid, uid)
    await repo.delete_for_user(rid, uid)

    assert len(executed_sql) == 3
    assert "resumes.user_id =" in executed_sql[0]
    assert "LIMIT" in executed_sql[0] and "OFFSET" in executed_sql[0]
    assert "resumes.id =" in executed_sql[1] and "resumes.user_id =" in executed_sql[1]
    assert "DELETE FROM public.resumes" in executed_sql[2] and "resumes.user_id =" in executed_sql[2]
    assert ProfileRepository is not None
