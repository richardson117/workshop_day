# ADR 0001 — No caching on the freshness endpoint

**Status:** Accepted
**Date:** 2026-07-04
**Feature:** snapshot-freshness-badge

## Context

The freshness endpoint runs a single `SELECT brand, MAX(scraped_at) GROUP BY brand` per
request. The dashboard is single-user. On workshop-sized data (dozens of brands, a few
thousand snapshots) this query is under 5 ms.

We considered caching for two reasons: (a) if the workshop DB grows, and (b) if we
later expose the endpoint to multiple viewers. Both are hypothetical.

## Decision

**No caching.** The endpoint queries the DB directly on every call.

## Alternatives considered

- **In-memory cache with 30s TTL.** Rejected: adds invalidation logic (when
  `import_snapshots.py` runs, the cache is stale). One more moving part to explain in
  the workshop.
- **HTTP `Cache-Control: max-age=30` header.** Rejected: pushes the problem to the
  browser and makes the "did my import land?" check confusing during a live demo.
- **Materialised freshness column on the brands table.** Rejected: schema change for a
  read-only workshop dashboard is not justified.

## Consequences

- **Positive.** Simplest possible code path. Import → refresh dashboard → you see it.
  No cache to clear.
- **Positive.** One less concept to teach on Day 2.
- **Negative.** If the endpoint gets hammered by 40 dashboards simultaneously, the DB
  gets 40 concurrent reads. Fine at workshop scale; would need revisiting if this
  became a public service.

## Reversibility

Fully reversible. If caching is later needed, add a `functools.lru_cache` with a small
TTL in `lobby_db.freshest_by_brand()` — one function, no schema change, no API change.
