# spec.md — snapshot-freshness-badge

> **Reference example.** This is what a completed `/specify` output looks like.
> Nothing here is auto-run at workshop time — students build their own feature.

## 1. Context

The dashboard shows brands and their lobby state, but never says **how old** the
displayed data is. Users assume it's live. It might be from yesterday. When someone
opens the dashboard on Monday morning and the last snapshot was Saturday evening, they
can't tell.

**Trigger:** two people in the last workshop asked "is this live?" while looking at
data that was 40 hours old.

**Who suffers:** anyone using the dashboard to make a decision (buy signal, competitive
check, "should we rerun the scan?"). Right now they check `data/` file timestamps
manually. That's not obvious.

## 2. Goals

1. User sees the age of the freshest snapshot for each brand, without leaving the
   dashboard.
2. User can tell "stale" from "fresh" at a glance (colour or text state, not just a
   date).
3. Zero new dependencies. Zero new services.

## 3. Non-goals

- No historical age chart. Just the current freshness.
- No push notifications when data gets old.
- No auto-refresh trigger. If it's stale, the user re-runs the scan themselves.
- No per-geo freshness split. One age per brand is enough for v1.

## 4. User stories

1. **As** a workshop attendee reading the dashboard,
   **I want** to see how old each brand's data is,
   **so that** I know if I'm looking at real state or a weekend snapshot.

2. **As** the workshop instructor pointing at the dashboard live,
   **I want** the age to update after I re-import snapshots,
   **so that** I don't have to reload with a hard cache-bust.

3. **As** someone giving a demo,
   **I want** stale data to be visually flagged,
   **so that** viewers don't misread yesterday's numbers as today's.

## 5. Acceptance criteria

### Happy path
- **AC-happy-1:** When the dashboard loads and the freshest snapshot for `rocket_play`
  is less than 6 hours old, the brand tile shows a small `fresh` badge with the age
  ("3h ago").
- **AC-happy-2:** When the freshest snapshot is between 6 and 24 hours old, the badge
  reads `stale` with the age ("18h ago"), styled in a muted colour.
- **AC-happy-3:** When the freshest snapshot is older than 24 hours, the badge reads
  `old` with the age ("2d ago"), styled in a warning colour.

### Error path
- **AC-error-1:** When a brand has zero snapshots in the DB, the tile shows a `no data`
  badge instead of an age, and the tile does not crash the rest of the dashboard.
- **AC-error-2:** When the DB is unreachable, the API endpoint returns an empty age map
  (200 OK, `{}`), and the frontend renders tiles without badges (no JS error in
  console).

### Invariant
- **AC-invariant-1:** The freshness badge for a brand never shows an age computed from
  a snapshot belonging to a different brand. (Sanity check: don't accidentally join
  wrong.)
- **AC-invariant-2:** Existing tests keep passing: `python smoke_check.py` returns 0
  after the change.

## 6. Open questions

| # | Question | Owner | Blocker? |
|---|---|---|---|
| 1 | Do we compute age server-side or client-side (from timestamps)? | user (design.md) | no — pick in design |
| 2 | Do we colour "fresh" green or leave it neutral to keep the UI calm? | user (design.md) | no |
| 3 | Is 6h / 24h the right split? Or 12h / 48h for a weekend-heavy workflow? | user | no — v1 uses 6/24, adjust after workshop feedback |
