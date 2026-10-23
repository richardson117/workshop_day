# Verify Report for snapshot-freshness-badge (round 3)

Date: 2026-10-23
Reviewer: sdd-reviewer (adversarial)
Branch: `feature/snapshot-freshness-badge`, base `master`
Commit range: `69ad340..59bfb74` (15 commits). Round-2 fixes: `3c5a9da` (T-009), `9e71910` (T-010), `1e14190` (T-011), `59bfb74` (docs).
Files touched: `app.py`, `lobby_db.py`, `smoke_check.py`, `static/app.js`, `static/index.html`, `static/styles.css`, `test_freshness.py` (new), and four docs under `docs/features/snapshot-freshness-badge/`.
Overall: **CHANGES_REQUESTED (nits only)**. 0 blockers, 0 important, 6 nits. All 8 ACs pass and R2-1 is fixed. The only reason this is not PASS is the threshold: PASS allows at most 2 nits.

## Commands run

| Command | Result |
|---|---|
| `python smoke_check.py` (Python 3.13.2, repo root) | exit 0. `ok: 11 runs, 3 brands, 2267 game placements`, `running test_freshness.py`, Ran 28 tests, OK |
| `python -m unittest test_freshness -v` | Ran 28 tests, OK. Round 2 had 26; the 2 new tests are `test_load_freshness_renders_tiles_into_freshness_grid` and `test_rows_are_ordered_alphabetically_by_brand_name` |
| `node --check static/app.js` | syntax OK |
| Mutation pass 1 (`mutate.py`): 32 mutants, each in a scratch copy, each followed by `python smoke_check.py` | 22 killed, 10 survived (details below). Every round-2 mutant M1–M6 is now killed |
| Mutation pass 2 (`mutate2.py`): CSS and SQL mutants | CSS colour swap and colour-rule removal survive. Status-filter and clamp mutants are killed |
| Browser probe (`browser_probe.py`): headless Chromium (Playwright) against `app.Handler` on a DB copy | (1) Real data: Lucky Dreams `12h ago`/stale, OnlyWin `3d ago`/old, RocketPlay `1h ago`/fresh, in alphabetical order. Computed colours: fresh `rgb(13,95,75)` green, old `rgb(138,90,0)` amber. Console clean, no responses ≥400. (2) With `/api/meta` aborted and `/api/overview` returning 500: all 3 tiles still render. (3) An XSS brand name renders as text (`imgs: 0`, payload did not run); all 4 tier classes are correct. (4) With `/api/freshness` aborted: the panel shows "Freshness unavailable." and `#scoreGrid` is not affected |
| Collation probe on an in-memory DB | `brand_freshness` returns `['Alpha', 'Zeta', 'betway', …]` (case-sensitive order, N5) |
| `git status --short` after all runs | clean; HEAD is `59bfb74` |

Scripts and the DB copy are in the reviewer's temporary folder: `mutate.py`, `mutate2.py`, `browser_probe.py`, and `work\` (code copy plus `work\data\lobby_monitor.sqlite3`). No repo files or git state were changed.

### Mutation results

| Mutant | Result |
|---|---|
| M1 `await Promise.all([refreshMeta(), loadOverview()]); loadFreshness();` | **killed** |
| M2 `// loadFreshness();` | **killed** |
| M1b `await loadFreshness();` as the first statement | **killed** |
| M1c `loadFreshness()` moved after meta/overview | **killed** |
| M1e `/* loadFreshness(); */` | **killed** |
| M3 `card.append(name);` | **killed** |
| M4 tier class set on `name` | **killed** |
| M5 tiles rendered into `#scoreGrid` | **killed** |
| M6 `badge.textContent = row.brand;` | **killed** |
| M7 tier class dropped (`freshness-badge` only) | **killed** |
| M8a `name.innerHTML = row.brand` / M8b grid built with `innerHTML` | **killed** |
| M9a `title` dropped | **killed** |
| M11 `getJson("/api/meta")` used in `loadFreshness` | **killed** |
| M1d `await refreshMeta();` added inside `loadFreshness`'s `try` | **SURVIVED** (N1) |
| M10 `const rows = getJson(...)` without `await` | **SURVIVED** (N1) |
| M14 `catch (error) {}` | **SURVIVED** (N1) |
| M9b title set on `name` / M9c `setAttribute("title", "")` | **SURVIVED** (N2) |
| C1 fresh and old colour blocks swapped / C2 all tier colour rules removed | **SURVIVED** (N2) |
| M12 extra `badge.textContent = row.brand;` after the label line | SURVIVED (accepted as L6) |
| M13 commented-out duplicate of the asserted line | SURVIVED (accepted as L6) |
| H1 `hidden` on the freshness section, M15 `boot();` removed | SURVIVED (contrived, or not caused by this feature) |
| Python: status filter `<> 'error'`, no status filter, `MIN`, `<=` at 6h, inner `JOIN runs`, naive `now`, route renamed, no `ORDER BY`, future timestamp not clamped | all **killed** |
| P7 `GROUP BY b.name` | SURVIVED. Same result unless two projects share a brand name (L3) |

