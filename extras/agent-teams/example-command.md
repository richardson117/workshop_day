# Demo command — Day 2 workshop

Paste this into a **second** Claude Code session (fork) with the beta flag active.
Runs ~2–4 minutes. Do a full dry-run at home once before the workshop.

## One-time prep

1. Fresh empty folder next to your main workshop folder:

   ```bash
   mkdir agent-team-demo && cd agent-team-demo
   ```

2. Drop in a small demo file — this is what the team will edit. Save as `_demo.py`:

   ```python
   def compute_sum(numbers):
       total = 0
       for n in numbers:
           total += n
       return total

   def compute_product(numbers):
       total = 1
       for n in numbers:
           total *= n
       return total

   def compute_average(numbers):
       return compute_sum(numbers) / len(numbers)
   ```

3. Start Claude Code with the beta flag on:

   ```bash
   CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
   ```

## The prompt (copy-paste into the fork session)

```
Create a team of 3 teammates for a short demo. Load their role profiles from the
following files (absolute paths; adjust to where you cloned workshop_day):

- <path>/workshop_day/extras/agent-teams/teammate-researcher.md
- <path>/workshop_day/extras/agent-teams/teammate-implementer.md
- <path>/workshop_day/extras/agent-teams/teammate-reviewer.md

Give them these three tasks. Do not assign — let each teammate claim one from the
shared task list:

1. Add a docstring to compute_sum in _demo.py explaining what it does, its
   arguments, and its return value.
2. Add a docstring to compute_product in _demo.py in the same style.
3. Add a docstring to compute_average in _demo.py in the same style. Also note the
   edge case: empty input raises ZeroDivisionError.

After each teammate posts their report to the shared task list, print a summary of
who did what and show me the final _demo.py.
```

## What the room should see

- Three teammates announce themselves and read the task list.
- Each claims one task. Order varies between runs — that's the point.
- They work in parallel; their edits stream in at roughly the same time.
- Each posts a report referencing the task it took.
- Final summary lines up: task 1 → teammate X, task 2 → teammate Y, task 3 →
  teammate Z.
- `_demo.py` now has three docstrings, one per function.

## If the demo misbehaves

- Beta flag not recognised → check `claude --version`, upgrade if old.
- Team never claims tasks → restart the fork session (beta state gets sticky).
- Two teammates race the same task → the second should see "already claimed" and
  pick another. If both write to the same task, you have a race — restart.
- It just refuses → fall back to the SDD subagents demo. This is a tease, not the
  centrepiece.

## After the workshop

Post one link to the group so people can experiment at home:

```
https://github.com/richardson117/workshop_day/tree/main/extras/agent-teams
```
