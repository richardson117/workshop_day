# verify-report.md — snapshot-freshness-badge

**Verifier:** `sdd-reviewer` (adversarial evaluator)
**Date:** 2026-07-04
**Feature:** snapshot-freshness-badge
**Spec ref:** `spec.md`, **Design ref:** `design.md`

## Overall verdict: PASS with 1 nit

All 8 AC covered. Two blockers found in the first pass, both fixed and reverified. One
nit remains that's below the ship bar.

## Per-AC verdict

| AC | Verdict | Evidence |
|---|---|---|
| happy-1 (<6h → fresh) | PASS | Manual test with fresh snapshot, badge reads "2h ago", green tier |
| happy-2 (6-24h → stale) | PASS | Time-travelled DB with 12h-old snapshot, badge reads "12h ago", muted tier |
| happy-3 (>24h → old) | PASS | 3-day-old snapshot, badge reads "3d ago", warning tier |
| error-1 (no data → badge) | PASS | Emptied one brand's rows, tile renders "no data" badge, no console error |
| error-2 (DB down → 200 {}) | PASS | Renamed `data/lobby.db`, endpoint returns `200 OK` `{}`, dashboard silent |
| invariant-1 (no cross-brand) | PASS | Checked SQL: `GROUP BY brand` on `snapshots.brand` column, no join to unrelated tables |
| invariant-2 (smoke stays green) | PASS | `python smoke_check.py` exits 0, extended smoke also passes |

## Findings from first pass (now fixed)

### [BLOCKER] 1 — Timezone-naive comparison in `formatAge`
**Where:** `static/app.js` — `formatAge()`
**Issue:** Server returns ISO strings from SQLite (naive UTC). Frontend passed them to
`new Date()` which interprets ambiguously across browsers. Chrome parsed as UTC, older
Firefox as local. 8-hour discrepancy in tier assignment.
**Fix:** Server now appends `Z` suffix to enforce UTC. `formatAge` explicitly
uses `Date.UTC` on parse. Reverified: all browsers agree on tier.

### [BLOCKER] 2 — Empty-DB path threw before AC-error-2
**Where:** `lobby_db.py` — `freshest_by_brand()`
**Issue:** With zero rows, `MAX(scraped_at)` returned `None`, and the endpoint tried to
`isoformat()` on `None`.
**Fix:** Filter out `None` rows in the helper. Endpoint now returns `{}` cleanly.
Reverified.

## Remaining finding

### [nit] 1 — Age "just now" threshold
**Where:** `static/app.js` — `formatAge()`
**Issue:** Anything under 90 seconds returns "just now" — but the spec doesn't define
this. Might confuse a viewer who imports and then sees "just now" for 90 seconds.
**Fix suggestion:** either document 90s in the spec §5, or narrow to 30s.
**Ship blocker?** No. Documented as post-workshop tweak.

## What the evaluator tried to break

Attempts to refute:
1. **Alternate correct impl that satisfies AC and is wrong.** Tried: what if
   `freshest_by_brand` returns strings but frontend expects timestamps? Would satisfy
   the type but produce garbage ages. Checked: JS side does `Date.parse()`, would
   catch. OK.
2. **Edge case: multiple brands with same freshest time.** Would `GROUP BY` collapse
   them? Checked: no, `GROUP BY brand` gives one row per brand. OK.
3. **Regression in other dashboard endpoints.** Checked `/api/brands`, `/api/games`,
   `/api/providers` — all still return same shape. OK.

## Green-light checklist for /ship

- [x] All AC PASS
- [x] `python smoke_check.py` exits 0
- [x] No new dependencies in `requirements.txt`
- [x] Frontend still loads (no JS console errors)
- [x] Live scan flow untouched (`competitor_lobby_monitor.py` unmodified)

Ready to `/ship`.
