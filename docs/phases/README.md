# Phase evaluation documents

Each phase has an **eval** document defining how to verify that phase is complete before moving on.

| Phase | Document | Focus |
|-------|----------|-------|
| 0 | [phase-0-eval.md](./phase-0-eval.md) | Project foundation |
| 1 | [phase-1-eval.md](./phase-1-eval.md) | Data pipeline |
| 2 | [phase-2-eval.md](./phase-2-eval.md) | Filter & domain |
| 3 | [phase-3-eval.md](./phase-3-eval.md) | LLM integration |
| 4 | [phase-4-eval.md](./phase-4-eval.md) | Orchestrator |
| 5 | [phase-5-eval.md](./phase-5-eval.md) | CLI |
| 6 | [phase-6-eval.md](./phase-6-eval.md) | Hardening & MVP sign-off |
| 7 | [phase-7-eval.md](./phase-7-eval.md) | Optional UI/API |

**Related:** [edgecase.md](../edgecase.md) · [implementation-plan.md](../implementation-plan.md) · [architecture.md](../architecture.md)

**Gate rule:** All **must-pass** criteria in `phase-N-eval.md` are green before starting phase N+1.
