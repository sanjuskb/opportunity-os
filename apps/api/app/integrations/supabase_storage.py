"""Private Supabase Storage & Local Sandbox Resume Storage Adapter."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from uuid import UUID

import httpx

from app.core.config import Settings, settings

logger = logging.getLogger("opportunity_os.storage")

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_PLACEHOLDER_MARKERS = ("placeholder-", "your-", "<your", "changeme", "dummy")


def sanitize_storage_filename(filename: str) -> str:
    base = Path(filename or "resume.pdf").name
    cleaned = _SAFE_FILENAME_RE.sub("_", base).strip("._")
    return cleaned or "resume.pdf"


def build_resume_storage_path(user_id: UUID, resume_id: UUID, filename: str) -> str:
    safe_name = sanitize_storage_filename(filename)
    return f"{user_id}/{resume_id}/{safe_name}"


class ResumeStorageClient:
    """Stores private student resumes in Supabase Storage with safe local dev fallback."""

    def __init__(self, app_settings: Settings | None = None) -> None:
        self._settings = app_settings or settings

    @property
    def bucket(self) -> str:
        return self._settings.SUPABASE_STORAGE_BUCKET or "resumes"

    def _has_remote_storage(self) -> bool:
        url = self._settings.SUPABASE_URL.strip()
        key = self._settings.SUPABASE_SERVICE_ROLE_KEY.strip()
        if not url or not key or len(key) < 16:
            return False
        low = key.lower()
        return not any(marker in low for marker in _PLACEHOLDER_MARKERS)

    def _local_object_path(self, storage_path: str) -> Path:
        root = Path(self._settings.LOCAL_RESUME_STORAGE_DIR).resolve()
        root.mkdir(parents=True, exist_ok=True)
        target = (root / storage_path).resolve()
        if root not in target.parents and target != root:
            raise ValueError("Storage path escapes root directory.")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    async def upload_bytes(
        self,
        *,
        storage_path: str,
        raw_bytes: bytes,
        content_type: str,
        prefer_local: bool = False,
    ) -> str:
        """Upload raw resume bytes to private Supabase Storage or local sandbox directory."""
        if not prefer_local and self._has_remote_storage():
            endpoint = f"{self._settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}/{storage_path}"
            headers = {
                "Authorization": f"Bearer {self._settings.SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": self._settings.SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": content_type,
                "x-upsert": "true",
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, content=raw_bytes, headers=headers)
                    if resp.status_code in {200, 201}:
                        return "supabase_storage"
                    logger.warning(
                        "Supabase Storage upload returned %s; falling back cleanly if dev.",
                        resp.status_code,
                    )
            except httpx.HTTPError as exc:
                logger.warning(
                    "Supabase Storage HTTP error (%s); using local fallback.", type(exc).__name__
                )
                if self._settings.is_production:
                    raise

        if self._settings.is_production and not prefer_local:
            raise RuntimeError("Supabase Storage must succeed in production.")

        local_file = self._local_object_path(storage_path)
        local_file.write_bytes(raw_bytes)
        return "local_sandbox"

    async def create_signed_url(
        self,
        *,
        storage_path: str,
        expires_in_seconds: int = 300,
    ) -> str | None:
        """Generate a short-lived signed download URL when stored in Supabase Storage."""
        if not self._has_remote_storage():
            return None
        endpoint = f"{self._settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/sign/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self._settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": self._settings.SUPABASE_SERVICE_ROLE_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    endpoint,
                    json={"expiresIn": expires_in_seconds},
                    headers=headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    signed_path = data.get("signedURL") or data.get("signedUrl")
                    if isinstance(signed_path, str) and signed_path:
                        if signed_path.startswith("http"):
                            return signed_path
                        return f"{self._settings.SUPABASE_URL.rstrip('/')}/storage/v1{signed_path}"
        except httpx.HTTPError:
            return None
        return None

    async def delete_object(self, storage_path: str) -> None:
        local_file = self._local_object_path(storage_path)
        if local_file.exists():
            local_file.unlink()
        if not self._has_remote_storage():
            return
        endpoint = f"{self._settings.SUPABASE_URL.rstrip('/')}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self._settings.SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": self._settings.SUPABASE_SERVICE_ROLE_KEY,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.delete(endpoint, headers=headers)
        except httpx.HTTPError:
            logger.debug("Ignoring non-fatal cleanup error removing %s", storage_path)
