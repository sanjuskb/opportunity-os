"""Unit tests for SupabaseJWTVerifier (HS256, asymmetric JWKS + rotation, and claim checks)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import Settings
from app.core.errors import ProblemDetailError
from app.core.security import SupabaseJWTVerifier

TEST_HS256_SECRET = "test-super-secret-supabase-jwt-key-32-chars"
TEST_ISSUER = "https://demo-project.supabase.co/auth/v1"


def _make_hs256_token(
    *,
    secret: str = TEST_HS256_SECRET,
    sub: str | None = None,
    aud: str = "authenticated",
    iss: str = TEST_ISSUER,
    exp_delta_seconds: int = 3600,
    role: object = "authenticated",
    include_sub: bool = True,
    include_role: bool = True,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "aud": aud,
        "iss": iss,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=exp_delta_seconds)).timestamp()),
        "email": "student@iitb.ac.in",
    }
    if include_role:
        payload["role"] = role
    if include_sub:
        payload["sub"] = sub if sub is not None else str(uuid4())
    return jwt.encode(payload, secret, algorithm="HS256")


def _verifier(secret: str = TEST_HS256_SECRET) -> SupabaseJWTVerifier:
    return SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_SECRET=secret,
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )


def test_valid_hs256_jwt() -> None:
    uid = uuid4()
    token = _make_hs256_token(sub=str(uid))
    user = _verifier().verify_token(token)
    assert user.user_id == uid
    assert user.email == "student@iitb.ac.in"
    assert user.supabase_role == "authenticated"


def test_missing_or_malformed_role_rejected() -> None:
    for token in (
        _make_hs256_token(include_role=False),
        _make_hs256_token(role=""),
        _make_hs256_token(role="   "),
        _make_hs256_token(role=123),
    ):
        with pytest.raises(ProblemDetailError) as exc:
            _verifier().verify_token(token)
        assert exc.value.status_code == 401


def test_production_settings_defaults_and_validation() -> None:
    prod = Settings(
        ENVIRONMENT="production",
        SUPABASE_URL="https://demo-project.supabase.co",
        REDIS_URL="redis://redis:6379/0",
    )
    assert prod.DEBUG is False

    with pytest.raises(ValueError, match="DEBUG must be false"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SUPABASE_URL="https://demo-project.supabase.co",
            REDIS_URL="redis://redis:6379/0",
        )

    with pytest.raises(ValueError, match="SUPABASE_URL or SUPABASE_JWT_ISSUER"):
        Settings(
            ENVIRONMENT="production",
            SUPABASE_URL="",
            SUPABASE_JWT_ISSUER="",
            REDIS_URL="redis://redis:6379/0",
        )

    with pytest.raises(ValueError, match="REDIS_URL"):
        Settings(
            ENVIRONMENT="production",
            SUPABASE_URL="https://demo-project.supabase.co",
            REDIS_URL="",
        )

    dev = Settings(ENVIRONMENT="development")
    assert dev.DEBUG is True


def test_invalid_signature_rejected() -> None:
    token = _make_hs256_token(secret="wrong-secret-key-at-least-32-characters-long")
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_expired_jwt_rejected() -> None:
    token = _make_hs256_token(exp_delta_seconds=-60)
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_incorrect_issuer_rejected() -> None:
    token = _make_hs256_token(iss="https://evil-issuer.example.com/auth/v1")
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_incorrect_audience_rejected() -> None:
    token = _make_hs256_token(aud="anon")
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_missing_subject_rejected() -> None:
    token = _make_hs256_token(include_sub=False)
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_malformed_uuid_subject_rejected() -> None:
    token = _make_hs256_token(sub="not-a-valid-uuid")
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_alg_none_rejected() -> None:
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "iat": int(datetime.now(UTC).timestamp()),
            "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
        },
        "",
        algorithm="none",
    )
    with pytest.raises(ProblemDetailError) as exc:
        _verifier().verify_token(token)
    assert exc.value.status_code == 401


def test_asymmetric_jwks_and_key_rotation(monkeypatch: pytest.MonkeyPatch) -> None:
    key_1 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_2 = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    keys_by_kid = {
        "kid-1": key_1.public_key(),
        "kid-2": key_2.public_key(),
    }

    class FakeJWKClient:
        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            hdr = jwt.get_unverified_header(token)
            return SimpleNamespace(key=keys_by_kid[hdr["kid"]])

    verifier = SupabaseJWTVerifier(
        Settings(
            SUPABASE_URL="https://demo-project.supabase.co",
            SUPABASE_JWT_AUDIENCE="authenticated",
        )
    )
    monkeypatch.setattr(verifier, "_get_jwks_client", lambda _url: FakeJWKClient())

    uid_1 = uuid4()
    uid_2 = uuid4()
    now = datetime.now(UTC)
    tok_1 = jwt.encode(
        {
            "sub": str(uid_1),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        key_1,
        algorithm="RS256",
        headers={"kid": "kid-1"},
    )
    tok_2 = jwt.encode(
        {
            "sub": str(uid_2),
            "aud": "authenticated",
            "iss": TEST_ISSUER,
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        key_2,
        algorithm="RS256",
        headers={"kid": "kid-2"},
    )

    assert verifier.verify_token(tok_1).user_id == uid_1
    assert verifier.verify_token(tok_2).user_id == uid_2
