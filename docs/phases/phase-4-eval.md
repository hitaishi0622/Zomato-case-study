# Phase 4 evaluation: Recommendation orchestrator

**Phase goal:** Single `recommend(preferences)` wiring filter → LLM → validate with correct error paths.

**References:** [implementation-plan.md § Phase 4](../implementation-plan.md#phase-4-recommendation-orchestrator) · [architecture.md §4.1, §7–8, §13](../architecture.md)

---

## Prerequisites

- Phases [2-eval](./phase-2-eval.md) and [3-eval](./phase-3-eval.md) passed
- Composition root in `main.py` loads dependencies

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Workflow | Must-pass | Full pipeline matches architecture sequence |
| Short-circuit | Must-pass | No LLM on empty candidates or invalid input |
| Metadata | Should-pass | Timings and candidate count |
| DI / testability | Must-pass | Mock LLM injectable |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 4-M1 | `recommend()` returns `RecommendationResult` on happy path | Mock LLM test | ☐ |
| 4-M2 | Happy path returns ≥3 recommendations when data allows | `test_orchestrator_happy_path` | ☐ |
| 4-M3 | Empty filter → `NoMatchResult`; LLM `call_count == 0` | `test_orchestrator_no_match_skips_llm` | ☐ |
| 4-M4 | Invalid preferences → error before filter/LLM | `test_orchestrator_invalid_prefs` | ☐ |
| 4-M5 | Pipeline order: validate → filter → cap → prompt → LLM → parse → validate | Code review / integration test | ☐ |
| 4-M6 | Metadata includes `candidate_count` | Assert on result | ☐ |
| 4-M7 | Bootstrap loads repo + clients at startup; fails if dataset missing (F-07) | Start without cache | ☐ |
| 4-M8 | Double LLM failure uses rating fallback (O-05) | Mock test | ☐ |

**Gate:** All `4-M*` checked → proceed to Phase 5.

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 4-S1 | `filter_ms` and `llm_ms` in metadata | Result object | ☐ |
| 4-S2 | Partial validation (&lt;3 recs) returns flag in metadata (O-03) | Mock bad ids | ☐ |
| 4-S3 | End-to-end with live LLM &lt; 5s typical (architecture NFR) | Log `duration_ms` | ☐ |
| 4-S4 | Callable from Python REPL without CLI | REPL smoke test | ☐ |

---

## Automated tests

| Test | Assert |
|------|--------|
| `test_orchestrator_no_match_skips_llm` | No LLM on empty |
| `test_orchestrator_happy_path` | ≥3 recs + explanations |
| `test_orchestrator_invalid_prefs` | Early validation |
| `test_orchestrator_fallback` | Degraded mode |

---

## Manual checklist

1. REPL: `orchestrator.recommend(UserPreferences(...))` for Bangalore / Italian / medium / 4.0.
2. Strict query → `NoMatchResult` with actionable hints.
3. Kill network mid-LLM (optional)—observe retry/fallback behavior.

---

## Phase-specific edge cases

[edgecase.md §6](../edgecase.md#6-orchestrator--application-flow): O-01 through O-07.

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
