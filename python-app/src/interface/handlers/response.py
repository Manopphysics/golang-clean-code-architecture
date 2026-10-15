"""
HTTP response helpers.

Mirrors Go: src/interface/handlers/gofiber/entities/response.go

Go's NewResponse builder had two shapes:
  Success: returns the data directly (no envelope)
  Error:   returns { "trace_id": "...", "message": "..." }

FastAPI's JSONResponse is used here to match that exact behaviour.
"""
from fastapi import status
from fastapi.responses import JSONResponse


def success_response(data: object, status_code: int = status.HTTP_200_OK) -> JSONResponse:
    """
    Return data directly — no wrapper envelope.
    Mirrors Go's NewResponse(c).Success(code, data).Response().
    """
    return JSONResponse(content=_serialise(data), status_code=status_code)


def error_response(
    trace_id: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """
    Return { "trace_id": "...", "message": "..." }.
    Mirrors Go's NewResponse(c).Error(code, traceId, msg).Response().
    """
    return JSONResponse(
        content={"trace_id": trace_id, "message": message},
        status_code=status_code,
    )


def _serialise(data: object) -> object:
    """
    Convert Pydantic models and dataclasses to JSON-safe dicts.
    Handles nested models, lists, and plain values.
    """
    if data is None:
        return None
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    if isinstance(data, list):
        return [_serialise(item) for item in data]
    if isinstance(data, dict):
        return {k: _serialise(v) for k, v in data.items()}
    return data
