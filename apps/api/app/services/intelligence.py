"""Domain service orchestrating Olostep web discovery, Crustdata company intelligence & Watchtower."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ProblemDetailError
from app.integrations.crustdata import CrustdataClient, CrustdataError
from app.integrations.olostep import OlostepClient, OlostepError, validate_public_http_url
from app.models.entities import (
    Opportunity,
    OpportunityEligibility,
    OpportunityMonitor,
    OpportunitySource,
    Organization,
)
from app.repositories.embeddings import EmbeddingRepository
from app.schemas.common import (
    CompanyEnrichRequest,
    MonitorCreateRequest,
    MonitorResponse,
    OrganizationResponse,
    ResearchDiscoverRequest,
    ResearchDiscoverResponse,
)
from app.services.opportunities import OpportunityService
from app.services.opportunity_text import build_opportunity_embedding_payload

logger = logging.getLogger("opportunity_os.intelligence")


def _infer_opportunity_type(title: str, description: str) -> str:
    txt = f"{title} {description}".lower()
    if "hackathon" in txt:
        return "hackathon"
    if "fellowship" in txt:
        return "fellowship"
    if "scholarship" in txt or "grant" in txt:
        return "scholarship"
    if "intern" in txt:
        return "internship"
    return "full_time"


def _infer_location(text: str) -> str:
    low = text.lower()
    for city in (
        "Bengaluru",
        "Bangalore",
        "Hyderabad",
        "Mumbai",
        "Pune",
        "Chennai",
        "Delhi",
        "Remote",
    ):
        if city.lower() in low:
            return "Bengaluru" if city == "Bangalore" else city
    return "India / Remote"


def _extract_org_name(title: str, url: str) -> str:
    for sep in (" at ", " - ", " | "):
        if sep in title:
            parts = title.split(sep)
            candidate = parts[-1].strip()
            if 2 <= len(candidate) <= 80:
                return candidate
    host = (urlparse(url).hostname or "verified-source").replace("www.", "")
    return host.split(".")[0].capitalize()


class IntelligenceService:
    """Orchestrates real Olostep discovery, Crustdata company caching, and watchtower monitors."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        olostep_client: OlostepClient | None = None,
        crustdata_client: CrustdataClient | None = None,
    ) -> None:
        self._session = session
        self._olostep = olostep_client or OlostepClient()
        self._crustdata = crustdata_client or CrustdataClient()

    async def research_opportunities(
        self,
        _user_id: UUID,
        payload: ResearchDiscoverRequest,
    ) -> ResearchDiscoverResponse:
        """Search/scrape genuine web sources via Olostep, deduplicate, and persist with provenance."""
        discovered_raw: list[dict[str, str]] = []
        sources_recorded: list[str] = []

        try:
            if payload.target_url:
                scraped = await self._olostep.scrape(payload.target_url)
                discovered_raw.append(
                    {
                        "title": scraped.title
                        or f"Opportunity at {urlparse(scraped.url).hostname}",
                        "url": scraped.url,
                        "description": scraped.markdown[:2000] or "Scraped posting content.",
                    }
                )
            else:
                search_res = await self._olostep.search(payload.query)
                for item in search_res.items[: payload.limit]:
                    discovered_raw.append(
                        {
                            "title": item.title,
                            "url": item.url,
                            "description": item.markdown or item.snippet or item.title,
                        }
                    )
        except ValueError as exc:
            raise ProblemDetailError(
                status_code=422,
                problem_type="urn:problem:validation_failed",
                title="Disallowed Target URL",
                detail=str(exc),
            ) from exc
        except OlostepError as exc:
            raise ProblemDetailError(
                status_code=exc.status_code or 502,
                problem_type="urn:problem:external_provider_error",
                title="Olostep Research Unavailable",
                detail=str(exc),
            ) from exc

        persisted: list[Opportunity] = []
        dedup_count = 0
        emb_repo = EmbeddingRepository(self._session)

        for entry in discovered_raw:
            url = entry["url"].strip()
            title = entry["title"].strip()[:250]
            desc = entry["description"].strip() or title
            org_name = _extract_org_name(title, url)
            domain = (urlparse(url).hostname or "unknown").lower()

            existing_stmt = (
                select(Opportunity)
                .where(
                    or_(
                        Opportunity.source_url == url,
                        (
                            (func.lower(Opportunity.title) == title.lower())
                            & (func.lower(Opportunity.organization) == org_name.lower())
                        ),
                    )
                )
                .options(selectinload(Opportunity.eligibility))
            )
            existing_opp = (await self._session.execute(existing_stmt)).scalars().first()
            await self._record_source_hit(domain=domain, provider="olostep")
            if domain not in sources_recorded:
                sources_recorded.append(domain)

            if existing_opp is not None:
                dedup_count += 1
                persisted.append(existing_opp)
                continue

            content_hash = hashlib.sha256(f"{title}|{org_name}|{url}".encode()).hexdigest()
            opp = Opportunity(
                title=title,
                organization=org_name,
                location=_infer_location(f"{title} {desc}"),
                type=_infer_opportunity_type(title, desc),
                description=desc[:5000],
                source_url=url,
                source_provider="olostep",
                retrieval_timestamp=datetime.now(UTC),
                last_verified_at=datetime.now(UTC),
                content_hash=content_hash,
                confidence_score=Decimal("0.850"),
                is_active=True,
                raw_data={"research_query": payload.query, "domain": domain},
            )
            self._session.add(opp)
            await self._session.flush()

            elig = OpportunityEligibility(opportunity_id=opp.id, required_skills=[])
            self._session.add(elig)
            await self._session.flush()
            opp.eligibility = elig

            _, emb_hash = build_opportunity_embedding_payload(opp)
            await emb_repo.upsert_pending(opp.id, content_hash=emb_hash)
            persisted.append(opp)

            if payload.enrich_companies and self._crustdata.is_configured:
                try:
                    enriched = await self.enrich_company(
                        CompanyEnrichRequest(domain=domain, company_name=org_name)
                    )
                    opp.organization_id = enriched.id
                except ProblemDetailError:
                    pass

        await self._session.commit()

        return ResearchDiscoverResponse(
            query=payload.query,
            discovered_count=len(persisted) - dedup_count,
            deduplicated_count=dedup_count,
            opportunities=[OpportunityService._to_response(o) for o in persisted],
            sources_recorded=sources_recorded,
            usage_stats=dict(self._olostep.usage_stats),
        )

    async def enrich_company(self, payload: CompanyEnrichRequest) -> OrganizationResponse:
        """Enrich or return 24h-cached organization firmographics via Crustdata."""
        if not payload.domain and not payload.company_name:
            raise ProblemDetailError(
                status_code=422,
                problem_type="urn:problem:validation_failed",
                title="Missing Company Identifier",
                detail="Provide either domain or companyName.",
            )

        norm_domain = payload.domain.strip().lower() if payload.domain else None
        norm_name = payload.company_name.strip() if payload.company_name else None

        existing: Organization | None = None
        if norm_domain:
            existing = (
                await self._session.execute(
                    select(Organization).where(Organization.domain == norm_domain)
                )
            ).scalar_one_or_none()
        elif norm_name:
            existing = (
                await self._session.execute(
                    select(Organization).where(func.lower(Organization.name) == norm_name.lower())
                )
            ).scalar_one_or_none()

        fresh_cutoff = datetime.now(UTC) - timedelta(hours=24)
        if (
            not payload.force_refresh
            and existing is not None
            and existing.last_enriched_at is not None
            and (
                existing.last_enriched_at
                if existing.last_enriched_at.tzinfo
                else existing.last_enriched_at.replace(tzinfo=UTC)
            )
            >= fresh_cutoff
        ):
            return self._org_to_response(existing)

        try:
            intel = await self._crustdata.identify_or_enrich_company(
                domain=norm_domain, company_name=norm_name
            )
        except CrustdataError as exc:
            raise ProblemDetailError(
                status_code=exc.status_code or 502,
                problem_type="urn:problem:external_provider_error",
                title="Crustdata Intelligence Unavailable",
                detail=str(exc),
            ) from exc

        if intel is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Company Not Found",
                detail="No firmographic record found for supplied identifier.",
            )

        now = datetime.now(UTC)
        if existing is None and intel.domain:
            existing = (
                await self._session.execute(
                    select(Organization).where(Organization.domain == intel.domain.lower())
                )
            ).scalar_one_or_none()

        if existing is None:
            existing = Organization(
                name=intel.name,
                domain=intel.domain.lower() if intel.domain else None,
                industry=intel.industry,
                headcount_range=intel.headcount_range,
                funding_stage=intel.funding_stage,
                description=intel.description,
                hiring_velocity_score=(
                    Decimal(str(round(intel.hiring_velocity_score, 2)))
                    if intel.hiring_velocity_score is not None
                    else None
                ),
                is_verified=intel.is_verified,
                crustdata_payload=intel.raw_payload,
                last_enriched_at=now,
            )
            self._session.add(existing)
        else:
            existing.name = intel.name
            existing.industry = intel.industry
            existing.headcount_range = intel.headcount_range
            existing.funding_stage = intel.funding_stage
            existing.description = intel.description
            existing.hiring_velocity_score = (
                Decimal(str(round(intel.hiring_velocity_score, 2)))
                if intel.hiring_velocity_score is not None
                else None
            )
            existing.is_verified = intel.is_verified
            existing.crustdata_payload = intel.raw_payload
            existing.last_enriched_at = now

        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(existing)
        return self._org_to_response(existing)

    async def list_companies(self, *, limit: int = 50) -> list[OrganizationResponse]:
        rows = (
            (
                await self._session.execute(
                    select(Organization).order_by(Organization.created_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [self._org_to_response(r) for r in rows]

    async def get_company(self, org_id: UUID) -> OrganizationResponse:
        row = (
            await self._session.execute(select(Organization).where(Organization.id == org_id))
        ).scalar_one_or_none()
        if row is None:
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Organization Not Found",
                detail="Requested company record does not exist.",
            )
        return self._org_to_response(row)

    async def list_monitors(self, user_id: UUID) -> list[MonitorResponse]:
        rows = (
            (
                await self._session.execute(
                    select(OpportunityMonitor)
                    .where(OpportunityMonitor.user_id == user_id)
                    .order_by(OpportunityMonitor.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return [self._monitor_to_response(m) for m in rows]

    async def create_monitor(self, user_id: UUID, payload: MonitorCreateRequest) -> MonitorResponse:
        criteria = dict(payload.criteria or {})
        criteria["frequency"] = payload.frequency
        if payload.target_url:
            try:
                safe_url = validate_public_http_url(payload.target_url)
            except ValueError as exc:
                raise ProblemDetailError(
                    status_code=422,
                    problem_type="urn:problem:validation_failed",
                    title="Invalid Monitor URL",
                    detail=str(exc),
                ) from exc
            criteria["targetUrl"] = safe_url
            if self._olostep.is_configured:
                try:
                    remote = await self._olostep.create_monitor(
                        safe_url, frequency=payload.frequency
                    )
                    if remote.get("id"):
                        criteria["olostepMonitorId"] = str(remote["id"])
                except OlostepError as exc:
                    logger.warning("Olostep remote monitor skipped cleanly: %s", exc)

        monitor = OpportunityMonitor(
            user_id=user_id,
            target_organization=payload.target_organization,
            criteria=criteria,
            is_active=True,
        )
        self._session.add(monitor)
        await self._session.commit()
        await self._session.refresh(monitor)
        return self._monitor_to_response(monitor)

    async def delete_monitor(self, user_id: UUID, monitor_id: UUID) -> None:
        stmt = delete(OpportunityMonitor).where(
            OpportunityMonitor.id == monitor_id,
            OpportunityMonitor.user_id == user_id,
        )
        res = await self._session.execute(stmt)
        if (res.rowcount or 0) == 0:  # type: ignore[attr-defined]
            raise ProblemDetailError(
                status_code=404,
                problem_type="urn:problem:not_found",
                title="Monitor Not Found",
                detail="Requested watchtower monitor does not exist.",
            )
        await self._session.commit()

    async def _record_source_hit(self, *, domain: str, provider: str) -> None:
        src = (
            await self._session.execute(
                select(OpportunitySource).where(
                    OpportunitySource.provider == provider,
                    OpportunitySource.domain == domain,
                )
            )
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if src is None:
            self._session.add(
                OpportunitySource(
                    provider=provider,
                    domain=domain,
                    last_scraped_at=now,
                    status="healthy",
                    last_response_code=200,
                    requests_count=1,
                )
            )
        else:
            src.last_scraped_at = now
            src.status = "healthy"
            src.last_response_code = 200
            src.requests_count = int(src.requests_count or 0) + 1

    @staticmethod
    def _org_to_response(org: Organization) -> OrganizationResponse:
        return OrganizationResponse(
            id=org.id,
            name=org.name,
            domain=org.domain,
            industry=org.industry,
            headcount_range=org.headcount_range,
            funding_stage=org.funding_stage,
            description=org.description,
            hiring_velocity_score=(
                float(org.hiring_velocity_score) if org.hiring_velocity_score is not None else None
            ),
            is_verified=bool(org.is_verified),
            last_enriched_at=org.last_enriched_at,
        )

    @staticmethod
    def _monitor_to_response(monitor: OpportunityMonitor) -> MonitorResponse:
        return MonitorResponse(
            id=monitor.id,
            user_id=monitor.user_id,
            target_organization=monitor.target_organization,
            criteria=dict(monitor.criteria or {}),
            is_active=True if monitor.is_active is None else bool(monitor.is_active),
            created_at=monitor.created_at,
        )
