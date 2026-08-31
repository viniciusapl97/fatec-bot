# Roadmap — Bot (Telegram)

See [`ROADMAP.md`](ROADMAP.md) for the general index across areas.

Last updated: 2026-08-21.

## ✅ Done

A full code review (2026-08-21) found and fixed 4 critical bugs that broke
the bot in production:
- `dialogs.py` was missing several constants referenced by
  `activity_handler.py` and `subject_handler.py` — `/gerenciartrabalhos` and
  `/gerenciarprovas` were 100% broken (`AttributeError`).
- `/cancelar` was broken in `/broadcast`, `/lembrar`, and `/bug` (the
  fallback passed a `dialogs` string as the `CommandHandler`'s callback
  instead of a function).
- Fake `Update`/`CallbackQuery` hacks in `activity_handler.py` and
  `grade_handler.py` that broke when reloading the screen after editing an
  activity or a grade.

After fixing the bugs, implemented in this order:

1. Timezone (`America/Sao_Paulo`) applied via `Defaults(tzinfo=...)` — fixed
   the daily deadline reminder, which was firing at the wrong time.
2. `conversation_timeout` (10 min) on every `ConversationHandler` — prevents
   an abandoned conversation from staying stuck forever.
3. Persistence of custom reminders (`/lembrar`) — used to live only in
   memory and vanish on a restart; now they live in the `reminders` table
   and get rescheduled on startup
   (`main.py:reschedule_pending_reminders`).
4. Attendance `%` per subject (optional `total_classes` field +
   `subject_service.get_attendance_info`) and grade average
   (`grade_service.get_average`) — shown in `/faltas`, `/relatorio`, and
   `/gerenciarnotas`.
5. `/exportar` — downloads a JSON with everything belonging to the user
   (subjects, activities, absences, grades, pending reminders).
6. Unit test suite (`tests/`, pytest, in-memory SQLite) covering the whole
   `bot/services/` layer.
7. `CLAUDE.md` and `docs/ROADMAP.md`.
8. `/meuslembretes` — lists the user's pending reminders with a cancel
   button for each; canceling removes both the DB record and the in-memory
   scheduled job (`job_queue.get_jobs_by_name` + `schedule_removal()`),
   otherwise the reminder would still fire even after being canceled.
9. `/privacidade` — actually implemented (previously only mentioned in
   `/help`, with no handler). Text lives in `dialogs.PRIVACY_POLICY_TEXT`,
   informational rather than a formal legal policy — revise/update it if
   what the bot collects or shares changes.
10. Schedule conflict handling in manual `/addmateria` — new
    `subject_service.check_conflict_with_existing` (same overlap logic as
    `course_service.check_schedule_conflict`, but compared against the
    user's already-registered subjects instead of the catalog). On a
    conflict, it says which subject collides and asks for a new start time
    (goes back to the `START_TIME` conversation state).
11. Editing a subject's schedule in `/gerenciarmaterias` — the
    `start_time`/`end_time` conversion/validation logic already existed in
    `receive_field_update` (unused, the buttons were missing). Added the
    "Start Time"/"End Time" buttons in `build_subject_edit_view`, and
    editing now goes through the same conflict check from item 10 —
    `check_conflict_with_existing` gained the `exclude_subject_id`
    parameter so a subject doesn't collide with itself.
12. Automatic weekly summary — the `send_weekly_summary_job` job
    (`bot/jobs.py`) runs every Monday at 08:00 (`job_queue.run_daily(...,
    days=(1,))`; heads up: in python-telegram-bot v20+, `days` is
    0-6=Sunday-Saturday, not the old Monday-Sunday convention) and sends
    every registered user the same summary as `/semana`. Extracted
    `build_week_summary_message(db, user)` from `common.py` so it can be
    reused by both the command and the job.
13. `/notificacoes` — toggles automatic deadline reminders per user
    (`User.notifications_enabled`, default `True`). Command + toggle
    button; `check_deadlines_job` skips anyone who opted out via
    `user_service.get_user_ids_with_notifications_disabled`. **Bonus: found
    and fixed a real, pre-existing bug while testing this** —
    `check_deadlines_job` called
    `activity_service.get_upcoming_activities`, but that function had
    always been defined in `user_service.py`, not
    `activity_service.py`. The daily deadline-reminder job had been
    throwing an `AttributeError` (swallowed by APScheduler) every time it
    ran — the "due tomorrow"/"due in 3 days" reminders had never actually
    been delivered in production. Fixed.
14. `/exportarcalendario` — generates a `.ics` (iCalendar/RFC 5545) file
    with the user's assignments and exams, to import into Google
    Calendar/Apple Calendar/Outlook. It's a point-in-time snapshot
    (downloadable), not a live subscription — the bot has no public HTTP
    server to host a calendar URL that apps could re-sync on their own.
    Built by hand in `export_service.build_activities_ics` (RFC 5545
    escaping and line folding implemented from scratch, no new dependency).
    **Real bug found and fixed**: the first version of the handler built
    the `.ics` outside the `with SessionLocal()` block, and since that
    accesses `activity.subject.name` (lazy load), it broke with
    `DetachedInstanceError` as soon as the session closed.
15. `/stats` for admins — general counts
    (`bot/services/stats_service.py`): registered users, subjects,
    activities (assignments/exams separated), absence records, grades
    entered, pending reminders. **Scope note:** `User` doesn't store a
    registration or last-access date, so "active users" here means "total
    ever registered", not "recently active".
16. Configurable notification time per user
    (`/horarionotificacao`) — a 0h-23h button grid,
    `User.notification_hour` (default 9). Changed the deadline job's
    architecture: it used to run once a day at a fixed 9am for everyone,
    now it runs hourly (`run_repeating`) and internally filters for whoever
    has `notification_hour == current_hour`.
17. Pagination in `/grade` and `/calendario` — **automatic**, doesn't
    change anything for someone with few subjects/activities (the common
    case): it only kicks in if the whole message wouldn't fit Telegram's
    4096-character limit. `/calendario` paginates by a fixed item count
    (`ACTIVITIES_PER_PAGE = 10`); `/grade` paginates by **weekday**
    (`SUBJECT_DAYS_PER_PAGE = 2`) so a day's subjects are never split
    across two pages. Manually validated by forcing 32 subjects and 62
    activities — no generated page ever exceeds 4096 characters.
18. Migrations with Alembic — replaces `Base.metadata.create_all()`. Full
    details, including the adoption step needed for an existing dev
    database, in
    [`specs/alembic-migrations.md`](specs/alembic-migrations.md).

See `git log` for the full commit history of each item.

## 🔭 Pending

- Handler/integration tests (deliberately out of scope for the current test
  suite — would require mocking a lot of `python-telegram-bot`'s API; the
  `services/` layer concentrates the testable business logic and is reused
  1:1 by the API — see [`roadmap-api.md`](roadmap-api.md)).
