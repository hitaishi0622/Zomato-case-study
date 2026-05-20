# Architectural & Technology Decisions

This document records major decisions made while designing and implementing the AI-Powered Restaurant Recommendation system, and the reasoning behind each choice. Use this as a single-source summary of trade-offs, alternatives considered, and next steps.

---

## Summary

- Primary goal: fast, deterministic filtering with an optional LLM-based ranking step to provide explainable, human-readable recommendations.
- Layers: Presentation → Application (Orchestrator) → Services → Domain → Infrastructure.
- Primary LLM provider: Groq (default model: `llama-3.3-70b-versatile`).
- UI: Typer CLI for local use and Streamlit for interactive demos.
- Dataset: Hugging Face dataset `ManikaSaini/zomato-restaurant-recommendation` (Bangalore subset used during preprocessing).
- Packaging: Python package with `src/` layout; dependencies managed in `requirements.txt` and `pyproject.toml`.

---

## Decisions

### 1) Project layout

- Decision: Use `src/` layout with a top-level package `restaurant_rec` and `docs/`, `data/`, `config/`, `tests/` folders.
- Reasoning: `src/` layout prevents accidental imports of local modules during tests and mirrors modern Python packaging best practices.
- Alternatives considered: flat layout. Rejected because it can cause import shadowing and packaging ambiguity.

### 2) Language & Runtime

- Decision: Python 3.11+ (project uses features compatible with 3.11/3.12).
- Reasoning: Strong ecosystem for data processing (pandas), ML/LLM integration, and rapid developer productivity.
- Alternatives: Node/TypeScript (not chosen due to richer Python data tooling).

### 3) Data source & preprocessing

- Decision: Use the Hugging Face dataset `ManikaSaini/zomato-restaurant-recommendation` and preprocess to a city-scoped cache (Bangalore subset used for demos).
- Reasoning: Public dataset with realistic attributes (ratings, cuisines, cost, locality). Preprocessing reduces in-app compute and simplifies UI.
- Caching behavior: Save preprocessed data to `data/restaurants.parquet` (parquet preferred for speed) with CSV fallback when `pyarrow` is unavailable.
- Alternatives: Build custom scraper / use Zomato APIs (not used due to rate limits, TOS and extra engineering).

### 4) Cache format

- Decision: Primary cache format `parquet` (`data/restaurants.parquet`), fallback to CSV.
- Reasoning: Parquet is faster for read/write and preserves typing. CSV fallback keeps the project runnable without `pyarrow`.

### 5) Configuration management

- Decision: Use `pydantic-settings` and YAML (`config/settings.yaml`) with `.env` overrides; `get_settings()` centralizes access.
- Reasoning: Strong typing, environment override precedence, simple YAML defaults for non-secrets, and clear `.env.example` for user guidance.

### 6) LLM provider & model

- Decision: Default LLM provider is `groq`. Default model is `llama-3.3-70b-versatile`.
- Reasoning: Groq provides a usable LLaMA 3.3 hosted model; project tested using Groq client and retry logic. `llama-3.3-70b-versatile` balances instruction-following and cost/latency characteristics for ranking.
- Override: `LLM_MODEL` environment variable and `llm_model` in `config/settings.yaml` enable switching models.
- Alternatives: OpenAI, Anthropic, Ollama. These were considered, but Groq was selected for this project's experimentation and availability of a free tier key during development.

### 7) LLM integration pattern

- Decision: Keep deterministic filtering separate from LLM ranking. Only pass a small candidate set (configurable, default 15) to the LLM for ranking.
- Reasoning: Reduces LLM prompts and cost; ensures reproducible basic results and a graceful degraded mode when the LLM fails.
- Degraded mode: On LLM failure or missing API key the system returns top-rated fallback recommendations.

### 8) Prompt & response handling

- Decision: Use `prompt_builder` to assemble structured prompts and `response_parser` to validate and parse LLM outputs.
- Reasoning: Structured prompts and parsing reduce hallucinations and increase reliability. Retry logic (2 attempts) and validation of responses implemented.

### 9) Orchestrator pattern

- Decision: `RecommendationOrchestrator` composes services (repository, filter service, recommendation engine) and returns `RecommendationResult` or `NoMatchResult`.
- Reasoning: Keeps presentation layer thin and centralizes workflow, timing metrics, and error handling.

### 10) Presentation

- Decision: Provide both a CLI (`Typer`) and a Streamlit UI.
- Reasoning: CLI supports automation, tests, and developer workflows. Streamlit provides an easy-to-use demo UI for non-technical stakeholders.

### 11) Streamlit deployment strategy

- Decision: Offer Streamlit Cloud deployment instructions and root `streamlit_app.py` wrapper for compatibility.
- Reasoning: Streamlit Cloud is the quickest path to host a demo. Root wrapper ensures the `src/` layout imports correctly in the hosted environment.
- Secrets: `GROQ_API_KEY` stored via Streamlit Cloud Secrets (not committed).

### 12) Testing

- Decision: Unit tests for data pipeline, filtering, repository, and (optionally) LLM layer. Live LLM tests gated and can be skipped in CI unless secrets are provided.
- Reasoning: Keep core deterministic logic tested. Live LLM tests provide integration validation but require secrets; keep them optional.

### 13) Error handling & observability

- Decision: Explicit error types (e.g. `LLMError`), meaningful user messages in Streamlit, and logging for backend operations.
- Reasoning: Avoids crashing the UI on missing API keys or remote failures; provides guidance to users and developers.

### 14) Security & secrets

- Decision: Do NOT commit `.env` or keys. Provide `.env.example`. For hosted deployment, use Streamlit/Platform secrets or environment variables.
- Reasoning: Prevent secret leakage and follow best practices.

### 15) Dependency management & reproducibility

- Decision: Use `requirements.txt` and `pyproject.toml` to capture runtime requirements and package metadata; recommend `pip install -e .` during local dev.
- Reasoning: Simple reproducible install for collaborators and CI.

### 16) CI/CD (future)

- Decision: No CI configured yet. Recommended next steps: add GitHub Actions for tests, linting, and optionally a deploy step for Streamlit Cloud (triggered via push).

---

## Alternatives considered (short list)

- Full end-to-end LLM-only recommendations (rejected for cost and latency).
- Using a heavier vector DB + semantic search (rejected for scope; candidate for Phase 6).
- Packaging as a Flask/FastAPI microservice (not chosen because Streamlit + CLI met goals and required less infra).

---

## Operational notes & trade-offs

- Dataset cache persistence: Streamlit Cloud ephemeral runtime means pre-caching the dataset (committing the parquet file) gives fastest cold-start, but increases repo size. Trade-off: faster start vs larger repo.
- LLM costs & limits: Keep candidate set small and temperature low by default to reduce calls and variance.
- Windows-specific terminal encoding issues: `safe_text()` strategy implemented in CLI to avoid garbled characters.

---

## Next steps (recommended)

- Add GitHub Actions to run tests and static checks on each PR.
- Consider optional vectorization (FAISS/GROQ vector store) for semantic recommendations in a later phase.
- Add a short CHANGELOG and release tags for versioned deployments.

---

## Document history

- Created: 2026-05-20
- Author: Project maintainer

