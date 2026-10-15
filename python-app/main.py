"""
Application entry point.

Mirrors Go's src/infrastructure/gofiber/main.go — this is where
the app is wired together and started.

Run with:
    cd python-app
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.infrastructure.database.mongodb import close_mongo

settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# Mirrors Go's graceful shutdown via os.Interrupt signal handler.
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    # startup — nothing to do yet (SQLAlchemy pool is lazy)
    yield
    # shutdown — close MongoDB client cleanly
    await close_mongo()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Python (FastAPI) rewrite of the Golang Clean Architecture template.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — mirrors Go's cors.New(cors.Config{ AllowOrigins: "*" })
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ---------------------------------------------------------------------------
# Health-check — placeholder until PR-07 wires the real monitor handler
# ---------------------------------------------------------------------------
@app.get("/api/v1/", tags=["Monitor"])
async def health_check() -> dict[str, str]:
    return {"name": settings.app_name, "version": settings.app_version}
