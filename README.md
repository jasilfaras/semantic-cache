# Semantic Cache for Local LLMs

Semantic Cache is a full-stack reference app for reusing LLM responses across semantically similar prompts. It pairs a FastAPI backend with a Vite/React terminal UI, uses Ollama for embeddings and generation, and stores reusable answers in MongoDB with vector search.

The codebase is organized as a small but deliberate system rather than a prototype dump:

- the backend keeps routing, runtime wiring, service orchestration, and persistence concerns separate
- the cache layer fails open, so MongoDB lookup or write issues do not prevent a fresh Ollama response from being returned
- the frontend is split into focused presentation, message, and API modules instead of a single component doing everything

## Features

- Semantic cache lookups backed by MongoDB `$vectorSearch`
- Local embedding and generation through Ollama
- Graceful degradation when cache infrastructure is unavailable
- Structured API errors with stable error codes and `X-Request-ID`
- Environment-driven configuration for backend and frontend
- A MongoDB setup CLI for collection and vector index provisioning

## Architecture

### Backend

- [`backend/main.py`](/Users/artemis/Desktop/src/dbms/backend/main.py) creates the FastAPI app, registers middleware, and wires the application lifespan.
- [`backend/routes.py`](/Users/artemis/Desktop/src/dbms/backend/routes.py) exposes the HTTP surface area.
- [`backend/runtime.py`](/Users/artemis/Desktop/src/dbms/backend/runtime.py) builds the runtime dependencies shared across requests.
- [`backend/services/semantic_cache.py`](/Users/artemis/Desktop/src/dbms/backend/services/semantic_cache.py) coordinates embedding, cache lookup, fallback generation, and cache persistence.
- [`backend/services/cache.py`](/Users/artemis/Desktop/src/dbms/backend/services/cache.py) encapsulates MongoDB vector search and document writes.
- [`backend/services/ollama.py`](/Users/artemis/Desktop/src/dbms/backend/services/ollama.py) provides a thin, defensive client for Ollama.
- [`backend/config.py`](/Users/artemis/Desktop/src/dbms/backend/config.py) centralizes validated runtime settings.
- [`backend/setup_db.py`](/Users/artemis/Desktop/src/dbms/backend/setup_db.py) provisions the collection and vector search index.

### Frontend

- [`frontend/src/App.jsx`](/Users/artemis/Desktop/src/dbms/frontend/src/App.jsx) owns high-level session state and request flow.
- [`frontend/src/components/SessionHeader.jsx`](/Users/artemis/Desktop/src/dbms/frontend/src/components/SessionHeader.jsx) renders session metrics and terminal status.
- [`frontend/src/components/MessageRow.jsx`](/Users/artemis/Desktop/src/dbms/frontend/src/components/MessageRow.jsx) renders terminal log entries.
- [`frontend/src/components/PromptComposer.jsx`](/Users/artemis/Desktop/src/dbms/frontend/src/components/PromptComposer.jsx) handles prompt composition and shortcuts.
- [`frontend/src/lib/semanticCacheApi.js`](/Users/artemis/Desktop/src/dbms/frontend/src/lib/semanticCacheApi.js) isolates HTTP concerns and response normalization.
- [`frontend/src/lib/messages.js`](/Users/artemis/Desktop/src/dbms/frontend/src/lib/messages.js) contains message factories and terminal state helpers.

## Request Flow

```text
React terminal UI
  -> POST /ask
  -> FastAPI route
  -> Ollama embeddings API
  -> MongoDB vector search
     -> cache hit: return cached answer
     -> cache miss or cache failure: call Ollama generation
           -> best-effort cache write
           -> return generated answer
```

## Requirements

- Python 3.11+
- Node.js 20+
- Ollama running locally
- A MongoDB deployment with Search / `$vectorSearch` support

Recommended Ollama models:

```bash
ollama pull nomic-embed-text
ollama pull llama3
```

## Getting Started

1. Create the Python environment and install backend dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Install frontend dependencies.

```bash
cd frontend
npm install
cd ..
```

3. Copy the sample environment file and adjust values if needed.

```bash
cp .env.example .env
```

4. Provision the MongoDB collection and vector index.

```bash
./venv/bin/python -m backend.setup_db
```

5. Start the backend.

```bash
source venv/bin/activate
uvicorn backend.main:app --reload --env-file .env
```

6. Start the frontend in a second terminal.

```bash
cd frontend
npm run dev
```

## Configuration

The application reads configuration from environment variables. The most relevant settings are:

- `MONGODB_URI`, `MONGODB_DATABASE`, `MONGODB_COLLECTION`
- `OLLAMA_BASE_URL`, `OLLAMA_EMBED_MODEL`, `OLLAMA_GENERATE_MODEL`
- `VECTOR_INDEX_NAME`, `VECTOR_FIELD_NAME`, `EMBEDDING_DIMENSIONS`
- `SIMILARITY_THRESHOLD`, `VECTOR_SEARCH_LIMIT`, `VECTOR_SEARCH_CANDIDATES`
- `BACKEND_CORS_ORIGINS`
- `VITE_API_BASE_URL`, `VITE_MAX_QUERY_LENGTH`

## API

### `GET /health`

Returns service metadata:

```json
{
  "status": "ok",
  "app_name": "Semantic Cache API",
  "version": "0.1.0"
}
```

### `POST /ask`

Request:

```json
{
  "query": "Why does semantic caching reduce latency?"
}
```

Response:

```json
{
  "query": "Why does semantic caching reduce latency?",
  "answer": "Because semantically similar prompts can reuse an earlier answer...",
  "cache_hit": true,
  "similarity_score": 0.94
}
```

Error responses include a stable `code` and request identifier:

```json
{
  "detail": "Unable to reach the local Ollama service.",
  "code": "ollama_unavailable",
  "request_id": "..."
}
```

## Testing

Backend tests use the standard library test runner:

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Frontend quality checks:

```bash
cd frontend
npm run lint
npm run build
```
