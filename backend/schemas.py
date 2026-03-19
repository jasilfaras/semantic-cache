from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.config import DEFAULT_MAX_QUERY_LENGTH


@dataclass(slots=True)
class CacheMatch:
    answer: str
    score: float


class AskRequest(BaseModel):
    """Request payload for semantic cache lookups."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=DEFAULT_MAX_QUERY_LENGTH,
        description="Natural language query to answer.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("Query must not be blank.")
        return cleaned_value


class AskResponse(BaseModel):
    """Response payload for semantic cache lookups."""

    query: str
    answer: str
    cache_hit: bool
    similarity_score: float | None = Field(
        default=None,
        description="Cosine similarity score for cache hits.",
    )


class HealthResponse(BaseModel):
    """Health check payload."""

    status: Literal["ok"]
    app_name: str
    version: str


class ErrorResponse(BaseModel):
    """Structured error payload returned by the API."""

    detail: str
    code: str
    request_id: str | None = None
