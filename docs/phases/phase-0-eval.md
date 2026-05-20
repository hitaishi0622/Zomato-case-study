# Phase 0 evaluation: Project foundation

**Phase goal:** Repo structure, dependencies, configuration, and tooling ready for implementation.

**References:** [implementation-plan.md § Phase 0](../implementation-plan.md#phase-0-project-foundation) · [architecture.md §10–11](../architecture.md)

---

## Prerequisites

- Python 3.11+ installed
- Git repository initialized (optional)

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Structure | Must-pass | Folders and package layout match architecture |
| Config | Must-pass | Settings load from YAML + env |
| Tooling | Must-pass | Install, import, pytest run |
| Security | Must-pass | Secrets excluded from VCS |
| Documentation | Should-pass | README covers setup |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 0-M1 | `pip install -r requirements.txt` succeeds on clean venv | Fresh venv; install | ☐ |
| 0-M2 | Editable install works (`pip install -e .` if using pyproject) | `python -c "import restaurant_rec"` | ☐ |
| 0-M3 | Directory layout exists: `src/restaurant_rec/`, `config/`, `data/`, `tests/`, `docs/` | File tree inspection | ☐ |
| 0-M4 | `Settings` loads defaults from `config/settings.yaml` | Unit test or REPL | ☐ |
| 0-M5 | Environment overrides YAML (e.g. `DATA_CACHE_PATH`) | Set env; assert value | ☐ |
| 0-M6 | `config/budget_tiers.yaml` present with low/medium/high ranges | Open file | ☐ |
| 0-M7 | `.env` in `.gitignore`; `.env.example` documents required vars | Inspect `.gitignore` | ☐ |
| 0-M8 | `pytest` exits 0 (0 tests acceptable) | `pytest` | ☐ |
| 0-M9 | Invalid config rejected (e.g. negative `MAX_CANDIDATES_FOR_LLM`) | Test C-05 from [edgecase.md](../edgecase.md) | ☐ |

**Gate:** All `0-M*` checked → proceed to Phase 1.

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 0-S1 | README lists Python version, install steps, env vars | Read README | ☐ |
| 0-S2 | `data/.gitkeep` exists | File exists | ☐ |
| 0-S3 | Major deps pinned in `requirements.txt` | No bare unpinned critical libs | ☐ |

---

## Automated tests (recommended)

| Test file | Cases |
|-----------|--------|
| `tests/test_settings.py` | Default load, env override, invalid values |

---

## Manual checklist

1. Clone repo on a second machine or fresh folder.
2. Follow README install steps only—no tribal knowledge.
3. Confirm no `.env` file is required for Phase 0-only verification.

---

## Phase-specific edge cases

See [edgecase.md](../edgecase.md): **§2 Configuration** (C-01 through C-08).

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
