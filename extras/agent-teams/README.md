# Agent Teams — beta experimentation

Files here support the 3-minute Agent Teams demo shown at Day 2 of the Product Builder
Workshop v2. They are **not** part of the `lobby-monitor` plugin — install the plugin
normally, then use these separately when you want to try Agent Teams.

## What Agent Teams is

A beta Claude Code feature where multiple "teammates" share a task list. Each teammate
claims the next open task, works on it in its own context, then reports back. Unlike
subagents (which are isolated), teammates can see and coordinate around each other's
work.

The distinction matters:

- **Subagent** — main session spawns an isolated worker for one task. No shared state.
  This is what SDD-lite uses (`sdd-test-author`, `sdd-implementer`, `sdd-reviewer`,
  `sdd-context-checker`).
- **Agent Team** — main session creates a shared task list. N teammates claim tasks,
  work in parallel, coordinate through the list. Good for a batch of similar tasks.

## Activate

Once per session, via env var:

```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
```

Or set once globally in `~/.claude/settings.json`:

```json
{
  "experimentalAgentTeams": true
}
```

Restart Claude Code after either. It's beta — behaviour may shift across releases.

## Files in this folder

- `teammate-researcher.md` — role profile: investigates + summarises
- `teammate-implementer.md` — role profile: writes small scoped code changes
- `teammate-reviewer.md` — role profile: adversarial code review
- `example-command.md` — the exact prompt used in the workshop demo

The three teammate profiles are intentionally universal. They do not know anything
about Lobby Monitor. Reuse them in any codebase.

## When Agent Teams beats subagents

- N similar tasks, all parallelisable, low interdependency (batch of similar refactors)
- Discovery + summarisation across many files
- Multi-brand / multi-region rollouts of the same change

## When subagents beat Agent Teams

- Tightly-coupled work with strict ordering (SDD-lite: test-author must finish before
  implementer starts)
- Adversarial roles that must not share context (the reviewer should not see the
  implementer's rationale — only the diff)
- Anything where isolation is the point, not the obstacle

## Caveats

- Beta. API may shift between Claude Code releases.
- Not covered by the `lobby-monitor` plugin. Agent Teams is a separate concern.
- Not required for any workshop lab. Purely a "next level" tease. Practice comes in
  the follow-up Complex Systems workshop.
