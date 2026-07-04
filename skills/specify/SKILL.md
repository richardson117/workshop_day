---
name: specify
description: Turn a one-line feature idea into a structured spec.md (6 sections). Use when starting a new feature in Lobby Monitor. Refuses if no feature slug. Triggers on /specify <slug>, "specify X", "spec for X", "напиши спецификацію X".
model: opus
effort: medium
---

# Skill: specify

## What you do

Turn a one-line raw idea ("add Polish geo", "show provider counts per geo") into a
structured `docs/features/<slug>/spec.md` with 6 sections. Run a Socratic interview to
get there.

## How

1. **Check input**: did the user provide a slug? If not, ask: "What's the feature slug?
   (kebab-case, e.g. add-polish-geo)". Refuse to proceed without one.

2. **Read context**: glance at the existing repo
   - `README.md` (1 min)
   - `AGENTS.md` if it exists
   - `docs/features/` to see existing specs (for naming consistency)

3. **Run interview** — depth-tuned:
   - **Simple feature (XS/S):** 3–5 questions. Examples:
     - "What problem does this solve for the user?"
     - "How will you know it works?" (acceptance criterion)
     - "What's explicitly out of scope here?"
   - **Medium feature (M):** 8–12 questions. Add:
     - "Why now? What changed that this surfaced?"
     - "What's the simplest approach you've considered?"
     - "What could break in the existing system if we add this?"
     - "Who uses Lobby Monitor that this affects?"

4. **Draft spec.md** using `templates/spec-template.md`. Use the user's answers verbatim
   where possible — don't invent.

5. **Self-critic pass**: re-read your draft. Check:
   - Are all 6 sections filled?
   - At least 3 user stories?
   - At least 3 ACs (1 happy + 1 error + 1 invariant)?
   - Any tech-detail leaks in ACs? (HTTP verbs, /api/... paths, SQL, JSON shapes)
   - Open questions explicit with owner?

6. **Write to disk**: `docs/features/<slug>/spec.md`. If file already exists, **refuse**
   and tell user — don't overwrite.

7. **Handoff**: print:
   ```
   [OK] spec.md written to docs/features/<slug>/spec.md
   
   Next step: /design <slug>
   ```

## What you DON'T do

- Don't pick the design / approach. That's `/design`'s job.
- Don't write code. That's `/implement`'s job.
- Don't make up answers. If user is vague, ask follow-up. Better 1 more question than
  3 wrong assumptions.
- Don't auto-fill open questions. Leave them as `TBD — owner: <user>` unless user
  explicitly says.

## Anti-patterns to catch

- User answers "fast" / "good" / "intuitive" for AC -> push back: "what's the verifiable
  version? e.g. responds in < 500ms"
- User says "this is simple, no questions needed" -> still ask the 3 mandatory ones
  (problem, AC, out-of-scope). Otherwise the feature creeps.
- User asks you to "be flexible / handle any input" -> push back: list 3 specific input
  shapes you'll handle, mark rest as out-of-scope.

## Frontmatter for the output

```yaml
---
status: Draft v1
owner: <user-provided>
created_at: <today>
size: <XS|S|M> (you estimate based on question count and complexity)
---
```
