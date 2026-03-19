from __future__ import annotations

import os
from functools import lru_cache
from typing import Callable, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend import __version__

LOCAL_MONGODB_URI = "mongodb://127.0.0.1:27017/?directConnection=true"
DEFAULT_CORS_ORIGINS = ("http://localhost:5173", "http://127.0.0.1:5173")
DEFAULT_MAX_QUERY_LENGTH = 2_000
DEFAULT_EMBEDDING_DIMENSIONS = 768

_T = TypeVar("_T")


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(frozen=True)

    app_name: str = "Semantic Cache API"
    app_version: str = __version__
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    mongodb_uri: str = LOCAL_MONGODB_URI
    mongodb_database: str = "ai_cache"
    mongodb_collection: str = "queries"
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    generation_model: str = "llama3"
    embedding_dimensions: int = Field(default=DEFAULT_EMBEDDING_DIMENSIONS, ge=1)
    vector_index_name: str = "vector_index"
    vector_field_name: str = "embedding"
    similarity_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    vector_search_limit: int = Field(default=1, ge=1)
    vector_search_candidates: int = Field(default=20, ge=1)
    ollama_timeout_seconds: float = Field(default=60.0, gt=0)
    max_query_length: int = Field(default=DEFAULT_MAX_QUERY_LENGTH, ge=1)

    @field_validator("app_name", "mongodb_database", "mongodb_collection")
    @classmethod
    def validate_non_blank_values(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Setting must not be blank.")
        return normalized_value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: tuple[str, ...] | list[str] | str) -> tuple[str, ...]:
        if isinstance(value, str):
            items = tuple(origin.strip().rstrip("/") for origin in value.split(",") if origin.strip())
        else:
            items = tuple(origin.strip().rstrip("/") for origin in value if origin and origin.strip())

        if not items:
            raise ValueError("At least one CORS origin must be configured.")

        return items

    @field_validator("ollama_base_url")
    @classmethod
    def normalize_ollama_base_url(cls, value: str) -> str:
        normalized_value = value.strip().rstrip("/")
        if not normalized_value:
            raise ValueError("OLLAMA_BASE_URL must not be blank.")
        return normalized_value

    @field_validator("embedding_model", "generation_model", "vector_index_name", "vector_field_name")
    @classmethod
    def validate_identifier_values(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("Setting must not be blank.")
        return normalized_value

    @model_validator(mode="after")
    def validate_vector_search_constraints(self) -> Settings:
        if self.vector_search_candidates < self.vector_search_limit:
            raise ValueError("VECTOR_SEARCH_CANDIDATES must be greater than or equal to VECTOR_SEARCH_LIMIT.")
        return self


def _get_env(name: str, default: _T, parser: Callable[[str], _T]) -> _T:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return parser(raw_value)


def _get_csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    return tuple(item.strip() for item in raw_value.split(","))


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Semantic Cache API"),
        app_version=os.getenv("APP_VERSION", __version__),
        cors_origins=_get_csv_env("BACKEND_CORS_ORIGINS", DEFAULT_CORS_ORIGINS),
        mongodb_uri=os.getenv("MONGODB_URI", LOCAL_MONGODB_URI),
        mongodb_database=os.getenv("MONGODB_DATABASE", "ai_cache"),
        mongodb_collection=os.getenv("MONGODB_COLLECTION", "queries"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        embedding_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
        generation_model=os.getenv("OLLAMA_GENERATE_MODEL", "llama3"),
        embedding_dimensions=_get_env("EMBEDDING_DIMENSIONS", DEFAULT_EMBEDDING_DIMENSIONS, int),
        vector_index_name=os.getenv("VECTOR_INDEX_NAME", "vector_index"),
        vector_field_name=os.getenv("VECTOR_FIELD_NAME", "embedding"),
        similarity_threshold=_get_env("SIMILARITY_THRESHOLD", 0.85, float),
        vector_search_limit=_get_env("VECTOR_SEARCH_LIMIT", 1, int),
        vector_search_candidates=_get_env("VECTOR_SEARCH_CANDIDATES", 20, int),
        ollama_timeout_seconds=_get_env("OLLAMA_TIMEOUT_SECONDS", 60.0, float),
        max_query_length=_get_env("MAX_QUERY_LENGTH", DEFAULT_MAX_QUERY_LENGTH, int),
    )
