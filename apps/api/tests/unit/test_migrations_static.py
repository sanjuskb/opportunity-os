"""Static validation tests for Supabase migrations, seed data, and Docker Compose config."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"
SEED_FILE = REPO_ROOT / "supabase" / "seed" / "seed.sql"
DOCKER_COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"

EXPECTED_TABLES = [
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
]


def _read_all_migrations() -> str:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    assert len(files) >= 3, f"Expected at least 3 migration files, found {[f.name for f in files]}"
    return "\n".join(f.read_text(encoding="utf-8") for f in files)


def test_migration_files_ordered_and_present() -> None:
    files = sorted(f.name for f in MIGRATIONS_DIR.glob("*.sql"))
    assert "20261123000001_initial_schema.sql" in files
    assert "20261126000001_harden_rls_and_auth_trigger.sql" in files
    assert "20261126000002_constraints_and_vector_alignment.sql" in files
    assert "20261126000003_security_audit_remediation.sql" in files
    assert files == sorted(files)


def test_all_25_tables_created_and_rls_enabled() -> None:
    sql = _read_all_migrations()
    for table in EXPECTED_TABLES:
        assert re.search(rf"CREATE TABLE IF NOT EXISTS public\.{table}\b", sql), (
            f"Missing CREATE TABLE for public.{table}"
        )
        assert re.search(rf"ALTER TABLE public\.{table} ENABLE ROW LEVEL SECURITY;", sql), (
            f"Missing ENABLE ROW LEVEL SECURITY for public.{table}"
        )


def test_restricted_tables_have_no_client_policies() -> None:
    hardening_sql = (MIGRATIONS_DIR / "20261126000001_harden_rls_and_auth_trigger.sql").read_text(
        encoding="utf-8"
    )
    for table in ("opportunity_sources", "opportunity_embeddings"):
        assert not re.search(rf"CREATE POLICY[^;]*\bON public\.{table}\b", hardening_sql), (
            f"public.{table} must not expose client RLS policies"
        )


def test_public_read_tables_allow_anon_and_authenticated() -> None:
    hardening_sql = (MIGRATIONS_DIR / "20261126000001_harden_rls_and_auth_trigger.sql").read_text(
        encoding="utf-8"
    )
    for table in ("opportunities", "opportunity_eligibility", "skills"):
        assert re.search(
            rf"CREATE POLICY[^;]*\bON public\.{table}\b[^;]*FOR SELECT\s+TO anon, authenticated",
            hardening_sql,
        ), f"public.{table} must allow SELECT TO anon, authenticated"


def test_append_only_and_approval_tables_block_client_mutations() -> None:
    hardening_sql = (MIGRATIONS_DIR / "20261126000001_harden_rls_and_auth_trigger.sql").read_text(
        encoding="utf-8"
    )
    for table in ("agent_events", "browser_execution_logs", "approval_requests", "agent_sessions"):
        assert not re.search(
            rf"CREATE POLICY[^;]*\bON public\.{table}\b[^;]*FOR (INSERT|UPDATE|DELETE)",
            hardening_sql,
        ), f"public.{table} must not allow client INSERT/UPDATE/DELETE"


def test_auth_signup_trigger_is_security_definer_with_restricted_search_path() -> None:
    hardening_sql = (MIGRATIONS_DIR / "20261126000001_harden_rls_and_auth_trigger.sql").read_text(
        encoding="utf-8"
    )
    remediation_sql = (MIGRATIONS_DIR / "20261126000003_security_audit_remediation.sql").read_text(
        encoding="utf-8"
    )
    assert "AFTER INSERT ON auth.users" in hardening_sql
    assert "CREATE OR REPLACE FUNCTION public.handle_new_user()" in remediation_sql
    assert "SECURITY DEFINER" in remediation_sql
    assert "SET search_path = public, pg_temp" in remediation_sql
    assert "OWNER TO postgres" in remediation_sql
    assert "@no-email.local" in remediation_sql


def test_column_grants_and_application_update_revocations() -> None:
    remediation_sql = (MIGRATIONS_DIR / "20261126000003_security_audit_remediation.sql").read_text(
        encoding="utf-8"
    )
    assert "REVOKE UPDATE ON public.applications FROM authenticated;" in remediation_sql
    assert "REVOKE UPDATE ON public.notifications FROM authenticated;" in remediation_sql
    assert "GRANT UPDATE (is_read) ON public.notifications TO authenticated;" in remediation_sql
    assert "REVOKE UPDATE ON public.profiles FROM authenticated;" in remediation_sql
    assert (
        "GRANT UPDATE (full_name, avatar_url, preferred_language) ON public.profiles TO authenticated;"
        in remediation_sql
    )


def test_constraints_and_dual_vector_alignment() -> None:
    constraints_sql = (
        MIGRATIONS_DIR / "20261126000002_constraints_and_vector_alignment.sql"
    ).read_text(encoding="utf-8")
    assert "uq_applications_user_opportunity" in constraints_sql
    assert "UNIQUE (user_id, opportunity_id)" in constraints_sql
    assert "uq_opportunity_eligibility_opportunity_id" in constraints_sql
    assert "RAISE EXCEPTION" in constraints_sql  # Never silently delete duplicates
    assert "embedding_minilm_384 vector(384)" in constraints_sql
    assert "idx_embeddings_minilm_384_hnsw" in constraints_sql


def test_embedding_pipeline_metadata_migration() -> None:
    meta_sql = (MIGRATIONS_DIR / "20261126000004_embedding_pipeline_metadata.sql").read_text(
        encoding="utf-8"
    )
    for col in ("content_hash", "embedding_status", "error_message", "retry_count", "updated_at"):
        assert col in meta_sql
    assert "CHECK (embedding_status IN ('pending', 'ready', 'failed'))" in meta_sql
    assert "CHECK (retry_count >= 0)" in meta_sql
    assert "CHECK (embedding_status <> 'ready' OR embedding_minilm_384 IS NOT NULL)" in meta_sql
    assert "embedding_model_id = 'sentence-transformers/all-MiniLM-L6-v2'" in meta_sql
    assert "DROP COLUMN" not in meta_sql
    assert "CREATE POLICY" not in meta_sql


def test_seed_sql_is_idempotent() -> None:
    seed_sql = SEED_FILE.read_text(encoding="utf-8")
    assert "INSERT INTO public.skills" in seed_sql
    assert "INSERT INTO public.opportunities" in seed_sql
    assert seed_sql.count("ON CONFLICT") >= 2


def test_docker_compose_uses_supabase_host_and_asyncpg() -> None:
    compose = DOCKER_COMPOSE_FILE.read_text(encoding="utf-8")
    assert "/docker-entrypoint-initdb.d" not in compose
    assert "postgres:" not in compose or "host.docker.internal:54322" in compose
    assert "host.docker.internal:host-gateway" in compose
    assert "postgresql+asyncpg://postgres:postgres@host.docker.internal:54322/postgres" in compose
