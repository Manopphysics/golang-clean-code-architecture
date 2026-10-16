"""
Application entry point.

Mirrors Go's src/infrastructure/gofiber/main.go — this is where
the app is wired together and started.

Run with:
    cd python-app
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.config import get_settings
from src.infrastructure.database.mongodb import close_mongo
from src.infrastructure.server.modules import register_routes

settings = get_settings()

# ---------------------------------------------------------------------------
# OpenAPI tag descriptions — shown in the /docs sidebar
# ---------------------------------------------------------------------------
TAGS_METADATA = [
    {
        "name": "Monitor",
        "description": "Health-check endpoint. No authentication required.",
    },
    {
        "name": "Users",
        "description": (
            "User registration, authentication, and token management. "
            "Uses stateful JWT — tokens are stored in the database and "
            "validated on every authenticated request."
        ),
    },
    {
        "name": "CRUD",
        "description": (
            "Generic data access endpoints for any registered entity model. "
            "Use the `entity_model_slug` path parameter to target a model "
            "(e.g. `users`, `user-tokens`, `user-permissions`). "
            "All endpoints require a valid Bearer token."
        ),
    },
]


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await close_mongo()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "## Python (FastAPI) Clean Architecture API\n\n"
        "A faithful Python rewrite of the "
        "[Golang Clean Architecture](https://github.com/max38/golang-clean-code-architecture) "
        "template, implementing the same four-layer architecture:\n\n"
        "| Layer | Go | Python |\n"
        "|---|---|---|\n"
        "| Domain | Entities + Interfaces | Pydantic schemas + ABCs |\n"
        "| Use Cases | `usecases/` | `src/usecases/` |\n"
        "| Interface | Handlers + Repositories | FastAPI routers + SQLAlchemy |\n"
        "| Infrastructure | GoFiber + GORM + Motor | FastAPI + SQLAlchemy + Motor |\n\n"
        "### Authentication\n"
        "Protected endpoints require a `Bearer` token in the `Authorization` header.\n"
        "1. Register → `POST /api/v1/users/register`\n"
        "2. Login → `POST /api/v1/users/login` — returns `access` + `refresh` tokens\n"
        "3. Pass `Authorization: Bearer <access_token>` on protected requests\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
    contact={
        "name": "API Repository",
        "url": "https://github.com/max38/golang-clean-code-architecture",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
register_routes(app)


# ---------------------------------------------------------------------------
# Custom OpenAPI schema — adds HTTPBearer security scheme globally
# so the "Authorize" button appears in /docs
# ---------------------------------------------------------------------------
def custom_openapi() -> dict:  # type: ignore[type-arg]
    if app.openapi_schema:
        return app.openapi_schema  # type: ignore[return-value]

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=TAGS_METADATA,
    )

    # Register the Bearer security scheme
    schema.setdefault("components", {})
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token from POST /api/v1/users/login",
        }
    }

    app.openapi_schema = schema
    return schema  # type: ignore[return-value]


app.openapi = custom_openapi  # type: ignore[method-assign]
