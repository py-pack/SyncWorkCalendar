from fastapi import APIRouter

from src.api.schemas.common import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")
