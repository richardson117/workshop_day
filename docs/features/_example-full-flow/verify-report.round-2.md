# Verify Report for snapshot-freshness-badge (round 2)

Date: 2026-10-23
Reviewer: sdd-reviewer (adversarial)
Branch: `feature/snapshot-freshness-badge`, base `master`
Commit range: `69ad340..38749d6` (10 commits). Round-2 fixes are `3a36c5e` (T-007), `d0c08a2` (T-008) and `38749d6` (spec open questions).
Round: 2. The round-1 report (`d4514ca`) returned CHANGES_REQUESTED.
Files touched: `app.py`, `lobby_db.py`, `smoke_check.py`, `static/app.js`, `static/index.html`, `static/styles.css`, `test_freshness.py` (new), plus the four feature docs.
Overall: **CHANGES_REQUESTED** (0 blockers, 1 important, 9 nits)

## Commands run

| Command | Result |
|---|---|
| `python smoke_check.py` (AGENTS.md gate, Python 3.13.2) | exit 0. `ok: 11 runs, 3 brands, 2267 game placements`, `running test_freshness.py`, Ran 26 tests, OK. When the output is piped, the unittest output appears above the canary line. That's only stdout/stderr buffering. |
| `python -m unittest test_freshness -v` | Ran 26 tests in 1.367s, OK. That's 24 from round 1 plus 2 new ones: `test_freshness_tile_renders_label_and_tier_class_via_text_content` and `test_boot_starts_freshness_independently_of_meta_and_overview`. |
| `node --check static/app.js` | syntax OK |
| Gate-goes-red check, in a scratch copy: inverted one assertion in the T-007 test, then ran `python smoke_check.py` | exit 1, `FAILED (failures=1)`. The gate still fails on a failing test. |
| Probe: `app.freshness()` on a copy of `data/lobby_monitor.sqlite3` with the real `now` | RocketPlay `1h ago`/fresh, Lucky Dreams `12h ago`/stale, OnlyWin `3d ago`/old. This matches the manual-check record in tasks.md T-005. |
| Probe: ran `static/app.js` in Node `vm` with a stub DOM and stubbed `fetch` (`probe_boot.js`) | Finding 1 is fixed. With `/api/meta` failing, or `/api/overview` returning bad JSON, `#freshnessGrid` still renders all tiles with the right class, text and title. An XSS brand name renders as plain text. If `/api/freshness` fails or returns a dict, the panel shows "Freshness unavailable." If it returns `[]`, the panel stays empty (nit 7 is still open). |
| Mutation run: 6 edits to `static/app.js`, each followed by `python smoke_check.py` (`mutate.py`) | **All 6 mutants survive with exit 0.** See finding R2-1. |
| Concurrency probe: 100 `/api/freshness` and 100 `/api/meta` requests in parallel over 32 threads, against a DB copy (`stress.py`) | 200/200 OK. T-007 makes these two endpoints run at the same time, and both write through `init_db`/`ensure_defaults`. No `database is locked` errors. |
| Re-ran the round-1 nit probes for 3, 4 and 5 | All three still reproduce. See the follow-up table. |

Probe scripts and DB copies are in the reviewer's temporary folder (`probe_boot.js`, `mutate.py`, `stress.py`, `mut2\`, `db_copy.sqlite3`). No repo files or git state were changed.

## Round-1 findings follow-up

