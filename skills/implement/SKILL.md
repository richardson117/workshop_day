---
name: implement
description: Run the TDD loop across all unchecked tasks. Spawns sdd-test-author (RED) then sdd-implementer (GREEN) per task. Parallelises [parallel]-marked tasks. Updates tasks.md as it goes.
model: opus
effort: high
---

# Skill: implement

## What you do

Read `docs/features/<slug>/tasks.md` and work through every unchecked task using TDD
+ project gate check. Use subagents.

## How

1. **Gate**: check `tasks.md` exists + has at least 1 unchecked task. If not, refuse.

2. **Read** tasks.md + the project's `AGENTS.md` (for tech-stack-specific commands like
   `pytest tests/` if present, else `python smoke_check.py`).

3. **Plan execution order**:
   - Group tasks by dependency level
   - Within a level, identify `[parallel]`-marked tasks that don't share files
   - Sequential tasks run one at a time
   - Parallel-safe tasks dispatch as concurrent subagents (max 4 in parallel — token cost)

4. **For each task (or parallel group)**:

   a) **RED phase** — dispatch `sdd-test-author` subagent with prompt:
      ```
      Task: <T-NNN title>
      AC to cover: <from spec.md §5>
      Files allowed to create/edit: <from task's Files: line>
      
      Write a failing test that asserts the AC. Run it. Return:
      - test code (full file)
      - run output proving it fails for the right reason (not import error / typo)
      ```

   b) Check RED output:
      - GOOD-red: test fails because feature doesn't exist yet -> proceed
      - BAD-red: test fails for unrelated reason (syntax error, missing import) -> ask
        test-author to fix and re-run
      - FALSE-PASS: test accidentally passes -> fix the test before proceeding
      
   c) **GREEN phase** — dispatch `sdd-implementer` subagent with prompt:
      ```
      Task: <T-NNN title>
      AC: <ref>
      RED test that must pass: <test code>
      Files allowed to create/edit: <list>
      Project gate: <e.g. "python smoke_check.py" or "pytest tests/" if AGENTS.md defines one>
      
      Write minimal code to make the test pass. Run the test. Run the project gate.
      Return:
      - code (full diff)
      - test run output (must be green)
      - gate result (must be green; if not — STOP and report)
      ```

   d) Check GREEN output:
      - Gate green -> mark task `[x]` in tasks.md, continue to next task
      - Gate red -> re-dispatch implementer with "the gate broke; fix what your code did"
      - Test still red -> escalate. STOP. Report: "task T-NNN's test wasn't satisfiable
        by minimal code, may indicate spec/design issue"

   e) **Optional context-checker** every 3 tasks:
      - Dispatch `sdd-context-checker` to verify no drift between code and spec / design
      - If checker reports drift -> flag in the implementation log, continue or pause

5. **When all tasks done**: print:
   ```
   [OK] All N tasks GREEN. tasks.md updated.
   📊 Total: <N> tasks, <M> parallel, <K> minutes total wall time
   
   Next step: /verify <slug>
   ```

## What you DON'T do

- Don't write code yourself in the main loop. Delegate to subagents.
- Don't skip the RED phase ("the test is trivial") — the RED catches mis-specified ACs.
- Don't mark a task complete if the gate isn't green. Half-done is not done.
- Don't add features beyond the task scope. If you see something else needs fixing,
  add a NEW task to tasks.md (don't sneak it in).

## Parallel rules (important)

Tasks run in parallel ONLY if:
- They're explicitly marked `[parallel]` in tasks.md
- Their Files: lines don't overlap
- They don't depend on each other's output

If unsure -> run sequentially. Token cost is bounded; correctness is paramount.

## Escalation matrix

| Issue | Action |
|---|---|
| Test passes but gate fails | implementer to fix without weakening test |
| Test still fails after 3 GREEN attempts | STOP, escalate to user with details |
| sdd-implementer says spec/AC is wrong | STOP, route to user to update spec |
| Subagent times out / errors | retry once, then mark task `[!]` and continue with next |