## Round-2 findings follow-up

| # | Round-2 finding | Status | Evidence |
|---|---|---|---|
| R2-1 | [important] The `boot()` test doesn't guard T-007 | **Resolved** | `test_freshness.py:484-486` strips `//` comments and requires `\A\s*loadFreshness\(\);`. M1, M2, M1b, M1c and M1e all fail the gate. One remaining hole: M1d brings the meta dependency back inside `loadFreshness` (N1) |
| R2-2 | [nit] Tile wiring isn't checked | **Resolved** | `:456`, `:459`, `:468` assert the full `badge.className = …`, `card.append(name, badge)` and `el("freshnessGrid").replaceChildren(...rows.map(freshnessTile))`. M3–M6 are killed |
| R2-3 | [nit] Spec and design still say the questions are open | **Resolved** | `spec.md:2` and `design.md:2` now say `Final v1`. `design.md:143-145` no longer says "confirm before /sdd:tasks". `spec.md:95` marks #1 as non-blocking for ship. Leftover: `tasks.md:2` still says `Draft v1` (N4) |
| R2-4 | [nit] Human sign-offs were written by the agent; console not mentioned | **Resolved honestly** | `59bfb74` removes the made-up "Ros ✅" line. `tasks.md:38` now says it was an automated Playwright run ("Людина цю перевірку не робила"), mentions the console and the 404s, and flags human confirmation before ship. `spec.md:96-97` say the thresholds came from the interview and still need human confirmation. This is not papered over. Human confirmation is still owed at `/sdd:ship`. Small ambiguity in the record, see N4 |
| r1-#3 | String `MAX(run_at)` | Accepted, documented | `design.md:155-157` (L1), cross-referenced from D2 |
| r1-#4 | Naive timestamp shows `no data` | Accepted, documented | `design.md:158-159` (L2), referenced from D9 |
| r1-#5 | No `ORDER BY` | **Fixed** | `lobby_db.py:319` `ORDER BY b.name`; test at `test_freshness.py:128-137`. P2 is killed. Case-sensitivity nit is N5 |
| r1-#6 | Query not scoped to one project | Accepted, documented | `design.md:29` now says "all projects, see §7 L3"; L3 is at `:160-161` |
| r1-#7 | Empty DB shows an empty panel | Accepted, documented | L4 at `design.md:162-163` |
| r1-#9 | No refresh while the page is open | Accepted, documented | L5 at `design.md:164-165` |

## Per-AC verdicts