| # | Round-1 finding | Status | Evidence |
|---|---|---|---|
| 1 | [important] The freshness panel only loads if meta and overview succeed | **Fixed in code. The regression test is weak (R2-1).** | `app.js:178-179`: `loadFreshness();` is now the first statement of `boot()` and is not awaited. The stub-DOM probe confirms tiles render when `/api/meta` throws. But the new test (`test_freshness.py:455-464`) still passes when the same bug comes back as `await Promise.all([refreshMeta(), loadOverview()]); loadFreshness();` (mutant M1), and when the call is commented out (M2). |
| 2 | [important] The UI half of happy-1/2/3 and error-1 was checked by greps only | **Partially fixed.** The suggested asserts were added verbatim and the manual check is recorded. | `test_freshness.py:436-445` now looks inside the `freshnessTile` body for the template literal, `badge.textContent = row.label`, `name.textContent = row.brand`, and no `innerHTML`. The tasks.md T-005 manual check says `1h ago / 12h ago / 3d ago`, which matches what the real DB returns right now. The tile wiring is still untested: dropping `badge` from `card.append` (M3), moving the tier class onto `name` (M4), rendering into `#scoreGrid` (M5), or overwriting the label with the brand name (M6) all keep the gate green. |
| 3 | [nit] Comparing `run_at` as a string goes wrong with mixed offsets or a garbage row | **Open, not documented** | `lobby_db.py:314` is unchanged. The probe still gives Alpha `11h ago`/stale when it should be `2h ago`/fresh, and Zeta `no data` even though it has a valid ok scan. `design.md` D2 was not updated (no round-2 commit touches design.md). |
| 4 | [nit] A naive timestamp shows as `no data` | **Open** | `freshness_badge('2026-10-23T16:00:00', NOW)` still returns `{'label': 'no data', 'tier': 'none'}`. D9 was not updated and there is no test. |
| 5 | [nit] Tile order is undefined | **Open** | `lobby_db.py:318` still has `GROUP BY b.id` with no `ORDER BY`. The probe returns `Zeta` before `Alpha`. |
| 6 | [nit] The query isn't limited to one project | **Open** | Query unchanged. Design §1 still says "for each brand in the project". |
| 7 | [nit] An empty DB shows an empty panel | **Open** | Probe "empty list": `#freshnessGrid` has 0 children and no `.empty` message. |
| 8 | [nit/process] Thresholds and label format were never confirmed | **Fixed, with two leftovers (R2-3)** | `spec.md:96-97` marks #2 and #3 as Resolved and cites D7/D8. But `spec.md:2` still says `status: Draft v1`, and `design.md:141` still says "Ros should confirm or override them before `/sdd:tasks`". |
| 9 | [nit] Badges are never refreshed while the page is open | **Open, not noted as a known limitation** | `app.js:179` is the only call site. |

## Per-AC verdicts

