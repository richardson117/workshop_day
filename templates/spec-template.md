---
status: Draft v1
owner: <your name>
created_at: <YYYY-MM-DD>
size: <XS|S|M>
---

# Spec: <feature-slug>

## 1. Context

<1–2 paragraphs.>

¶1 — The concrete problem. What's happening today that's not right? Who suffers?

¶2 — Why now. What changed (incident, deadline, customer request, opportunity)?

## 2. Goals

<2–3 bullets, measurable.>

- <Outcome 1 — observable / measurable>
- <Outcome 2>
- <Outcome 3>

## 3. Non-goals

<3–4 bullets. Things we deliberately won't do in this feature.>

- <Thing we won't do>
- <Thing we won't do>
- <Thing we won't do>

## 4. User stories

<≥3. Format: As a <role>, I want <action>, so that <benefit>.>

1. **As a** <role>, **I want** <action>, **so that** <benefit>.
2. **As a** <role>, **I want** <action>, **so that** <benefit>.
3. **As a** <role>, **I want** <action>, **so that** <benefit>.

## 5. Acceptance criteria

<≥3 ACs. At least 1 each of: happy, error, invariant. Given/When/Then format.>

### happy-1
**Given** <preconditions>,
**When** <user action>,
**Then** <observable outcome>.

### error-1
**Given** <bad-input or failure preconditions>,
**When** <user action>,
**Then** <error is surfaced clearly with reason>.

### invariant-1
**Given** <a domain invariant>,
**When** <attempted violation>,
**Then** <system blocks it and names the invariant>.

**FORBIDDEN in ACs:** HTTP verbs, URL paths, status codes, SQL fragments, JSON shapes,
module names. ACs are user-observable, not implementation-detail.

## 6. Open questions

<Explicit unknowns. Owner + due date — never bare "TBD".>

| # | Question | Owner | Due |
|---|---|---|---|
| 1 | <question> | <name> | <YYYY-MM-DD> |
| 2 | <question> | <name> | <YYYY-MM-DD> |
