# Phase 3 evaluation: LLM integration layer

**Phase goal:** Prompt, call LLM, parse JSON, validate ids, merge facts from repository.

**References:** [implementation-plan.md § Phase 3](../implementation-plan.md#phase-3-llm-integration-layer) · [architecture.md §4.3–4.6, §9](../architecture.md)

**Touches success criteria:** Explanations present; no fabricated venues.

---

## Prerequisites

- Phase [2-eval](./phase-2-eval.md) passed
- `LLM_API_KEY` for live test (optional if mock-only gate)
- `MockLLMClient` implemented for CI

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Contract | Must-pass | Prompt includes ids; JSON schema |
| Parser | Must-pass | Valid and fenced JSON handled |
| Validator | Must-pass | Anti-hallucination rules |
| Resilience | Must-pass | Retry and fallback paths |
| Live LLM | Should-pass | One successful real API call |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 3-M1 | `LLMClient` interface defined; Groq implementation works | Mock + optional live call | ☐ |
| 3-M2 | Prompt contains every candidate `id` | `test_prompt_includes_all_candidate_ids` | ☐ |
| 3-M3 | System prompt forbids out-of-list recommendations | Code review prompt template | ☐ |
| 3-M4 | Parser handles valid JSON response | `test_parser_valid_json` | ☐ |
| 3-M5 | Parser strips markdown JSON fences (L-06) | Fixture with fences | ☐ |
| 3-M6 | Validator drops unknown ids (L-13) | `test_validator_rejects_unknown_id` | ☐ |
| 3-M7 | Display fields (name, rating, cost) from dataset row, not LLM | `test_validator_uses_dataset_facts` | ☐ |
| 3-M8 | `MockLLMClient` E2E produces ≥1 `Recommendation` | `test_mock_llm_end_to_end` | ☐ |
| 3-M9 | Validation failure triggers one retry with stricter prompt | Unit test O-04 | ☐ |
| 3-M10 | Double failure → top 3 by rating, no explanations (L-01, O-05) | Mock double fail | ☐ |
| 3-M11 | Logs include `llm_ms` and validation drop count | Log inspection | ☐ |

**Gate:** All `3-M*` checked → proceed to Phase 4.

**Note:** CI gate may use **mock only**; live LLM is should-pass for local sign-off.

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 3-S1 | Live Groq call returns ranked JSON for sample query | Manual with `GROQ_API_KEY` | ☐ |
| 3-S2 | `extras` included in user prompt when provided | Inspect prompt | ☐ |
| 3-S3 | Partial JSON without `summary` still works (L-08) | Mock response | ☐ |
| 3-S4 | Duplicate ranks/ids handled (L-11, L-12) | Mock response | ☐ |
| 3-S5 | Missing API key → clear error, not hang (C-01, L-03) | Unset `LLM_API_KEY` | ☐ |

---

## Automated tests

| Test | Assert |
|------|--------|
| `test_prompt_includes_all_candidate_ids` | All ids in prompt |
| `test_parser_valid_json` | Parse success |
| `test_parser_fenced_json` | Fence stripping |
| `test_validator_rejects_unknown_id` | Foreign id removed |
| `test_validator_uses_dataset_facts` | Facts match repo |
| `test_mock_llm_end_to_end` | Full chain |
| `test_llm_fallback_on_failure` | Rating-only fallback |

---

## Manual checklist

1. Run one live query with `extras`; explanations mention family-friendly (or similar).
2. Intentionally inject bad id in mock—confirm it never appears in output.
3. Compare printed rating/cost to parquet row for top pick.

---

## Phase-specific edge cases

[edgecase.md §5](../edgecase.md#5-llm-integration): L-01 through L-21.

**MVP minimum:** L-01, L-03, L-05, L-06, L-13, L-15, L-16, L-17.

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Live LLM tested? | ☐ Yes · ☐ No (mock only) |
| Notes | |
