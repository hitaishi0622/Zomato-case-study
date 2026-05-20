# Phase 6 evaluation: Hardening, testing & MVP sign-off

**Phase goal:** All problem-statement success criteria met; stable demo and CI.

**References:** [implementation-plan.md § Phase 6](../implementation-plan.md#phase-6-hardening-testing--documentation) · [problemstatement.md § Success criteria](../problemstatement.md#success-criteria)

---

## Prerequisites

- Phase [5-eval](./phase-5-eval.md) passed
- Full test suite implemented

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Success criteria | Must-pass | All 5 from problem statement |
| Test coverage | Must-pass | Unit + E2E with mock LLM |
| Error paths | Must-pass | Architecture §13 scenarios |
| Docs | Must-pass | README onboarding |
| Observability | Should-pass | Structured logs |

---

## Must-pass: problem statement success criteria

| ID | Success criterion | Verification method | Pass? |
|----|-------------------|---------------------|-------|
| SC-1 | Dataset loads reliably | Integration test + CLI cold/warm start | ☐ |
| SC-2 | ≥3 relevant suggestions for valid queries | E2E + manual matrix (5 cities × 3 cuisines) | ☐ |
| SC-3 | No fabricated venues | Validator tests + manual spot-check 10 outputs | ☐ |
| SC-4 | Preference-aware explanations | Manual review of queries with `--extras` | ☐ |
| SC-5 | Reasonable demo latency | `duration_ms` &lt; 5s typical for ≤15 candidates | ☐ |

**MVP rule:** All SC-* must pass.

---

## Must-pass: technical gate

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 6-M1 | `pytest` passes with no network (mock LLM default) | CI/local pytest | ☐ |
| 6-M2 | Service layer coverage ≥80% (filter, validator, parser) | `pytest --cov` | ☐ |
| 6-M3 | E2E: orchestrator + `MockLLMClient` ≥3 recommendations | `test_orchestrator_happy_path` | ☐ |
| 6-M4 | All architecture §13 error paths implemented | Matrix below | ☐ |
| 6-M5 | README: install, env vars, examples, troubleshooting | New dev test &lt; 15 min | ☐ |
| 6-M6 | No secrets in repo or logs | Audit | ☐ |

---

## Error path matrix (architecture §13)

| Scenario | Expected behavior | Test / manual | Pass? |
|----------|-------------------|---------------|-------|
| Invalid preferences | No LLM; clear error | U-01 | ☐ |
| Zero candidates | `NoMatchResult` + hints | F-01 | ☐ |
| LLM timeout / 5xx | Retry → fallback | L-01, L-02 | ☐ |
| Malformed JSON | Retry → fallback | L-05 | ☐ |
| Hallucinated id | Stripped; partial OK | L-13 | ☐ |
| Dataset load failure | Fail fast at startup | D-01, F-07 | ☐ |

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 6-S1 | Structured logs: filter count, timings | Log sample | ☐ |
| 6-S2 | `@slow` integration test for HF load (skippable in CI) | pytest -m "not slow" | ☐ |
| 6-S3 | Manual test log documented (date, queries, results) | `docs/` or issue | ☐ |
| 6-S4 | Success criteria checkboxes updated in problemstatement.md | Doc review | ☐ |

---

## Manual test matrix (minimum)

Run via CLI; record candidate count and top-3 names.

| Location | Budget | Cuisine | Min rating | Extras | ≥3 results? | Names match data? |
|----------|--------|---------|------------|--------|-------------|-------------------|
| Bangalore | medium | Italian | 4.0 | family-friendly | | |
| Delhi | low | Chinese | 3.5 | quick service | | |
| Mumbai | high | North Indian | 4.5 | — | | |
| Hyderabad | medium | Biryani | 4.0 | — | | |
| Chennai | medium | South Indian | 4.0 | — | | |

---

## Automated test inventory

| Layer | Required tests |
|-------|----------------|
| Unit | filter, validator, parser, settings |
| Integration | repository, optional HF load |
| E2E | orchestrator + mock LLM |

---

## Phase-specific edge cases

Full catalog: [edgecase.md](../edgecase.md). Phase 6 should confirm all **P0** cases have documented behavior (pass or known limitation).

---

## MVP sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| MVP approved? | ☐ Yes · ☐ No |
| SC-1..SC-5 all pass? | ☐ |
| Notes | |

**After pass:** Optional Phase 7 (UI/API) may begin.
