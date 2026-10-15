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
from fastapi.responses import JSONResponse

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
from src.interface.handlers.schemas import ErrorResponse
from src.usecases.user_usecase import IUserUsecase

router = APIRouter(prefix="/users", tags=["Users"])

# Reusable error response doc for 400 and 401
_ERR_400 = {
    "model": ErrorResponse,
    "content": {
        "application/json": {
            "example": {"trace_id": "users-001", "message": "email pattern is invalid"}
        }
    },
}
_ERR_401 = {
    "model": ErrorResponse,
    "content": {
        "application/json": {
            "example": {"trace_id": "middleware-002", "message": "missing authorization header"}
        }
    },
}


@router.post(
    "/register",
    response_model=UserEntity,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description=(
        "Create a new user account. "
        "Password is hashed with bcrypt (cost 10) before storage."
    ),
    responses={
        201: {"model": UserEntity},
        400: {
            **_ERR_400,
            "content": {
                "application/json": {
                    "example": {"trace_id": "users-001", "message": "email pattern is invalid"}
                }
            },
        },
    },
)
async def register_user(
    body: UserRegisterRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> JSONResponse:
    """Register a new user. Mirrors Go's RegisterUser() — trace_id: users-001."""
    try:
        user = await usecase.register_user(body)
    except Exception as exc:
        return error_response("users-001", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(user, status.HTTP_201_CREATED)


@router.post(
    "/login",
    response_model=UserLoginResponse,
    summary="User Login",
    description=(
        "Authenticate with email and password. "
        "Returns a JWT access token and refresh token. "
        "Tokens are stored in the database (stateful auth)."
    ),
    responses={
        200: {"model": UserLoginResponse},
        400: {
            **_ERR_400,
            "content": {
                "application/json": {
                    "example": {"trace_id": "users-002", "message": "password is invalid"}
                }
            },
        },
    },
)
async def user_login(
    body: UserLoginRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> JSONResponse:
    """Authenticate and return tokens. Mirrors Go's UserLogin() — trace_id: users-002."""
    try:
        response = await usecase.user_login(body)
    except Exception as exc:
        return error_response("users-002", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(response)


@router.post(
    "/logout",
    summary="User Logout",
    description=(
        "Invalidate the current session by deleting the token row from the database. "
        "Requires the refresh token in the request body."
    ),
    responses={
        200: {
            "description": "Logged out successfully",
            "content": {"application/json": {"example": None}},
        },
        400: {
            **_ERR_400,
            "content": {
                "application/json": {
                    "example": {"trace_id": "users-004", "message": "user token not found"}
                }
            },
        },
    },
)
async def user_logout(
    body: UserRefreshTokenRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> JSONResponse:
    """Logout by deleting token row. Mirrors Go's UserLogout() — trace_id: users-004."""
    try:
        await usecase.user_logout(body)
    except Exception as exc:
        return error_response("users-004", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(None)


@router.post(
    "/refresh-token",
    response_model=UserLoginResponse,
    summary="Refresh Token",
    description=(
        "Issue a new access token using a valid refresh token. "
        "The refresh token expiry is preserved (never extended). "
        "Both new tokens are upserted in the database."
    ),
    responses={
        200: {"model": UserLoginResponse},
        400: {
            **_ERR_400,
            "content": {
                "application/json": {
                    "example": {"trace_id": "users-003", "message": "token had expired"}
                }
            },
        },
    },
)
async def refresh_token(
    body: UserRefreshTokenRequest,
    usecase: IUserUsecase = Depends(get_user_usecase),
) -> JSONResponse:
    """Refresh access token. Mirrors Go's RefreshToken() — trace_id: users-003."""
    try:
        response = await usecase.user_refresh_token(body)
    except Exception as exc:
        return error_response("users-003", str(exc), status.HTTP_400_BAD_REQUEST)
    return success_response(response)


@router.get(
    "/profile",
    response_model=UserEntity,
    summary="Get User Profile",
    description=(
        "Return the authenticated user's profile. "
        "Requires a valid Bearer token in the Authorization header. "
        "User data is read from the JWT middleware context — no extra DB call."
    ),
    dependencies=[Depends(jwt_auth)],
    responses={
        200: {"model": UserEntity},
        401: _ERR_401,
    },
)
async def get_user_profile(request: Request) -> JSONResponse:
    """
    Return authenticated user profile.
    Mirrors Go's GetUserProfile() — note: Go used POST, corrected to GET.
    """
    return success_response(request.state.user)
