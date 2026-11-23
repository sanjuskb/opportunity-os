from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthResponse, OpportunityResponse

v1_router = APIRouter(prefix="/v1")


@v1_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Returns the current operational status of the API."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.ENVIRONMENT,
    )


@v1_router.get("/opportunities", response_model=list[OpportunityResponse], tags=["Opportunities"])
async def list_opportunities() -> list[OpportunityResponse]:
    """Returns vetted opportunities matched for Indian college students."""
    return []
