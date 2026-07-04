# Lobby Radar Workshop Starter

Day 2 starter project for the Product Builder Workshop v2. Small Python + vanilla JS
dashboard reading competitor lobby snapshots from SQLite, plus a Claude Code plugin
bundling SDD-lite (Spec-Driven Development) — 6 skills, 4 subagents, 4 templates.

## Quick start

```powershell
python smoke_check.py    # sanity: DB opens, one row loads
python app.py            # starts the dashboard
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Install the plugin

Inside Claude Code:

```
> /plugin marketplace add richardson117/workshop_day
> /plugin install workshop-day
```

You get 6 slash commands:

- `/specify <slug>` — turn a raw feature idea into `docs/features/<slug>/spec.md`
- `/design <slug>` — read spec, draft `design.md` (+ ADR if irreversible)
- `/tasks <slug>` — decompose design into atomic tasks
- `/implement <slug>` — test-author + implementer subagents walk the tasks
- `/verify <slug>` — adversarial reviewer looks for holes
- `/ship <slug>` — changelog + branch + PR

And 4 subagents: `sdd-test-author`, `sdd-implementer`, `sdd-reviewer`,
`sdd-context-checker`.

## Learn by example

Full reference artifacts for a real feature (add snapshot freshness badges to the
dashboard) live in [`docs/features/_example-full-flow/`](docs/features/_example-full-flow/).
Look here to see what a good `spec.md`, `design.md`, ADR, and verify-report look like
in this codebase.

## Live scan

Live competitor scan needs a residential proxy. Create `.env`:

```bash
cp .env.example .env
```

Fill in:

```text
GEO_PROXY_AU=http://user:pass@proxy-host:port
GEO_PROXY_DE=http://user:pass@proxy-host:port
```

Restart `python app.py` and click **Run live scan** in the UI.

## Docs

- [AGENTS.md](AGENTS.md) — architecture context Claude reads first
- [docs/sdd-lite.md](docs/sdd-lite.md) — methodology overview
- [docs/sdd-lite-pipeline.md](docs/sdd-lite-pipeline.md) — stage-by-stage walkthrough
- [docs/features/_example-full-flow/](docs/features/_example-full-flow/) — complete
  reference artifacts

## Layout

```
workshop_day/
  app.py                       # HTTP server + dashboard
  lobby_db.py                  # SQLite schema + queries
  competitor_lobby_monitor.py  # live scan (Playwright-optional)
  smoke_check.py               # sanity check
  static/                      # single-page dashboard
  snapshots/                   # seed data
  docs/                        # methodology + feature specs
  .claude/                     # plugin skills, agents, commands, templates
  .claude-plugin/              # plugin manifest
```
