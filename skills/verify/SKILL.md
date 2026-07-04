---
name: verify
description: Adversarial Generator-Evaluator pass. Dispatches sdd-reviewer in fresh context with skeptical system prompt to grade against spec. Writes verify-report.md.
model: opus
effort: high
---

# Skill: verify

## What you do

After `/implement` reports all GREEN, run an **adversarial** evaluation. Your job is
to spawn a fresh `sdd-reviewer` subagent in clean context and let it try hard to find
why the feature is NOT actually done.

## Why this exists

Per slack research (F0B8T21GD7G):

> "Out of the box, Claude is a poor QA agent. It would identify legitimate issues, then
> talk itself into deciding they weren't a big deal and approve the work anyway."

Self-evaluation = pastka. Builder ≠ judge. Different agent + skeptical prompt + clean
context = the only honest QA at this scale.

## How

1. **Gate**: check `tasks.md` has all tasks marked `[x]`. If any `[ ]` or `[!]` -> refuse:
   ```
   [NO] Cannot verify — not all tasks complete. Finish /implement first.
   ```

2. **Gather inputs for evaluator**:
   - spec.md (full)
   - design.md (full)
   - git diff for this feature (since branch creation)
   - tasks.md (with status)
   - project AGENTS.md (for context)

3. **Dispatch `sdd-reviewer`** with prompt:
   ```
   You are an ADVERSARIAL code reviewer. Your default is FAIL. Only PASS if you've
   honestly tried to find issues and couldn't.
   
   Inputs:
   <attach spec.md, design.md, git diff, tasks.md>
   
   For each AC in spec.md §5:
   1. Find the code that's supposed to satisfy it
   2. Find the test that's supposed to exercise it
   3. Ask: does the test really exercise the AC, or could it pass for the wrong reason?
   4. Ask: would the AC fail in any plausible edge case the implementer didn't think of?
   5. Verdict per AC: PASS / FAIL / WEAK (passes but for wrong reason)
   
   For the diff overall:
   - Any regression to unrelated features? (run the project gate on the FULL test suite)
   - Any visible side effects? (e.g. new file format, schema change, public API change)
   - Any obvious security/correctness issues?
   
   Output format:
   - Per-AC verdict table
   - Overall: PASS / FAIL / CHANGES_REQUESTED
   - If FAIL or CHANGES_REQUESTED: numbered list of issues with severity (blocker / important / nit) and suggested fix
   - Be specific, cite files:line, quote code
   ```

4. **Capture reviewer output** -> write to `docs/features/<slug>/verify-report.md`.

5. **Decide next action**:
   - **All ACs PASS + Overall PASS**: print success message, hand off to `/ship`
   - **Any FAIL or Overall != PASS**: 
     - Add new tasks to `tasks.md` for each blocker issue (T-NNN — Fix <issue>)
     - Mark spec/design as needing update if reviewer flagged AC ambiguity
     - Print: "[NO] Verify failed. <N> blockers. New tasks added. Re-run /implement."
   - **WEAK ACs (test passes for wrong reason)**:
     - Add task: "Strengthen test for AC X"
     - Don't block ship, but flag in handoff

6. **Handoff (success)**:
   ```
   [OK] Verify PASS. All N ACs satisfied + tested honestly.
   📄 verify-report.md written.
   
   Next step: /ship <slug>
   ```

## What you DON'T do

- Don't review the code yourself in main context. You'd just confirm your own implementation.
- Don't give the reviewer access to write tools. Read-only.
- Don't compress the reviewer's findings. Pass them through verbatim — don't soften.
- Don't argue with reviewer findings in main context. If you disagree, escalate to user.

## Anti-patterns to catch

- Reviewer reports "looks good, nothing to find" too easily -> re-prompt with "you found
  nothing — but did you actually try? Find at least 2 things, even if low severity."
- Per-AC tables that just restate the AC instead of evaluating it -> re-prompt with
  "evaluate, don't echo."
- Tests that pass without exercising the AC (e.g. mock returns the right thing without
  calling real code) -> reviewer should catch this as WEAK.

## Note on cost

This stage runs a full second pass with Opus + high effort. Budget ~10–30k tokens per
feature. If running on Pro plan, this is fine for a feature/day. For higher volume,
consider Sonnet for the reviewer (less skeptical but cheaper).
