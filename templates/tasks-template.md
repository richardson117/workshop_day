---
status: Open
owner: <name>
created_at: <YYYY-MM-DD>
spec_ref: docs/features/<slug>/spec.md
design_ref: docs/features/<slug>/design.md
---

# Tasks: <feature-slug>

## Overview

- Total tasks: <N>
- Parallel-safe: <M>
- Estimated wall time: <~K> min

## Tasks

- [ ] **T-001** — <imperative title>
  - **AC:** §5 happy-1
  - **Files:** `tools/scraper.py`, `tests/test_scraper.py`
  - **DoD:** `pytest tests/test_scraper.py::test_X` passes

- [ ] **T-002** — [parallel] <imperative title>
  - **AC:** §5 happy-2
  - **Files:** `config/geos.yaml`, `tests/test_geo_config.py`
  - **DoD:** `python scripts/list_geos.py` outputs new geo

- [ ] **T-003** — [parallel] <imperative title>
  - **AC:** §5 error-1
  - **Files:** `tools/error_handler.py`, `tests/test_errors.py`
  - **DoD:** error case raises clear exception with reason

- [ ] **T-004** — <imperative title> (depends on T-001)
  - **AC:** §5 invariant-1
  - **Files:** `tools/scraper.py` (modify result of T-001)
  - **DoD:** invariant test in `tests/test_invariants.py` passes

## Status legend

- `[ ]` — not started
- `[x]` — complete (verified green by /implement)
- `[!]` — escalated (sdd-implementer hit a blocker)

## Parallel notes

Tasks marked `[parallel]` can run in concurrent subagents IF they don't share files.
Above example: T-002 and T-003 don't share files -> parallel-safe. T-004 depends on T-001
-> must wait.
