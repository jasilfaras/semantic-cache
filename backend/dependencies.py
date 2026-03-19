from __future__ import annotations

from fastapi import Request

from backend.services.semantic_cache import SemanticCacheService


def get_semantic_cache_service(request: Request) -> SemanticCacheService:
    return request.app.state.semantic_cache_service
