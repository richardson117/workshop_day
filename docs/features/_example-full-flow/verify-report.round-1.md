# Verify Report for snapshot-freshness-badge

Date: 2026-10-23
Reviewer: sdd-reviewer (adversarial)
Branch: `feature/snapshot-freshness-badge`, base `master`
Commit range: `69ad340..e1835fa` (6 commits, T-001..T-006)
Files touched: `app.py`, `lobby_db.py`, `smoke_check.py`, `static/app.js`, `static/index.html`, `static/styles.css`, `test_freshness.py` (new), plus the three feature docs
Overall: **CHANGES_REQUESTED**

## Commands run

| Command | Result |
|---|---|
| `python smoke_check.py` (AGENTS.md gate, Python 3.13.2) | exit 0. Prints `ok: 11 runs, 3 brands, 2267 game placements` and `running test_freshness.py`. Ran 24 tests, OK |
| `python -m unittest test_freshness -v` | Ran 24 tests in 1.149s, OK |
| T-006 DoD check: copied the repo to the scratchpad, changed one assertion in `test_freshness.py` to fail, then ran `python smoke_check.py` in the copy | exit 1, `FAILED (failures=1)`. The gate does go red on a failing test |
| `node --check static/app.js` | syntax OK |
| `ast.parse` on all 6 root `.py` files | OK, no import or shape breakage |
| Probe script: `app.freshness()` on a copy of `data/lobby_monitor.sqlite3`, plus edge-case inputs | see findings 3–6 |
| Probe script: ran `static/app.js` in Node `vm` with a stub DOM and stubbed `fetch` | see findings 1 and 2 |

All probe scripts and DB copies are in the reviewer's temporary folder. No source files or git state were changed.

There are no other test files in the repo. The full suite is `smoke_check.py` plus `test_freshness.py`.

## Per-AC verdicts

