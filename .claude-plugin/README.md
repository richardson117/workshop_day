# Lobby Monitor · Workshop Plugin

Claude Code plugin bundling the SDD-lite methodology on top of the Lobby Radar workshop
starter. Install once, get 6 slash commands + 4 subagents.

## What ships

### Skills — slash commands
- `/specify <slug>` — turn a raw feature idea into a structured `spec.md`
- `/design <slug>` — read the spec, draft `design.md` (+ ADR if irreversible)
- `/tasks <slug>` — decompose design into atomic tasks in `tasks.md`
- `/implement <slug>` — walk tasks with test-author + implementer subagents
- `/verify <slug>` — adversarial Generator-Evaluator pass
- `/ship <slug>` — changelog + PR

### Subagents
- `sdd-test-author` — writes failing tests before code (RED)
- `sdd-implementer` — writes minimal code to green the tests
- `sdd-reviewer` — adversarial post-implementation review
- `sdd-context-checker` — validates AC coverage before ship

### Templates
- `spec-template.md`, `design-template.md`, `tasks-template.md`, `adr-template.md`

### Project scaffold
The existing Lobby Radar Workshop Starter: `app.py`, `competitor_lobby_monitor.py`,
`lobby_db.py`, sample snapshots, dashboard.

## Install

```
> claude
> /plugin marketplace add richardson117/workshop_day
> /plugin install lobby-monitor
```

Then start with:
```
> /specify add-notifications
```

## Update

Push to the repo. Users refresh via `/plugin update lobby-monitor`.

## Docs

- `docs/sdd-lite.md` — methodology overview
- `docs/sdd-lite-pipeline.md` — detailed stage-by-stage walkthrough
