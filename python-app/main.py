"""
Application entry point.

Mirrors Go's src/infrastructure/gofiber/main.go — this is where
the app is wired together and started.

Run with:
    cd python-app
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Python (FastAPI) rewrite of the Golang Clean Architecture template.",
    docs_url="/docs",
    redoc_url="/redoc",
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
async def health_check():
    return {"name": settings.app_name, "version": settings.app_version}
