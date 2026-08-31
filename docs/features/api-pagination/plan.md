# Plan: Pagination for the API's listing endpoints

**Status:** Draft — assumes the recommended answer to `spec.md`'s open
question (envelope only when `page`/`page_size` are sent). Revise this plan
if the final decision is different.

Prerequisite: [`spec.md`](spec.md).

## Layers affected

- [ ] `api/schemas.py` — new generic pagination envelope schema
- [ ] `api/routers/subjects.py`, `activities.py`, `absences.py`,
      `grades.py` — `page`/`page_size` query params
- [ ] `bot/services/*` — **unchanged**: services already return full lists
      (`db.query(...).all()`), pagination is the HTTP layer's
      responsibility, not the service's (the bot doesn't need it)
- [ ] `web/src/api/types.ts` + `resources.ts` — only if/when the site
      adopts pagination in the UI (out of scope for this slice; the API
      is ready, the site's consumption comes later)

## Design

- Query params `page` (1-indexed, absent by default = current behavior) and
  `page_size` (default 20 when `page` is sent without `page_size`, cap
  100).
- When `page` is sent: the response becomes `{"items": [...], "total": N,
  "page": P, "page_size": S}` instead of the bare list. When `page` is
  omitted: the response stays the current bare list — **a dual contract,
  kept only until existing consumers (the site) migrate, then it becomes
  always-envelope in a future slice.**
- `page`/`page_size` validation (`>0`, `page_size` ≤ 100) via FastAPI's
  `Query(gt=0, ...)` — automatic 422 from Pydantic, no manual validation
  needed.
- Implemented once in `api/deps.py` (a `paginate(query, page, page_size)`
  helper that takes the SQLAlchemy query before `.all()`) and reused across
  the 4 routers — same pattern as the already-shared `get_owned_subject`
  (see `docs/architecture/api.md`).

## Non-obvious decisions

The dual contract (bare list vs. envelope, depending on whether `page` was
sent) is a conscious transitional choice, not the desired end state — if
that's still true by the time this feature is implemented, it's worth a
spec in `docs/specs/` explaining why and the criteria for migrating to
always-envelope.

## Risks / trade-offs

- Two possible response shapes for the same endpoint is a real gotcha for
  anyone consuming the API without knowing about it — mitigated by
  documenting it explicitly in `docs/architecture/api.md` once
  implemented.
- The extra `COUNT(*)` per page costs one extra query per request —
  acceptable at the expected volume (see "Out of scope" in `spec.md`).
