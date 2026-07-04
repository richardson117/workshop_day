---
status: Draft v1
owner: <name>
created_at: <YYYY-MM-DD>
spec_ref: docs/features/<slug>/spec.md
---

# Design: <feature-slug>

## 1. Approach summary

<1–2 paragraphs. Plain English.>

What we'll build, what existing code we'll reuse, what we'll add. Reference the spec's
goals (§2) by ID where helpful.

Example:
> To satisfy Goal §2.1 (capture provider lists per geo), we'll extend the existing
> `parse_lobby_browser` in `tools/scraper_playwright.py` to accept a `geo` arg and
> branch on it. We'll reuse the existing `snapshots` SQLite table — adding a `geo`
> column via migration. No new modules.

## 2. Key decisions

<Bulleted. For each: decision + 1-line reason.>

- **Decision 1** — <choice>. Reason: <1 line>.
- **Decision 2** — <choice>. Reason: <1 line>.
- **Decision 3** — <choice>. Reason: <1 line>.

For each decision, apply the **2-of-3 ADR test**:
- Irreversible? (schema, public API, file format)
- Multi-module? (affects 3+ folders or 3+ people)
- Has legitimate rejected alternatives?

If ≥2 of 3 -> spawn ADR at `docs/features/<slug>/adr-NNNN-<title>.md`.

## 3. C4 Context sketch

<One diagram. ASCII or Mermaid. Show what touches what at module level.>

```
                                  ┌──────────────────┐
                                  │  scrape_lobby.py │
                                  │  (entry point)   │
                                  └────────┬─────────┘
                                           │
                            ┌──────────────┴────────────┐
                            ▼                           ▼
                  ┌────────────────────┐    ┌─────────────────────┐
                  │ scraper_playwright │    │  scraper_apify      │
                  │  (browser geo-aware)│    │  (HTTP fallback)    │
                  └──────────┬─────────┘    └──────────┬──────────┘
                             │                          │
                             ▼                          ▼
                  ┌────────────────────────────────────────────┐
                  │  state_db.py (writes to lobby.db)           │
                  └────────────────────────────────────────────┘
```

Don't go deeper than container level. If you need detail, that's a sequence diagram in
a separate file (not part of SDD-lite).

## 4. Files this design touches

<List the modules. This helps tasks.md decompose.>

- `tools/scraper_playwright.py` (extend)
- `config/geos.yaml` (add new geo)
- `tools/state_db.py` (add geo column via migration)
- `tests/test_scraper.py` (extend)

## 5. ADRs spawned (if any)

<List any ADR files created from §2 decisions.>

- `adr-0001-store-geo-in-snapshots-not-runs.md`
- (none, if no decisions met the 2-of-3 bar)
