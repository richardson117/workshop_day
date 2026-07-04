# AGENTS.md — architecture context for Claude

Short guardrails for the Product Builder Workshop starter. Anything Claude Code should
read before touching this repo goes here.

## What this repo is

Lobby Radar Workshop Starter — a small Python + vanilla JS project. Reads competitor
lobby snapshots from SQLite, optionally runs a live scan behind a residential proxy,
serves a small dashboard.

## The layout

```
workshop_day/
  app.py                    # HTTP server + dashboard endpoints (no framework)
  lobby_db.py               # SQLite helpers, schema, snapshot import
  competitor_lobby_monitor.py  # live scan (Playwright-optional)
  smoke_check.py            # quick sanity: DB opens, one row loads
  import_snapshots.py       # loads seed data from snapshots/*.json
  static/                   # single-page dashboard (index.html + app.js + styles)
  data/                     # SQLite lives here (created on first run)
  snapshots/                # seed JSON files
  docs/                     # SDD-lite docs + feature specs
  skills/                   # plugin skills (auto-discovered)
  commands/                 # plugin slash commands
  agents/                   # plugin subagents
  templates/                # artifact templates
  .claude-plugin/           # plugin manifest + marketplace
```

## Prefer touching

- `app.py` — HTTP handlers, JSON endpoints, dashboard glue
- `static/index.html`, `static/app.js`, `static/styles.css` — UI
- `lobby_db.py` — SQL queries and small helpers

## Prefer NOT touching (unless task requires)

- `competitor_lobby_monitor.py` — the scanner. Don't rewrite; add near it.
- `smoke_check.py` — it's a canary. Extend, don't break.
- Existing SQLite schema — additive migrations only; don't rename columns.

## Style conventions

- Python: stdlib-first (no Flask, no FastAPI, no ORM). The repo already avoids deps.
- Frontend: vanilla JS, no build step. Keep it that way for the workshop.
- SQL: parameterised queries. Never string-concat user input.

## Testing gate

There is no `tests/` folder in this scaffold by design. The gate is:

```
python smoke_check.py
```

If a feature needs verification beyond smoke, add a `test_<feature>.py` next to
`smoke_check.py` and wire it into the smoke run.

## Domain assumptions

- Snapshots are read-only historical data. Import once, query many.
- Live scan is optional and requires `.env` with proxy vars. Don't assume it runs on
  every machine.
- Dashboard is single-user, no auth. Keep it that way in the workshop.

## SDD-lite

The `/specify`, `/design`, `/tasks`, `/implement`, `/verify`, `/ship` commands are
installed by the plugin. See:

- `WORKSHOP.md` — Day 2 lab flow (3-step compressed loop)
- `HOMEWORK.md` — full 6-stage flow for at-home
- `docs/features/_example-full-flow/` — reference feature showing all artifacts

## Anti-patterns this workshop actively prevents

1. **"Just rewrite it in FastAPI"** — no. The stdlib server is intentional.
2. **"Let's add a build step"** — no. Vanilla JS stays vanilla.
3. **"Refactor while you're there"** — no. Surgical changes tied to the current task.
4. **"Add tests everywhere"** — no. `smoke_check.py` is enough for the workshop.
