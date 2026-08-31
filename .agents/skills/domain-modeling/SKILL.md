---
name: domain-modeling
description: Build and sharpen a project's domain model. Use when discussing codebase terminology, writing or editing a CONTEXT.md, or recording or editing an ADR.
---

# Domain Modeling

Actively build and sharpen the project's domain model as you design. This is the *active* discipline: challenging terms, inventing edge-case scenarios, and writing the glossary and decisions down the moment they crystallise. (Merely *reading* `CONTEXT.md` for vocabulary is not this skill: that's a one-line habit any skill can do. This skill is for when you're changing the model, not just consuming it.)

## File structure — this repo's layout (adapted from upstream)

This repo already has an established docs system (see `docs/ROADMAP.md` and
`CLAUDE.md`'s documentation map) — don't create a root `CONTEXT.md` or
`docs/adr/`. Use the existing equivalents instead:

```
/
├── CLAUDE.md                     ← lean index, points here
└── docs/
    ├── architecture/
    │   └── glossary.md           ← THE glossary (= CONTEXT.md "Language" section)
    ├── specs/
    │   └── <topic>.md            ← design decisions (= ADRs, prose format, not numbered)
    ├── roadmap-<area>.md         ← changelog per area; links specs when relevant
    └── features/<slug>/          ← spec-driven planning for a feature not yet built
```

Single-context: this is a small, single-app repo (bot + api + web sharing
one `bot/services/` layer) — there's no `CONTEXT-MAP.md`/multi-context split
here, and none should be introduced without discussing it with the user
first.

Both `docs/architecture/glossary.md` and `docs/specs/` already exist and are
populated — treat them as living documents to extend, not files to create
from scratch. See [`CONTEXT-FORMAT.md`](./CONTEXT-FORMAT.md) and
[`ADR-FORMAT.md`](./ADR-FORMAT.md) in this folder for how each maps onto
this repo's actual format.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y. Which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account': do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible. Which is right?"

### Update the glossary inline

When a term is resolved, update `docs/architecture/glossary.md` right there. Don't batch these up: capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

The glossary should be totally devoid of implementation details. Do not treat it as a spec, a scratch pad, or a repository for implementation decisions. It is a glossary and nothing else — implementation decisions go in `docs/specs/` instead (see below).

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip recording it. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md) — a new file in `docs/specs/`, linked from the matching `docs/roadmap-<area>.md` (same convention `CLAUDE.md` already documents: "write a new spec only for a genuinely non-obvious design decision").
