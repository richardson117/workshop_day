---
status: Final v1 — accepted limitations in §7; потребує підтвердження людиною перед /sdd:ship
owner: Ros
created_at: 2026-10-23
spec_ref: docs/features/snapshot-freshness-badge/spec.md
---

# Design: snapshot-freshness-badge

## 0. Reality check (schema read before designing)

What the code actually has, from `lobby_db.py` / `app.py` / `static/`:

- There is **no `snapshots` table and no `scraped_at` column**. The ones in `_example-full-flow/design.md` don't exist.
  A brand's scan result lives in `brand_runs(run_id, brand_id, status, …)`. The scan time is on the parent
  row, `runs.run_at`. GEO is on `runs.geo_code`.
- `brand_runs.status` has three real values: `ok`, `partial`, `error` (seed DB: 23 / 4 / 6).
  The scanner writes `partial` when it finds no games (`competitor_lobby_monitor.py:387`).
- `runs.run_at` is always UTC ISO-8601 with an offset (`2026-10-23T17:55:15+00:00`), both from the seed
  data and from the scanner's `utc_now()`.
- **The dashboard has no brand tiles today.** It has score cards, diff cards (shown only when something
  changed), pills and a games table. The spec's "плитка бренду" has to be built as part of this feature.
- Every brand row is created together with a `brand_runs` row (`ensure_brand` is only called from
  `ingest_snapshot`), so in practice a brand always has at least one scan. That scan may be a failure, and
  the code has to handle a brand with zero scans anyway.

## 1. Approach summary

We add one read query in `lobby_db.py`. For each brand in the DB (all projects, see §7 L3), ordered by brand name, it returns the latest `runs.run_at`,
counting only that brand's `brand_runs` rows with `status = 'ok'`, across all GEOs. A `LEFT JOIN` from
`brands` makes sure a brand with no successful scan still comes back, with `NULL` as its timestamp
(spec error-1). Taking the maximum over all GEOs gives one freshness per brand (happy-4). Filtering on
`ok` means a newer failed scan never refreshes the badge (invariant-1). Grouping by brand means one
brand's scan can't change another's freshness (invariant-2).

A pure Python helper, `freshness_badge(last_ok_at, now)`, turns that timestamp into
`{label, tier}`: label is `2h ago` / `12h ago` / `3d ago` / `no data`, tier is
`fresh | stale | old | none`. A new endpoint, `GET /api/freshness` in `app.py`, returns one entry
per brand. On the frontend, `static/app.js` fetches the endpoint at boot and renders a new
"Brand freshness" strip: one tile per brand with the brand name and a badge. `static/styles.css`
gets one CSS block with a colour class per tier. Verification is a stdlib `test_freshness.py` next
to `smoke_check.py`, run from the smoke check (AGENTS.md testing gate, invariant-3). No schema
change and no new dependencies.

## 2. Key decisions

- **D1. Only `status = 'ok'` counts as a successful scan. `partial` and `error` don't.**
  Reason: the spec defines success as status `ok`. `partial` means the scanner got no games, so it isn't real data.
- **D2. Freshness = `MAX(runs.run_at)` over the brand's `ok` rows in `brand_runs`, across all GEOs. Compare `run_at` as a string in SQL.**
  Reason: freshness isn't stored anywhere, and both writers produce the same UTC `+00:00` ISO format,
  so the strings sort in time order. The query is one `GROUP BY` with no migration.
  Limitation: mixed offsets or a garbage `run_at` break the string order (§7 L1).
- **D3. No schema change. Freshness is computed when the endpoint is called, not stored.**
  Reason: AGENTS.md allows additive migrations only. A stored column would have to be kept in sync
  in `ingest_snapshot`, and the query is cheap on a workshop-sized DB.
- **D4. Compute age, label and tier on the server, in a pure Python function that takes `now` as an argument.**
  Reason: the project's only test gate is Python (`smoke_check.py` + `test_<feature>.py`), and
  JS has no test runner and no build step. A function with `now` injected makes every AC
  (2h / 12h / 3d / no data / boundaries) a deterministic unit test. This deliberately differs from
  the example design, which put this logic on the client.
- **D5. Use a new `GET /api/freshness` endpoint and leave `/api/meta` as it is.**
  Reason: `meta()` builds the brand dropdown with an inner `JOIN`. Changing its query would risk
  the dropdown for no gain. A separate endpoint is a small, additive change.
- **D6. Freshness ignores the dashboard's Geo / Brand / Search filters and always shows every brand.**
  Reason: spec non-goal says "one freshness per brand, not per GEO". Hiding stale brands behind a filter would
  undo the point of the feature ("see it at a glance").
