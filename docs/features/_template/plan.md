# Plan: <feature name>

Prerequisite: [`spec.md`](spec.md) with closed acceptance criteria.

## Layers affected

- [ ] `bot/db/models.py` (+ Alembic migration — see
      `docs/architecture/data.md`)
- [ ] `bot/services/`
- [ ] `bot/handlers/`
- [ ] `bot/core/dialogs.py`
- [ ] `api/schemas.py` + `api/routers/`
- [ ] `web/src/api/` (`types.ts` + `resources.ts`) + `web/src/pages/`

Delete the lines that don't apply.

## Design

New/changed contract(s) — service function signature, endpoint (method +
path + request/response), DB column, etc. Reference the existing pattern
being followed (e.g. "same pagination shape as X", "same `_to_out()`
pattern as `api/routers/subjects.py`") instead of re-explaining from
scratch — see `docs/architecture/` for the already-documented patterns.

## Non-obvious decisions

If any choice here isn't obvious from the code (why this approach and not
another), consider creating a spec in `docs/specs/` and linking it from
here — see `docs/features/README.md`.

## Risks / trade-offs

What could go wrong, or what's being consciously left aside.
