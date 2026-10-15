"""
User HTTP handlers.

Mirrors Go: src/interface/handlers/gofiber/modules/user/user.go

Routes (all under /api/v1/users):
  POST /register       → register_user
  POST /login          → user_login
  POST /logout         → user_logout
  POST /refresh-token  → refresh_token
  GET  /profile        → get_user_profile  (Go used POST — fixed to GET here)
"""
from fastapi import APIRouter, Depends, Request, status

from src.domain.entities.user import (
    UserEntity,
    UserLoginRequest,
    UserLoginResponse,
    UserRefreshTokenRequest,
    UserRegisterRequest,
)
from src.infrastructure.server.dependencies import get_user_usecase
from src.infrastructure.server.middlewares import jwt_auth
from src.interface.handlers.response import error_response, success_response
from src.usecases.user_usecase import IUserUsecase

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    responses={400: {"description": "Validation or duplicate email error"}},
)
async def register_user(
    body: UserRegisterRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> UserEntity:
    """
    Register a new user.
    Mirrors Go's RegisterUser() handler — trace_id: users-001.
    """
    try:
        user = await usecase.register_user(body)
    except Exception as exc:
        return error_response("users-001", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(user, status.HTTP_201_CREATED)  # type: ignore[return-value]


@router.post(
    "/login",
    summary="User Login",
    responses={400: {"description": "Invalid credentials"}},
)
async def user_login(
    body: UserLoginRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> UserLoginResponse:
    """
    Authenticate and return access + refresh tokens.
    Mirrors Go's UserLogin() handler — trace_id: users-002.
    """
    try:
        response = await usecase.user_login(body)
    except Exception as exc:
        return error_response("users-002", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(response)  # type: ignore[return-value]


@router.post(
    "/logout",
    summary="User Logout",
    responses={400: {"description": "Invalid or missing refresh token"}},
)
async def user_logout(
    body: UserRefreshTokenRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> None:
    """
    Logout by deleting the token row.
    Mirrors Go's UserLogout() handler — trace_id: users-004.
    """
    try:
        await usecase.user_logout(body)
    except Exception as exc:
        return error_response("users-004", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(None)  # type: ignore[return-value]


@router.post(
    "/refresh-token",
    summary="Refresh Token",
    responses={400: {"description": "Invalid or expired refresh token"}},
)
async def refresh_token(
    body: UserRefreshTokenRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> UserLoginResponse:
    """
    Issue a new access token using a valid refresh token.
    Mirrors Go's RefreshToken() handler — trace_id: users-003.
    """
    try:
        response = await usecase.user_refresh_token(body)
    except Exception as exc:
        return error_response("users-003", str(exc), status.HTTP_400_BAD_REQUEST)  # type: ignore[return-value]
    return success_response(response)  # type: ignore[return-value]


@router.get(
    "/profile",
    summary="Get User Profile",
    responses={401: {"description": "Invalid or missing token"}},
    dependencies=[Depends(jwt_auth)],
)
async def get_user_profile(request: Request) -> UserEntity:
    """
    Return the authenticated user's profile.
    Mirrors Go's GetUserProfile() handler.
    Note: Go used POST — corrected to GET for proper REST semantics.
    User is set on request.state by jwt_auth dependency (mirrors Go's
    c.Locals("user") set by the JwtAuth middleware).
    """
    return success_response(request.state.user)  # type: ignore[return-value]
