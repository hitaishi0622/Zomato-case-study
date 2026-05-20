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

## Advanced Settings: Streamlit Cloud Deployment

### Prerequisites

1. **GitHub repository**: Project must be on GitHub (https://github.com/hitaishi0622/Zomato-case-study.git)
2. **Streamlit account**: Sign up at https://streamlit.io/cloud
3. **Groq API key**: From https://console.groq.com/keys
4. **Python 3.10+** in `requirements.txt` specification

### Step-by-Step Streamlit Cloud Deployment

#### Step 1: Prepare the Repository

Ensure these files are in the repository root:
- `src/restaurant_rec/presentation/streamlit_app.py` ✓ (main app entry point)
- `requirements.txt` ✓ (with streamlit>=1.30.0)
- `.streamlit/config.toml` ✓ (app configuration)
- `pyproject.toml` ✓ (package metadata)
- `.env.example` ✓ (for documentation)

**Note**: Do NOT commit `.env` to GitHub. It will be added via Streamlit Cloud secrets.

#### Step 2: Push Latest Code to GitHub

```bash
git add .
git commit -m "Deploy: Ready for Streamlit Cloud"
git push origin main
```

#### Step 3: Connect to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click **"New app"** button
3. Choose repository: `hitaishi0622/Zomato-case-study`
4. Choose branch: `main`
5. Set main file path: `src/restaurant_rec/presentation/streamlit_app.py`
6. Click **"Deploy"**

Streamlit Cloud will automatically:
- Install dependencies from `requirements.txt`
- Build the app
- Start the Streamlit server

#### Step 4: Configure Secrets in Streamlit Cloud

After deployment starts, add environment secrets:

1. Click the **three dots** (⋯) → **Settings** in the deployed app
2. Go to **Secrets** tab
3. Add these secrets (one per line in TOML format):

```toml
# Required: Groq API Key for LLM
GROQ_API_KEY = "your-groq-api-key-here"

# Optional: Override LLM settings
LLM_PROVIDER = "groq"
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = "0.2"
LLM_TIMEOUT_SEC = "60"
MAX_CANDIDATES_FOR_LLM = "15"
MAX_RECOMMENDATIONS = "5"

# Optional: Dataset override (default: ManikaSaini/zomato-restaurant-recommendation)
# HF_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
```

**Important**: Secrets are accessed in Python as `st.secrets["GROQ_API_KEY"]` and also as environment variables.

#### Step 5: Verify Deployment

The app should:
1. ✅ Load without errors
2. ✅ Display the sidebar with inputs (Location, Budget, Cuisine, Rating, Extras)
3. ✅ Show **"Filter preview"** button (no API needed)
4. ✅ Show **"Generate recommendations"** button (uses Groq API)
5. ✅ Display cache path info and LLM provider

If the dataset cache is missing on first load, it will auto-download from Hugging Face (may take 1-2 minutes).

### Troubleshooting Streamlit Cloud Deployment

#### Issue: "GROQ_API_KEY not found"

**Solution**: Check Streamlit Cloud **Secrets** are saved:
1. Click app **⋯** → **Settings** → **Secrets**
2. Verify `GROQ_API_KEY` is listed
3. Click **"Save"** button (easy to forget)
4. Refresh the app (Ctrl+F5)

#### Issue: "Dataset not found / ModuleNotFoundError"

**Solution**: Verify `requirements.txt` includes required packages:
```
huggingface-hub>=0.19.0
pandas>=2.0.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
```

#### Issue: "PermissionError: data/restaurants.parquet"

**Cause**: Streamlit Cloud is read-only for file persistence. The cache must be rebuilt on each deployment.

**Solution**: This is expected. The app will:
1. Check for cache at `data/restaurants.parquet`
2. If missing, download from Hugging Face (first run: ~1-2 min)
3. Cache in memory for subsequent filter/recommend calls
4. Cache clears when app restarts

#### Issue: Slow app startup

**Cause**: Dataset download on first load can take 1-2 minutes.

**Solutions**:
- Option A: User refreshes cache once, then subsequent calls are fast
- Option B: Pre-cache dataset locally (see below)

#### Issue: "App running but recommendations are empty"

**Solution**: 
1. Check GROQ_API_KEY is correct (try on free Groq tier first)
2. Check internet connectivity
3. Check Streamlit Cloud logs: Click app **⋯** → **Manage app** → **View logs**

### Advanced: Pre-Cache Dataset (Optional)

To avoid the dataset download delay on first load, you can include a pre-cached dataset:

1. **Locally build cache**:
   ```bash
   python -c "from restaurant_rec.infrastructure import RestaurantRepository; from restaurant_rec.config.settings import get_settings; RestaurantRepository.from_settings(get_settings(), refresh=True)"
   ```
   This creates `data/restaurants.parquet`

2. **Commit to GitHub**:
   ```bash
   git add data/restaurants.parquet
   git commit -m "Add pre-cached dataset"
   git push origin main
   ```

3. **Redeploy** in Streamlit Cloud (or it auto-redeploys on push)

Now users see instant load time on first visit.

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ YES | N/A | API key from https://console.groq.com/keys |
| `LLM_PROVIDER` | ❌ No | `groq` | LLM backend (only `groq` supported) |
| `LLM_MODEL` | ❌ No | `llama-3.3-70b-versatile` | Groq model name |
| `LLM_TEMPERATURE` | ❌ No | `0.2` | LLM creativity (0.0-1.0) |
| `LLM_TIMEOUT_SEC` | ❌ No | `60` | API request timeout in seconds |
| `MAX_CANDIDATES_FOR_LLM` | ❌ No | `15` | Max restaurants to pass to LLM |
| `MAX_RECOMMENDATIONS` | ❌ No | `5` | Max recommendations to return |
| `HF_DATASET_ID` | ❌ No | `ManikaSaini/zomato-restaurant-recommendation` | Hugging Face dataset |
| `DATA_CACHE_PATH` | ❌ No | `data/restaurants.parquet` | Cache file location |

### App URL

After deployment, your app will be at:
```
https://<username>-zomato-case-study.streamlit.app
```

Replace `<username>` with your Streamlit Cloud username.

### Performance Metrics

The app displays timing metrics:
- **Filter time**: Milliseconds to filter restaurants
- **LLM time**: Milliseconds for AI ranking (typically 0.5-3 seconds for Groq)
- **Total time**: Entire workflow duration

## Deployment checklist

- [x] Add `streamlit` to project dependencies.
- [x] Create `src/restaurant_rec/presentation/streamlit_app.py`.
- [x] Verify `RecommendationOrchestrator` works from Streamlit.
- [x] Add `.env.example` with placeholder keys.
- [x] Confirm dataset refresh runs on startup when cache is missing.
- [x] Store API keys securely for hosted deployment.
- [x] Test locally with the same commands as Streamlit Cloud.
- [x] Pushed to GitHub: https://github.com/hitaishi0622/Zomato-case-study.git

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
