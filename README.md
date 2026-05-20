# AI-Powered Restaurant Recommendation System

Prototype that combines a **Zomato-style Hugging Face dataset**, **rule-based filtering**, and an **LLM** to rank restaurants and explain why each option fits your preferences.

## Requirements

- **Python 3.11–3.12** recommended (3.13+ may lack prebuilt wheels for `pyarrow`)
- pip

## Quick start

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install package and dependencies (Phase 0)
pip install -r requirements.txt
pip install -e .

# Optional: Parquet cache support (recommended)
pip install -r requirements-data.txt

# Build local restaurant cache from Hugging Face
python -m restaurant_rec.main --refresh-data

# Preview filtered results (Phase 2, no LLM)
python -m restaurant_rec.main filter -l bangalore -b medium -c italian --min-rating 4.0

# Full recommendations with Groq LLM (Phase 3)
python -m restaurant_rec.main recommend -l bangalore -b medium -c italian --min-rating 4.0 -e "family-friendly"

# Streamlit deployment
python -m streamlit run src/restaurant_rec/presentation/streamlit_app.py

# Verify installation
python -c "import restaurant_rec; print(restaurant_rec.__version__)"
pytest
```

## Configuration

Settings load in this order (later wins):

1. Defaults in code
2. [`config/settings.yaml`](config/settings.yaml)
3. Environment variables and [`.env`](.env) (if present)

Copy the example env file for secrets:

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

### Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (required Phase 3+) | — |
| `LLM_API_KEY` | Alias for Groq key | — |
| `HF_DATASET_ID` | Hugging Face dataset id | `ManikaSaini/zomato-restaurant-recommendation` |
| `DATA_CACHE_PATH` | Cached parquet path | `data/restaurants.parquet` |
| `MAX_CANDIDATES_FOR_LLM` | Max rows sent to LLM | `15` |
| `MAX_RECOMMENDATIONS` | Max results shown | `5` |
| `LLM_PROVIDER` | LLM provider (`groq` default) | `groq` |
| `LLM_MODEL` | Groq model name | `llama-3.3-70b-versatile` |
| `LLM_TEMPERATURE` | Sampling temperature | `0.2` |
| `LLM_TIMEOUT_SEC` | Request timeout (seconds) | `60` |
| `BUDGET_TIERS_PATH` | Budget tier YAML path | `config/budget_tiers.yaml` |

Budget tiers for filtering are defined in [`config/budget_tiers.yaml`](config/budget_tiers.yaml).

## Project layout

```
src/restaurant_rec/     # Application package
config/                 # YAML configuration
data/                   # Cached dataset (gitignored)
docs/                   # Problem statement, architecture, implementation plan
tests/                  # pytest suite
```

## Development status

| Phase | Status |
|-------|--------|
| 0 — Project foundation | Complete |
| 1 — Data pipeline | Complete |
| 2 — Filter service | Complete |
| 3 — LLM integration (Groq) | Complete |
| 4 — Orchestrator | Planned |
| 5 — CLI | Planned |
| 6 — Hardening | Planned |

See [`docs/implementation-plan.md`](docs/implementation-plan.md) for the full roadmap.

## Documentation

- [Problem statement](docs/problemstatement.md)
- [Architecture](docs/architecture.md)
- [Implementation plan](docs/implementation-plan.md)
- [Edge cases](docs/edgecase.md)
- [Phase evaluations](docs/phases/)

## License

Educational / prototype use.
