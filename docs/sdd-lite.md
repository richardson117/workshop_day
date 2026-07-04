# SDD-lite — Spec-Driven Development for Lobby Monitor (workshop variant)

Six-stage pipeline that turns a raw feature idea into a shipped PR, with human gates
between stages and file artifacts everyone can read. Built for the Product Builder
Workshop v2 with Lobby Monitor as the case study.

**Why lite:** full SDD-style methodologies use 15+ skills and one agent per role.
Powerful in the long run, overwhelming for a 2.5h session. SDD-lite keeps the 6
backbone stages, merges clarify into specify, drops the formal architecture-doc
stage, drops separate data-model and API stages.

## The pipeline

```
specify ──▶ design ──▶ tasks ──▶ implement ──▶ verify ──▶ ship
   │           │          │           │            │          │
spec.md   design.md   tasks.md  code + tests   eval-pass    PR + changelog
   ↑           ↑          ↑           ↑            ↑          ↑
ИДЕЯ      підхід    список       код           перевірка   реліз
        + ADR (if    задач      + per-task     adversarial
        irreversible)         GATE          evaluator
```

Each stage **reads the previous stage's artifact** and **refuses to start** if it's
missing. Each stage **writes one artifact** that the next stage will read.

Total: **6 stages, 4 agents, 1 template per stage.** Fits in a 2.5h workshop.

## Folder layout

```
sdd-lite/
  README.md                ← this file
  pipeline.md              ← detailed stage-by-stage walkthrough
  skills/                  ← one .md per stage (skill = "how Claude runs this stage")
    specify.md
    design.md
    tasks.md
    implement.md
    verify.md
    ship.md
  agents/                  ← one .md per agent (.claude/agents/-style)
    sdd-test-author.md
    sdd-implementer.md
    sdd-reviewer.md
    sdd-context-checker.md
  templates/               ← skeletons each stage outputs
    spec-template.md
    design-template.md
    tasks-template.md
```

## How to use in a Lobby Monitor session

1. Copy `sdd-lite/skills/*.md` → `~/.claude/skills/` (user-level) or `.claude/skills/`
   (project-level) in your fork of Lobby Monitor.
2. Copy `sdd-lite/agents/*.md` → `~/.claude/agents/` or `.claude/agents/`.
3. In Claude Code, invoke a skill: `/specify <feature-name>` (e.g. `/specify add-pl-geo`)
4. Claude runs the specify skill → produces `docs/features/add-pl-geo/spec.md`.
5. Next: `/design add-pl-geo` → reads spec.md, refuses if missing, produces design.md.
6. Continue: `/tasks` → `/implement` → `/verify` → `/ship`.

## Gates (refusal rules)

| Stage | Refuses to start unless... |
|---|---|
| specify | feature slug provided + writable `docs/features/<slug>/` |
| design | `spec.md` exists at expected path |
| tasks | `design.md` exists + has filled "Decisions" section |
| implement | `tasks.md` exists + has at least 1 unchecked task |
| verify | implement reports GREEN gate (code + tests passing locally) |
| ship | verify reports PASS (adversarial evaluator agreed) |

If a gate refuses, the agent **says explicitly** "I can't run this — needs `<artifact>`
first." Doesn't silently degrade or make up a placeholder.

## The verify stage — Generator-Evaluator pass

After `implement`, SDD-lite runs a **verify** stage: an adversarial
Generator-Evaluator pass with a fresh skeptical agent that only cares about breaking
what the implementer just shipped.

```
generator (sdd-implementer) ──▶ output ──▶ evaluator (skeptical 3rd agent)
                                              │
                                              ▼
                                          (grades against spec.md ACs)
                                              │
                                ┌─────────────┴────────────┐
                                ▼                          ▼
                            PASS → ship                FAIL → loop back to implement
```

Self-eval is a trap — a single agent grading its own output is unreliable ("Out of the
box, Claude is a poor QA agent"). The evaluator is a different agent with a
`you must try to refute this` system prompt.

## Why this is a workshop, not just docs

Reading SDD-lite is one thing. Running through it on a real feature is another. Day 2
of the workshop walks one full SDD-lite cycle live — specify a tiny Lobby Monitor
improvement, design, tasks, implement (with sdd-implementer in parallel for 3 brands),
verify (with sdd-evaluator catching at least one issue), ship.
