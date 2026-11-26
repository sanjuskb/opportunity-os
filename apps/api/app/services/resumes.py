"""Domain service for Resume CRUD, file ingestion, NLI-grounded tailoring, and PDF export."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ProblemDetailError
from app.integrations.supabase_storage import ResumeStorageClient, build_resume_storage_path
from app.models.entities import Resume, ResumeVersion
from app.repositories.career_passports import CareerPassportRepository
from app.repositories.opportunities import OpportunityRepository
from app.repositories.profiles import ProfileRepository
from app.repositories.resumes import ResumeRepository
from app.repositories.student_profiles import StudentProfileRepository
from app.schemas.common import (
    ResumeAnalyzeResponse,
    ResumeCreateRequest,
    ResumeCustomizationResponse,
    ResumeDownloadUrlResponse,
    ResumeResponse,
    ResumeTailorRequest,
    ResumeVersionResponse,
)
from app.services.resume_parser import (
    compute_sha256,
    extract_text_from_bytes,
    parse_structured_resume,
    validate_resume_upload,
    verify_claim_against_premise,
)
from app.services.resume_pdf import render_resume_pdf

logger = logging.getLogger("opportunity_os.resumes")


class ResumeService:
    """Business logic for public.resumes, versions, customizations & private storage."""

    def __init__(
        self,
        session: AsyncSession,
        storage_client: ResumeStorageClient | None = None,
    ) -> None:
        self._session = session
        self._repo = ResumeRepository(session)
        self._profile_repo = ProfileRepository(session)
        self._student_repo = StudentProfileRepository(session)
        self._passport_repo = CareerPassportRepository(session)
        self._opp_repo = OpportunityRepository(session)
        self._storage = storage_client or ResumeStorageClient()

    async def list_resumes(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ResumeResponse]:
        try:
            rows = await self._repo.list_for_user(user_id, limit=limit, offset=offset)
        except (SQLAlchemyError, OSError) as exc:
            logger.warning("Database error while listing resumes.")
            raise self._db_unavailable_error() from exc
        return [self._to_response(row) for row in rows]

    async def get_resume(self, resume_id: UUID, user_id: UUID) -> ResumeResponse:
        record = await self._require_owned_resume(resume_id, user_id)
        return self._to_response(record)

    async def create_resume(self, user_id: UUID, payload: ResumeCreateRequest) -> ResumeResponse:
        try:
            if await self._profile_repo.get_by_user_id(user_id) is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Profile Not Found",
                    detail="User profile must exist before creating a resume.",
                )
            created = await self._repo.create_for_user(
                user_id,
                title=payload.title,
                master_content=payload.master_content,
            )
            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error while creating resume.")
            raise self._db_unavailable_error() from exc
        return self._to_response(created)

    async def upload_resume(
        self,
        user_id: UUID,
        *,
        filename: str,
        raw_bytes: bytes,
        title: str | None = None,
        sync_to_profile: bool = False,
        prefer_local_storage: bool = False,
    ) -> ResumeResponse:
        try:
            mime_type = validate_resume_upload(filename, raw_bytes)
            raw_text = extract_text_from_bytes(filename, raw_bytes)
            if not raw_text:
                raise ValueError("Uploaded document contains no extractable text.")
        except ValueError as exc:
            raise ProblemDetailError(
                status_code=422,
                problem_type="urn:problem:validation_failed",
                title="Invalid Resume File",
                detail=str(exc),
            ) from exc

        structured = parse_structured_resume(raw_text)
        sha256 = compute_sha256(raw_bytes)
        resume_id = uuid4()
        storage_path = build_resume_storage_path(user_id, resume_id, filename)
        resolved_title = (title or "").strip() or (
            filename.rsplit(".", 1)[0][:255] or "Uploaded Resume"
        )

        try:
            if await self._profile_repo.get_by_user_id(user_id) is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Profile Not Found",
                    detail="User profile must exist before uploading a resume.",
                )

            await self._storage.upload_bytes(
                storage_path=storage_path,
                raw_bytes=raw_bytes,
                content_type=mime_type,
                prefer_local=prefer_local_storage,
            )

            confidence = structured.get("confidence")
            created = await self._repo.create_for_user(
                user_id,
                resume_id=resume_id,
                title=resolved_title,
                master_content=structured,
                storage_bucket=self._storage.bucket,
                storage_path=storage_path,
                original_filename=filename[:255],
                mime_type=mime_type,
                file_size_bytes=len(raw_bytes),
                file_sha256=sha256,
                raw_text=raw_text[:100_000],
                extraction_status=str(structured.get("validation_status") or "valid")[:30],
                extraction_confidence=(
                    Decimal(str(round(float(confidence), 3))) if confidence is not None else None
                ),
            )
            await self._repo.create_version(
                created.id,
                version_number=1,
                content=structured,
                pdf_url=f"/api/v1/resumes/{created.id}/pdf",
            )

            if sync_to_profile:
                await self._sync_extracted_profile(user_id, structured)

            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error during resume upload.")
            raise self._db_unavailable_error() from exc

        return self._to_response(created)

    async def list_versions(self, resume_id: UUID, user_id: UUID) -> list[ResumeVersionResponse]:
        await self._require_owned_resume(resume_id, user_id)
        try:
            versions = await self._repo.list_versions(resume_id)
        except (SQLAlchemyError, OSError) as exc:
            raise self._db_unavailable_error() from exc
        return [self._version_to_response(v) for v in versions]

    async def get_download_url(self, resume_id: UUID, user_id: UUID) -> ResumeDownloadUrlResponse:
        record = await self._require_owned_resume(resume_id, user_id)
        signed_url: str | None = None
        if record.storage_path:
            signed_url = await self._storage.create_signed_url(storage_path=record.storage_path)
        return ResumeDownloadUrlResponse(
            resume_id=record.id,
            storage_bucket=record.storage_bucket,
            storage_path=record.storage_path,
            signed_url=signed_url,
            fallback_pdf_endpoint=f"/api/v1/resumes/{record.id}/pdf",
        )

    async def analyze_resume(
        self,
        resume_id: UUID,
        user_id: UUID,
        *,
        opportunity_id: UUID | None = None,
    ) -> ResumeAnalyzeResponse:
        record = await self._require_owned_resume(resume_id, user_id)
        content = dict(record.master_content or {})
        skills = self._extract_skills_list(content)
        raw_profile = content.get("profile")
        profile: dict[str, Any] = raw_profile if isinstance(raw_profile, dict) else {}

        score = 25.0
        warnings: list[str] = list(content.get("warnings") or [])
        recommendations: list[str] = []

        if profile.get("full_name"):
            score += 10.0
        else:
            recommendations.append("Add your full name header for ATS readability.")
        if profile.get("degree") and profile.get("graduation_year"):
            score += 20.0
        else:
            recommendations.append("Include degree, branch, and graduation batch clearly.")
        if len(skills) >= 3:
            score += 25.0
        elif skills:
            score += 12.0
            recommendations.append("Add more domain technical skills relevant to target roles.")
        else:
            recommendations.append("Add a dedicated Technical Skills section.")
        if content.get("projects") or content.get("experience"):
            score += 20.0
        else:
            recommendations.append(
                "Add verified academic projects or internship experience bullets."
            )

        matched_skills: list[str] = []
        missing_skills: list[str] = []
        if opportunity_id is not None:
            opp = await self._opp_repo.get_by_id(opportunity_id)
            if opp is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Opportunity Not Found",
                    detail="Target opportunity for resume analysis does not exist.",
                )
            req_skills = list(opp.eligibility.required_skills or []) if opp.eligibility else []
            owned_lower = {s.lower() for s in skills}
            for req in req_skills:
                if req.lower() in owned_lower:
                    matched_skills.append(req)
                else:
                    missing_skills.append(req)
            if missing_skills:
                recommendations.append(
                    f"Consider building verified Career Passport proof for missing skills: {', '.join(missing_skills[:5])}."
                )

        return ResumeAnalyzeResponse(
            resume_id=record.id,
            opportunity_id=opportunity_id,
            completeness_score=min(100.0, round(score, 2)),
            extracted_skills=skills,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            warnings=warnings,
            recommendations=recommendations,
        )

    async def tailor_resume(
        self,
        resume_id: UUID,
        user_id: UUID,
        payload: ResumeTailorRequest,
    ) -> ResumeCustomizationResponse:
        record = await self._require_owned_resume(resume_id, user_id)
        try:
            opp = await self._opp_repo.get_by_id(payload.opportunity_id)
        except (SQLAlchemyError, OSError) as exc:
            raise self._db_unavailable_error() from exc
        if opp is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Opportunity Not Found",
                detail="Target opportunity does not exist.",
            )

        passport = await self._passport_repo.get_by_user_id(user_id)
        content = dict(record.master_content or {})
        resume_skills = self._extract_skills_list(content)
        req_skills = list(opp.eligibility.required_skills or []) if opp.eligibility else []

        # Build verified evidence premise strictly from Career Passport + stored Resume text
        evidence_lines: list[str] = []
        passport_bullets: list[str] = []
        if record.raw_text:
            evidence_lines.append(record.raw_text)
        if passport is not None:
            for bucket in (
                passport.projects,
                passport.verified_achievements,
                passport.coursework,
                passport.certifications,
            ):
                if isinstance(bucket, list):
                    for item in bucket:
                        if isinstance(item, dict):
                            summary = " - ".join(
                                str(item[k])
                                for k in ("title", "name", "description", "summary", "issuer")
                                if item.get(k)
                            )
                            if summary:
                                evidence_lines.append(summary)
                                passport_bullets.append(summary)

        for key in ("projects", "experience"):
            items = content.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        line = " - ".join(
                            str(item[k])
                            for k in ("title", "name", "description", "summary", "text")
                            if item.get(k)
                        )
                        if line:
                            evidence_lines.append(line)
                            passport_bullets.append(line)

        if resume_skills:
            evidence_lines.append("Skills: " + ", ".join(resume_skills))

        premise = "\n".join(evidence_lines).strip() or record.title

        # Prioritize matching existing verified evidence items for target opportunity keywords
        target_keywords = {s.lower() for s in req_skills}
        target_keywords.update(
            w.lower() for w in f"{opp.title} {payload.custom_focus or ''}".split() if len(w) > 3
        )
        prioritized = sorted(
            dict.fromkeys(passport_bullets),
            key=lambda b: sum(1 for kw in target_keywords if kw in b.lower()),
            reverse=True,
        )

        claims_to_verify = list(payload.candidate_claims) + prioritized[:5]
        if not claims_to_verify and resume_skills:
            claims_to_verify = [
                f"Applied {', '.join(resume_skills[:4])} in documented coursework and projects."
            ]

        verified_claims: list[dict[str, Any]] = []
        rejected_claims: list[dict[str, Any]] = []
        for idx, claim_text in enumerate(claims_to_verify, start=1):
            check = verify_claim_against_premise(f"tailor-{idx}", premise, claim_text)
            if check.get("is_grounded") and check.get("verdict") != "contradicted":
                verified_claims.append({"claim": claim_text, **check})
            else:
                rejected_claims.append({"claim": claim_text, **check})

        owned_lower = {s.lower() for s in resume_skills}
        matched = [s for s in req_skills if s.lower() in owned_lower]
        alignment = (
            round((len(matched) / max(1, len(req_skills))) * 100.0, 2)
            if req_skills
            else (85.0 if verified_claims else 65.0)
        )

        tailored_payload: dict[str, Any] = {
            **content,
            "target_opportunity": {
                "id": str(opp.id),
                "title": opp.title,
                "organization": opp.organization,
            },
            "tailored_summary": (
                f"Tailored for {opp.title} at {opp.organization}. Verified alignment across "
                f"{len(verified_claims)} evidence-backed bullet(s)."
            ),
            "tailored_bullets": [c["claim"] for c in verified_claims],
            "matched_skills": matched,
            "missing_skills": [s for s in req_skills if s.lower() not in owned_lower],
            "custom_focus": payload.custom_focus,
            "verification_summary": {
                "verified_count": len(verified_claims),
                "rejected_count": len(rejected_claims),
            },
        }

        try:
            next_ver = await self._repo.next_version_number(record.id)
            await self._repo.create_version(
                record.id,
                version_number=next_ver,
                content=tailored_payload,
                pdf_url=f"/api/v1/resumes/{record.id}/pdf?version={next_ver}",
            )
            custom = await self._repo.create_customization(
                record.id,
                opp.id,
                tailored_content=tailored_payload,
                alignment_score=Decimal(str(alignment)),
            )
            await self._session.commit()
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            raise self._db_unavailable_error() from exc

        return ResumeCustomizationResponse(
            id=custom.id,
            resume_id=record.id,
            opportunity_id=opp.id,
            version_number=next_ver,
            alignment_score=alignment,
            tailored_content=tailored_payload,
            verified_claims=verified_claims,
            rejected_claims=rejected_claims,
            created_at=custom.created_at,
        )

    async def export_pdf(
        self,
        resume_id: UUID,
        user_id: UUID,
        *,
        version_number: int | None = None,
    ) -> tuple[bytes, str]:
        record = await self._require_owned_resume(resume_id, user_id)
        content = dict(record.master_content or {})
        try:
            versions = await self._repo.list_versions(record.id)
        except (SQLAlchemyError, OSError):
            versions = []

        selected_version: ResumeVersion | None = None
        if version_number is not None:
            for ver in versions:
                if ver.version_number == version_number:
                    selected_version = ver
                    break
            if selected_version is None:
                raise ProblemDetailError(
                    status_code=404,
                    problem_type="urn:problem:not_found",
                    title="Resume Version Not Found",
                    detail=f"Resume version {version_number} does not exist.",
                )
        elif versions:
            selected_version = versions[0]

        if selected_version is not None:
            content = dict(selected_version.content or {})

        pdf_bytes = render_resume_pdf(record.title, content)
        filename = f"nexteras-resume-{record.id}.pdf"
        return pdf_bytes, filename

    async def delete_resume(self, resume_id: UUID, user_id: UUID) -> None:
        record = await self._repo.get_for_user(resume_id, user_id)
        try:
            deleted = await self._repo.delete_for_user(resume_id, user_id)
            if not deleted:
                raise self._not_found_error()
            await self._session.commit()
        except ProblemDetailError:
            raise
        except (SQLAlchemyError, OSError) as exc:
            await self._session.rollback()
            logger.warning("Database error while deleting resume.")
            raise self._db_unavailable_error() from exc

        if record and record.storage_path:
            await self._storage.delete_object(record.storage_path)

    async def _require_owned_resume(self, resume_id: UUID, user_id: UUID) -> Resume:
        try:
            record = await self._repo.get_for_user(resume_id, user_id)
        except (SQLAlchemyError, OSError) as exc:
            logger.warning("Database error while fetching resume.")
            raise self._db_unavailable_error() from exc
        if record is None:
            raise self._not_found_error()
        return record

    async def _sync_extracted_profile(self, user_id: UUID, structured: dict[str, Any]) -> None:
        raw_profile = structured.get("profile")
        profile_block: dict[str, Any] = raw_profile if isinstance(raw_profile, dict) else {}
        existing = await self._student_repo.get_by_user_id(user_id)
        college = (existing.college_name if existing else None) or "University Profile"
        degree = profile_block.get("degree") or (existing.degree if existing else None) or "B.Tech"
        branch = (
            profile_block.get("branch_or_specialization")
            or (existing.branch if existing else None)
            or "General"
        )
        grad_year = profile_block.get("graduation_year") or (
            existing.graduation_year if existing else 2027
        )
        cgpa_val = profile_block.get("cgpa")
        cgpa = (
            Decimal(str(cgpa_val))
            if cgpa_val is not None
            else (existing.cgpa if existing else None)
        )
        await self._student_repo.upsert_for_user(
            user_id,
            college_name=college,
            degree=str(degree)[:100],
            branch=str(branch)[:120],
            graduation_year=int(grad_year),
            cgpa=cgpa,
            state=existing.state if existing else None,
            bio=existing.bio if existing else None,
        )

    @staticmethod
    def _extract_skills_list(content: dict[str, Any]) -> list[str]:
        raw = content.get("normalized_skills") or content.get("skills") or []
        if not isinstance(raw, list):
            return []
        return [str(s) for s in raw if str(s).strip()]

    @staticmethod
    def _not_found_error() -> ProblemDetailError:
        return ProblemDetailError(
            status_code=404,
            problem_type="urn:problem:not_found",
            title="Resume Not Found",
            detail="Requested resume does not exist.",
        )

    @staticmethod
    def _db_unavailable_error() -> ProblemDetailError:
        return ProblemDetailError(
            status_code=503,
            problem_type="urn:problem:service_unavailable",
            title="Service Unavailable",
            detail="Database is temporarily unavailable.",
        )

    @staticmethod
    def _to_response(record: Resume) -> ResumeResponse:
        return ResumeResponse(
            id=record.id,
            user_id=record.user_id,
            title=record.title,
            master_content=dict(record.master_content or {}),
            storage_bucket=record.storage_bucket,
            storage_path=record.storage_path,
            original_filename=record.original_filename,
            mime_type=record.mime_type,
            file_size_bytes=record.file_size_bytes,
            file_sha256=record.file_sha256,
            extraction_status=record.extraction_status,
            extraction_confidence=record.extraction_confidence,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _version_to_response(version: ResumeVersion) -> ResumeVersionResponse:
        return ResumeVersionResponse(
            id=version.id,
            resume_id=version.resume_id,
            version_number=version.version_number,
            content=dict(version.content or {}),
            pdf_url=version.pdf_url,
            created_at=version.created_at,
        )
