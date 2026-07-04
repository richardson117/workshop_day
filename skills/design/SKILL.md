---
name: design
description: Turn spec.md into design.md with approach summary, key decisions, and a C4 context sketch. Optionally spawns ADRs for irreversible decisions. Triggers on /design <slug>, "design X", "спроектуй X".
model: opus
effort: medium
---

# Skill: design

## What you do

Read `docs/features/<slug>/spec.md` and produce `docs/features/<slug>/design.md` —
how the team plans to solve the spec. 3 sections + optional ADRs.

## How

1. **Gate**: check `docs/features/<slug>/spec.md` exists. If not, **refuse**:
   ```
   [NO] Cannot design — needs spec.md first. Run: /specify <slug>
   ```

2. **Read context**:
   - `spec.md` (the spec you're designing for) — full read
   - `architecture.md` of the project if it exists
   - `AGENTS.md` for any architectural constraints
   - Glance at the modules listed as `Files touched` in similar past features

3. **Draft design.md** using `templates/design-template.md`. Three sections:
   - **§1 Approach summary** — 1–2 paragraphs, plain English. What you'll build,
     what existing code you'll reuse, what you'll add.
   - **§2 Key decisions** — bulleted list of choices made (e.g.
     "Scrape via Playwright not API", "Reuse existing snapshots table not a new one",
     "Add geo as runtime config not new column"). For each: one-line reason.
   - **§3 C4 Context** — one ASCII or Mermaid diagram showing what touches what at
     module level. Don't go deeper than container level.

4. **Decide on ADRs**:
   For each decision in §2, ask the 2-of-3 test:
   - **Irreversible?** (changes schema, public API, file format that users rely on)
   - **Multi-module?** (affects 3+ folders or 3+ team members)
   - **Has legitimate rejected alternatives?** (not strawmen — real options with real
     trade-offs)
   
   If decision meets ≥2 of 3 -> spawn ADR at `docs/features/<slug>/adr-NNNN-<title>.md`
   using `templates/adr-template.md`. Numbering: start at the highest existing ADR + 1
   across the whole project.
   
   If decision meets <2 of 3 -> it stays in design.md §2, no separate ADR.

5. **Self-critic pass**:
   - Does §1 actually solve the spec's goals?
   - Does §2 list decisions, not just observations?
   - Is §3 readable? (text labels, not just shapes)
   - Are ADRs in decision form (`use sliding-window counter`) not problem form
     (`rate limiting`)?

6. **Handoff**: print:
   ```
   [OK] design.md written to docs/features/<slug>/design.md
   📋 ADRs written: <list, if any>
   
   Next step: /tasks <slug>
   ```

## What you DON'T do

- Don't write pseudocode. Plain English + module names is enough.
- Don't decompose into individual tasks. That's `/tasks`'s job.
- Don't introduce new architectural patterns (Hexagonal, Microservices, etc.) — if
  the project doesn't use them already, you don't either.
- Don't propose a full system redesign for a small feature. Match the feature's size.

## Anti-patterns to catch

- "We'll use Hexagonal Architecture" for a 30-min feature -> push back: overkill, this
  is XS, just add a function in the existing module.
- "Strawman alternatives" in ADRs — listing options that are obviously bad just to make
  your choice look better. Reject. List only real options.
- ADR title = problem name (`rate limiting`) — rewrite as decision (`use sliding-window
  counter`).
- Design that contradicts spec's non-goals — flag and stop. Either spec or design must
  change.
