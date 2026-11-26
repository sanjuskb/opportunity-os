"""RFC 7807 Problem Details exceptions and FastAPI handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ProblemDetailError(Exception):
    """Structured RFC 7807 Problem Details exception."""

    def __init__(
        self,
        *,
        status_code: int,
        problem_type: str,
        title: str,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.problem_type = problem_type
        self.title = title
        self.detail = detail
        self.headers = headers or {}


async def problem_detail_exception_handler(
    request: Request,
    exc: ProblemDetailError,
) -> JSONResponse:
    """Render ProblemDetailError as application/problem+json."""
    payload = {
        "type": exc.problem_type,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url.path),
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        headers=exc.headers,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global RFC 7807 exception handlers on the FastAPI app."""
    app.add_exception_handler(ProblemDetailError, problem_detail_exception_handler)  # type: ignore[arg-type]
