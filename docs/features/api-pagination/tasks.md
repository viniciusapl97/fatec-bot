# Tasks: Pagination for the API's listing endpoints

**Status:** Draft — don't start implementation before the first task below
is resolved.

Prerequisite: [`plan.md`](plan.md).

- [ ] Resolve `spec.md`'s open question (always-envelope vs. opt-in) and
      update `Status` to `Approved` in `spec.md`, `plan.md`, and this file
- [ ] `api/deps.py`: `paginate(query, page, page_size)` helper
- [ ] `api/schemas.py`: pagination envelope schema
- [ ] `api/routers/subjects.py`: query params + conditional envelope
- [ ] `api/routers/activities.py`: same
- [ ] `api/routers/absences.py`: same
- [ ] `api/routers/grades.py`: same
- [ ] Tests in `tests/test_api.py`: full page, partial last page, page past
      the total, invalid `page`/`page_size` — for all 4 endpoints
- [ ] `docs/architecture/api.md`: document the pagination shape
- [ ] `docs/roadmap-api.md`: move the item from "Next steps" to "Done",
      link this folder
- [ ] `Status` in `spec.md`/`plan.md`/`tasks.md` to `Done`
