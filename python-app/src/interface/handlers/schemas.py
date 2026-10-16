"""
Shared OpenAPI response schemas.

These Pydantic models are used exclusively for documentation — they tell
FastAPI what the error response body looks like so Swagger renders it
correctly in the UI.

Mirrors Go's error shape: { "trace_id": "...", "message": "..." }
"""
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned on 4xx / 5xx responses."""

    trace_id: str = Field(
        ...,
        description="Error code identifying the source handler",
        examples=["users-001"],
    )
    message: str = Field(
        ...,
        description="Human-readable error description",
        examples=["email pattern is invalid"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "trace_id": "users-001",
                "message": "email pattern is invalid",
            }
        }
    }
