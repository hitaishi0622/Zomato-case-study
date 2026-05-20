# Phase 5 evaluation: CLI presentation layer

**Phase goal:** User can run recommendations from the terminal with clear output and errors.

**References:** [implementation-plan.md § Phase 5](../implementation-plan.md#phase-5-cli-presentation-layer) · [architecture.md §3](../architecture.md)

**Touches success criteria:** Display results to user.

---

## Prerequisites

- Phase [4-eval](./phase-4-eval.md) passed
- Dataset cache present
- `LLM_API_KEY` set for full demo (or document mock-only demo)

---

## Evaluation dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| CLI flags | Must-pass | All preference fields exposed |
| Output | Must-pass | Readable ranked results |
| Errors | Must-pass | Validation and no-match UX |
| UX | Should-pass | Help text, refresh data |

---

## Must-pass criteria (gate)

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 5-M1 | `python -m restaurant_rec.main` runs without import errors | Execute module | ☐ |
| 5-M2 | Flags: `--location`, `--budget`, `--cuisine`, `--min-rating`, `--extras` | `--help` lists all | ☐ |
| 5-M3 | Successful run shows ≥3 recommendations when data exists | Demo query below | ☐ |
| 5-M4 | Each line/card shows: name, cuisine, rating, cost, explanation | Visual inspection | ☐ |
| 5-M5 | Invalid input → clear error, non-zero exit (e.g. missing location) | U-01 | ☐ |
| 5-M6 | No-match query → helpful message (not stack trace) | Strict filters | ☐ |
| 5-M7 | No duplicated business logic in CLI (calls orchestrator only) | Code review | ☐ |

**Gate:** All `5-M*` checked → proceed to Phase 6.

**Demo command:**

```bash
python -m restaurant_rec.main \
  --location Bangalore \
  --budget medium \
  --cuisine Italian \
  --min-rating 4.0 \
  --extras "family-friendly, quick service"
```

---

## Should-pass criteria

| ID | Criterion | How to verify | Pass? |
|----|-----------|---------------|-------|
| 5-S1 | `--help` documents all options | CLI-02 | ☐ |
| 5-S2 | `--refresh-data` rebuilds cache | CLI-04 | ☐ |
| 5-S3 | Summary line printed when LLM provides it | Output inspection | ☐ |
| 5-S4 | Non-developer can run demo in &lt; 5 min with README | Fresh user test | ☐ |

---

## Manual checklist

1. Run [demo matrix](../implementation-plan.md#suggested-demo-queries) — 4 queries, record pass/fail.
2. `--min-rating abc` → parser error (U-11).
3. `--budget cheap` → validation error (U-06).
4. Unknown flag → Typer error (CLI-03).

---

## Phase-specific edge cases

[edgecase.md §7](../edgecase.md#7-cli-presentation): CLI-01 through CLI-07.

---

## Sign-off

| Field | Value |
|-------|-------|
| Evaluator | |
| Date | |
| Result | ☐ Pass · ☐ Fail |
| Notes | |
