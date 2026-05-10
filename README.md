# Lobby Radar Workshop Starter

This is the Day 2 starter project.

It is intentionally smaller than the full Lobby Radar MVP:

- reads real competitor lobby snapshots from SQLite;
- can run a live AU/DE scan when proxy env vars are configured;
- shows a simple dashboard, New section changes, provider groups, and games.

## Run

```powershell
python smoke_check.py
python app.py
```

Open:

```text
http://127.0.0.1:8765
```

## Live Scan

Set a proxy for the geo you want to scan:

```powershell
$env:GEO_PROXY_AU='http://USER:PASSWORD@HOST:PORT'
$env:GEO_PROXY_DE='http://USER:PASSWORD@HOST:PORT'
```

Then click **Run live scan** in the UI.

If no proxy is configured, the app still opens with seeded real snapshots.

## Workshop Goal

Pick one small product improvement that makes this tool more useful for your product team.

Start from your own product need:

- What decision should this tool help a PM make?
- What signal is currently hard to notice?
- What would make the lobby data easier to inspect?
- What would make the output more useful for your business context?

Keep the change narrow, visible, and demoable.
