"""Supabase JWT verification and FastAPI authentication dependencies."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWTError
from pydantic import BaseModel, ConfigDict

from app.core.config import Settings, settings
from app.core.errors import ProblemDetailError

logger = logging.getLogger("opportunity_os.auth")

ALLOWED_ASYMMETRIC_ALGS = ("ES256", "RS256")
ALLOWED_SYMMETRIC_ALGS = ("HS256",)
ALLOWED_ALGORITHMS = ALLOWED_ASYMMETRIC_ALGS + ALLOWED_SYMMETRIC_ALGS
_PLACEHOLDER_MARKERS = ("placeholder-", "your-", "changeme", "<your", "dummy")

_bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Verified Supabase user identity derived exclusively from a validated JWT."""

    model_config = ConfigDict(frozen=True)

    user_id: UUID
    email: str | None = None
    supabase_role: str
    aal: str | None = None
    session_id: str | None = None


def _is_usable_secret(secret: str) -> bool:
    stripped = secret.strip()
    if len(stripped) < 16:
        return False
    low = stripped.lower()
    return not any(marker in low for marker in _PLACEHOLDER_MARKERS)


def _unauthorized(detail: str = "Invalid or expired authentication token.") -> ProblemDetailError:
    return ProblemDetailError(
        status_code=401,
        problem_type="urn:problem:unauthorized",
        title="Unauthorized",
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _forbidden(
    detail: str = "You do not have permission to perform this action.",
) -> ProblemDetailError:
    return ProblemDetailError(
        status_code=403,
        problem_type="urn:problem:forbidden",
        title="Forbidden",
        detail=detail,
    )


class SupabaseJWTVerifier:
    """Verifies Supabase-issued JWTs using JWKS (asymmetric) or JWT secret (HS256)."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings
        self._jwks_client: PyJWKClient | None = None
        self._jwks_url: str = ""

    def _get_jwks_client(self, jwks_url: str) -> PyJWKClient:
        if self._jwks_client is None or self._jwks_url != jwks_url:
            self._jwks_client = PyJWKClient(
                jwks_url,
                cache_jwk_set=True,
                lifespan=300,
                timeout=5,
            )
            self._jwks_url = jwks_url
        return self._jwks_client

    def _resolve_verification_key(self, token: str, alg: str) -> tuple[Any, list[str]]:
        if alg in ALLOWED_ASYMMETRIC_ALGS:
            jwks_url = self._settings.effective_jwks_url
            if not jwks_url:
                logger.error(
                    "Asymmetric JWT received but SUPABASE_URL/SUPABASE_JWKS_URL is not configured."
                )
                raise _unauthorized(
                    "Authentication service is not configured for asymmetric tokens."
                )
            jwk_client = self._get_jwks_client(jwks_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            return signing_key.key, [alg]

        if alg in ALLOWED_SYMMETRIC_ALGS:
            secret = self._settings.SUPABASE_JWT_SECRET
            if not _is_usable_secret(secret):
                logger.error(
                    "HS256 JWT received but SUPABASE_JWT_SECRET is missing or placeholder."
                )
                raise _unauthorized(
                    "Authentication service is not configured for symmetric tokens."
                )
            return secret, [alg]

        raise _unauthorized("Unsupported JWT signing algorithm.")

    def verify_token(self, token: str) -> AuthenticatedUser:
        """Verify JWT signature and claims, returning an AuthenticatedUser."""
        if not token or token.count(".") != 2:
            raise _unauthorized("Malformed bearer token.")

        issuer = self._settings.effective_jwt_issuer
        if self._settings.is_production and not issuer:
            raise _unauthorized("JWT issuer validation is not configured.")

        try:
            header = jwt.get_unverified_header(token)
        except PyJWTError as exc:
            raise _unauthorized("Malformed JWT header.") from exc

        alg = header.get("alg")
        if not isinstance(alg, str) or alg not in ALLOWED_ALGORITHMS:
            raise _unauthorized("Unsupported or missing JWT signing algorithm.")

        try:
            key, algorithms = self._resolve_verification_key(token, alg)
            decode_kwargs: dict[str, Any] = {
                "algorithms": algorithms,
                "audience": self._settings.SUPABASE_JWT_AUDIENCE,
                "options": {
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "verify_iss": bool(issuer),
                    "require": ["exp", "iat", "sub", "aud", "role"],
                },
            }
            if issuer:
                decode_kwargs["issuer"] = issuer

            claims: dict[str, Any] = jwt.decode(token, key, **decode_kwargs)
        except ProblemDetailError:
            raise
        except PyJWTError as exc:
            raise _unauthorized("Invalid or expired authentication token.") from exc

        raw_sub = claims.get("sub")
        if not isinstance(raw_sub, str) or not raw_sub:
            raise _unauthorized("Token missing subject claim.")

        try:
            user_id = UUID(raw_sub)
        except ValueError as exc:
            raise _unauthorized("Token subject claim is not a valid UUID.") from exc

        raw_role = claims.get("role")
        if not isinstance(raw_role, str) or not raw_role.strip():
            raise _unauthorized("Token missing or malformed role claim.")

        email = claims.get("email")
        if email is not None and not isinstance(email, str):
            email = None

        aal = claims.get("aal")
        if aal is not None and not isinstance(aal, str):
            aal = None

        session_id = claims.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            session_id = None

        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            supabase_role=raw_role,
            aal=aal,
            session_id=session_id,
        )


_default_verifier = SupabaseJWTVerifier()


def get_jwt_verifier() -> SupabaseJWTVerifier:
    """FastAPI dependency returning the active SupabaseJWTVerifier."""
    return _default_verifier


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    verifier: Annotated[SupabaseJWTVerifier, Depends(get_jwt_verifier)],
) -> AuthenticatedUser:
    """Extract and verify Supabase Bearer JWT, returning AuthenticatedUser."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise _unauthorized("Missing or invalid Authorization header.")
    return verifier.verify_token(credentials.credentials)


def require_supabase_role(*allowed_roles: str):  # type: ignore[no-untyped-def]
    """Dependency factory enforcing Supabase JWT role (separate from app-level roles)."""

    async def _check_role(
        current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if current_user.supabase_role not in allowed_roles:
            raise _forbidden("Insufficient Supabase role for this resource.")
        return current_user

    return _check_role
