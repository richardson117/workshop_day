# SDD-lite Pipeline — Stage by Stage

Detailed walk through each of the 6 stages: what it reads, what it writes, what gates
it enforces, what agents it uses.

## Stage 1 — specify

**Skill file:** `skills/specify.md`
**Reads:** raw feature idea (1–3 sentences from user)
**Writes:** `docs/features/<slug>/spec.md`
**Gate:** none (entry point)
**Agents used:** none (the skill itself drives the Socratic interview)

### What happens

Claude opens an interview to turn a one-liner ("add Polish geo") into a structured spec
with 6 sections:

1. **Context** — what's the trigger, who suffers if we don't do this
2. **Goals** — 2–3 measurable outcomes
3. **Non-goals** — 3–4 things we deliberately won't do
4. **User stories** — ≥3 As-a / I-want / so-that
5. **Acceptance criteria** — Given/When/Then, ≥1 of each of 3 types (happy, error, invariant)
6. **Open questions** — explicit unknowns + owner

The interview is **depth-tuned**: simple feature gets 3–5 questions, complex feature gets
10–15. Skill stops early when the spec stops getting tighter.

### Forbidden in acceptance criteria

(Non-negotiable — AC describes user-observable behavior, not implementation)

- HTTP verbs (GET / POST), URL paths (/api/...), status codes (200 / 404)
- Error code strings (`payment.declined`)
- JSON / SQL fragments
- Specific module names

Why: AC describes **what the user observes**, not how the system implements it. Tech
detail in AC locks the design prematurely.

---

## Stage 2 — design

**Skill file:** `skills/design.md`
**Reads:** `spec.md` (refuses if missing)
**Writes:** `docs/features/<slug>/design.md`, optionally `docs/features/<slug>/adr-NNNN.md`
**Gate:** `spec.md` exists and has all 6 sections non-empty
**Agents used:** none in lite version

### What happens

Claude reads the spec, drafts a `design.md` with 3 sections:

1. **Approach summary** — 1–2 paragraphs on how we'll solve it
2. **Key decisions** — bullets of choices made (e.g. "scrape via Playwright not API",
   "store in existing snapshots table")
3. **C4 context sketch** — one diagram (ASCII or Mermaid) of what touches what

### When to write an ADR

If a decision is **irreversible** (e.g. data schema change), **multi-module**
(e.g. affects scraper + agent + db), OR **has legitimate alternatives that were rejected**,
spawn an ADR: `docs/features/<slug>/adr-NNNN-<title>.md` with MADR shape.

If decision doesn't meet 2-of-3 above → just goes in `design.md` body, no separate ADR.

---

## Stage 3 — tasks

**Skill file:** `skills/tasks.md`
**Reads:** `spec.md` + `design.md`
**Writes:** `docs/features/<slug>/tasks.md`
**Gate:** both spec and design exist, design has "Decisions" filled
**Agents used:** none

### What happens

Decompose into atomic tasks (≤ 1 hour each). Each task in `tasks.md` has:

- ID: T-001, T-002, ...
- Title: imperative ("Add PL to geos.yaml")
- AC reference: which spec AC it covers
- Files touched (best estimate): `tools/scraper_playwright.py`, etc.
- Definition of Done: 1–2 verifiable lines

Tasks listed in dependency order. Items that CAN run in parallel marked `[parallel]`.

### Example

```markdown
## Tasks for add-pl-geo

- [ ] T-001 — Add PL to `geos.yaml` with locale `pl-PL` + flag.
  AC: §5 happy-1
  Files: `geos.yaml`
  DoD: `python scripts/scrape_lobby.py --list-geos` includes "PL"

- [ ] T-002 — [parallel] Update tests/test_state_db.py to include PL in fixtures.
  AC: §5 happy-1, error-1
  Files: `tests/test_state_db.py`
  DoD: `pytest tests/` still green

- [ ] T-003 — Run scrape on rocket_play × PL.
  AC: §5 happy-2
  Files: (none)
  DoD: at least one new row in `lobby.db` with geo='PL'
```

