# Lobby Radar Workshop Starter

Day 2 starter for the Product Builder Workshop v2. Small Python + vanilla JS dashboard
reading competitor lobby snapshots from SQLite, packaged as a Claude Code plugin that
also ships SDD-lite (Spec-Driven Development) — 7 skills, 4 subagents, 4 templates.

## One-time setup (do this before the workshop)

Inside Claude Code:

```
> /plugin marketplace add richardson117/workshop_day
> /plugin install lobby-monitor@workshop-day
```

That's it — commands and subagents are now available in every Claude Code session.

## Workshop day — start a fresh lab

```bash
mkdir my-lab
cd my-lab
claude
```

Then in Claude Code:

```
> /init
```

That copies the starter code (`app.py`, `lobby_db.py`, snapshots, dashboard,
reference example) from the plugin cache into your empty folder, initialises git,
and runs the smoke check.

After `/init`, you can:

```bash
python app.py    # dashboard on http://127.0.0.1:8765
```

Or jump straight in with your first feature spec:

```
> /specify <slug>
```

## The 7 skills

- `/init` — copy the starter code + init git (run once per lab folder)
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

## Live scan (optional)

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
  skills/                      # plugin skills (auto-discovered)
  commands/                    # plugin slash commands
  agents/                      # plugin subagents
  templates/                   # artifact templates used by skills
  .claude-plugin/              # plugin manifest + marketplace
```

## Fallback if `/init` fails

If your machine can't resolve the plugin cache (rare — Codex ranked this the safest
path but not risk-free), grab the ZIP:

```bash
curl -L https://github.com/richardson117/workshop_day/archive/main.tar.gz | tar xz
cd workshop_day-main
```

Or download the ZIP from the GitHub UI ("Code → Download ZIP") and extract.
