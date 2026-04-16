from fastapi import APIRouter

from app.core.config import HealthInfo, settings

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthInfo)
async def health_check() -> HealthInfo:
    return HealthInfo(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
    )
