"""Live PostgreSQL / Supabase integration tests for Opportunity OS schema and RLS.

These tests verify actual database behavior (migrations, auth trigger, RLS isolation,
column-level grants, public reads, service-role access, uniqueness constraints, and
pgvector indexes). They skip cleanly when no live PostgreSQL/Supabase instance is reachable.
"""

from __future__ import annotations

import json
import os
import uuid
from urllib.parse import urlparse

import asyncpg
import pytest

from app.core.config import settings


def _normalize_asyncpg_dsn(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://", 1)


async def _get_live_connection() -> asyncpg.Connection:
    dsn = _normalize_asyncpg_dsn(os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL))
    parsed = urlparse(dsn)
    if parsed.scheme not in ("postgres", "postgresql"):
        pytest.skip(f"Unsupported DATABASE_URL scheme for live Postgres test: {parsed.scheme}")
    try:
        return await asyncpg.connect(dsn, timeout=2.0)
    except Exception as exc:
        pytest.skip(f"Live Supabase/PostgreSQL instance unavailable ({exc})")


async def _set_auth_user(conn: asyncpg.Connection, user_id: uuid.UUID) -> None:
    await conn.execute("SET LOCAL ROLE authenticated")
    await conn.execute(
        "SELECT set_config('request.jwt.claim.sub', $1, true)",
        str(user_id),
    )
    await conn.execute(
        "SELECT set_config('request.jwt.claims', $1, true)",
        json.dumps({"sub": str(user_id), "role": "authenticated"}),
    )


