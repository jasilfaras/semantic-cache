from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from pymongo.collection import Collection
from pymongo.errors import OperationFailure, PyMongoError

from backend.errors import CacheQueryError, InvalidRequestError, PersistenceError
from backend.schemas import CacheMatch


class MongoSemanticCacheRepository:
    def __init__(
        self,
        collection: Collection,
        embedding_model: str,
        generation_model: str,
        vector_index_name: str,
        vector_field_name: str,
        vector_search_limit: int = 1,
        vector_search_candidates: int = 20,
    ) -> None:
        self._collection = collection
        self._embedding_model = embedding_model
        self._generation_model = generation_model
        self._vector_index_name = vector_index_name
        self._vector_field_name = vector_field_name
        self._vector_search_limit = vector_search_limit
        self._vector_search_candidates = vector_search_candidates

    def find_best_match(self, embedding: Sequence[float]) -> CacheMatch | None:
        if not embedding:
            return None

        pipeline = self._build_vector_search_pipeline(list(embedding))

        try:
            document = next(self._collection.aggregate(pipeline), None)
        except OperationFailure as exc:
            raise CacheQueryError(
                "Vector search failed. Ensure MongoDB Search is enabled and the configured index exists.",
            ) from exc
        except PyMongoError as exc:
            raise CacheQueryError("MongoDB query failed while reading from the semantic cache.") from exc

        if not document:
            return None

        answer = document.get("answer")
        if not isinstance(answer, str) or not answer.strip():
            return None

        score = float(document.get("score", 0.0))
        return CacheMatch(answer=answer.strip(), score=score)

    def store(self, query: str, embedding: Sequence[float], answer: str) -> None:
        normalized_query = query.strip()
        normalized_answer = answer.strip()

        if not normalized_query:
            raise InvalidRequestError("Query must not be blank.")
        if not normalized_answer:
            raise InvalidRequestError("Answer must not be blank.")
        if not embedding:
            raise InvalidRequestError("Embedding payload must not be empty.")

        document = {
            "query": normalized_query,
            "embedding": list(embedding),
            "answer": normalized_answer,
            "embedding_model": self._embedding_model,
            "generation_model": self._generation_model,
            "created_at": datetime.now(timezone.utc),
        }

        try:
            self._collection.insert_one(document)
        except PyMongoError as exc:
            raise PersistenceError(
                "MongoDB insert failed while storing the generated response.",
            ) from exc

    def _build_vector_search_pipeline(self, embedding: list[float]) -> list[dict[str, object]]:
        return [
            {
                "$vectorSearch": {
                    "index": self._vector_index_name,
                    "path": self._vector_field_name,
                    "queryVector": embedding,
                    "numCandidates": self._vector_search_candidates,
                    "limit": self._vector_search_limit,
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "answer": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
