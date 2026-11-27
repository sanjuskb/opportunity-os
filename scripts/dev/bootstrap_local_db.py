"""Bootstrap the local NexteRaS PostgreSQL 17 + pgvector Docker database cleanly.

Applies `infra/docker/init-local-db.sql`, ordered SQL files in `supabase/migrations/`,
Supabase-parity role grants, and idempotent `supabase/seed/seed.sql`.
Safety guard: refuses non-local hosts unless `--allow-non-local` is explicitly passed.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse

import asyncpg

REPO_ROOT = Path(__file__).resolve().parents[2]
INIT_SQL = REPO_ROOT / "infra" / "docker" / "init-local-db.sql"
MIGRATIONS_DIR = REPO_ROOT / "supabase" / "migrations"
SEED_SQL = REPO_ROOT / "supabase" / "seed" / "seed.sql"

DEFAULT_LOCAL_DSN = "postgresql://postgres:postgres@127.0.0.1:54332/postgres"

SUPABASE_DEFAULT_GRANTS_SQL = """
GRANT USAGE ON SCHEMA public, extensions, auth, storage TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
"""


def _normalize_dsn(raw: str) -> str:
    return raw.replace("postgresql+asyncpg://", "postgresql://", 1).strip()


def _assert_local_dsn(dsn: str, allow_non_local: bool) -> None:
    parsed = urlparse(dsn)
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "localhost", "::1"} and not allow_non_local:
        raise SystemExit(
            f"Refusing to bootstrap non-local database host {host!r}. "
            "Use a local container on 127.0.0.1/localhost."
        )


async def _wait_for_postgres(dsn: str, retries: int = 20) -> asyncpg.Connection:
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            return await asyncpg.connect(dsn, timeout=3.0)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            await asyncio.sleep(1.0)
    raise SystemExit(f"Could not connect to local Postgres: {last_err}")


async def bootstrap(dsn: str, *, include_seed: bool, allow_non_local: bool) -> None:
    _assert_local_dsn(dsn, allow_non_local=allow_non_local)
    conn = await _wait_for_postgres(dsn)
    try:
        # 1. Compatibility schema / roles / extensions
        await conn.execute(INIT_SQL.read_text(encoding="utf-8"))

        applied = {
            row["version"]
            for row in await conn.fetch(
                "SELECT version FROM supabase_migrations.schema_migrations"
            )
        }

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for mig in migration_files:
            version = mig.name.split("_", 1)[0]
            if mig.name in applied or version in applied:
                print(f"[skip] {mig.name}")
                continue

            # Ensure Supabase-standard table grants exist right before security remediation
            if version == "20261126000003":
                await conn.execute(SUPABASE_DEFAULT_GRANTS_SQL)

            sql = mig.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    """
                    INSERT INTO supabase_migrations.schema_migrations (version, name)
                    VALUES ($1, $2)
                    ON CONFLICT (version) DO NOTHING
                    """,
                    mig.name,
                    mig.stem,
                )
            print(f"[applied] {mig.name}")

        # Ensure service_role always has privileges on newly created tables, while preserving
        # explicit column REVOKEs from 20261126000003 (only grant if 20261126000003 was just absent)
        await conn.execute(
            """
            GRANT USAGE ON SCHEMA public, extensions, auth, storage TO anon, authenticated, service_role;
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role;
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role;
            """
        )

        if include_seed and SEED_SQL.exists():
            async with conn.transaction():
                await conn.execute(SEED_SQL.read_text(encoding="utf-8"))
            print(f"[seeded] {SEED_SQL.name}")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or DEFAULT_LOCAL_DSN,
        help="PostgreSQL connection string (defaults to TEST_DATABASE_URL / DATABASE_URL / 127.0.0.1:54332)",
    )
    parser.add_argument("--no-seed", action="store_true", help="Skip supabase/seed/seed.sql")
    parser.add_argument(
        "--allow-non-local",
        action="store_true",
        help="Override local-only host guard (dangerous on hosted Supabase)",
    )
    args = parser.parse_args()
    asyncio.run(
        bootstrap(
            _normalize_dsn(args.dsn),
            include_seed=not args.no_seed,
            allow_non_local=args.allow_non_local,
        )
    )


if __name__ == "__main__":
    main()