@pytest.mark.asyncio
async def test_schema_tables_rls_and_vector_indexes() -> None:
    conn = await _get_live_connection()
    try:
        rows = await conn.fetch(
            "SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public'"
        )
        rls_map = {r["tablename"]: r["rowsecurity"] for r in rows}
        expected = {
            "profiles",
            "student_profiles",
            "education",
            "skills",
            "user_preferences",
            "career_passports",
            "opportunities",
            "opportunity_sources",
            "opportunity_eligibility",
            "opportunity_embeddings",
            "saved_opportunities",
            "applications",
            "resumes",
            "resume_versions",
            "resume_customizations",
            "agent_sessions",
            "agent_events",
            "approval_requests",
            "browser_execution_logs",
            "conversations",
            "conversation_messages",
            "voice_sessions",
            "notifications",
            "opportunity_monitors",
            "analytics_events",
        }
        assert expected.issubset(rls_map.keys())
        for table in expected:
            assert rls_map[table] is True, f"RLS not enabled on public.{table}"

        cols = await conn.fetch(
            """
            SELECT attname AS column_name, format_type(atttypid, atttypmod) AS data_type
            FROM pg_attribute
            WHERE attrelid = 'public.opportunity_embeddings'::regclass
              AND attnum > 0
              AND NOT attisdropped
            """
        )
        col_types = {c["column_name"]: c["data_type"] for c in cols}
        assert col_types.get("embedding") == "vector(768)"
        assert col_types.get("embedding_minilm_384") == "vector(384)"

        indexes = await conn.fetch(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'opportunity_embeddings'
            """
        )
        index_names = {i["indexname"] for i in indexes}
        assert "idx_embeddings_vector" in index_names
        assert "idx_embeddings_minilm_384_hnsw" in index_names
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_null_email_signups_and_rls_security_matrix() -> None:
    conn = await _get_live_connection()
    try:
        has_auth = await conn.fetchval("SELECT to_regclass('auth.users') IS NOT NULL")
        if not has_auth:
            pytest.skip("auth.users table not present (Supabase Auth runtime required)")

        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        opp_id = uuid.uuid4()
        session_id = uuid.uuid4()
        approval_id = uuid.uuid4()
        notif_id = uuid.uuid4()

        async with conn.transaction():
            # 1. Multiple NULL/empty email signups must succeed without unique_violation
            await conn.execute(
                "INSERT INTO auth.users (id, email) VALUES ($1, NULL), ($2, '')",
                user_a,
                user_b,
            )
            emails = await conn.fetch(
                "SELECT id, email FROM public.profiles WHERE id IN ($1, $2)",
                user_a,
                user_b,
            )
            assert len(emails) == 2
            assert {r["email"] for r in emails} == {
                f"{user_a}@no-email.local",
                f"{user_b}@no-email.local",
            }

            # 2. Seed public catalog, restricted tables, notification, session & approval as superuser
            await conn.execute(
                """
                INSERT INTO public.opportunities (
                    id, title, organization, location, type, description, source_url, source_provider
                ) VALUES ($1, 'Test Opp', 'Test Org', 'Remote', 'internship', 'Desc', 'https://example.com', 'olostep')
                """,
                opp_id,
            )
            await conn.execute(
                "INSERT INTO public.opportunity_eligibility (opportunity_id) VALUES ($1)",
                opp_id,
            )
            await conn.execute(
                "INSERT INTO public.opportunity_embeddings (opportunity_id) VALUES ($1)",
                opp_id,
            )
            await conn.execute(
                "INSERT INTO public.opportunity_sources (provider, domain) VALUES ('olostep', 'example.com')"
            )
            await conn.execute(
                "INSERT INTO public.notifications (id, user_id, title, message) VALUES ($1, $2, 'Match', 'New match')",
                notif_id,
                user_a,
            )
            await conn.execute(
                "INSERT INTO public.agent_sessions (id, user_id, agent_type) VALUES ($1, $2, 'application')",
                session_id,
                user_a,
            )
            await conn.execute(
                """
                INSERT INTO public.approval_requests (
                    id, session_id, user_id, opportunity_id, action_type, payload_summary
                ) VALUES ($1, $2, $3, $4, 'form_submission', '{}'::jsonb)
                """,
                approval_id,
                session_id,
                user_a,
                opp_id,
            )

            # 3. Anonymous access: public catalogs readable, private/restricted tables denied/empty
            await conn.execute("SET LOCAL ROLE anon")
            assert (
                await conn.fetchval(
                    "SELECT COUNT(*) FROM public.opportunities WHERE id = $1", opp_id
                )
                == 1
            )
            assert (
                await conn.fetchval(
                    "SELECT COUNT(*) FROM public.opportunity_eligibility WHERE opportunity_id = $1",
                    opp_id,
                )
                == 1
            )
            assert await conn.fetchval("SELECT COUNT(*) FROM public.skills") >= 0
            for private_table in (
                "profiles",
                "applications",
                "resumes",
                "opportunity_embeddings",
                "opportunity_sources",
            ):
                assert await conn.fetchval(f"SELECT COUNT(*) FROM public.{private_table}") == 0
            await conn.execute("RESET ROLE")

            # 4. Authenticated User A: draft application, uniqueness, column-grant & tamper checks
            await _set_auth_user(conn, user_a)
            await conn.execute(
                "INSERT INTO public.applications (user_id, opportunity_id, status) VALUES ($1, $2, 'drafting')",
                user_a,
                opp_id,
            )
            with pytest.raises(asyncpg.UniqueViolationError):
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO public.applications (user_id, opportunity_id, status) VALUES ($1, $2, 'drafting')",
                        user_a,
                        opp_id,
                    )

            # Application status tampering blocked (UPDATE revoked from authenticated)
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE public.applications SET status = 'submitted' WHERE user_id = $1",
                        user_a,
                    )

            # Notification: is_read succeeds, title/message/type tampering blocked
            await conn.execute(
                "UPDATE public.notifications SET is_read = true WHERE id = $1", notif_id
            )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE public.notifications SET title = 'Tampered' WHERE id = $1", notif_id
                    )

            # Profile: full_name/preferred_language succeeds, email tampering blocked
            await conn.execute(
                "UPDATE public.profiles SET full_name = 'User A', preferred_language = 'hi' WHERE id = $1",
                user_a,
            )
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE public.profiles SET email = 'spoof@example.com' WHERE id = $1",
                        user_a,
                    )

            # Approval requests: client mutations blocked by RLS (0 rows affected)
            res_upd = await conn.execute(
                "UPDATE public.approval_requests SET status = 'approved' WHERE id = $1",
                approval_id,
            )
            assert res_upd == "UPDATE 0"
            res_del = await conn.execute(
                "DELETE FROM public.approval_requests WHERE id = $1", approval_id
            )
            assert res_del == "DELETE 0"
            assert (
                await conn.fetchval(
                    "SELECT status FROM public.approval_requests WHERE id = $1", approval_id
                )
                == "pending"
            )
            await conn.execute("RESET ROLE")

            # 5. Cross-user isolation: User B cannot read or delete User A's records
            await _set_auth_user(conn, user_b)
            assert (
                await conn.fetchval(
                    "SELECT COUNT(*) FROM public.applications WHERE user_id = $1", user_a
                )
                == 0
            )
            deleted = await conn.execute(
                "DELETE FROM public.applications WHERE user_id = $1", user_a
            )
            assert deleted == "DELETE 0"
            await conn.execute("RESET ROLE")

            # 6. Service-role backend access succeeds for status & approval transitions
            await conn.execute("SET LOCAL ROLE service_role")
            await conn.execute(
                "UPDATE public.approval_requests SET status = 'approved' WHERE id = $1",
                approval_id,
            )
            await conn.execute(
                "UPDATE public.applications SET status = 'submitted' WHERE user_id = $1 AND opportunity_id = $2",
                user_a,
                opp_id,
            )
            await conn.execute("RESET ROLE")

            raise RuntimeError("Rollback test transaction")
    except RuntimeError as exc:
        if str(exc) != "Rollback test transaction":
            raise
    finally:
        await conn.close()
