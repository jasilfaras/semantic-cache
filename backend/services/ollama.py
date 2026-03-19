from __future__ import annotations

from typing import Any

from requests import Response, Session
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from backend.errors import DependencyUnavailableError, InvalidRequestError, UpstreamServiceError

EMBEDDINGS_PATH = "/api/embeddings"
GENERATE_PATH = "/api/generate"


class OllamaClient:
    def __init__(
        self,
        session: Session,
        base_url: str,
        embedding_model: str,
        generation_model: str,
        timeout_seconds: float,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._embedding_model = embedding_model
        self._generation_model = generation_model
        self._timeout_seconds = timeout_seconds

    def embed(self, prompt: str) -> list[float]:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise InvalidRequestError("Query must not be blank.")

        payload = {"model": self._embedding_model, "prompt": normalized_prompt}
        data = self._post_json(EMBEDDINGS_PATH, payload, operation="embedding request")
        embedding = data.get("embedding")

        if not isinstance(embedding, list) or not embedding:
            raise UpstreamServiceError("Ollama did not return a usable embedding.", code="ollama_invalid_embedding")

        try:
            return [float(value) for value in embedding]
        except (TypeError, ValueError) as exc:
            raise UpstreamServiceError(
                "Ollama returned an invalid embedding payload.",
                code="ollama_invalid_embedding",
            ) from exc

    def generate(self, prompt: str) -> str:
        normalized_prompt = prompt.strip()
        if not normalized_prompt:
            raise InvalidRequestError("Query must not be blank.")

        payload = {
            "model": self._generation_model,
            "prompt": normalized_prompt,
            "stream": False,
        }
        data = self._post_json(GENERATE_PATH, payload, operation="generation request")
        response_text = data.get("response")

        if not isinstance(response_text, str) or not response_text.strip():
            raise UpstreamServiceError("Ollama did not return a usable response.", code="ollama_invalid_response")

        return response_text.strip()

    def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        operation: str,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        response: Response | None = None

        try:
            response = self._session.post(url, json=payload, timeout=self._timeout_seconds)
            response.raise_for_status()
            data = response.json()
        except Timeout as exc:
            raise UpstreamServiceError(
                f"Ollama timed out during {operation}.",
                status_code=504,
                code="ollama_timeout",
            ) from exc
        except ConnectionError as exc:
            raise DependencyUnavailableError(
                "Unable to reach the local Ollama service.",
                code="ollama_unavailable",
            ) from exc
        except HTTPError as exc:
            raise UpstreamServiceError(
                self._build_http_error_detail(response=response, operation=operation),
                code="ollama_http_error",
            ) from exc
        except RequestException as exc:
            raise UpstreamServiceError(
                f"Request to Ollama failed during {operation}.",
                code="ollama_request_failed",
            ) from exc
        except ValueError as exc:
            raise UpstreamServiceError("Ollama returned invalid JSON.", code="ollama_invalid_json") from exc

        if not isinstance(data, dict):
            raise UpstreamServiceError("Ollama returned an unexpected payload.", code="ollama_invalid_payload")

        return data

    @staticmethod
    def _build_http_error_detail(*, response: Response | None, operation: str) -> str:
        if response is None:
            return f"Ollama returned an error during {operation}."

        detail: str | None = None

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if isinstance(payload, dict):
            for key in ("error", "detail", "message"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    detail = value.strip()
                    break

        if detail:
            return f"Ollama returned an error during {operation}: {detail}"

        return f"Ollama returned HTTP {response.status_code} during {operation}."
