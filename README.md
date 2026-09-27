# Adaptive RAG Agent

Adaptive Retrieval-Augmented Generation agent with ingestion, hybrid retrieval, verification, evaluation, and FastAPI layers.

## Status

Project scaffold created. Implementation modules are intentionally small placeholders and can be filled incrementally.

## Layout

- `src/`: application packages
- `tests/`: unit, integration, and end-to-end tests
- `evaluation/`: datasets, benchmarks, and reports
- `docs/`: architecture and development documentation
- `infra/`: deployment configuration

## Development

Install development dependencies with your preferred Python package manager, then run:

```bash
pytest
ruff check .
```

## Streamlit UI

With the FastAPI backend already running (default `http://localhost:8000`):

```bash
streamlit run app.py
```

Optional: set `API_BASE_URL` if the API is not on localhost port 8000.

```bash
uvicorn src.api.main:app --reload
streamlit run app.py
```