| AC | Code | Test | Verdict | Reasoning |
|---|---|---|---|---|
| happy-1 (2h, fresh, green) | `app.py:110-127`, `app.js:125-136`, `styles.css` `.freshness-badge.freshness--fresh` | `test_freshness.py:149`, `:314`, `:366` (real `Handler` over HTTP), `:436-445` (tile body), plus the manual check in tasks.md T-005 | **PASS** | The server path is tested end to end. The tile body now ties the class and the label to the badge. The manual check is recorded and agrees with the DB's real output (RocketPlay `1h ago`/fresh). The remaining gap is wiring inside the tile (M3/M4 survive), tracked as R2-2. |
| happy-2 (12h, stale) | same | `:155`, `:173-181` (boundaries), `:342`, `:436-445`, manual check (Lucky Dreams `12h ago`/stale) | **PASS** | Same as happy-1. |
| happy-3 (3d, old) | same | `:159`, `:183-185`, `:315`, `:367`, `:436-445`, manual check (OnlyWin `3d ago`/old) | **PASS** | Same as happy-1. |
| happy-4 (several GEOs, newest ok wins) | `lobby_db.py:311-322` `MAX(r.run_at) … GROUP BY b.id` | `:69-79` | **PASS** (nit 3 still applies) | Correct for the `+00:00` format that both writers produce. Mixed offsets are still wrong and still undocumented. |
| error-1 (`no data`, other tiles render normally) | `lobby_db.py:316-317` LEFT JOINs; `app.py:111-114`; `app.js:138-148`, `:179` | `:93-109`, `:163`, `:294-324`, `:326-342`, `:436-445`, `:455-464` | **PASS** (the test for the T-007 part is weak, R2-1) | Server side: both a never-scanned brand and an only-failed brand give `no data`/`none`, and one broken row doesn't affect other brands. UI side: the probe confirms the panel now renders when meta or overview fail. The AC is met. The guard that keeps it met can be beaten, see R2-1. |
| invariant-1 (a newer failed scan doesn't refresh) | `lobby_db.py:316` `AND br.status = ?` with `("ok",)` | `:81-91` | **PASS** | Unchanged since round 1. The `partial` row in the test catches a `!= 'error'` mutation. |
| invariant-2 (another brand's scan doesn't change this one) | `GROUP BY b.id` | `:111-125`, `:326-342` | **PASS** | Unchanged since round 1. |
| invariant-3 (`python smoke_check.py` passes) | `smoke_check.py:1,14-15` | the gate itself | **PASS** | exit 0 on HEAD, and exit 1 when a test is broken in a scratch copy. |

## Findings

### R2-1. [important] The T-007 regression test doesn't guard the bug it was written for
**Location:** `test_freshness.py:455-464`
```python
self.assertIn("loadFreshness(", boot_body)
before_freshness = boot_body[: boot_body.index("loadFreshness(")]
self.assertNotIn("await refreshMeta", before_freshness)
self.assertNotIn("await loadOverview", before_freshness)
```
**Evidence (mutation run, each mutant leaves `python smoke_check.py` at exit 0 with 26/26 OK):**
- M1: `boot()` becomes `await Promise.all([refreshMeta(), loadOverview()]);` followed by `loadFreshness();`. This is round-1 finding 1 again in another shape: if meta or overview rejects, freshness never loads. The test passes because the text before `loadFreshness(` contains `await Promise.all`, not `await refreshMeta`.
- M2: `// loadFreshness();`. Freshness never loads at all. The test passes because `assertIn` matches the comment. The older `test_boot_loads_freshness` (`:447-453`) passes too, because it only looks for the word "freshness".

So no test in the gate fails if the freshness panel stops loading. T-007's DoD says "тест перевіряє це в тілі `boot`". Today the test only checks that the text appears, not that the call happens or what order it happens in.
**Suggested fix (stdlib, still a text check):** remove `//` line comments from `boot_body`, then assert that the first non-blank statement is exactly `loadFreshness();` (for example, `re.match(r"\s*loadFreshness\(\);", stripped_body)`). Also assert that no `await` appears before it. With this change M1 and M2 both fail. You can delete `test_boot_loads_freshness`, since the new test covers it.

### R2-2. [nit] Wiring inside the tile is still unchecked
**Location:** `test_freshness.py:436-445` against `app.js:131`, `:134` and `:141`
**Evidence:** these mutants survive:
- M3: `card.append(name);`. The badge is never shown.
- M4: `name.className = \`freshness-badge freshness--${row.tier}\``. The badge has no colour.
- M5: `el("scoreGrid").replaceChildren(...)`. Tiles go into the score grid, and `loadOverview` then overwrites them.
- M6: `badge.textContent = row.brand`. The label is wrong.

The manual check covers the current code. Nothing stops these regressions later.
**Suggested fix:** in the same `freshnessTile` body test, assert `` badge.className = `freshness-badge freshness--${row.tier}` `` as a full statement and `card.append(name, badge)`. In the `loadFreshness` body, assert `el("freshnessGrid").replaceChildren(...rows.map(freshnessTile))`. That's three more `assertIn` lines and still no JS runner.

### R2-3. [nit / process] The spec and design still describe the questions as open
**Location:** `spec.md:2` `status: Draft v1`; `design.md:141`: "Ros should confirm or override them before `/sdd:tasks`."
**Evidence:** `38749d6` marks Open questions #2 and #3 as resolved in §6 but leaves the stale wording in both places. Open question #1 ("Why now") is still `TBD` and has no due date.
**Suggested fix:** raise the spec status (e.g. `Approved v1`), change design §6 to say "confirmed 2026-10-23", and either answer #1 or mark it explicitly as non-blocking for ship.

### R2-4. [nit / process] The human sign-offs were recorded by the agent, and the manual check doesn't mention console errors
**Location:** `tasks.md:38`, `tasks.md:55`, `spec.md:96-97`
**Evidence:** both "Ros confirmed" records come from agent-co-authored commits with the same timestamp, `d0c08a2` and `38749d6` at `21:17:08 +0200`. The manual-check line matches exactly what `app.freshness()` returns on the seed DB at that time. That fits a real browser run, but a script would also produce it. T-005's DoD also requires "без помилок у консолі", and the record doesn't mention the console.
**Suggested fix:** Ros confirms in person (one line in the PR, or a screenshot), and adds "console clean" to the T-005 record.

### Carried over from round 1 (still open, see the follow-up table)
5. [nit] #3: string `MAX(run_at)` with mixed offsets or a garbage row. `lobby_db.py:314`
6. [nit] #4: naive timestamp gives `no data`. `app.py:111-114`
7. [nit] #5: no `ORDER BY b.name`. `lobby_db.py:318`
8. [nit] #6: the query isn't limited to one project, or design §1 needs rewording
9. [nit] #7: an empty panel has no `.empty` message. `app.js:141`

Round-1 nit #9 (no refresh while the page is open) is still open too. I don't count it here because the ACs say "when the user opens the dashboard". If you won't fix it, add one line to design saying so.

The cheapest way to close nits 5–9 without code changes is to document them as accepted limitations in design D2, D9 and §1. Nit 5 (`ORDER BY b.name`) is a one-line fix.

## Diff-wide checks

- [OK] No regressions. The gate is green (26/26), `node --check` passes, and round 2 doesn't change Python modules. The only code change is two lines in `app.js:179-181`. `/api/meta` and `/api/overview` are unchanged.
- [OK] New concurrency from T-007: `/api/freshness` now runs alongside `/api/meta`, and both call `init_db` and `ensure_defaults` (writes). A 200-request parallel stress run on a DB copy gave 200/200 OK. Python's default 5 s sqlite busy timeout is enough here.
- [OK] Unhandled rejections: when meta fails, `boot()` still raises an unhandled rejection (`Error: network down` in the probe). That was already true before this feature. `loadFreshness()` is not awaited but catches its own errors, so it adds no new unhandled rejection.
- [OK] XSS: the probe renders brand `<img src=x onerror=alert(1)>` as text. The tile body has no `innerHTML`, and the new test enforces that.
- [OK] No schema change, no new dependencies, no new env vars. The only new public surface is `GET /api/freshness`, documented in design §3.
- [OK] SQL is parameterised (`("ok",)`), and the endpoint ignores query params (tested at `:344-371`).
- [OK] Scope: round 2 changed only `static/app.js`, `test_freshness.py`, `tasks.md` and `spec.md`. That's surgical and traces back to the round-1 findings.
- ⚠️ Same as round 1: a GET to `/api/freshness` writes to the DB through `init_db`/`ensure_defaults`. This copies the existing `/api/meta` pattern, so it's not a new risk.

## Overall

**CHANGES_REQUESTED.** All 8 ACs PASS. There are 0 blockers, 1 important finding (R2-1) and 9 nits (R2-2, R2-3, R2-4 and five carried over from round 1).

Round 1's two important findings were addressed. The code fix for #1 is correct and confirmed by the probe, and #2 was implemented as suggested. But the test written to keep #1 fixed passes when the panel never loads, and when #1 comes back as a `Promise.all` refactor. That test needs to be tightened before ship:

1. **R2-1:** make the `boot()` test require that `loadFreshness();` is the first real (non-comment) statement, with no `await` before it.
2. Recommended, and cheap: add the R2-2 asserts and `ORDER BY b.name`. Update spec/design status (R2-3), and either document nits 3, 4, 6, 7 and 9 as accepted limitations in design or fix them. Ros should confirm R2-4 in person.

If R2-1 is fixed and the remaining nits are fixed or documented as accepted, round 3 should be a PASS.

---
_Round-1 report is preserved in git at commit `d4514ca`._
