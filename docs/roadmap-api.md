# Roadmap — API (`api/`)

See [`ROADMAP.md`](ROADMAP.md) for the general index across areas, and
[`specs/api-design.md`](specs/api-design.md) for the design decisions
(authentication, schema separation, testing gotchas found).

Last updated: 2026-08-21.

## ✅ Done

1. **First API slice** (2026-08-21) — FastAPI exposing `bot/services/` over
   HTTP, without duplicating any logic:
   - Authentication via personal access token. New `AccessToken` model
     (`bot/db/models.py`), `/tokendeacesso` (generates, shows once) and
     `/revogartokens` (invalidates all at once) commands on the bot.
     Migration `e00d525f47d4_adiciona_access_tokens`.
   - Endpoints: `GET /health` (no auth), `GET /me`, `GET /subjects`.
   - `api/deps.py` (shared dependencies `get_db`/`get_current_user`),
     `api/schemas.py` (Pydantic response models).
   - 12 new tests (`tests/test_access_token_service.py`,
     `tests/test_api.py`).
2. **More read endpoints** (2026-08-21):
   - `GET /activities` — accepts `?activity_type=trabalho|prova`.
   - `GET /absences` — new `absence_service.get_absences_by_user` (used to
     only exist per-subject).
   - `GET /grades`.
   - All three embed `subject_name` in the response (assembled in the
     router, not a direct model attribute).
   - 9 new tests (2 in `tests/test_absence_service.py`, 7 in
     `tests/test_api.py`, including the case that exposed the test
     isolation bug documented in `specs/api-design.md`).
3. **Attendance and grades per subject** (2026-08-21):
   - `GET /subjects/{id}/attendance` — reuses
     `subject_service.get_attendance_info`; the percentage/remaining-absence
     fields come back `null` if the subject doesn't have `total_classes`
     set yet (same semantics as the bot).
   - `GET /subjects/{id}/grades` — the subject's grade list + average
     (`grade_service.get_average`), bundled into a single payload instead
     of flattened into the general `/grades` listing.
   - Both check ownership of the subject (`subject.user_id ==
     user.user_id`) and return 404 (not 403) both for a nonexistent
     subject and for another user's subject, so as not to leak which IDs
     exist.
   - 10 new tests in `tests/test_api.py`.
4. **Write endpoints** (2026-08-21) — POST/PATCH/DELETE for the 4
   entities, full CRUD parity with the bot:
   - Subjects: `POST /subjects`, `PATCH /subjects/{id}`,
     `DELETE /subjects/{id}`. Checks same-day schedule conflicts (409),
     just like `/addmateria`/editing on the bot — only when the resulting
     day+start+end (after merging the PATCH with the current value) are
     all defined. `PATCH` uses Pydantic's `exclude_unset` to update only
     the fields sent, distinguishing "field omitted" from "field sent as
     `null`" (used to clear `total_classes`).
   - Activities: `POST /activities`, `PATCH /activities/{id}` (including
     moving to another subject via `subject_id`), `DELETE
     /activities/{id}`. `activity_type` isn't editable (same rule as the
     bot — it's fixed at creation).
   - Absences: `POST /absences`, `PATCH /absences/{id}` (only `quantity`,
     same limitation as the bot), `DELETE /absences/{id}` — all three
     recompute `Subject.total_absences` via `absence_service` (not
     duplicated in the router).
   - Grades: `POST /grades`, `PATCH /grades/{id}` (name and value
     together, same signature as `grade_service.update_grade`), `DELETE
     /grades/{id}`.
   - Every endpoint that receives a `subject_id` (in the body or the URL)
     validates ownership with the new `api/deps.get_owned_subject` — 404 if
     the subject doesn't exist or belongs to another user. Moved from
     `subjects.py` to `deps.py` because activities/absences/grades also
     needed the same check.
   - 49 API tests in total now (`tests/test_api.py`), covering
     authentication, ownership, validation (invalid weekday, quantity ≤0,
     negative grade), and schedule conflicts.
5. **Telegram Login Widget** (2026-08-21) — `POST /auth/telegram`, login
   for the site (built ahead of the site itself, by explicit request — see
   [`specs/api-design.md`](specs/api-design.md) for the full decision):
   - Validates the widget payload's HMAC-SHA256 signature against
     `SHA256(TELEGRAM_TOKEN)`, rejects an `auth_date` older than 24h.
   - Doesn't create a new session mechanism: resolves the user via
     `user_service.get_or_create_user` and issues a regular `AccessToken`
     (same mechanism as the bot's `/tokendeacesso`) — the site later
     authenticates exactly like the app, via Bearer token.
   - 5 new tests in `tests/test_api.py` (new user, existing user, tampered
     payload, wrong hash, expired `auth_date`).

6. **CORS** (2026-08-24) — `CORSMiddleware` in `api/main.py`, allowing the
   React site's origin (`web/`, see [`roadmap-app.md`](roadmap-app.md)).
   New optional env var `FRONTEND_ORIGINS` (`bot/core/settings.py`),
   default `http://localhost:5173`. No `allow_credentials` — auth is via
   Bearer token, not cookies.
7. **`SubjectOut` gained the attendance-risk fields** (2026-08-24) —
   `percent`, `remaining_allowed`, `at_risk`, `failed` (the same fields as
   `AttendanceOut`) are now embedded in `GET/POST/PATCH /subjects`, not
   just `GET /subjects/{id}/attendance`. Reason: the risk banner on the
   site's dashboard (`roadmap-app.md`) needs this info for every subject
   at once, without N extra calls. `api/routers/subjects.py` gained a
   `_to_out()` (same pattern as the other routers) — the 3 endpoints used
   to return the SQLAlchemy `Subject` directly via `from_attributes`,
   which can't compute derived fields.

See `git log` for the full commit history of each item.

## 🎯 Next steps

- Decide whether listings get real pagination — the API doesn't have
  Telegram's 4096-character limit, but large lists still deserve
  pagination for performance/UX. Spec in progress (Draft):
  [`features/api-pagination/`](features/api-pagination/).
- Expiration/rotation for tokens issued by `/auth/telegram` — they don't
  have any yet (same mechanism as `/tokendeacesso`, which also doesn't
  expire). The site (`web/`, see [`roadmap-app.md`](roadmap-app.md))
  already stores the token in `localStorage`; the expiration decision was
  deferred.

## Operational reminder

Every time a new model is added (e.g. `AccessToken`), it needs a migration
— see [`specs/alembic-migrations.md`](specs/alembic-migrations.md).
