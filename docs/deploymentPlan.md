# Streamlit Deployment Plan

This deployment plan is for hosting the AI-Powered Restaurant Recommendation System as a Streamlit app. It covers local deployment, Streamlit Cloud, and optional Docker packaging.

## Goals

- Provide a simple browser-based frontend for the existing backend.
- Enable manual testing and demo runs with minimal setup.
- Preserve the current dataset cache, config, and LLM integration flow.

## Assumptions

- The project root is `c:/Users/suman/OneDrive/Desktop/Ai`.
- The backend is already implemented in `src/restaurant_rec/`.
- The project uses `requirements.txt` and `.env` for configuration.
- The dataset cache is built via `python -m restaurant_rec.main --refresh-data`.
- The LLM provider is Groq, configured with `GROQ_API_KEY` or `LLM_API_KEY`.

## Required Streamlit components

1. Add a Streamlit UI module at `src/restaurant_rec/presentation/streamlit_app.py`.
2. Add `streamlit` to `requirements.txt` or create a dedicated `requirements-ui.txt`.
3. Use the existing orchestrator and services from `restaurant_rec.application.orchestrator`.
4. Support the same `.env` variables and cached dataset path.

## Deployment targets

### Option A: Streamlit Cloud

Best for a simple hosted demo.

Requirements:
- GitHub repository with the project.
- `requirements.txt` containing `streamlit`.
- A `Procfile` or `streamlit` app entry specified in Streamlit settings.
- `.streamlit/config.toml` for any app-specific configuration (optional).

Steps:
1. Commit the code and push to GitHub.
2. Create a Streamlit app in the repository pointing to `src/restaurant_rec/presentation/streamlit_app.py`.
3. Add env secrets in Streamlit Cloud for `GROQ_API_KEY` / `LLM_API_KEY`.
4. Add `HF_DATASET_ID` only if overriding the default.
5. Deploy the app.

Streamlit Cloud notes:
- The app should use cached data if available and refresh only on demand.
- A local dataset cache may not persist across rebuilds, so `--refresh-data` should be supported on startup if the cache is missing.

### Option B: Local machine / developer testing

Steps:
1. Create and activate a venv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
3. Install Streamlit:
   ```bash
   pip install streamlit
   ```
4. Create `.env` with keys:
   ```text
   GROQ_API_KEY=...
   LLM_API_KEY=...
   ```
5. Build the dataset cache:
   ```bash
   python -m restaurant_rec.main --refresh-data
   ```
6. Run Streamlit:
   ```bash
   streamlit run src/restaurant_rec/presentation/streamlit_app.py
   ```

### Option C: Docker deployment (optional)

Use Docker for a reproducible runtime.

Possible Dockerfile:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit
COPY . .
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
EXPOSE 8501
CMD ["streamlit", "run", "src/restaurant_rec/presentation/streamlit_app.py"]
```

For production, mount a volume for the cache and provide secrets via runtime environment variables.

## Runtime configuration

The Streamlit app should read config from:
- `config/settings.yaml`
- `.env` in the repository root
- environment variables

Required env vars:
- `GROQ_API_KEY` or `LLM_API_KEY`
- `DATA_CACHE_PATH` (optional if using default `data/restaurants.parquet`)
- `HF_DATASET_ID` (optional override)

Recommended env vars:
- `MAX_CANDIDATES_FOR_LLM=15`
- `MAX_RECOMMENDATIONS=5`
- `LLM_TEMPERATURE=0.2`
- `LLM_TIMEOUT_SEC=60`

## App behavior

The Streamlit UI should:
- Allow the user to enter:
  - `location`
  - `budget`
  - `cuisine`
  - `min_rating`
  - `extras`
- Display a filter-only preview option and a full recommend option.
- Display results as cards:
  - Restaurant name
  - City
  - Rating
  - Cost for two
  - Explanation
- Show status when the app is building or refreshing the dataset cache.
- Show clear errors when API key or dataset cache is missing.

## Deployment architecture

1. Browser frontend: Streamlit UI.
2. Application backend: `RecommendationOrchestrator`.
3. Filter service: `FilterService`.
4. LLM ranking: `RecommendationEngine`.
5. Dataset cache: `data/restaurants.parquet` or CSV fallback.
6. Config: `config/settings.yaml` + `.env`.

## Deployment checklist

- [ ] Add `streamlit` to project dependencies.
- [ ] Create `src/restaurant_rec/presentation/streamlit_app.py`.
- [ ] Verify `RecommendationOrchestrator` works from Streamlit.
- [ ] Add `.env.example` with placeholder keys.
- [ ] Confirm dataset refresh runs on startup when cache is missing.
- [ ] Store API keys securely for hosted deployment.
- [ ] Test locally with the same commands as Streamlit Cloud.

## Verification steps

1. Install dependencies and Streamlit.
2. Run dataset refresh.
3. Start the Streamlit app.
4. Enter sample query values.
5. Confirm results appear with explanations.
6. Confirm the app shows a helpful error if the API key is missing.

## Notes for Streamlit Cloud

- Use the existing `requirements.txt` with `streamlit` added.
- Use Streamlit secrets for `GROQ_API_KEY` / `LLM_API_KEY`.
- Set the app entry path to the Streamlit app file.
- Keep the app lightweight by caching dataset loads.

## Future improvements

- Add a `Streamlit` sidebar for quick example queries.
- Add a cache refresh button in the app.
- Add a status banner for dataset and LLM availability.
- Add a `Dockerfile` and `docker-compose.yml` for containerized deployment.
