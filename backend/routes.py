from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from backend.config import Settings
from backend.dependencies import get_semantic_cache_service
from backend.schemas import AskRequest, AskResponse, HealthResponse
from backend.services.semantic_cache import SemanticCacheService

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
    )


@router.post("/ask", response_model=AskResponse, tags=["semantic-cache"])
def ask(
    payload: AskRequest,
    semantic_cache_service: SemanticCacheService = Depends(get_semantic_cache_service),
) -> AskResponse:
    return semantic_cache_service.ask(payload.query)
