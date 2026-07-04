---
name: tasks
description: Break a designed feature into atomic tasks (≤1h each), in dependency order, with parallel-safe ones marked. Reads spec.md + design.md, writes tasks.md.
model: sonnet
effort: medium
---

# Skill: tasks

## What you do

Read `docs/features/<slug>/spec.md` + `design.md` and produce a flat checklist
`docs/features/<slug>/tasks.md`.

## How

1. **Gate**: check both `spec.md` AND `design.md` exist. If either missing -> refuse:
   ```
   [NO] Cannot decompose — needs both spec.md and design.md. Run: /specify and /design first.
   ```

2. **Read**:
   - spec.md (especially §5 acceptance criteria)
   - design.md (especially §2 key decisions — they map to tasks)

3. **Decompose**:
   - Each AC -> at least 1 task (often 1, sometimes 2 if implementation needs splitting)
   - Each key decision in design §2 -> 0 or 1 task (only if it requires concrete code change)
   - Tasks are **atomic**: ≤ 1 hour for an experienced developer
   - Order by dependency (T-001 unblocks T-002 unblocks T-003)
   - Mark `[parallel]` for tasks that don't share files and can run concurrently

4. **Per-task format**:
   ```markdown
   - [ ] T-001 — <imperative title>
     - AC: §5 happy-1 (or similar reference)
     - Files: `path/to/file.py`, `path/to/test.py`
     - DoD: <1–2 verifiable lines, e.g. "pytest tests/test_X.py passes">
   ```

5. **Self-critic**:
   - Every AC has at least one task covering it
   - No task references > 5 files (if so, split it)
   - All tasks have DoD that's actually runnable (not "looks good")
   - Parallel tasks really don't touch the same files

6. **Handoff**:
   ```
   [OK] tasks.md written with N tasks (M can run in parallel)
   
   Next step: /implement <slug>
   ```

## What you DON'T do

- Don't write code. Just describe what each task will do.
- Don't estimate hours per task beyond "≤1h" / ">1h, split me". Time-boxing isn't
  the value here.
- Don't add tasks that aren't traceable to an AC or design decision. Cut them.
- Don't auto-assign tasks to people. That's not your job.

## Anti-patterns to catch

- 30-task list for an XS feature -> too granular, merge.
- 1-task list for an M feature -> too coarse, split.
- DoD = "implement X" -> that's the task title, not the DoD. DoD is "X is observable
  by running Y and seeing Z".
