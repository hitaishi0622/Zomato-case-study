# Phase 7 evaluation: Optional Web UI or REST API

**Phase goal:** Demo-friendly interface without duplicating core logic.

**References:** [implementation-plan.md § Phase 7](../implementation-plan.md#phase-7-optional-web-ui-or-rest-api) · [architecture.md §12](../architecture.md)

**Note:** Complete **either** Streamlit (7A) **or** FastAPI (7B) eval sections below.

---

## Prerequisites

- Phase [6-eval](./phase-6-eval.md) passed (MVP signed off)
- Same `recommend()` orchestrator as CLI

---

## Shared must-pass (both options)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 7-M0 | UI/API calls `orchestrator.recommend()` only—no duplicate filter/LLM logic | Code review | ☐ |
| 7-M1 | Happy path shows same results as CLI for identical preferences | Side-by-side run | ☐ |
| 7-M2 | No-match handled with user-friendly message | Strict query | ☐ |
| 7-M3 | Demo runnable without terminal flags | UI/API only | ☐ |

---

## Option A: Streamlit (7A)

### Must-pass

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 7A-M1 | Form fields: location, budget, cuisine, min rating, extras | UI inspection | ☐ |
| 7A-M2 | Submit triggers recommend; results as cards/table | Manual test | ☐ |
| 7A-M3 | Loading indicator during LLM call (S-03) | Slow mock | ☐ |
| 7A-M4 | Empty required fields blocked (S-01) | Submit empty | ☐ |
| 7A-M5 | Cards show name, cuisine, rating, cost, explanation | Visual | ☐ |

### Should-pass

| ID | Criterion | Pass? |
|----|-----------|-------|
| 7A-S1 | Sidebar: dataset stats | ☐ |
| 7A-S2 | Refresh data control | ☐ |
| 7A-S3 | Double-submit prevented (S-02) | ☐ |

**Run:** `streamlit run src/restaurant_rec/presentation/streamlit_app.py`

---

## Option B: FastAPI (7B)

### Must-pass

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 7B-M1 | `POST /api/v1/recommendations` returns 200 + body schema | curl / Swagger | ☐ |
| 7B-M2 | `GET /api/v1/health` returns 200 when ready | curl | ☐ |
| 7B-M3 | `GET /api/v1/meta/locations` returns city list | curl | ☐ |
| 7B-M4 | Invalid body → 422 (A-02) | Bad JSON | ☐ |
| 7B-M5 | No matches → 404 + suggestions (A-04) | Strict query | ☐ |
| 7B-M6 | OpenAPI docs at `/docs` | Browser | ☐ |

### Should-pass

| ID | Criterion | Pass? |
|----|-----------|-------|
| 7B-S1 | `GET /api/v1/meta/cuisines` | ☐ |
| 7B-S2 | LLM failure → 502 or degraded 200 (documented) (A-05) | ☐ |
| 7B-S3 | `extras` length limit (A-06) | ☐ |

**Sample request:**

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"location":"Delhi","budget":"low","cuisine":"Chinese","min_rating":3.5,"extras":"quick service"}'
```

---

## Phase-specific edge cases

- Streamlit: [edgecase.md §9](../edgecase.md#9-streamlit-ui-phase-7a--optional)
- API: [edgecase.md §8](../edgecase.md#8-rest-api-phase-7b--optional)

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Option completed | ☐ 7A Streamlit · ☐ 7B FastAPI |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
