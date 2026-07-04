---
name: init
description: Copy the Lobby Radar workshop starter code from the installed plugin cache into the current working directory, then initialise git and run the smoke check. Use when starting a fresh workshop project. Triggers on /init, "init the workshop", "setup workshop project", "розгорни воркшоп сюди".
model: sonnet
effort: low
---

# Skill: init

## What you do

Bootstrap a fresh workshop directory by copying the Lobby Radar starter code from
this plugin's cache into the student's current working directory (CWD). Then
initialise git, commit the seed, and run the smoke check.

## Order of operations (do not skip steps)

1. **Locate `python`.** Try `python --version`. If that fails, try `python3 --version`.
   Use whichever works. Refuse if neither is on PATH — print:

   > `python not found. Install Python 3.9+ (https://www.python.org/downloads/) and re-run /init.`

2. **Check CWD emptiness.** List files in `.`. Allowed to be present without warning:
   `.git/`, `.claude/`, `.env`, `.gitignore`. If ANY other files/dirs exist, STOP and print:

   > `Directory not empty. Move to an empty folder (mkdir my-lab && cd my-lab) and re-run /init.`

   Do not offer `--force`. Do not overwrite. This is a hard gate.

3. **Resolve plugin cache + copy.** Save this Python script as `_lobby_init.py` in CWD,
   then execute it via the detected `python` command. Delete the script after it runs.

   ```python
   import shutil, sys
   from pathlib import Path

   cache_root = Path.home() / ".claude" / "plugins" / "cache" / "workshop-day" / "lobby-monitor"
   if not cache_root.exists():
       print(f"ERROR: plugin cache not found at {cache_root}")
       print("Reinstall the plugin: /plugin install lobby-monitor@workshop-day")
       sys.exit(2)

   versions = sorted([p for p in cache_root.iterdir() if p.is_dir()], reverse=True)
   if not versions:
       print(f"ERROR: no version subdirs under {cache_root}")
       sys.exit(2)

   src = versions[0]
   dst = Path.cwd()
   print(f"Source: {src}")
   print(f"Target: {dst}")

   # Plugin-only content — DO NOT copy into the student's project
   skip = {
       ".claude-plugin", "skills", "commands", "agents", "templates",
       ".git", "__pycache__", ".pytest_cache", "_lobby_init.py",
   }

   copied = 0
   for item in src.iterdir():
       if item.name in skip:
           continue
       target = dst / item.name
       if target.exists():
           print(f"  skip (exists): {item.name}")
           continue
       if item.is_dir():
           shutil.copytree(item, target)
       else:
           shutil.copy2(item, target)
       print(f"  + {item.name}")
       copied += 1

   print(f"Copied {copied} items.")
   sys.exit(0)
   ```

   If the script exits non-zero, STOP. Show its stderr verbatim. Do not proceed.

4. **Initialise git if not already a repo.**
   - If `.git/` does not exist, run: `git init && git add . && git commit -m "chore: init from lobby-monitor plugin"`
   - If `.git/` already exists, skip. Do not touch existing history.

5. **Run the smoke check.** `python smoke_check.py` (or `python3` if that was detected).
   Capture stdout and exit code. Print both. If exit code != 0, warn but do not roll back.

6. **Print the ready banner:**

   ```
   [OK] Workshop starter ready.
   [OK] Files landed: app.py, lobby_db.py, static/, snapshots/, docs/features/_example-full-flow/
   [OK] Smoke check: <passed|failed with exit N>

   Next:
     python app.py            # start the dashboard on http://127.0.0.1:8765
     /specify <slug>          # start your first feature spec
   ```

## Refusal cases (each prints its own message and stops)

- Python not on PATH
- CWD not empty (per the strict list in step 2)
- Plugin cache directory missing → tell them to reinstall the plugin
- Plugin cache has no version subdirs → tell them to reinstall the plugin

## What you do NOT do

- Do NOT touch the plugin cache itself
- Do NOT delete anything in CWD (even if it looks stale)
- Do NOT try to install Python packages, run pip, or edit requirements.txt
- Do NOT push anything to any git remote
- Do NOT ask the user for consent mid-copy — either the CWD passed the emptiness gate or it didn't

## Success criterion

After you finish, CWD contains at least:
- `app.py`, `lobby_db.py`, `smoke_check.py`, `README.md`, `AGENTS.md`
- `static/`, `snapshots/`, `data/`, `docs/`
- `.git/` initialised

If any of those are missing, warn the student.
