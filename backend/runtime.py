from __future__ import annotations

from dataclasses import dataclass

import requests
from pymongo import MongoClient

from backend.config import Settings
from backend.services.cache import MongoSemanticCacheRepository
from backend.services.ollama import OllamaClient
from backend.services.semantic_cache import SemanticCacheService


@dataclass(slots=True)
class AppRuntime:
    mongo_client: MongoClient
    http_session: requests.Session
    semantic_cache_service: SemanticCacheService


def build_runtime(settings: Settings) -> AppRuntime:
    mongo_client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=5_000,
    )
    http_session = requests.Session()
    collection = mongo_client[settings.mongodb_database][settings.mongodb_collection]

    semantic_cache_service = SemanticCacheService(
        ollama_client=OllamaClient(
            session=http_session,
            base_url=settings.ollama_base_url,
            embedding_model=settings.embedding_model,
            generation_model=settings.generation_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        ),
        cache_repository=MongoSemanticCacheRepository(
            collection=collection,
            embedding_model=settings.embedding_model,
            generation_model=settings.generation_model,
            vector_index_name=settings.vector_index_name,
            vector_field_name=settings.vector_field_name,
            vector_search_limit=settings.vector_search_limit,
            vector_search_candidates=settings.vector_search_candidates,
        ),
        similarity_threshold=settings.similarity_threshold,
        max_query_length=settings.max_query_length,
    )

    return AppRuntime(
        mongo_client=mongo_client,
        http_session=http_session,
        semantic_cache_service=semantic_cache_service,
    )
