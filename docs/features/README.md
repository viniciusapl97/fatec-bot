# Features — spec-driven development

Workflow for planning a new feature (or a change big enough to deserve
planning before code) in a way that an AI agent — or you — can pick up the
full context without having to reconstruct decisions from the original
author's head.

This complements, not replaces, the system that already exists:

- **`docs/features/<slug>/`** (here) — a feature's plan *before/during*
  implementation: what to build, how, in what order.
- **`docs/roadmap-*.md`** — the condensed changelog per area (what's already
  shipped). When a feature is done, add an entry there pointing back to the
  feature folder.
- **`docs/specs/`** — design decisions that outlive the feature that
  triggered them (auth architecture, why Alembic, etc.) — not per-feature,
  per-decision. A feature may spawn a new spec if it makes a non-obvious
  call; most won't.
- **`docs/architecture/`** — how the existing code already works. A
  feature's `plan.md` references those files instead of re-explaining an
  already-documented pattern.

## When to create a feature folder

Worth it for anything touching more than one file/layer, or with a real
design decision (even a small one) — not for a one-line bug fix or "add one
more endpoint that just mirrors a service that already existed" (that's just
code + a roadmap entry).

## Workflow

1. **`spec.md`** — the what and why. Requirements, acceptance criteria, what's
   out of scope. Written before thinking about how to implement — if you
   can't write the acceptance criteria yet, the feature isn't clear enough
   to become code.
2. **`plan.md`** — the how. Technical design: which layers change
   (handler/service/model/migration/API/web), new contracts (endpoint,
   schema, DB column), trade-offs considered. This is also where a
   non-obvious decision should turn into a link to a new spec in
   `docs/specs/`, if warranted.
3. **`tasks.md`** — an ordered checklist, each item sized to be its own
   commit (or PR). An AI agent implementing the feature should be able to
   follow the list top to bottom without needing to re-read
   `spec.md`/`plan.md` at every step — the necessary context was already
   decided in the first two steps.
4. Implement, checking tasks off (`- [x]`) as you go.
5. When done (or abandoned), update the matching area's `roadmap-*.md` and
   change the `Status` at the top of `spec.md` (and `plan.md`/`tasks.md`, if
   they have one too) to `Done` (or `Abandoned`, with the reason).

The feature folder is **not deleted or moved** once done — it stays as a
historical record, just like `docs/specs/`. The `Status` at the top of each
file is what says whether it's still current.

## Starting a new feature

Copy `_template/` to `docs/features/<feature-slug>/` (short, kebab-case
slug, the same one across spec/plan/tasks) and fill in `spec.md` first.
Don't skip to `plan.md` before `spec.md` has concrete acceptance criteria.

Full worked example (a real feature, pending item already tracked in
`roadmap-api.md`, still `Draft`): [`api-pagination/`](api-pagination/).
