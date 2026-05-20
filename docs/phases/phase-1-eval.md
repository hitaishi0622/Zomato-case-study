# Phase 1 evaluation: Data pipeline

**Phase goal:** Load Hugging Face dataset, preprocess, cache Parquet, expose `RestaurantRepository`.

**References:** [implementation-plan.md § Phase 1](../implementation-plan.md#phase-1-data-pipeline) · [architecture.md §4.7, §6](../architecture.md)

**Touches success criterion:** Dataset loads reliably.

---

## Prerequisites

- Phase [0-eval](./phase-0-eval.md) passed
- Network access for first-time HF download

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Ingest | Must-pass | HF load and schema mapping |
| Preprocess | Must-pass | Clean types, ids, normalization |
| Cache | Must-pass | Parquet write and reload |
| Repository | Must-pass | Query API returns domain models |
| Resilience | Should-pass | Graceful failures per edge cases |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 1-M1 | First run downloads dataset and creates `data/restaurants.parquet` | Delete cache; run loader | ☐ |
| 1-M2 | Second run loads cache in &lt; 2 seconds (warm start) | Time second load | ☐ |
| 1-M3 | Row count &gt; 0 after preprocess | Log or assert count | ☐ |
| 1-M4 | Every row has unique `restaurant_id` | `test_preprocessor_assigns_ids` | ☐ |
| 1-M5 | Required fields present: name, city, cuisines, rating, cost_for_two | Schema test | ☐ |
| 1-M6 | `RestaurantRepository.get_all()` returns list of `Restaurant` models | Integration test | ☐ |
| 1-M7 | `get_by_ids([...])` returns matching rows only | Unit test | ☐ |
| 1-M8 | `--refresh-data` (or equivalent) rebuilds cache | Run refresh; compare mtime | ☐ |
| 1-M9 | Null ratings handled (dropped or imputed—document which) | Fixture test D-08 | ☐ |
| 1-M10 | City and cuisine strings normalized (lowercase, trimmed) | Sample row inspection | ☐ |

**Gate:** All `1-M*` checked → proceed to Phase 2.

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 1-S1 | Startup logs: row count, distinct cities | Run loader | ☐ |
| 1-S2 | Budget tiers derived or documented in `budget_tiers.yaml` | Config matches data | ☐ |
| 1-S3 | Column mapping documented in code for schema drift | Code comment / docstring | ☐ |
| 1-S4 | Corrupt cache triggers re-ingest or clear error (D-04) | Truncate parquet | ☐ |

---

## Automated tests

| Test | Assert |
|------|--------|
| `test_preprocessor_assigns_ids` | Unique ids |
| `test_repository_loads_cache` | count &gt; 0, columns present |
| `test_no_null_ratings_after_clean` | Policy enforced |
| `test_get_by_ids_unknown` | Empty or omit unknown ids (F-08) |

Mark HF integration test `@slow` if it hits network.

---

## Manual checklist

1. Inspect 5 random `Restaurant` objects in REPL—fields look reasonable.
2. Confirm `Bangalore` (or similar) exists in distinct cities.
3. Verify parquet is gitignored and not committed.

---

## Phase-specific edge cases

[edgecase.md §1](../edgecase.md#1-data-ingestion--preprocessing): D-01 through D-17.

**Minimum MVP handling:** D-01, D-02, D-03, D-05, D-07, D-08, D-10, D-11.

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
