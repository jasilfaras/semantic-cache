from __future__ import annotations

import logging

from backend.errors import CacheBackendError, InvalidRequestError
from backend.schemas import AskResponse, CacheMatch
from backend.services.cache import MongoSemanticCacheRepository
from backend.services.ollama import OllamaClient

logger = logging.getLogger(__name__)


class SemanticCacheService:
    def __init__(
        self,
        ollama_client: OllamaClient,
        cache_repository: MongoSemanticCacheRepository,
        similarity_threshold: float,
        max_query_length: int,
    ) -> None:
        self._ollama_client = ollama_client
        self._cache_repository = cache_repository
        self._similarity_threshold = similarity_threshold
        self._max_query_length = max_query_length

    def ask(self, query: str) -> AskResponse:
        normalized_query = self._normalize_query(query)
        embedding = self._ollama_client.embed(normalized_query)
        match = self._find_cache_match(embedding)

        if match and match.score >= self._similarity_threshold:
            return AskResponse(
                query=normalized_query,
                answer=match.answer,
                cache_hit=True,
                similarity_score=match.score,
            )

        answer = self._ollama_client.generate(normalized_query)
        self._store_generated_answer(query=normalized_query, embedding=embedding, answer=answer)

        return AskResponse(
            query=normalized_query,
            answer=answer,
            cache_hit=False,
            similarity_score=None,
        )

    def _normalize_query(self, query: str) -> str:
        normalized_query = query.strip()
        if not normalized_query:
            raise InvalidRequestError("Query must not be blank.")
        if len(normalized_query) > self._max_query_length:
            raise InvalidRequestError(
                f"Query is too long. Maximum length is {self._max_query_length} characters.",
            )
        return normalized_query

    def _find_cache_match(self, embedding: list[float]) -> CacheMatch | None:
        try:
            return self._cache_repository.find_best_match(embedding)
        except CacheBackendError as exc:
            logger.warning("Semantic cache lookup skipped after cache backend failure: %s", exc.detail)
            return None

    def _store_generated_answer(self, *, query: str, embedding: list[float], answer: str) -> None:
        try:
            self._cache_repository.store(query=query, embedding=embedding, answer=answer)
        except CacheBackendError as exc:
            logger.warning("Generated response was returned without caching: %s", exc.detail)
