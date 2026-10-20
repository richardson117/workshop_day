---
name: init
description: Copy the Lobby Radar workshop starter code from the installed plugin cache into the current working directory, then initialise git and run the smoke check. Use when starting a fresh workshop project. Triggers on /sdd:init, "init the workshop", "setup workshop project", "розгорни воркшоп сюди".
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

   > `python not found. Install Python 3.9+ (https://www.python.org/downloads/) and re-run /sdd:init.`

2. **Check CWD emptiness.** List files in `.`. Allowed to be present without warning:
   `.git/`, `.claude/`, `.env`, `.gitignore`. If ANY other files/dirs exist, STOP and print:

   > `Directory not empty. Move to an empty folder (mkdir my-lab && cd my-lab) and re-run /sdd:init.`

   Do not offer `--force`. Do not overwrite. This is a hard gate.

3. **Copy the starter from the plugin.** Save this Python script as `_lobby_init.py` in
   CWD, exactly as written (the plugin path below is already filled in), then execute it
   via the detected `python` command. The script deletes itself when it finishes — do
   not delete it yourself and do not commit it.

   ```python
   import atexit, shutil, sys
   from pathlib import Path

   atexit.register(lambda: Path(__file__).unlink(missing_ok=True))

   src = Path(r"${CLAUDE_PLUGIN_ROOT}")
   if not (src / "app.py").exists():
       print(f"ERROR: starter code not found in plugin folder {src}")
       print("Reinstall the plugin: /plugin install sdd@workshop-day")
       sys.exit(2)

   dst = Path.cwd()
   print(f"Source: {src}")
   print(f"Target: {dst}")

   # Plugin-only content — DO NOT copy into the student's project
   skip = {
       ".claude-plugin", "skills", "commands", "agents", "templates",
       ".git", "__pycache__", ".pytest_cache", "_lobby_init.py",
       ".in_use",  # Claude Code plugin marker, not project code
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
   - If `.git/` does not exist, run: `git init && git add . && git commit -m "chore: init from sdd workshop plugin"`
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
     /sdd:specify <slug>          # start your first feature spec
   ```

## Refusal cases (each prints its own message and stops)

- Python not on PATH
- CWD not empty (per the strict list in step 2)
- Starter code not found in the plugin folder → tell them to reinstall the plugin

## What you do NOT do

- Do NOT touch the plugin folder itself
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