| AC | Code | Test | Verdict | Reasoning |
|---|---|---|---|---|
| happy-1 (2h, fresh, green) | `app.py:110-127` `freshness_badge`; `app.js:125-136` `freshnessTile`; `styles.css` `.freshness-badge.freshness--fresh` | `test_freshness.py:149` (unit), `:314` (via `freshness()`), `:366` (real HTTP route); UI only `:427-434` | **WEAK** | The server side is tested properly, including the real `Handler` over HTTP. The "visible on the tile, in green" part is checked only by text greps over `app.js`. `assertIn("freshness--", js)` and `assertIn(".tier", js)` would still pass if those strings were somewhere other than the badge code. No test proves the label reaches the tile with the right class. My stub-DOM probe shows the code does render correctly (`freshness-badge freshness--fresh`, text `2h ago`), but the repo's tests don't prove it. T-005's "manual browser check" has no recorded evidence. |
| happy-2 (12h, stale) | same | `:155`, `:342`; UI grep only | **WEAK** | Same as happy-1. Boundaries are well covered (5h59m fresh, 6h stale, 23h59m stale, 24h old/`1d ago`). |
| happy-3 (3d, old) | same | `:159`, `:315`, `:367`; UI grep only | **WEAK** | Same as happy-1. |
| happy-4 (several GEOs, newest ok wins) | `lobby_db.py:311-322` `MAX(r.run_at) … GROUP BY b.id` | `:69-79` (3 GEOs, newest inserted in the middle) | **PASS** (with nit 3) | Correct for the formats the scanner and seed data actually write (`+00:00`). Ties on `run_at` across GEOs are harmless with `MAX`. The edge case with mixed offsets is wrong (finding 3), but design D2 accepts that risk explicitly. |
| error-1 (`no data`, other tiles normal) | `lobby_db.py:316-317` LEFT JOINs; `app.py:111-114`; `app.js:138-148` | `:93-109` (only-failed brand and never-scanned brand); `:163`; `:294-324`; `:326-342` (one broken `run_at` leaves the other brands alone) | **WEAK** | The server is solid: a brand with zero rows and a brand with only error/partial rows both come back as `None` → `no data`/`none`. Two gaps: (a) the tile is checked by grep only, as in happy-1; (b) in the UI the whole freshness panel never renders if `/api/meta` or `/api/overview` fails (finding 1). In that case every tile is missing, not just one. |
| invariant-1 (newer failed scan doesn't refresh) | `lobby_db.py:316` `AND br.status = ?` with `("ok",)` | `:81-91` (newer `error` in the same GEO and newer `partial` in another GEO) | **PASS** | The test would catch a mutation to `status != 'error'` because of the `partial` row. `unknown` (written by `ingest_snapshot` when status is missing, `lobby_db.py:246`) is also excluded, which matches D1. |
| invariant-2 (another brand's scan doesn't change this one) | `GROUP BY b.id` | `:111-125` (before/after comparison), `:326-342` | **PASS** | Removing the per-brand grouping would make the test fail. |
| invariant-3 (`python smoke_check.py` passes) | `smoke_check.py:1,14-15` `unittest.main(module="test_freshness", argv=["smoke_check"], verbosity=1)` | the gate itself | **PASS** | exit 0 on the branch. exit 1 when a test is deliberately broken (checked in a scratch copy). The original canary print still runs first. |

## Findings

### 1. [important] The freshness panel only loads if two unrelated endpoints succeed
**Location:** `static/app.js:178-181`
```js
async function boot() {
  await refreshMeta();
  await loadOverview();
  await loadFreshness();
```
**Evidence:** `getJson` (`app.js:4-7`) has no error handling, and neither does `refreshMeta` or `loadOverview`. If `/api/meta` or `/api/overview` rejects (network error, a 500 that drops the connection, bad JSON), `boot()` stops before `loadFreshness()` runs. I confirmed this with the stub-DOM probe: in the "overview fails" and "meta fails" cases, `#freshnessGrid` is never touched. It doesn't even show the "Freshness unavailable." fallback. The panel that exists to warn about bad data disappears exactly when other parts of the dashboard break.
**Suggested fix:** start the freshness load independently, e.g. call `loadFreshness();` (not awaited) as the first line of `boot()`, or use `Promise.allSettled([refreshMeta().then(loadOverview), loadFreshness()])`. `loadFreshness` already catches its own errors.

### 2. [important] The UI half of happy-1/2/3 and error-1 is checked by text greps only
**Location:** `test_freshness.py:420-442`
**Evidence:**
- `test_boot_loads_freshness` checks `assertIn("freshness", boot_body.lower())`. A comment like `// TODO freshness` inside `boot()` would pass.
- `test_app_js_sets_tier_class_and_title_on_badge` checks that `"freshness--"` and `".tier"` appear somewhere in the 190-line file. It doesn't tie them to the badge element.
- Nothing checks that the brand name and label are set with `textContent` rather than `innerHTML`. The rest of `app.js` (`:21`, `:70-74`, `:84-90`) uses `innerHTML` with server strings, so this is a likely regression. The current code is safe: my probe shows a brand named `<img src=x onerror=alert(1)>` rendered as plain text.
- T-005's DoD asks for a manual browser check, but there's no record of it.

**Suggested fix:** keep it stdlib and use the existing `function_body` helper on `function freshnessTile(row)`. Assert that the body contains `` `freshness-badge freshness--${row.tier}` ``, `badge.textContent = row.label`, `name.textContent = row.brand`, and no `innerHTML`. Also record the manual browser check (screenshot or a note) in tasks.md T-005.

### 3. [nit] Comparing `run_at` as a string picks the wrong scan when offsets differ, and one garbage row hides valid data
**Location:** `lobby_db.py:314` `MAX(r.run_at) AS last_ok_at`
**Evidence (probe, NOW = 2026-10-23T18:00Z):**
- A brand with an ok scan at `2026-10-23T16:00:00+00:00` (2h ago) and another at `2026-10-23T17:00:00+10:00` (= 07:00Z, 11h ago) gets `11h ago / stale` instead of `2h ago / fresh`.
- A brand with a valid ok scan at `2026-10-23T16:30:00+00:00` and an ok row with `run_at = "garbage-row"` gets `no data`, because `'g' > '2'`. D9 only promises that a bad row won't affect other brands. Here it hides the same brand's valid data.

D2 accepts this risk because both current writers produce UTC. But `ingest_snapshot` (`lobby_db.py:220`) stores whatever `run_at` the snapshot JSON contains, and workshop students will hand-edit snapshots.
**Suggested fix:** either document the assumption in D2, or pick the newest row by parsed time. Example: `ORDER BY julianday(r.run_at) DESC`; SQLite's date functions accept `Z` and `±HH:MM` and normalise to UTC, and unparseable values give NULL. Another option: return all ok `run_at` values per brand and take the max in Python after parsing.

### 4. [nit] Timestamps without an offset show as `no data`
**Location:** `app.py:111-114`
**Evidence:** `freshness_badge("2026-10-23T16:00:00", NOW)` returns `{'label': 'no data', 'tier': 'none'}`. `fromisoformat` parses it fine; the error is the `TypeError` from subtracting a naive datetime from an aware one, and `except (ValueError, TypeError)` swallows it. D9 says only *unparseable* strings become `no data`. This one parses.
**Suggested fix:** treat naive values as UTC (`if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)`), or state in D9 that naive means no data, and add a test either way.

### 5. [nit] Tile order is undefined
**Location:** `lobby_db.py:315-319`. There is a `GROUP BY b.id` but no `ORDER BY`.
**Evidence:** the tile order depends on SQLite's internal ordering. Everything else in the dashboard sorts brands by name (`app.py:179` `ORDER BY b.name`, `app.py:226`).
**Suggested fix:** add `ORDER BY b.name`.

### 6. [nit] Query isn't limited to one project
**Location:** `lobby_db.py:311-322`
**Evidence:** design §1 says "for each brand in the project", but the query reads every project. My probe with a second project produced two `Offsets` tiles, one fresh and one `no data`, with nothing to tell them apart. The existing `meta()` and `overview()` aren't project-scoped either, and only one project exists today, so this is low risk.
**Suggested fix:** filter on `b.project_id` for the default project, or update design §1 to say "all brands".

### 7. [nit] An empty DB shows an empty panel
**Location:** `static/app.js:141`
**Evidence:** when `/api/freshness` returns `[]`, the "Brand freshness" heading shows with nothing under it (probe "empty DB" case). The rest of the UI shows `.empty` messages in this situation (`app.js:62`).
**Suggested fix:** if `rows.length` is 0, render `<div class="empty">No brands yet.</div>`.

### 8. [nit / process] Thresholds and label format were never confirmed in the spec
**Location:** `spec.md` §6 still lists Open questions #2 and #3 as `TBD`, and the spec status is still `Draft v1`. Design §6 says: "Ros should confirm or override them before `/sdd:tasks`."
**Evidence:** I found no record of that confirmation. The rules from D7/D8 (exactly 6h is stale, exactly 24h is old, `Nm ago` under 1h) are now in code and tests as if they were accepted.
**Suggested fix:** Ros confirms, and spec §6 is updated with the answers before ship.

### 9. [nit] Badges are never refreshed while the page is open
**Location:** `static/app.js:181`. Freshness is fetched once at boot. It isn't re-fetched after `runScan` or on a timer.
**Evidence:** a tab left open overnight still says `2h ago / fresh`. This doesn't break any AC, since the ACs say "when the user opens the dashboard", but it works against the feature's purpose.
**Suggested fix:** optional. Re-call `loadFreshness()` on a timer (e.g. every 60s), or note this as a known limitation.

## Diff-wide checks

- [OK] No regressions. Both commands are green, all root modules parse, and `app.py` only added an import (`brand_freshness`, `timedelta`). `/api/meta` and `/api/overview` are unchanged (D5).
- [OK] No schema change and no migration (D3). There is one new public endpoint, `GET /api/freshness`, returning `[{brand, last_ok_at, label, tier}]`. It's documented in design §3. No new env vars and no new dependencies.
- [OK] The SQL uses a parameter (`("ok",)`) and takes no user input. The endpoint ignores query params, tested at `:344-371`.
- [OK] XSS: the brand name and label are set with `textContent`, and `tier` is a fixed server-side value placed in `className`. Confirmed with the probe.
- [OK] Tests don't touch real data. `FreshnessEndpointTest` patches `app.DEFAULT_DB_PATH` to a temp file. The route test keeps its timestamps far from tier boundaries, so the wall clock can't make it flaky.
- [OK] Matches the design decisions: D1, D2, D3, D4, D5, D6, D7, D8, D9 (future → `0m ago`, garbage → `no data`, tested), D10 (section directly after `#runProof`, uses `score-card`) and D11 (4 tier classes, `title` attribute). No scope creep. Non-goals (alerts, auto-rescan, history chart, per-GEO freshness) were left out.
- ⚠️ The `GET /api/freshness` handler calls `init_db` and `ensure_defaults`, so a GET writes to the DB. This copies the existing `/api/meta` pattern, so it's not new risk. Just noting it.

## Overall

**CHANGES_REQUESTED**: 4 ACs WEAK (happy-1, happy-2, happy-3, error-1), 0 FAIL, 2 important findings, 7 nits.

The data and server layers are correct and well tested. Two things should be fixed before ship:
1. Finding 1: make the freshness panel load independently of `/api/meta` and `/api/overview`.
2. Finding 2: tighten the `app.js` tests on the `freshnessTile` body and record the manual browser check.

Fixing nits 3–5 is cheap and recommended. Nit 8 needs Ros to sign off.
