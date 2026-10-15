"""
Monitor / health-check handler.

Mirrors Go: src/interface/handlers/gofiber/modules/monitor/monitor.go

Route: GET /api/v1/
"""
from fastapi import APIRouter

from src.config import get_settings
from src.domain.entities.crud import MonitorEntity

router = APIRouter(tags=["Monitor"])
_settings = get_settings()


@router.get("/", response_model=MonitorEntity, summary="Health Check")
async def health_check() -> MonitorEntity:
    """
    Returns the app name and version.
    Mirrors Go's HealthCheck handler.
    """
    return MonitorEntity(
        name=_settings.app_name,
        version=_settings.app_version,
    )
