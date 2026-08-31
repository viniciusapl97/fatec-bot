# Glossary — domain terms

Quick disambiguation for terms that show up across layers and are easy to
confuse. Not a replacement for reading the model definitions in
`bot/db/models.py` — just the "wait, which one is that again" lookup.

- **`CourseSubject` vs `Subject`** — `CourseSubject` is a shared, global
  catalog table (course/shift/semester → subject template), populated by
  `seed_db.py` from `data/courses.json`, used only by the `/fatec`
  onboarding (`fatec_handler.py` + `course_service.py`) to bulk-create a
  specific student's real, per-user `Subject` rows via
  `subject_service.bulk_create_from_course_subjects`. Everything else in the
  app (bot commands, API, web) operates on `Subject`, never `CourseSubject`.
- **`Activity` types** — a single `Activity` model covers both `trabalho`
  (assignment) and `prova` (exam), distinguished by `activity_type`.
  `activity_type` is fixed at creation — not editable afterward, in both the
  bot (`activity_handler.py`) and the API (`PATCH /activities/{id}`).
- **`AccessToken`** — one model, two ways to mint one: the bot's
  `/tokendeacesso` command (personal use, app), and `POST /auth/telegram`
  (Telegram Login Widget, for the site). Both produce the same kind of row;
  the API/`get_current_user` never distinguishes which origin issued a given
  token. See [`api.md`](api.md).
- **User identity** — Telegram's numeric user ID (`telegram_user.id`) is the
  only stable identity across the whole app. The local `User` row is lazily
  created on first contact via `user_service.get_or_create_user`, called at
  the top of nearly every bot handler.
- **`Reminder`** — only exists in the DB while pending; the delivery job
  deletes its own row right after sending. Not a historical log of reminders
  ever created.
