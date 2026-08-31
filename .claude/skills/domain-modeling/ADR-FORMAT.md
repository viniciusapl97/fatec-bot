# Decision-record format (this repo: `docs/specs/`)

Adapted from upstream's numbered `docs/adr/NNNN-slug.md` format to match the
convention already established in this repo: prose files under
`docs/specs/`, named by topic (not sequential number), cross-referenced
from the matching `docs/roadmap-<area>.md` and from `docs/ROADMAP.md`'s
"Specs" section. Don't introduce a separate `docs/adr/` — extend the
existing `docs/specs/` instead.

## Template (matches existing files, e.g. `docs/specs/api-design.md`)

```md
# Spec: {Short title of the decision}

Decisions made on {date}, when {context: implementing what}. See
[`../roadmap-<area>.md`](../roadmap-<area>.md) for the status/changelog
summary.

## {Decision heading, one per major call}

{The context, what was decided, and why — as much prose as the decision
actually needs. A one-paragraph decision is fine; a multi-section spec with
"Validation"/"Testing gotchas" subsections is also fine when there's real
substance to record (see `docs/specs/alembic-migrations.md` for an example
with more sections).}
```

No fixed section list, no `Status` frontmatter, no strict length cap — match
the depth of the existing files in `docs/specs/`, not the shorter upstream
ADR template.

## Naming and cross-referencing

- Filename: `docs/specs/<kebab-case-topic>.md` (e.g. `api-design.md`,
  `alembic-migrations.md`), not a sequential number.
- After creating one, add it to the "Specs" list in `docs/ROADMAP.md` and
  link it from the relevant `docs/roadmap-<area>.md` entry — same pattern
  as the existing specs.

## When to record one

All three of these must be true (unchanged from upstream):

1. **Hard to reverse**: the cost of changing your mind later is meaningful
2. **Surprising without context**: a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing" — this is also `CLAUDE.md`'s existing rule: "write a new spec only for a genuinely non-obvious design decision... not for mechanical additions."

### What qualifies

- **Architectural shape.** E.g. "migrations go through Alembic, not `create_all()`."
- **Technology/integration choices that carry lock-in.** Auth model, DB migration tool, frontend stack — not every library, just the ones costly to swap.
- **Boundary and scope decisions.** E.g. "`api/schemas.py` is a separate contract from `bot/db/models.py`, on purpose."
- **Deliberate deviations from the obvious path.** Anything where a reasonable reader would assume the opposite.
- **Constraints not visible in the code.** E.g. Telegram's 4096-character message limit forcing pagination in the bot.
- **Rejected alternatives when the rejection is non-obvious.**
