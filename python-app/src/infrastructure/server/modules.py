"""
Route registration.

Mirrors Go: src/infrastructure/gofiber/server/module.go

Mounts all routers onto the FastAPI app under /api/v1.
Each module function mirrors its Go equivalent:
  MonitorModule()  → monitor router
  UsersModule()    → users router
  CRUDModule()     → data router
"""
from fastapi import FastAPI

from src.interface.handlers import crud, monitor, user


def register_routes(app: FastAPI) -> None:
    """
    Register all API routers.
    Called once from main.py during app factory setup.
    Mirrors Go's module factory pattern in server.Start().
    """
    API_PREFIX = "/api/v1"

    # Monitor — GET /api/v1/
    app.include_router(monitor.router, prefix=API_PREFIX)

    # Users — POST /api/v1/users/...
    app.include_router(user.router, prefix=API_PREFIX)

    # CRUD  — GET  /api/v1/data/...
    app.include_router(crud.router, prefix=API_PREFIX)
