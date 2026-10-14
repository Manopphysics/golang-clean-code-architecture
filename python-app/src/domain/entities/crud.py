"""
Generic CRUD and monitor domain entities.

Mirrors Go:
  src/domain/entities/crud/models.go   — DataResponse, DataListResponse
  src/domain/entities/monitor/monitor.go — Monitor
"""
from typing import Any

from pydantic import BaseModel


class DataResponse(BaseModel):
    """
    Single-item CRUD response envelope.
    Mirrors Go's DataResponse.
    """
    code: int
    data: Any
    message: str
    data_schema: dict[str, Any] | None = None


class DataListResponse(BaseModel):
    """
    Paginated list CRUD response envelope.
    Mirrors Go's DataListResponse.
    """
    code: int
    data: Any
    page: int
    page_size: int
    total_page: int
    total_data: int
    message: str
    data_schema: dict[str, Any] | None = None


class MonitorEntity(BaseModel):
    """Health-check response payload. Mirrors Go's Monitor struct."""
    name: str
    version: str
