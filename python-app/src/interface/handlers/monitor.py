"""
Monitor / health-check handler.

Mirrors Go: src/interface/handlers/gofiber/modules/monitor/monitor.go

Route: GET /api/v1/
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.domain.entities.crud import MonitorEntity

router = APIRouter(tags=["Monitor"])
_settings = get_settings()


@router.get(
    "/",
    response_model=MonitorEntity,
    summary="Health Check",
    description="Returns the application name and version. No authentication required.",
    responses={
        200: {
            "description": "Application is running",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Python Clean Architecture API",
                        "version": "1.0.0",
                    }
                }
            },
        }
    },
)
async def health_check() -> JSONResponse:
    """
    Returns the app name and version.
    Mirrors Go's HealthCheck handler.
    """
    return JSONResponse(
        content={
            "name": _settings.app_name,
            "version": _settings.app_version,
        }
    )