---

## Stage 4 — implement

**Skill file:** `skills/implement.md`
**Reads:** `tasks.md`, plus the codebase
**Writes:** code + tests in the project
**Gate:** `tasks.md` has at least 1 unchecked task
**Agents used:** `sdd-test-author`, `sdd-implementer`, optional `sdd-context-checker`

### What happens

For each unchecked task in order:

1. **`sdd-test-author`** subagent writes a failing test for this task's AC.
   - Returns the test code + run output proving it fails.
2. **`sdd-implementer`** subagent writes minimal code to make the test pass.
   - Runs the test until green.
   - Runs the project's `make check` / `pytest tests/` / equivalent gate.
   - Reports: code + gate result.
3. Main loop marks the task `[x]` in `tasks.md`.

### Parallel tasks

If multiple tasks are marked `[parallel]` and don't share files, dispatch multiple
`sdd-implementer` subagents in parallel (one per task). Each works in its own context
window. Main loop collects all completions.

### Escalation

If `sdd-implementer` finds that a task's test encodes the wrong AC (i.e. spec was vague),
it STOPS and reports `ESCALATED — <reason>`. Main loop pauses and asks user to clarify
or update spec.

---

## Stage 5 — verify

**Skill file:** `skills/verify.md`
**Reads:** spec.md, design.md, code, tests, recent git diff
**Writes:** `docs/features/<slug>/verify-report.md`
**Gate:** implement reported all tasks GREEN
**Agents used:** `sdd-reviewer` (adversarial)

### What happens

**This is the Generator-Evaluator pass.** The evaluator (`sdd-reviewer`) is a different
agent in a fresh context with a skeptical system prompt:

> You're an adversarial code reviewer. Your job is to find why this feature is NOT
> actually done. Look for: AC not actually satisfied; test that passes by accident;
> edge case the implementer didn't think of; visible regression in unrelated features.
> Default to PASS only if you can't find a real issue after honest effort.

Output:

- Per-AC verdict: PASS / FAIL with evidence
- Per-finding: severity (blocker / important / nit) + suggested fix
- Overall: PASS or FAIL

If FAIL — loop back to implement (specific tasks re-opened). If PASS — proceed to ship.

### Why a separate agent

Solo agent self-eval is broken — a single agent grading its own output will identify
legitimate issues, then talk itself into deciding they weren't a big deal and approve
the work anyway. Separate evaluator with adversarial prompt is the only reliable QA
pattern at this scale.

---

## Stage 6 — ship

**Skill file:** `skills/ship.md`
**Reads:** verify-report.md (must be PASS)
**Writes:** updates to `CHANGELOG.md`, opens PR
**Gate:** verify-report PASS
**Agents used:** none

### What happens

1. Append entry to `CHANGELOG.md`: feature title + date + brief description + AC list.
2. Run final smoke check (`python scripts/scrape_lobby.py --dry-run --brand <X>` or
   project equivalent).
3. `git add` only the files touched in this feature. Commit with conventional
   message: `feat(<slug>): <one-line summary from spec §1>`.
4. Push branch. Open PR with body = spec.md summary + verify-report findings.
5. **Stop.** Don't auto-merge. Human (or follow-up agent) merges.

---

## Stage summary table

| Stage | Reads | Writes | Refuses if... | Agents | Time budget (workshop) |
|---|---|---|---|---|---|
| specify | (user input) | spec.md | feature slug missing | — | 10 min |
| design | spec.md | design.md (+ ADRs) | spec.md missing | — | 8 min |
| tasks | spec, design | tasks.md | design.md missing | — | 5 min |
| implement | tasks.md, code | code + tests | tasks.md missing or all done | test-author, implementer | 15–20 min |
| verify | spec, code, diff | verify-report.md | implement not GREEN | reviewer (adversarial) | 5 min |
| ship | verify-report.md | PR + changelog | verify FAIL | — | 2 min |

**Total for one tiny feature: ~45–50 min.** Fits in Day 2 Lab 1 (40 min) if students
don't over-scope.
