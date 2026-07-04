# tasks.md — snapshot-freshness-badge

Decomposed from `spec.md` + `design.md`. Each task ≤ 30 min, closes at least one AC.

## Order + parallelism

T-001 → T-002 → T-003 (backend, sequential — DB → helper → endpoint).
T-004, T-005 are `[parallel]` — frontend fetch + UI can run in different worktrees.
T-006 wires the DoD gate.

## Tasks

- [ ] **T-001** — Add `freshest_by_brand()` to `lobby_db.py`.
  - AC: happy-1, happy-2, happy-3, invariant-1
  - Files: `lobby_db.py`
  - DoD: `python -c "from lobby_db import freshest_by_brand, connect; print(freshest_by_brand(connect()))"` returns a `{brand: iso_str}` dict.

- [ ] **T-002** — Add `/api/freshness` handler in `app.py`.
  - AC: happy-1..3, error-2
  - Files: `app.py`
  - DoD: `curl http://127.0.0.1:8765/api/freshness` returns `200 OK` with JSON body.

- [ ] **T-003** — Handle empty-DB / no-snapshots case.
  - AC: error-1, error-2
  - Files: `app.py`, `lobby_db.py`
  - DoD: with an empty `data/lobby.db`, endpoint returns `{}` and does not raise.

- [ ] **T-004** `[parallel]` — Add `formatAge(iso)` helper + `injectBadge(tile, tier, label)` to `static/app.js`.
  - AC: happy-1..3, error-1
  - Files: `static/app.js`
  - DoD: unit-checkable in browser console: `formatAge(new Date().toISOString())` returns `{label: "just now", tier: "fresh"}`.

- [ ] **T-005** `[parallel]` — Add `.freshness`, `.freshness--fresh`, `.freshness--stale`, `.freshness--old`, `.freshness--none` CSS to `static/styles.css`.
  - AC: happy-1..3, error-1
  - Files: `static/styles.css`
  - DoD: static preview page (`static/preview.html` if you want) renders all 4 states.

- [ ] **T-006** — Wire `fetchFreshness()` on dashboard load + call `injectBadge` per tile.
  - AC: happy-1..3, invariant-1
  - Files: `static/app.js`
  - DoD: Dashboard shows a badge on every tile with data; tiles without data show `no data`.

- [ ] **T-007** — Extend `smoke_check.py` to hit `/api/freshness` and assert `dict` response.
  - AC: invariant-2
  - Files: `smoke_check.py`
  - DoD: `python smoke_check.py` still exits 0.

## Overall DoD

- All 3 happy-path AC pass a live check (open dashboard, see 3 tiers).
- Both error-path AC pass (empty DB test + kill DB test).
- `python smoke_check.py` exits 0.
- No new Python or JS dependencies (`requirements.txt` unchanged).
