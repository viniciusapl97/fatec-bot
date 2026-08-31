# Tasks: <feature name>

Prerequisite: [`plan.md`](plan.md). Each item should be implementable and
testable on its own (commit/PR-sized); check `- [x]` off as you go.

- [ ] Migration (if `plan.md` touches `models.py`): `alembic revision
      --autogenerate -m "..."`, review the generated file, `alembic
      upgrade head`
- [ ] Service (`bot/services/`) + tests (`tests/test_*.py`)
- [ ] Handler (`bot/handlers/`) — if applicable
- [ ] API endpoint (`api/schemas.py` + `api/routers/`) — if applicable
- [ ] Web (`web/src/api/types.ts` + `resources.ts` + page) — if applicable
- [ ] API tests (`tests/test_api.py`) — if a new endpoint
- [ ] Web tests (`web/src/pages/*.test.tsx`, following the
      `Subjects.test.tsx` pattern) — if a new page
- [ ] Update `docs/roadmap-xxx.md` with the feature's entry
- [ ] Update `Status` in `spec.md` to `Done`
