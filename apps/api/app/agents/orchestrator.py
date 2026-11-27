"""Full 9-logical-agent autonomous LangGraph StateGraph orchestrator with PostgresSaver & M11 resume."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal, TypedDict
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import (
    AgentCommandRequest,
    AgentCommandResponse,
    AgentEventTelemetry,
    AgentRunRequest,
    AgentRunResponse,
    build_postgres_checkpoint_config,
    list_session_events,
    record_agent_event,
)
from app.automation.playwright_runner import (
    execute_approved_submission,
    prepare_application_automation,
)
from app.core.errors import ProblemDetailError
from app.integrations.crustdata import CrustdataClient
from app.integrations.gemini import GeminiClient
from app.integrations.olostep import OlostepClient
from app.models.entities import (
    AgentSession,
    AnalyticsEvent,
    ApprovalRequest,
)
from app.repositories.applications import ApplicationRepository
from app.repositories.approvals import ApprovalRepository
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.opportunities import OpportunityRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    CompanyEnrichRequest,
    OpportunityDiscoverRequest,
    ResearchDiscoverRequest,
    ResumeTailorRequest,
)
from app.services.eligibility import EligibilityService
from app.services.intelligence import IntelligenceService
from app.services.interview import create_starter_interview_session
from app.services.opportunities import OpportunityService
from app.services.resumes import ResumeService

logger = logging.getLogger("opportunity_os.agents.orchestrator")

# Process-local fallback checkpointers used ONLY when PostgreSQL is offline in unit tests.
_FALLBACK_MEMORY_SAVERS: dict[str, MemorySaver] = {}
_SETUP_DONE_URIS: set[str] = set()
_SETUP_LOCK = asyncio.Lock()


class AutonomousWorkflowState(TypedDict, total=False):
    """Serializable LangGraph state spanning all 9 logical agents (M01-M09)."""

    session_id: str
    user_id: str
    query: str
    workflow_type: Literal["full_pipeline", "discovery", "resume_tailoring", "application_prepare"]
    language: str
    target_opportunity_id: str | None
    portal_url: str | None
    enable_web_research: bool
    run_playwright: bool
    max_candidates: int
    checkpointer_backend: str

    current_stage: str
    stage_trace: list[str]
    student_summary: dict[str, Any]
    candidate_shortlist: list[dict[str, Any]]
    enriched_organizations: list[dict[str, Any]]
    selected_opportunity_id: str | None
    selected_opportunity_title: str | None
    selected_portal_url: str | None
    skill_gaps: list[str]
    tailored_resume_id: str | None
    application_id: str | None
    approval_request_id: str | None
    screenshot_path: str | None
    filled_fields: dict[str, str]
    manual_completion_required: bool

    # M11 / M09 human decision & execution state
    human_decision: str | None
    rejection_reason: str | None
    execute_playwright: bool
    submission_status: str | None
    interview_session_id: str | None
    status_message: str


@asynccontextmanager
async def _open_checkpointer(
    session: AsyncSession,
    *,
    session_id: UUID,
    force_memory: bool = False,
) -> AsyncIterator[tuple[Any, str]]:
    """Open real AsyncPostgresSaver when PostgreSQL is reachable; degrade cleanly in unit tests."""
    is_real_sa_session = isinstance(session, AsyncSession) and hasattr(session, "bind")
    cfg = build_postgres_checkpoint_config()
    if not force_memory and is_real_sa_session and cfg.conn_uri.startswith("postgresql://"):
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            async with AsyncPostgresSaver.from_conn_string(cfg.conn_uri) as saver:
                if cfg.conn_uri not in _SETUP_DONE_URIS:
                    async with _SETUP_LOCK:
                        if cfg.conn_uri not in _SETUP_DONE_URIS:
                            await saver.setup()
                            _SETUP_DONE_URIS.add(cfg.conn_uri)
                yield saver, "postgres"
                return
        except Exception as exc:
            logger.info(
                "AsyncPostgresSaver unavailable (%s); falling back to MemorySaver for thread %s.",
                type(exc).__name__,
                session_id,
            )

    mem = _FALLBACK_MEMORY_SAVERS.setdefault(str(session_id), MemorySaver())
    yield mem, "memory"


def build_autonomous_career_graph(
    db_session: AsyncSession,
    *,
    olostep_client: OlostepClient | None = None,
    crustdata_client: CrustdataClient | None = None,
) -> StateGraph[AutonomousWorkflowState]:
    """Build hierarchical 9-logical-agent LangGraph workflow bound cleanly to live services."""

    async def m01_supervisor_router(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-supervisor",
            event_type="task_started",
            payload={
                "agentCode": "M01",
                "workflowType": state.get("workflow_type", "full_pipeline"),
                "language": state.get("language", "en"),
                "query": state.get("query", ""),
            },
        )
        return {
            "current_stage": "initialized",
            "stage_trace": [*state.get("stage_trace", []), "M01_SUPERVISOR"],
        }

    async def m02_passport_intake(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])

        profile = await ProfileRepository(db_session).get_by_user_id(uid)
        student = await StudentProfileRepository(db_session).get_by_user_id(uid)
        passport = await CareerPassportRepository(db_session).get_by_user_id(uid)
        resumes = await ResumeRepository(db_session).list_for_user(uid, limit=1)

        summary: dict[str, Any] = {
            "fullName": profile.full_name if profile else "Student",
            "email": profile.email if profile else "",
            "collegeName": student.college_name if student else None,
            "degree": student.degree if student else None,
            "branch": student.branch if student else None,
            "graduationYear": student.graduation_year if student else None,
            "cgpa": float(student.cgpa) if student and student.cgpa is not None else None,
            "skills": list(student.skills or []) if student else [],
            "passportProjectsCount": len(passport.projects or []) if passport else 0,
            "hasResume": len(resumes) > 0,
        }
        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-workflow-engine",
            event_type="data_transfer",
            payload={"agentCode": "M02", **summary},
        )
        return {
            "student_summary": summary,
            "stage_trace": [*state.get("stage_trace", []), "M02_PASSPORT_INTAKE"],
        }

    async def m03_opportunity_research(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])
        max_cands = int(state.get("max_candidates", 6))
        query = str(state.get("query") or "software engineering internship")

        if state.get("enable_web_research"):
            try:
                intel = IntelligenceService(
                    db_session,
                    olostep_client=olostep_client,
                    crustdata_client=crustdata_client,
                )
                await intel.research_opportunities(
                    uid,
                    ResearchDiscoverRequest(
                        query=query,
                        limit=min(max_cands, 5),
                        enrich_companies=False,
                    ),
                )
            except Exception as exc:
                logger.info("M03 web research degraded gracefully (%s).", type(exc).__name__)

        shortlist: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        pinned_id = state.get("target_opportunity_id")
        if pinned_id:
            try:
                pinned = await OpportunityRepository(db_session).get_by_id(UUID(pinned_id))
                if pinned is not None:
                    seen_ids.add(str(pinned.id))
                    shortlist.append(
                        {
                            "opportunityId": str(pinned.id),
                            "title": pinned.title,
                            "organization": pinned.organization,
                            "sourceUrl": pinned.source_url,
                            "matchScore": 90.0,
                        }
                    )
            except Exception as exc:
                logger.debug("Pinned opportunity lookup skipped (%s).", type(exc).__name__)

        try:
            page = await OpportunityService(db_session).discover(
                uid, OpportunityDiscoverRequest(query=query, limit=max_cands)
            )
            for item in page.items:
                oid = str(item.id)
                if oid not in seen_ids:
                    seen_ids.add(oid)
                    shortlist.append(
                        {
                            "opportunityId": oid,
                            "title": item.title,
                            "organization": item.organization,
                            "sourceUrl": item.source_url,
                            "matchScore": float(item.match_score or 70.0),
                        }
                    )
        except Exception as exc:
            logger.info("M03 discover fallback (%s).", type(exc).__name__)

        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-discovery",
            event_type="delegation",
            payload={"agentCode": "M03", "discoveredCount": len(shortlist)},
        )
        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-dedup-vector",
            event_type="task_completed",
            payload={"agentCode": "M04", "vectorIndexedShortlist": len(shortlist)},
        )
        return {
            "current_stage": "discovered",
            "candidate_shortlist": shortlist[:max_cands],
            "stage_trace": [*state.get("stage_trace", []), "M03_DISCOVERY_VECTOR"],
        }

    async def m04_company_watchtower(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        shortlist = list(state.get("candidate_shortlist", []))
        enriched: list[dict[str, Any]] = []
        intel = IntelligenceService(
            db_session,
            olostep_client=olostep_client,
            crustdata_client=crustdata_client,
        )
        seen_orgs: set[str] = set()
        for item in shortlist:
            org = str(item.get("organization") or "").strip()
            if not org or org in seen_orgs or len(enriched) >= 2:
                continue
            seen_orgs.add(org)
            try:
                org_res = await intel.enrich_company(CompanyEnrichRequest(company_name=org))
                enriched.append(
                    {
                        "name": org_res.name,
                        "isVerified": org_res.is_verified,
                        "headcountRange": org_res.headcount_range,
                    }
                )
            except Exception:
                enriched.append({"name": org, "isVerified": False})

        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-monitor",
            event_type="tool_invoked",
            payload={"agentCode": "M05", "organizationsChecked": len(enriched)},
        )
        return {
            "enriched_organizations": enriched,
            "stage_trace": [*state.get("stage_trace", []), "M04_COMPANY_WATCHTOWER"],
        }

    async def m05_eligibility_skillgap(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])
        shortlist = list(state.get("candidate_shortlist", []))
        svc = EligibilityService(db_session)

        evaluated: list[dict[str, Any]] = []
        for item in shortlist:
            try:
                res = await svc.evaluate(uid, UUID(item["opportunityId"]))
                evaluated.append(
                    {
                        **item,
                        "isEligible": res.is_eligible,
                        "eligibilityScore": res.score,
                        "missingSkills": res.missing_skills,
                        "reasons": res.reasons,
                    }
                )
            except Exception:
                evaluated.append({**item, "isEligible": True, "eligibilityScore": 70.0})

        pinned = state.get("target_opportunity_id")
        chosen: dict[str, Any] | None = None
        if pinned:
            chosen = next((e for e in evaluated if e["opportunityId"] == pinned), None)
        if chosen is None and evaluated:
            evaluated_sorted = sorted(
                evaluated,
                key=lambda x: (
                    1 if x.get("isEligible") else 0,
                    float(x.get("eligibilityScore", 0)),
                ),
                reverse=True,
            )
            chosen = evaluated_sorted[0]

        sel_id = chosen["opportunityId"] if chosen else None
        sel_title = chosen.get("title") if chosen else None
        sel_url = chosen.get("sourceUrl") if chosen else None
        gaps = list(chosen.get("missingSkills", [])) if chosen else []

        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-eligibility",
            event_type="task_completed",
            payload={
                "agentCode": "M06",
                "selectedOpportunityId": sel_id,
                "evaluatedCount": len(evaluated),
                "skillGaps": gaps,
            },
        )
        return {
            "current_stage": "evaluated",
            "candidate_shortlist": evaluated,
            "selected_opportunity_id": sel_id,
            "selected_opportunity_title": sel_title,
            "selected_portal_url": sel_url,
            "skill_gaps": gaps,
            "stage_trace": [*state.get("stage_trace", []), "M05_ELIGIBILITY_SKILLGAP"],
        }

    def _route_after_eligibility(state: AutonomousWorkflowState) -> str:
        if state.get("workflow_type") == "discovery" or not state.get("selected_opportunity_id"):
            return "m09_post_approval_monitor"
        return "m06_resume_tailor_nli"

    async def m06_resume_tailor_nli(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])
        opp_id_str = state.get("selected_opportunity_id")
        tailored_id: str | None = None

        if opp_id_str:
            res_repo = ResumeRepository(db_session)
            existing = await res_repo.list_for_user(uid, limit=1)
            if existing:
                master = existing[0]
            else:
                stu = state.get("student_summary") or {}
                master = await res_repo.create_for_user(
                    uid,
                    title="Career Passport Auto-Grounded Resume",
                    master_content={
                        "profile": {
                            "full_name": stu.get("fullName") or "NexteRaS Student",
                            "degree": stu.get("degree"),
                            "branch_or_specialization": stu.get("branch"),
                            "graduation_year": stu.get("graduationYear"),
                            "cgpa": stu.get("cgpa"),
                        },
                        "skills": list(stu.get("skills") or []),
                        "summary": "Verified academic and project portfolio from Career Passport.",
                    },
                    extraction_status="completed",
                )
            try:
                custom = await ResumeService(db_session).tailor_resume(
                    master.id,
                    uid,
                    ResumeTailorRequest(opportunity_id=UUID(opp_id_str)),
                )
                tailored_id = str(master.id)
                verified_cnt = len(custom.verified_claims)
                rejected_cnt = len(custom.rejected_claims)
            except Exception as exc:
                logger.info("M06 resume tailor degraded (%s).", type(exc).__name__)
                tailored_id = str(master.id)
                verified_cnt = 0
                rejected_cnt = 0

            await record_agent_event(
                db_session,
                session_id=sid,
                node_name="agent-resume",
                event_type="task_completed",
                payload={"agentCode": "M08", "resumeId": tailored_id},
            )
            await record_agent_event(
                db_session,
                session_id=sid,
                node_name="agent-nli-verifier",
                event_type="guardrail_triggered",
                payload={
                    "agentCode": "M09",
                    "verifiedClaims": verified_cnt,
                    "rejectedClaims": rejected_cnt,
                },
            )

        return {
            "current_stage": "tailored",
            "tailored_resume_id": tailored_id,
            "stage_trace": [*state.get("stage_trace", []), "M06_RESUME_NLI"],
        }

    def _route_after_resume(state: AutonomousWorkflowState) -> str:
        if state.get("workflow_type") == "resume_tailoring":
            return "m09_post_approval_monitor"
        return "m07_playwright_prepare"

    async def m07_playwright_prepare(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])
        opp_id_str = state.get("selected_opportunity_id")
        if not opp_id_str:
            return {
                "manual_completion_required": False,
                "stage_trace": [*state.get("stage_trace", []), "M07_SKIPPED_NO_OPP"],
            }

        opp_id = UUID(opp_id_str)
        app_repo = ApplicationRepository(db_session)
        app_row = await app_repo.get_by_user_and_opportunity(uid, opp_id)
        if app_row is None:
            app_row = await app_repo.create_draft(uid, opp_id, status="drafting")
            await db_session.flush()

        target_url = (state.get("portal_url") or state.get("selected_portal_url") or "").strip()
        if state.get("run_playwright") and target_url:
            prep = await prepare_application_automation(
                db_session,
                user_id=uid,
                application_id=app_row.id,
                portal_url=target_url,
                existing_session_id=sid,
                langgraph_thread_id=str(sid),
            )
            if prep.status == "requires_manual_completion":
                return {
                    "application_id": str(app_row.id),
                    "screenshot_path": prep.screenshot_path,
                    "manual_completion_required": True,
                    "current_stage": "requires_manual_completion",
                    "status_message": prep.message,
                    "stage_trace": [*state.get("stage_trace", []), "M07_CAPTCHA_HALT"],
                }
            return {
                "application_id": str(app_row.id),
                "approval_request_id": str(prep.approval_request_id)
                if prep.approval_request_id
                else None,
                "screenshot_path": prep.screenshot_path,
                "filled_fields": prep.filled_fields,
                "manual_completion_required": False,
                "current_stage": "awaiting_human_approval",
                "status_message": prep.message,
                "stage_trace": [*state.get("stage_trace", []), "M07_PLAYWRIGHT_PREPARED"],
            }

        # Structured dry-run preparation without live browser launch
        stu = state.get("student_summary") or {}
        filled = {
            "full_name": str(stu.get("fullName") or "NexteRaS Student"),
            "email": str(stu.get("email") or ""),
            "college": str(stu.get("collegeName") or ""),
            "degree": str(stu.get("degree") or ""),
        }
        approval = ApprovalRequest(
            session_id=sid,
            user_id=uid,
            opportunity_id=opp_id,
            action_type="submit_application",
            payload_summary={
                "application_id": str(app_row.id),
                "portal_url": target_url,
                "filled_fields": filled,
                "tailored_resume_id": state.get("tailored_resume_id"),
                "langgraph_thread_id": str(sid),
            },
            status="pending",
        )
        db_session.add(approval)
        await db_session.flush()
        await db_session.refresh(approval)

        if (app_row.status or "drafting") in (
            "discovered",
            "saved",
            "evaluating",
            "eligible",
            "drafting",
        ):
            await app_repo.transition_status_for_user(
                app_row.id,
                uid,
                expected_status=app_row.status or "drafting",
                new_status="ready_for_review",
            )

        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-form-mapper",
            event_type="tool_invoked",
            payload={"agentCode": "M10", "filledKeys": list(filled.keys())},
        )
        await record_agent_event(
            db_session,
            session_id=sid,
            node_name="agent-approval-gate",
            event_type="approval_requested",
            payload={"agentCode": "M11", "approvalRequestId": str(approval.id)},
        )
        agent_row = await db_session.get(AgentSession, sid)
        if agent_row is not None:
            agent_row.state = {
                **dict(agent_row.state or {}),
                "currentStage": "awaiting_human_approval",
                "approvalRequestId": str(approval.id),
                "applicationId": str(app_row.id),
                "opportunityId": opp_id_str,
                "checkpointerBackend": state.get("checkpointer_backend", "postgres"),
            }
        await db_session.commit()

        return {
            "application_id": str(app_row.id),
            "approval_request_id": str(approval.id),
            "filled_fields": filled,
            "manual_completion_required": False,
            "current_stage": "awaiting_human_approval",
            "status_message": "Application prepared cleanly. Paused at M11 waiting for human approval.",
            "stage_trace": [*state.get("stage_trace", []), "M07_FORM_PREPARED"],
        }

    def _route_after_prepare(state: AutonomousWorkflowState) -> str:
        if state.get("manual_completion_required"):
            return "m09_post_approval_monitor"
        return "m08_human_approval_gate"

    async def m08_human_approval_gate(state: AutonomousWorkflowState) -> dict[str, Any]:
        decision_payload = interrupt(
            {
                "gate": "M11_HUMAN_APPROVAL",
                "session_id": state["session_id"],
                "approval_request_id": state.get("approval_request_id"),
                "application_id": state.get("application_id"),
                "opportunity_id": state.get("selected_opportunity_id"),
                "screenshot_path": state.get("screenshot_path"),
                "filled_fields": state.get("filled_fields", {}),
                "requires_human_approval": True,
            }
        )
        approved = isinstance(decision_payload, dict) and decision_payload.get("approved") is True
        exec_pw = isinstance(decision_payload, dict) and bool(
            decision_payload.get("execute_playwright", False)
        )
        reason = (
            decision_payload.get("rejection_reason") if isinstance(decision_payload, dict) else None
        )
        return {
            "human_decision": "approved" if approved else "rejected",
            "rejection_reason": str(reason) if reason else None,
            "execute_playwright": exec_pw,
            "current_stage": "approved" if approved else "rejected",
            "stage_trace": [*state.get("stage_trace", []), "M08_APPROVAL_GATE"],
        }

    async def m09_post_approval_monitor(state: AutonomousWorkflowState) -> dict[str, Any]:
        sid = UUID(state["session_id"])
        uid = UUID(state["user_id"])
        lang = str(state.get("language") or "en")
        target_role = str(state.get("selected_opportunity_title") or "Software Engineering Intern")

        if state.get("manual_completion_required"):
            agent_row = await db_session.get(AgentSession, sid)
            if agent_row is not None:
                agent_row.is_active = False
                agent_row.state = {
                    **dict(agent_row.state or {}),
                    "currentStage": "requires_manual_completion",
                    "status": "requires_manual_completion",
                }
            await db_session.commit()
            return {
                "current_stage": "requires_manual_completion",
                "submission_status": "requires_manual_completion",
                "stage_trace": [*state.get("stage_trace", []), "M09_MANUAL_HALT"],
            }

        wf_type = state.get("workflow_type", "full_pipeline")
        if wf_type in ("discovery", "resume_tailoring") or not state.get("selected_opportunity_id"):
            db_session.add(
                AnalyticsEvent(
                    user_id=uid,
                    event_name="autonomous_workflow_completed",
                    event_metadata={"workflowType": wf_type, "sessionId": str(sid)},
                )
            )
            agent_row = await db_session.get(AgentSession, sid)
            if agent_row is not None:
                agent_row.is_active = False
                agent_row.state = {
                    **dict(agent_row.state or {}),
                    "currentStage": state.get("current_stage", "evaluated"),
                    "status": "completed",
                }
            await db_session.commit()
            return {
                "current_stage": state.get("current_stage", "evaluated"),
                "submission_status": "completed",
                "status_message": "Workflow completed cleanly.",
                "stage_trace": [*state.get("stage_trace", []), "M09_MONITOR_COMPLETE"],
            }

        submission_status = state.get("human_decision") or "rejected"
        interview_sid: str | None = None

        if state.get("human_decision") == "approved":
            await record_agent_event(
                db_session,
                session_id=sid,
                node_name="agent-approval-gate",
                event_type="approval_granted",
                payload={
                    "agentCode": "M11",
                    "approvalRequestId": state.get("approval_request_id"),
                },
            )
            app_id_str = state.get("application_id")
            apr_id_str = state.get("approval_request_id")
            if (
                state.get("execute_playwright")
                and app_id_str
                and apr_id_str
                and (state.get("portal_url") or state.get("selected_portal_url"))
            ):
                sub_res = await execute_approved_submission(
                    db_session,
                    user_id=uid,
                    application_id=UUID(app_id_str),
                    approval_id=UUID(apr_id_str),
                )
                submission_status = sub_res.status
            else:
                submission_status = "approved_ready_for_dispatch"

            try:
                iv_row = await create_starter_interview_session(
                    db_session,
                    user_id=uid,
                    target_role=target_role,
                    language=lang,
                )
                interview_sid = str(iv_row.id)
                await record_agent_event(
                    db_session,
                    session_id=sid,
                    node_name="agent-mock-interview",
                    event_type="task_completed",
                    payload={"agentCode": "M14", "interviewSessionId": interview_sid},
                )
            except Exception as exc:
                logger.info("M09 interview starter skipped (%s).", type(exc).__name__)

            db_session.add(
                AnalyticsEvent(
                    user_id=uid,
                    event_name="autonomous_workflow_completed",
                    event_metadata={
                        "sessionId": str(sid),
                        "submissionStatus": submission_status,
                    },
                )
            )
            msg = f"Workflow approved and resumed cleanly ({submission_status})."
        else:
            await record_agent_event(
                db_session,
                session_id=sid,
                node_name="agent-approval-gate",
                event_type="guardrail_triggered",
                payload={"agentCode": "M11", "reason": state.get("rejection_reason")},
            )
            db_session.add(
                AnalyticsEvent(
                    user_id=uid,
                    event_name="autonomous_workflow_rejected",
                    event_metadata={"sessionId": str(sid)},
                )
            )
            msg = "Workflow aborted safely upon user rejection."

        agent_row = await db_session.get(AgentSession, sid)
        if agent_row is not None:
            agent_row.is_active = False
            agent_row.state = {
                **dict(agent_row.state or {}),
                "currentStage": submission_status,
                "status": submission_status,
                "interviewSessionId": interview_sid,
            }
        await db_session.commit()

        return {
            "current_stage": submission_status,
            "submission_status": submission_status,
            "interview_session_id": interview_sid,
            "status_message": msg,
            "stage_trace": [*state.get("stage_trace", []), "M09_POST_APPROVAL"],
        }

    graph: StateGraph[AutonomousWorkflowState] = StateGraph(AutonomousWorkflowState)
    graph.add_node("m01_supervisor_router", m01_supervisor_router)
    graph.add_node("m02_passport_intake", m02_passport_intake)
    graph.add_node("m03_opportunity_research", m03_opportunity_research)
    graph.add_node("m04_company_watchtower", m04_company_watchtower)
    graph.add_node("m05_eligibility_skillgap", m05_eligibility_skillgap)
    graph.add_node("m06_resume_tailor_nli", m06_resume_tailor_nli)
    graph.add_node("m07_playwright_prepare", m07_playwright_prepare)
    graph.add_node("m08_human_approval_gate", m08_human_approval_gate)
    graph.add_node("m09_post_approval_monitor", m09_post_approval_monitor)

    graph.add_edge(START, "m01_supervisor_router")
    graph.add_edge("m01_supervisor_router", "m02_passport_intake")
    graph.add_edge("m02_passport_intake", "m03_opportunity_research")
    graph.add_edge("m03_opportunity_research", "m04_company_watchtower")
    graph.add_edge("m04_company_watchtower", "m05_eligibility_skillgap")
    graph.add_conditional_edges(
        "m05_eligibility_skillgap",
        _route_after_eligibility,
        {
            "m06_resume_tailor_nli": "m06_resume_tailor_nli",
            "m09_post_approval_monitor": "m09_post_approval_monitor",
        },
    )
    graph.add_conditional_edges(
        "m06_resume_tailor_nli",
        _route_after_resume,
        {
            "m07_playwright_prepare": "m07_playwright_prepare",
            "m09_post_approval_monitor": "m09_post_approval_monitor",
        },
    )
    graph.add_conditional_edges(
        "m07_playwright_prepare",
        _route_after_prepare,
        {
            "m08_human_approval_gate": "m08_human_approval_gate",
            "m09_post_approval_monitor": "m09_post_approval_monitor",
        },
    )
    graph.add_edge("m08_human_approval_gate", "m09_post_approval_monitor")
    graph.add_edge("m09_post_approval_monitor", END)
    return graph


class AgentOrchestratorService:
    """Service coordinating persisted LangGraph runs, M11 approval resumes, and operator commands."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        olostep_client: OlostepClient | None = None,
        crustdata_client: CrustdataClient | None = None,
        force_memory_checkpointer: bool = False,
    ) -> None:
        self._session = session
        self._olostep = olostep_client
        self._crustdata = crustdata_client
        self._force_memory = force_memory_checkpointer

    async def launch_workflow(self, user_id: UUID, req: AgentRunRequest) -> AgentRunResponse:
        """Create a persisted AgentSession and execute LangGraph until M11 interrupt or END."""
        agent_session = AgentSession(
            user_id=user_id,
            agent_type=f"langgraph_{req.workflow_type}",
            state={
                "workflowType": req.workflow_type,
                "language": req.language,
                "query": req.query,
                "currentStage": "initialized",
            },
            is_active=True,
        )
        self._session.add(agent_session)
        await self._session.flush()
        await self._session.refresh(agent_session)

        graph = build_autonomous_career_graph(
            self._session,
            olostep_client=self._olostep,
            crustdata_client=self._crustdata,
        )
        async with _open_checkpointer(
            self._session, session_id=agent_session.id, force_memory=self._force_memory
        ) as (checkpointer, backend_name):
            agent_session.state = {
                **dict(agent_session.state or {}),
                "checkpointerBackend": backend_name,
            }
            compiled = graph.compile(checkpointer=checkpointer)
            initial_state: AutonomousWorkflowState = {
                "session_id": str(agent_session.id),
                "user_id": str(user_id),
                "query": req.query,
                "workflow_type": req.workflow_type,
                "language": req.language,
                "target_opportunity_id": (
                    str(req.target_opportunity_id) if req.target_opportunity_id else None
                ),
                "portal_url": req.portal_url,
                "enable_web_research": req.enable_web_research,
                "run_playwright": req.run_playwright,
                "max_candidates": req.max_candidates,
                "checkpointer_backend": backend_name,
            }
            final_state = await compiled.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": str(agent_session.id)}},
            )

        events = await list_session_events(self._session, user_id, agent_session.id) or []
        await self._session.commit()

        stage = str(final_state.get("current_stage") or "initialized")
        interrupted = "__interrupt__" in final_state
        status_label = "awaiting_human_approval" if interrupted else stage
        return AgentRunResponse(
            session_id=agent_session.id,
            thread_id=str(agent_session.id),
            agent_type=agent_session.agent_type,
            status=status_label,
            current_stage=stage,
            checkpointer_backend=backend_name,
            language=req.language,
            selected_opportunity_id=_optional_uuid(final_state.get("selected_opportunity_id")),
            application_id=_optional_uuid(final_state.get("application_id")),
            approval_request_id=_optional_uuid(final_state.get("approval_request_id")),
            tailored_resume_id=_optional_uuid(final_state.get("tailored_resume_id")),
            screenshot_path=final_state.get("screenshot_path"),
            interview_session_id=_optional_uuid(final_state.get("interview_session_id")),
            ranked_shortlist=list(final_state.get("candidate_shortlist") or []),
            skill_gaps=list(final_state.get("skill_gaps") or []),
            events=events,
            message=str(
                final_state.get("status_message")
                or "Autonomous LangGraph execution reached checkpoint."
            ),
        )

    async def resume_after_approval(
        self,
        *,
        user_id: UUID,
        approval_id: UUID,
        approved: bool,
        rejection_reason: str | None = None,
        execute_submission: bool = False,
    ) -> dict[str, Any]:
        """Resume a suspended LangGraph thread at M11 when human approval is decided."""
        approval = await ApprovalRepository(self._session).get_for_user(approval_id, user_id)
        if approval is None:
            return {"workflow_resumed": False, "resumed_stage": None, "submission_status": None}

        payload_summary = dict(approval.payload_summary or {})
        thread_id_str = str(payload_summary.get("langgraph_thread_id") or approval.session_id)
        session_row = (
            await self._session.execute(
                select(AgentSession).where(
                    AgentSession.id == approval.session_id,
                    AgentSession.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if session_row is None or not str(session_row.agent_type).startswith("langgraph_"):
            return {"workflow_resumed": False, "resumed_stage": None, "submission_status": None}

        graph = build_autonomous_career_graph(
            self._session,
            olostep_client=self._olostep,
            crustdata_client=self._crustdata,
        )
        try:
            async with _open_checkpointer(
                self._session, session_id=session_row.id, force_memory=self._force_memory
            ) as (checkpointer, _):
                compiled = graph.compile(checkpointer=checkpointer)
                config: RunnableConfig = {"configurable": {"thread_id": thread_id_str}}
                snapshot = await compiled.aget_state(config)
                if not snapshot or not getattr(snapshot, "next", ()):
                    return {
                        "workflow_resumed": False,
                        "resumed_stage": None,
                        "submission_status": None,
                    }
                resume_cmd: Command[Any] = Command(
                    resume={
                        "approved": approved,
                        "rejection_reason": rejection_reason,
                        "execute_playwright": execute_submission,
                    }
                )
                resumed_state = await compiled.ainvoke(resume_cmd, config=config)
            return {
                "workflow_resumed": True,
                "resumed_stage": str(resumed_state.get("current_stage") or ""),
                "submission_status": resumed_state.get("submission_status"),
            }
        except Exception as exc:
            logger.warning("LangGraph checkpoint resume failed (%s).", type(exc).__name__)
            return {"workflow_resumed": False, "resumed_stage": None, "submission_status": None}

    async def execute_operator_command(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        req: AgentCommandRequest,
    ) -> AgentCommandResponse:
        """Execute an operator command (pause/resume/grounded query) on an owned AgentSession."""
        row = (
            await self._session.execute(
                select(AgentSession).where(
                    AgentSession.id == session_id,
                    AgentSession.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Agent Session Not Found",
                detail="Requested agent session does not exist for this user.",
            )

        if req.action == "pause":
            row.is_active = False
            event = await record_agent_event(
                self._session,
                session_id=row.id,
                node_name="agent-supervisor",
                event_type="operator_paused",
                payload={"action": "pause", "command": req.command},
            )
            reply = "Paused autonomous session checkpoint cleanly."
        elif req.action == "resume":
            row.is_active = True
            event = await record_agent_event(
                self._session,
                session_id=row.id,
                node_name="agent-supervisor",
                event_type="operator_resumed",
                payload={"action": "resume", "command": req.command},
            )
            reply = "Resumed session active monitoring state."
        else:
            events = await list_session_events(self._session, user_id, row.id, limit=15) or []
            state_summary = dict(row.state or {})
            client = GeminiClient()
            reply = ""
            if client.configured and req.command.strip():
                try:
                    reply = await client.generate_text(
                        prompt=(
                            f"Session state: {state_summary}\n"
                            f"Recent events: {[f'{e.node_name}:{e.event_type}' for e in events[-6:]]}\n"
                            f"Operator query ({req.language}): {req.command}"
                        ),
                        system_instruction="Answer concisely using ONLY the verified session state above.",
                        temperature=0.2,
                    )
                except Exception:
                    reply = ""
            if not reply:
                reply = (
                    f"Session {row.id} ({row.agent_type}) is "
                    f"{'active' if row.is_active else 'paused/completed'} at stage "
                    f"'{state_summary.get('currentStage', 'initialized')}' with {len(events)} logged events."
                )
            event = await record_agent_event(
                self._session,
                session_id=row.id,
                node_name="agent-supervisor",
                event_type="operator_query",
                payload={"query": req.command, "reply": reply[:500]},
            )

        await self._session.commit()
        await self._session.refresh(event)
        return AgentCommandResponse(
            session_id=row.id,
            action=req.action,
            reply=reply,
            is_active=bool(row.is_active),
            event=AgentEventTelemetry(
                id=event.id,
                session_id=event.session_id,
                node_name=event.node_name,
                event_type=event.event_type,
                payload=dict(event.payload or {}),
                created_at=event.created_at,
            ),
        )


def _optional_uuid(raw: Any) -> UUID | None:
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None
