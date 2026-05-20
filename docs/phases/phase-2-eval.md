# Phase 2 evaluation: Domain preferences & filter service

**Phase goal:** Deterministic filtering and top-N cap without LLM.

**References:** [implementation-plan.md § Phase 2](../implementation-plan.md#phase-2-domain-preferences--filter-service) · [architecture.md §4.2](../architecture.md)

**Touches success criteria:** Sensible candidate sets for common queries.

---

## Prerequisites

- Phase [1-eval](./phase-1-eval.md) passed
- `RestaurantRepository` populated

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Validation | Must-pass | `UserPreferences` rejects invalid input |
| Filters | Must-pass | Location, cuisine, rating, budget correct |
| Cap | Must-pass | Top-N by rating with stable ordering |
| No-match | Must-pass | Empty result + hints |
| Purity | Should-pass | No side effects; no LLM calls |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 2-M1 | Location filter is case-insensitive | `bangalore` vs `Bangalore` same count | ☐ |
| 2-M2 | Delhi query excludes Bangalore rows | `test_filter_location` | ☐ |
| 2-M3 | Cuisine filter matches substring in cuisines field | Italian query returns Italian-tagged rows | ☐ |
| 2-M4 | `min_rating` enforced: all results `rating >= min_rating` | Unit test | ☐ |
| 2-M5 | Budget `medium` only returns costs in configured range | `test_filter_budget_medium` | ☐ |
| 2-M6 | `cap_by_rating` returns ≤ `MAX_CANDIDATES_FOR_LLM` (default 15) | `test_cap_limits_count` | ☐ |
| 2-M7 | Over-strict filters → empty list + `NoMatchResult` hints | `test_no_match_empty` | ☐ |
| 2-M8 | Missing `location` rejected at validation | U-01 | ☐ |
| 2-M9 | Invalid budget enum rejected | U-06 | ☐ |
| 2-M10 | Sample query returns ≥1 candidate: Bangalore, medium, Italian, 4.0 | Manual script | ☐ |
| 2-M11 | Filter service has no network/LLM dependencies | Code review | ☐ |

**Gate:** All `2-M*` checked → proceed to Phase 3.

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 2-S1 | Unknown city returns empty (U-03) | Atlantis query | ☐ |
| 2-S2 | Budget boundary values documented and tested (F-05) | Edge costs 500/501 | ☐ |
| 2-S3 | Tie-breaking on rating uses secondary key (F-04) | Fixture with ties | ☐ |
| 2-S4 | Input trimming for whitespace (U-05) | `" Bangalore "` | ☐ |

---

## Automated tests

| Test | Assert |
|------|--------|
| `test_filter_location` | City isolation |
| `test_filter_budget_medium` | Cost in range |
| `test_filter_min_rating` | Rating threshold |
| `test_cap_limits_count` | Max N |
| `test_no_match_empty` | Empty + hints |
| `test_invalid_preferences` | Validation errors |

---

## Manual checklist

1. Run debug script with [demo matrix](../implementation-plan.md#suggested-demo-queries) — at least 3 cities return candidates.
2. Broaden then narrow filters; confirm candidate count changes logically.
3. Confirm `extras` field accepted but not used in filtering (until Phase 3).

---

## Milestone check (optional)

**Rating-only recommender:** Print top 10 by rating for a query without LLM—useful demo checkpoint.

---

## Phase-specific edge cases

[edgecase.md §3–4](../edgecase.md): U-01 through U-18, F-01 through F-09.

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