| AC | Code | Test | Verdict | Notes |
|---|---|---|---|---|
| happy-1 (2h, fresh, green) | `app.py:110-127`; `app.js:125-136`; `styles.css:189-193` | `test_freshness.py:161-163`, `:326`, `:378` (real `Handler` over HTTP), `:448-460`, `:462-468` | **PASS** | The server label and tier, the class wiring and the grid target are all mutation-guarded. My browser probe shows green computed colour for fresh. Nothing automated checks that fresh is green (C1 survives, N2) |
| happy-2 (12h, stale) | same; `styles.css:195-199` | `:165-167`, `:185-193` (6h and 23h59m boundaries), `:354` | **PASS** | Same as happy-1 |
| happy-3 (3d, old/warning) | same; `styles.css:201-205` | `:169-171`, `:195-197`, `:327`, `:379` | **PASS** | Same as happy-1. Amber is checked in the browser only (N2) |
| happy-4 (several GEOs, newest ok wins) | `lobby_db.py:311-323` `MAX(r.run_at) … GROUP BY b.id` | `:70-80` | **PASS** | The newest row is inserted in the middle, so a min or first-row implementation would fail (P3 is killed). The mixed-offset limitation is documented (L1) |
| error-1 (`no data`, other tiles normal) | `lobby_db.py:316-317` LEFT JOINs; `app.py:111-114`; `app.js:138-148`, `:179` | `:94-110`, `:173-175`, `:306-336`, `:338-354`, `:478-488` | **PASS** | Never-scanned, only-failed and broken-`run_at` brands are all covered. The UI keeps working when meta or overview fail (browser probe 2), and the gate now guards that against M1, M2, M1b and M1c. M1d and M10 still survive (N1) |
| invariant-1 (newer failed scan doesn't refresh) | `lobby_db.py:316` `br.status = ?` with `("ok",)` | `:82-92` | **PASS** | Both the `<> 'error'` mutant and the no-filter mutant are killed |
| invariant-2 (another brand's scan doesn't change this one) | `GROUP BY b.id` | `:112-126`, `:338-354` | **PASS** | Alpha and Beta share a run row, which is a good test of isolation |
| invariant-3 (`python smoke_check.py` passes) | `smoke_check.py:1,14-15` | the gate itself | **PASS** | exit 0 at HEAD; exit 1 for every killed mutant, so the gate really fails when a test fails |

## Findings

### N1. [nit] `loadFreshness()` fetch path is still unguarded: M1d, M10 and M14 survive
**Location:** `static/app.js:139-147`; the only test of this function is `test_freshness.py:462-468`.
```js
const rows = await getJson("/api/freshness");
el("freshnessGrid").replaceChildren(...rows.map(freshnessTile));
```
**Evidence:** the test only checks for the `replaceChildren(...)` line, so these mutants keep the gate green:
- **M10:** drop `await`. `rows.map` throws, the catch runs, and the panel always shows "Freshness unavailable."
- **M1d:** add `await refreshMeta();` inside the `try`. This is round-1 finding #1 again in a third shape: if meta fails, there are no tiles.
- **M14:** empty `catch`. A failure leaves a blank panel with no message.

`test_app_js_fetches_endpoint_and_targets_grid` (`:432-437`) searches the whole file for `/api/freshness`, so it doesn't tie the fetch to this function.

**Suggested fix (stdlib, still a text check):** in `test_load_freshness_renders_tiles_into_freshness_grid`, add:
- `assertIn('const rows = await getJson("/api/freshness");', load_body)`
- `assertNotIn("refreshMeta", load_body)` and `assertNotIn("loadOverview", load_body)`
- `assertIn('"Freshness unavailable."', load_body)`

### N2. [nit] Tier colours and the badge `title` aren't guarded: C1, C2, M9b and M9c survive
**Location:** `test_freshness.py:408-414` (CSS), `:439-446` (title); `styles.css:189-211`; `app.js:132`.
```python
self.assertIn(f".freshness--{tier}", css)
...
self.assertRegex(js, r"""setAttribute\(\s*["']title["']|\.title\s*=(?!=)|\btitle=""")
```
**Evidence:** swapping the fresh and old colour blocks (C1) makes fresh amber and old green, and the gate stays green. So the "green" in happy-1 and the "warning" in happy-3 are guarded only by a one-off browser run. Moving `title` to `name` (M9b) or setting it to `""` (M9c) also passes, because the regex searches the whole file. That undoes D11's "doesn't depend on colour alone".

**Suggested fix:**
- Brace-match the CSS block that starts at `.freshness-badge.freshness--fresh {`. Assert it contains `var(--accent-dark)`, and that the old block contains `#8a5a00`.
- In the `freshnessTile` body test, add ``assertIn('badge.setAttribute("title", `${row.tier}: ${row.label}`)', tile_body)``.

### N3. [nit / doc] Design §7 L6 understates what still survives
**Location:** `design.md:166-169`
> "Only the `boot()` test strips `//` comments, so a commented-out duplicate of an asserted line … would still pass. Mutants M1–M6 from verify round 2 are all caught."

**Evidence:** the second sentence is true; I confirmed it. But the limitation is described as if commented-out duplicates were the only gap. M1d, M10, M14, M9b, M9c, M12, C1 and C2 also survive, and none of them involves comments.

**Suggested fix:** fix N1 and N2, or list the surviving mutant classes in L6 so the accepted risk is stated accurately.

### N4. [nit / doc] Leftover doc inconsistencies
**Location:** `tasks.md:2`, `tasks.md:38`
- `tasks.md:2` still says `status: Draft v1`, while `spec.md:2` and `design.md:2` say `Final v1`.
- `tasks.md:38` lists the checked tiles as "RocketPlay / Lucky Dreams / OnlyWin; після T-011 плитки йдуть за алфавітом". That is the pre-T-011 id order. The record also says "~19:30 UTC", while T-011 was committed at 19:29:52 UTC and the docs at 19:31:31 UTC. So it's unclear whether the recorded browser run included T-011.

**No functional impact:** my probe on HEAD shows the alphabetical order (Lucky Dreams, OnlyWin, RocketPlay) with the correct classes and a clean console.

**Suggested fix:** set the tasks status to match the other docs. Reword the record to say explicitly that it was pre-T-011, or re-record it after T-011.

### N5. [nit] `ORDER BY b.name` sorts case-sensitively
**Location:** `lobby_db.py:319`
```sql
GROUP BY b.id
ORDER BY b.name
```
**Evidence:** SQLite's default BINARY collation puts lowercase names after uppercase ones. The probe returns `['Alpha', 'Zeta', 'betway', …]`. The seed brands are all capitalised, so nothing is wrong today.

**Suggested fix:** use `ORDER BY b.name COLLATE NOCASE` and add one lowercase brand to `:128-137`, or accept this in §7.

### N6. [nit] Test hygiene: one redundant test, one assertion that can never fail
**Location:** `test_freshness.py:470-476`, `:487-488`
```python
first_statement_end = stripped.index("loadFreshness();")
self.assertNotIn("await", stripped[:first_statement_end])
```
**Evidence:** the `\A\s*loadFreshness\(\);` anchor on `:486` already guarantees the slice is whitespace only, so the `assertNotIn` can never fail. `test_boot_loads_freshness` (`:470-476`) is fully covered by `:478-488`; round 2 suggested deleting it.

**Suggested fix:** delete both. Optional, since neither causes harm.

## Diff-wide checks

- [OK] **No regressions.** Gate 28/28 green, `node --check` OK. The round-3 code changes are one SQL line (`ORDER BY`) plus tests. `brand_freshness` is called only from `app.freshness`. `/api/meta` and `/api/overview` are unchanged. The diff touches only the feature files listed in the header.
- [OK] **Gate integrity.** Every killed mutant made `smoke_check.py` exit 1. `unittest.main(... argv=["smoke_check"])` passes the failure exit code through.
- [OK] **Runtime behaviour.** The browser probe at HEAD confirms 3 tiles with the correct text, classes, `title` and computed colours, a clean console and no responses ≥400. The panel is independent of meta and overview failures and degrades cleanly when `/api/freshness` fails.
- [OK] **XSS.** A brand named `<img src=x onerror=…>` renders as text and the handler doesn't run. `innerHTML` mutants are killed.
- [OK] **SQL** is parameterised (`("ok",)`). The endpoint ignores query parameters (tested at `:356-383`).
- [OK] **No schema change, no new dependencies, no new environment variables.** The only new public surface is `GET /api/freshness`, documented in design §3.
- [OK] **Docs vs code.** Design §1 ("ordered by brand name", "all projects"), D2, D9 and §7 L1–L5 match the code. The R2-3 and R2-4 fixes are honest: no human sign-off is claimed, and confirmation before ship is flagged in 4 places. Remaining gaps: N3 and N4.
- ⚠️ **GET writes to the DB.** `/api/freshness` calls `init_db`/`ensure_defaults`, which write. This copies the existing `/api/meta` pattern, so it is not a new risk.
- ⚠️ **Still waiting on Ros before `/sdd:ship`:** confirm the D7/D8 thresholds and label format, answer or waive Open question #1, and confirm the browser check in person. These are ship-gate items, not verify defects.

## Overall

**CHANGES_REQUESTED (nits only): 0 blockers, 0 important, 6 nits.**

R2-1 is genuinely fixed. Every round-2 mutant, and every variant of the six mutant types I was asked to re-run (awaited, moved after, tier class dropped, `innerHTML`, `title` dropped, grid target changed), now fails the gate. R2-2 and the `ORDER BY` nit are fixed. R2-3 and R2-4 were resolved honestly rather than papered over. All 8 ACs pass, and the browser probe confirms the feature works end to end at HEAD.

The verdict is CHANGES_REQUESTED only because the PASS threshold is at most 2 nits. To reach PASS:
1. Add the N1 and N2 assertions to `test_freshness.py`. That's about 6 `assertIn` lines, test-only, and it kills M1d, M10, M14, M9b, M9c and C1.
2. Fix N3–N6 or record them as accepted in design §7 / tasks.md. Each is a one-line doc or SQL change.

No production code change is required for this feature to be correct.
