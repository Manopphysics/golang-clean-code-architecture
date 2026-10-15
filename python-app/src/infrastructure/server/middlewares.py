"""
Middleware and auth dependencies.

Mirrors Go: src/infrastructure/gofiber/server/middlewares.go

Go had:
  Cors()        → handled by FastAPI CORSMiddleware in main.py
  Logger()      → handled by uvicorn access log
  RouterCheck() → FastAPI returns 404 automatically
  JwtAuth()     → replicated here as a FastAPI Depends() function

The JWT auth dependency sets two request-state values:
  request.state.user            — UserEntity
  request.state.user_permission — UserPermissionModel | None
matching Go's c.Locals("user") and c.Locals("user_permission").
"""
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.server.dependencies import get_user_usecase
from src.usecases.user_usecase import IUserUsecase

_bearer = HTTPBearer(auto_error=False)


async def jwt_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    user_usecase: IUserUsecase = Depends(get_user_usecase),
) -> None:
    """
    FastAPI dependency that validates a Bearer JWT on every protected route.

    Mirrors Go's JwtAuth() middleware:
      1. Extract token from Authorization header
      2. Call user_usecase.user_authentication(token)
      3. Set user + permissions on request state
      4. Return 401 on any failure (trace_id: "middleware-002")

    Usage:
        @router.get("/profile", dependencies=[Depends(jwt_auth)])
    Or inject directly to get the user:
        async def handler(request: Request, _=Depends(jwt_auth)):
            user = request.state.user
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"trace_id": "middleware-002", "message": "missing authorization header"},
        )

    try:
        user_entity, user_permission = await user_usecase.user_authentication(
            credentials.credentials
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"trace_id": "middleware-002", "message": str(exc)},
        ) from exc

    request.state.user = user_entity
    request.state.user_permission = user_permission
