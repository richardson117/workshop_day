# design.md — snapshot-freshness-badge

## Approach summary

Add a new dashboard endpoint that returns a `{brand: iso_timestamp_of_freshest}` map,
computed by a single SQL query grouped by brand. The frontend calls this map on load,
computes ages relative to `Date.now()`, and injects a small `<span class="freshness">`
into each brand tile.

Server work is one SQL and one handler. Frontend work is one fetch + one render helper
+ one CSS block. No new files needed on either side.

## Key decisions

1. **Compute age client-side, not server-side.**
   Server returns raw ISO timestamps. The client subtracts from `Date.now()`. Reason:
   the freshness thresholds (6h / 24h) might get tuned during the workshop, and the
   client is the cheapest place to change them. Server stays stable, frontend gets a
   config constant.

2. **One SQL round-trip for all brands.**
   `SELECT brand, MAX(scraped_at) FROM snapshots GROUP BY brand`. Small table, indexed
   on `brand`, no need for per-tile queries.

3. **No cache. No memoisation.**
   Dashboard is single-user. The query is fast (<5ms on a workshop-sized DB). Caching
   would just add invalidation bugs — see `adr-0001-cache-approach.md`.

4. **Age formatting stays in a single JS helper.**
   `formatAge(iso)` returns `{label, tier}` where tier is `fresh | stale | old | none`.
   All three UI concerns (text, colour class, aria label) key off the same tier value.

5. **Endpoint sits on `/api/freshness`, JSON.**
   Matches existing `/api/*` endpoints in `app.py`. No versioning yet.

## C4 context sketch

```
                +--------------------+
   browser  <-->|  static/app.js     |
                |   - fetchFreshness |
                |   - formatAge      |
                |   - injectBadge    |
                +---------+----------+
                          |
                          | GET /api/freshness
                          v
                +--------------------+
                |     app.py         |
                |   handle_freshness |
                +---------+----------+
                          |
                          | SELECT brand, MAX(scraped_at)
                          v
                +--------------------+
                |    lobby_db.py     |
                |  freshest_by_brand |
                +---------+----------+
                          |
                          v
                +--------------------+
                |   data/*.sqlite    |
                +--------------------+
```

Nothing here touches `competitor_lobby_monitor.py`. Live scan is untouched.

## ADRs

- [adr-0001-cache-approach.md](adr-0001-cache-approach.md) — why we're not caching.