- **D7. Thresholds (resolves spec Open question #2):** `age < 6h` → fresh, `6h ≤ age < 24h` → stale,
  `age ≥ 24h` → old. Exactly 6h is stale and exactly 24h is old.
  Reason: half-open intervals with no gaps, and a boundary goes to the worse state, which is the
  cautious choice for a warning feature.
- **D8. Label format (resolves spec Open question #3):** `age < 1h` → `Nm ago` (minimum `0m ago`);
  `1h ≤ age < 24h` → `Nh ago`; `age ≥ 24h` → `Nd ago`. All values are rounded down.
  Reason: units switch where the tiers do (24h = old = days), and rounding down never makes data look
  older than it is. Matches the ACs: 2h→`2h ago`, 12h→`12h ago`, 3d→`3d ago`.
- **D9. Treat a timestamp in the future (clock skew) as age 0 → `0m ago`, fresh. Treat an unparseable timestamp as `no data`.**
  Reason: one bad row must not break the other tiles (error-1, "the other tiles render normally").
  Limitation: a naive timestamp (no offset) also counts as unparseable → `no data` (§7 L2).
- **D10. The UI is a new "Brand freshness" section placed directly under `#runProof`, using the existing `score-card` look plus a tier modifier class.**
  Reason: there are no brand tiles to attach to (§0). Reusing the existing card style keeps the CSS change
  to one small block. The section goes next to the run proof because both answer "how current is this?".
- **D11. Badge colours:** fresh = green, stale = muted grey, old = amber/warning, none = neutral
  outline with the text `no data`. The tier is also in the text (`title` attribute), so the badge
  doesn't depend on colour alone.
  Reason: spec Goal 2, plus basic accessibility.

**ADR test (2-of-3):** no decision passes. D3 avoids an irreversible change because it adds no
schema. D5 adds a local, unversioned JSON endpoint with no outside consumers. The feature touches the
repo root and `static/`, which is fewer than 3 folders. D4 has a real alternative (computing on the
client), but it is easy to reverse and stays within one feature. So all decisions live here and
**no ADRs are spawned**.

## 3. C4 Context sketch

```
  browser
     │
     ▼
┌──────────────────────────────┐
│ static/app.js                │  boot → GET /api/freshness
│  renderFreshness(brands)     │  one tile per brand: name + badge
│ static/index.html            │  new <section id="freshnessGrid">
│ static/styles.css            │  .freshness--fresh|stale|old|none
└──────────────┬───────────────┘
               │ GET /api/freshness
               │ → [{brand, last_ok_at, label, tier}, …]
               ▼
┌──────────────────────────────┐
│ app.py                       │  Handler.do_GET route
│  freshness(conn, now)        │  maps rows → freshness_badge()
│  freshness_badge(ts, now)    │  pure: age → {label, tier}
└──────────────┬───────────────┘
               │ brand_freshness(conn)
               ▼
┌──────────────────────────────┐
│ lobby_db.py                  │  brands LEFT JOIN brand_runs (status='ok')
│                              │  LEFT JOIN runs → MAX(run_at) GROUP BY brand
└──────────────┬───────────────┘
               ▼
        data/lobby_monitor.sqlite3   (schema unchanged)

  test_freshness.py ──► freshness_badge + brand_freshness (in-memory DB)
  smoke_check.py    ──► runs test_freshness.py
  competitor_lobby_monitor.py — not touched
```

## 4. Files this design touches

- `lobby_db.py`: add the `brand_freshness(conn)` query
- `app.py`: add `freshness_badge(...)`, `freshness(conn, now)`, and the `/api/freshness` route
- `static/index.html`: add the freshness section container
- `static/app.js`: fetch the endpoint and render the tiles
- `static/styles.css`: one block for the tile badge and its 4 tier classes
- `test_freshness.py` (new): unit tests for the badge function (ACs + D7/D8 boundaries) and for the
  query on an in-memory SQLite DB (ok vs error vs partial, multiple GEOs, no successful scan, isolation between brands)
- `smoke_check.py`: extend it to run `test_freshness.py`. Extend only, don't rewrite.

## 5. ADRs spawned

- None. No decision met the 2-of-3 bar (see the note at the end of §2).

## 6. Spec feedback

- Open questions #2 and #3 are resolved by D7 and D8 (2026-10-23). The 6h/24h thresholds and the `Xm/Xh/Xd ago`
  format come from the `/sdd:specify` interview; nobody confirmed them separately in the automated run.
  **Потребує підтвердження людиною перед /sdd:ship.**
- Open question #1 (Why now) doesn't block the design or ship.
- The spec says "плитка бренду" as if brand tiles already existed. They don't (§0), so creating them is in
  scope here (D10). This doesn't conflict with the non-goals.

## 7. Accepted limitations

Verify round 2 nits we chose not to fix in this feature. None of them breaks an AC on data the two
writers actually produce today.

- **L1. String `MAX(run_at)`** (verify #3, D2). Mixed UTC offsets sort wrong, and a garbage `run_at` on an
  `ok` row sorts above valid ISO strings, so that brand shows `no data` even if it has a valid ok scan.
  Accepted because both writers emit UTC `+00:00` ISO. Fix if another writer appears: parse in Python and take the max there.
- **L2. Naive timestamp → `no data`** (verify #4, D9). `run_at` without an offset is treated as unparseable.
  Accepted for the same reason as L1; no writer produces naive timestamps.
- **L3. Not scoped to one project** (verify #6, §1). `brand_freshness` returns every brand in the DB. The
  workshop DB has one project, and `/api/meta` lists brands the same way.
- **L4. Empty DB → empty panel** (verify #7). With zero brands `#freshnessGrid` stays empty, without an
  `.empty` message. The rest of the dashboard is empty in that state too.
- **L5. No refresh while the page is open** (round-1 #9). Badges are computed once at `boot()`. The ACs say
  "when the user opens the dashboard"; reload the page to refresh.
- **L6. UI tests are text checks** (D4, context-checker after T-011). `FreshnessStaticAssetsTest` greps
  `app.js` source. Only the `boot()` test strips `//` comments, so a commented-out duplicate of an asserted
  line in `freshnessTile`/`loadFreshness` would still pass. Mutants M1–M6 from verify round 2 are all caught.
  Accepted because the project has no JS runner and adding one is out of scope (AGENTS.md: no build step).
