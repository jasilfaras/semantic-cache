from __future__ import annotations

import unittest

from backend.errors import CacheQueryError, InvalidRequestError, PersistenceError
from backend.schemas import CacheMatch
from backend.services.semantic_cache import SemanticCacheService


class FakeOllamaClient:
    def __init__(self) -> None:
        self.embed_calls: list[str] = []
        self.generate_calls: list[str] = []

    def embed(self, prompt: str) -> list[float]:
        self.embed_calls.append(prompt)
        return [0.25, 0.75]

    def generate(self, prompt: str) -> str:
        self.generate_calls.append(prompt)
        return "Fresh answer"


class FakeCacheRepository:
    def __init__(
        self,
        *,
        match: CacheMatch | None = None,
        lookup_error: Exception | None = None,
        store_error: Exception | None = None,
    ) -> None:
        self.match = match
        self.lookup_error = lookup_error
        self.store_error = store_error
        self.lookup_calls: list[list[float]] = []
        self.store_calls: list[tuple[str, list[float], str]] = []

    def find_best_match(self, embedding: list[float]) -> CacheMatch | None:
        self.lookup_calls.append(embedding)
        if self.lookup_error is not None:
            raise self.lookup_error
        return self.match

    def store(self, query: str, embedding: list[float], answer: str) -> None:
        self.store_calls.append((query, embedding, answer))
        if self.store_error is not None:
            raise self.store_error


class SemanticCacheServiceTests(unittest.TestCase):
    def build_service(
        self,
        *,
        match: CacheMatch | None = None,
        lookup_error: Exception | None = None,
        store_error: Exception | None = None,
    ) -> tuple[SemanticCacheService, FakeOllamaClient, FakeCacheRepository]:
        ollama_client = FakeOllamaClient()
        cache_repository = FakeCacheRepository(
            match=match,
            lookup_error=lookup_error,
            store_error=store_error,
        )
        service = SemanticCacheService(
            ollama_client=ollama_client,
            cache_repository=cache_repository,
            similarity_threshold=0.85,
            max_query_length=120,
        )
        return service, ollama_client, cache_repository

    def test_returns_cache_hit_when_similarity_threshold_is_met(self) -> None:
        service, ollama_client, cache_repository = self.build_service(
            match=CacheMatch(answer="Cached answer", score=0.97),
        )

        response = service.ask("What is semantic caching?")

        self.assertTrue(response.cache_hit)
        self.assertEqual("Cached answer", response.answer)
        self.assertEqual(0.97, response.similarity_score)
        self.assertEqual(["What is semantic caching?"], ollama_client.embed_calls)
        self.assertEqual([], ollama_client.generate_calls)
        self.assertEqual(1, len(cache_repository.lookup_calls))

    def test_generates_and_stores_response_when_cache_misses(self) -> None:
        service, ollama_client, cache_repository = self.build_service()

        response = service.ask("Explain vector search.")

        self.assertFalse(response.cache_hit)
        self.assertEqual("Fresh answer", response.answer)
        self.assertIsNone(response.similarity_score)
        self.assertEqual(["Explain vector search."], ollama_client.generate_calls)
        self.assertEqual(
            [("Explain vector search.", [0.25, 0.75], "Fresh answer")],
            cache_repository.store_calls,
        )

    def test_falls_back_to_generation_when_cache_lookup_fails(self) -> None:
        service, ollama_client, cache_repository = self.build_service(
            lookup_error=CacheQueryError("Vector search unavailable."),
        )

        response = service.ask("Why do cache hits lower latency?")

        self.assertFalse(response.cache_hit)
        self.assertEqual("Fresh answer", response.answer)
        self.assertEqual(["Why do cache hits lower latency?"], ollama_client.generate_calls)
        self.assertEqual(1, len(cache_repository.lookup_calls))
        self.assertEqual(1, len(cache_repository.store_calls))

    def test_returns_generated_response_even_if_cache_store_fails(self) -> None:
        service, ollama_client, cache_repository = self.build_service(
            store_error=PersistenceError("Insert failed."),
        )

        response = service.ask("Compare exact and semantic caching.")

        self.assertFalse(response.cache_hit)
        self.assertEqual("Fresh answer", response.answer)
        self.assertEqual(["Compare exact and semantic caching."], ollama_client.generate_calls)
        self.assertEqual(1, len(cache_repository.store_calls))

    def test_rejects_blank_queries(self) -> None:
        service, _, _ = self.build_service()

        with self.assertRaises(InvalidRequestError):
            service.ask("   ")


if __name__ == "__main__":
    unittest.main()
