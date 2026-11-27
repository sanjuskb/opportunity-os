"""WS9 Playwright semi-automated sandbox form filler with mandatory human-in-the-loop gate."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import record_agent_event
from app.core.config import settings
from app.core.errors import ProblemDetailError
from app.integrations.olostep import validate_public_http_url
from app.models.entities import (
    AgentSession,
    Application,
    ApprovalRequest,
    BrowserExecutionLog,
    Notification,
    Opportunity,
    Profile,
    Resume,
    StudentProfile,
)

logger = logging.getLogger("opportunity_os.automation.playwright")

_CAPTCHA_OR_MFA_SELECTORS = (
    "iframe[src*='recaptcha']",
    "iframe[src*='hcaptcha']",
    ".g-recaptcha",
    ".h-captcha",
    ".cf-turnstile",
    "[data-sitekey]",
    "input[name*='otp' i]",
    "input[name*='captcha' i]",
    "#captcha",
)

_CAPTCHA_TEXT_RE = re.compile(
    r"(verify you are human|complete the captcha|enter one-time password|two-factor authentication)",
    re.IGNORECASE,
)


@dataclass
class AutomationPrepareResult:
    application_id: UUID
    session_id: UUID
    status: str  # awaiting_approval | requires_manual_completion | error
    approval_request_id: UUID | None = None
    screenshot_path: str | None = None
    filled_fields: dict[str, str] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""


def _validate_target_url(url: str, *, allow_localhost_sandbox: bool) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme in ("http", "https") and parsed.hostname in ("localhost", "127.0.0.1", "::1"):
        if allow_localhost_sandbox:
            return url.strip()
        raise ValueError("Localhost automation targets require non-production sandbox mode.")
    return validate_public_http_url(url)


async def prepare_application_automation(
    session: AsyncSession,
    *,
    user_id: UUID,
    application_id: UUID,
    portal_url: str | None = None,
    existing_session_id: UUID | None = None,
    langgraph_thread_id: str | None = None,
) -> AutomationPrepareResult:
    """Fill form fields on an application portal in headless Chromium and STOP before submit."""
    app_row = (
        await session.execute(
            select(Application).where(
                Application.id == application_id,
                Application.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if app_row is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Application Not Found",
            detail="Target application does not exist for this user.",
        )

    opp = (
        await session.execute(select(Opportunity).where(Opportunity.id == app_row.opportunity_id))
    ).scalar_one_or_none()
    if opp is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Opportunity Not Found",
            detail="Linked opportunity does not exist.",
        )

    target_url = (portal_url or opp.source_url or "").strip()
    if not target_url:
        raise ProblemDetailError(
            status_code=422,
            problem_type="urn:problem:validation_failed",
            title="Missing Application Portal URL",
            detail="No portal URL is configured for this opportunity.",
        )

    try:
        safe_url = _validate_target_url(
            target_url,
            allow_localhost_sandbox=(not settings.is_production),
        )
    except ValueError as exc:
        raise ProblemDetailError(
            status_code=422,
            problem_type="urn:problem:validation_failed",
            title="Unsafe Portal URL",
            detail=str(exc),
        ) from exc

    profile = (
        await session.execute(select(Profile).where(Profile.id == user_id))
    ).scalar_one_or_none()
    student = (
        await session.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    ).scalar_one_or_none()
    latest_resume = (
        await session.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    agent_session: AgentSession | None = None
    if existing_session_id is not None:
        agent_session = (
            await session.execute(
                select(AgentSession).where(
                    AgentSession.id == existing_session_id,
                    AgentSession.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
    if agent_session is None:
        agent_session = AgentSession(
            user_id=user_id,
            agent_type="playwright_application_preparer",
            state={
                "applicationId": str(application_id),
                "opportunityId": str(opp.id),
                "portalUrl": safe_url,
            },
            is_active=True,
        )
        session.add(agent_session)
        await session.flush()
        await session.refresh(agent_session)
    else:
        agent_session.state = {
            **dict(agent_session.state or {}),
            "applicationId": str(application_id),
            "opportunityId": str(opp.id),
            "portalUrl": safe_url,
        }
        await session.flush()

    await record_agent_event(
        session,
        session_id=agent_session.id,
        node_name="playwright_runner",
        event_type="automation_started",
        payload={"portalUrl": safe_url, "applicationId": str(application_id)},
    )

    candidate_values = _build_candidate_field_map(profile, student, latest_resume)
    screenshot_dir = Path(settings.PLAYWRIGHT_SCREENSHOT_DIR)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    pre_shot_path = screenshot_dir / f"pre_submit_{application_id}_{agent_session.id}.png"

    filled_fields: dict[str, str] = {}
    logs: list[dict[str, Any]] = []

    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise ProblemDetailError(
            status_code=503,
            problem_type="urn:problem:service_unavailable",
            title="Browser Automation Unavailable",
            detail="Playwright runtime is not installed.",
        ) from exc

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(settings.PLAYWRIGHT_TIMEOUT_MS)
        try:
            await page.goto(safe_url, wait_until="domcontentloaded")
            await _add_log(
                session,
                logs,
                session_id=agent_session.id,
                step_description=f"Loaded portal page {safe_url}",
                action_type="navigate",
                target_selector="document",
                is_success=True,
            )

            # Never bypass CAPTCHA/MFA — halt cleanly for manual completion
            gate_detected = await _detect_manual_gate(page)
            if gate_detected:
                await page.screenshot(path=str(pre_shot_path), full_page=True)
                await _add_log(
                    session,
                    logs,
                    session_id=agent_session.id,
                    step_description=f"Halted cleanly at CAPTCHA/MFA gate: {gate_detected}",
                    action_type="manual_gate_halt",
                    target_selector=gate_detected,
                    screenshot_url=str(pre_shot_path),
                    is_success=False,
                    error_message="requires_manual_completion",
                )
                agent_session.state = {
                    **dict(agent_session.state or {}),
                    "status": "requires_manual_completion",
                    "gate": gate_detected,
                }
                agent_session.is_active = False
                await record_agent_event(
                    session,
                    session_id=agent_session.id,
                    node_name="playwright_runner",
                    event_type="requires_manual_completion",
                    payload={"gate": gate_detected, "portalUrl": safe_url},
                )
                await session.commit()
                return AutomationPrepareResult(
                    application_id=application_id,
                    session_id=agent_session.id,
                    status="requires_manual_completion",
                    screenshot_path=str(pre_shot_path),
                    logs=logs,
                    message=(
                        f"Portal requires manual verification ({gate_detected}). "
                        "Automation halted cleanly without bypass; complete verification directly."
                    ),
                )

            # Fill mapped fields cleanly WITHOUT clicking submit
            for selector_keys, value in candidate_values.items():
                if not value:
                    continue
                for sel in selector_keys:
                    loc = page.locator(sel).first
                    if await loc.count() > 0 and await loc.is_visible():
                        await loc.fill(value)
                        filled_fields[sel] = value
                        await _add_log(
                            session,
                            logs,
                            session_id=agent_session.id,
                            step_description=f"Filled field {sel}",
                            action_type="fill",
                            target_selector=sel,
                            is_success=True,
                        )
                        break

            await page.screenshot(path=str(pre_shot_path), full_page=True)
            await _add_log(
                session,
                logs,
                session_id=agent_session.id,
                step_description="Captured pre-submission review screenshot",
                action_type="screenshot",
                target_selector="body",
                screenshot_url=str(pre_shot_path),
                is_success=True,
            )
        finally:
            await context.close()
            await browser.close()

    approval_payload: dict[str, Any] = {
        "application_id": str(application_id),
        "portal_url": safe_url,
        "filled_fields": filled_fields,
        "screenshot_path": str(pre_shot_path),
    }
    if langgraph_thread_id:
        approval_payload["langgraph_thread_id"] = langgraph_thread_id

    approval = ApprovalRequest(
        session_id=agent_session.id,
        user_id=user_id,
        opportunity_id=opp.id,
        action_type="submit_application",
        payload_summary=approval_payload,
        status="pending",
    )
    session.add(approval)
    await session.flush()
    await session.refresh(approval)

    # Move application to ready_for_review if pre-review
    if app_row.status in ("discovered", "saved", "evaluating", "eligible", "drafting"):
        await session.execute(
            update(Application)
            .where(Application.id == application_id, Application.user_id == user_id)
            .values(status="ready_for_review", submission_method="playwright_assisted")
        )

    agent_session.state = {
        **dict(agent_session.state or {}),
        "status": "awaiting_approval",
        "approvalRequestId": str(approval.id),
    }
    await record_agent_event(
        session,
        session_id=agent_session.id,
        node_name="human_approval_gate",
        event_type="approval_requested",
        payload={"approvalRequestId": str(approval.id), "filledFields": list(filled_fields.keys())},
    )
    await session.commit()

    return AutomationPrepareResult(
        application_id=application_id,
        session_id=agent_session.id,
        status="awaiting_approval",
        approval_request_id=approval.id,
        screenshot_path=str(pre_shot_path),
        filled_fields=filled_fields,
        logs=logs,
        message="Form prepared cleanly. Awaiting explicit user approval before final submission.",
    )


async def execute_approved_submission(
    session: AsyncSession,
    *,
    user_id: UUID,
    application_id: UUID,
    approval_id: UUID,
) -> AutomationPrepareResult:
    """Execute final portal submission ONLY when user explicitly approved the approval request."""
    approval = (
        await session.execute(
            select(ApprovalRequest).where(
                ApprovalRequest.id == approval_id,
                ApprovalRequest.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if approval is None:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Approval Request Not Found",
            detail="Approval request does not exist.",
        )
    if approval.status != "approved":
        raise ProblemDetailError(
            status_code=403,
            problem_type="urn:problem:forbidden",
            title="Approval Required",
            detail=f"Cannot execute submission while approval status is '{approval.status}'.",
        )

    payload = dict(approval.payload_summary or {})
    safe_url = _validate_target_url(
        str(payload.get("portal_url") or ""),
        allow_localhost_sandbox=(not settings.is_production),
    )
    filled_fields: dict[str, str] = {
        str(k): str(v) for k, v in (payload.get("filled_fields") or {}).items()
    }
    screenshot_dir = Path(settings.PLAYWRIGHT_SCREENSHOT_DIR)
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    post_shot_path = screenshot_dir / f"submitted_{application_id}_{approval.id}.png"
    logs: list[dict[str, Any]] = []

    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(settings.PLAYWRIGHT_TIMEOUT_MS)
        try:
            await page.goto(safe_url, wait_until="domcontentloaded")
            for sel, val in filled_fields.items():
                loc = page.locator(sel).first
                if await loc.count() > 0:
                    await loc.fill(val)
            submit_btn = page.locator("button[type='submit'], input[type='submit']").first
            if await submit_btn.count() > 0:
                await submit_btn.click()
                await page.wait_for_timeout(300)
            await page.screenshot(path=str(post_shot_path), full_page=True)
            await _add_log(
                session,
                logs,
                session_id=approval.session_id,
                approval_request_id=approval.id,
                step_description="Executed user-approved application submission",
                action_type="submit",
                target_selector="button[type='submit']",
                screenshot_url=str(post_shot_path),
                is_success=True,
            )
        finally:
            await context.close()
            await browser.close()

    await session.execute(
        update(Application)
        .where(Application.id == application_id, Application.user_id == user_id)
        .values(status="submitted", applied_at=datetime.now(UTC))
    )
    await session.execute(
        update(AgentSession).where(AgentSession.id == approval.session_id).values(is_active=False)
    )
    await record_agent_event(
        session,
        session_id=approval.session_id,
        node_name="playwright_runner",
        event_type="application_submitted",
        payload={"applicationId": str(application_id), "approvalId": str(approval.id)},
    )
    session.add(
        Notification(
            user_id=user_id,
            title="Application Submitted",
            message="Your approved application submission completed and was archived.",
            type="application_status",
        )
    )
    await session.commit()

    return AutomationPrepareResult(
        application_id=application_id,
        session_id=approval.session_id,
        status="submitted",
        approval_request_id=approval.id,
        screenshot_path=str(post_shot_path),
        filled_fields=filled_fields,
        logs=logs,
        message="Approved application submitted cleanly.",
    )


async def _detect_manual_gate(page: Any) -> str | None:
    for selector in _CAPTCHA_OR_MFA_SELECTORS:
        if await page.locator(selector).count() > 0:
            return selector
    body_text = await page.locator("body").inner_text()
    if _CAPTCHA_TEXT_RE.search(body_text or ""):
        return "captcha_or_mfa_text"
    return None


def _build_candidate_field_map(
    profile: Profile | None,
    student: StudentProfile | None,
    resume: Resume | None,
) -> dict[tuple[str, ...], str]:
    full_name = profile.full_name if profile and profile.full_name else "NexteRaS Candidate"
    email = profile.email if profile else "candidate@nexteras.local"
    college = student.college_name if student else ""
    degree = student.degree if student else ""
    cgpa = f"{float(student.cgpa):.2f}" if student and student.cgpa is not None else ""
    summary = str((resume.master_content or {}).get("summary", "")) if resume else ""
    return {
        ("input[name='full_name']", "input[name='name']", "#full_name", "#name"): full_name,
        ("input[name='email']", "input[type='email']", "#email"): email,
        ("input[name='college']", "input[name='institution']", "#college"): college,
        ("input[name='degree']", "#degree"): degree,
        ("input[name='cgpa']", "#cgpa"): cgpa,
        ("textarea[name='summary']", "textarea[name='cover_letter']", "textarea"): summary,
    }


async def _add_log(
    session: AsyncSession,
    logs: list[dict[str, Any]],
    *,
    session_id: UUID,
    step_description: str,
    action_type: str,
    target_selector: str | None = None,
    screenshot_url: str | None = None,
    approval_request_id: UUID | None = None,
    is_success: bool = True,
    error_message: str | None = None,
) -> None:
    row = BrowserExecutionLog(
        approval_request_id=approval_request_id,
        session_id=session_id,
        step_description=step_description,
        action_type=action_type,
        target_selector=target_selector,
        screenshot_url=screenshot_url,
        is_success=is_success,
        error_message=error_message,
    )
    session.add(row)
    await session.flush()
    logs.append(
        {
            "stepDescription": step_description,
            "actionType": action_type,
            "targetSelector": target_selector,
            "screenshotUrl": screenshot_url,
            "isSuccess": is_success,
            "errorMessage": error_message,
        }
    )


async def load_owned_screenshot_bytes(
    session: AsyncSession,
    *,
    user_id: UUID,
    log_id: UUID,
) -> tuple[bytes, str]:
    """Load PNG screenshot bytes strictly scoped to a user-owned BrowserExecutionLog."""
    row = (
        await session.execute(
            select(BrowserExecutionLog)
            .join(AgentSession, BrowserExecutionLog.session_id == AgentSession.id)
            .where(
                BrowserExecutionLog.id == log_id,
                AgentSession.user_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None or not row.screenshot_url:
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Screenshot Not Found",
            detail="Requested screenshot log does not exist for this user.",
        )

    allowed_root = Path(settings.PLAYWRIGHT_SCREENSHOT_DIR).resolve()
    candidate = Path(row.screenshot_url).resolve()
    try:
        candidate.relative_to(allowed_root)
    except ValueError as exc:
        raise ProblemDetailError(
            status_code=403,
            problem_type="urn:problem:forbidden",
            title="Invalid Screenshot Path",
            detail="Screenshot artifact lies outside allowed sandbox storage.",
        ) from exc

    if not candidate.is_file():
        raise ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Screenshot Artifact Missing",
            detail="Screenshot PNG file is no longer present on disk.",
        )

    return candidate.read_bytes(), candidate.name
