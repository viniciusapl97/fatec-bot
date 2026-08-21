# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
pip install -r requirements.txt          # runtime deps only
pip install -r requirements-dev.txt      # runtime deps + pytest, for local dev

# Create/update the schema (Alembic — see "Migrations" below). Required before
# first run and after pulling any migration that isn't applied yet.
alembic upgrade head

# Run the bot (needs a .env — see "Configuration" below)
python main.py

# Seed the Fatec course catalog (data/courses.json -> course_subjects table)
# Needed for the /fatec onboarding flow to have anything to offer. Assumes
# tables already exist (run migrations first).
python seed_db.py

# Tests (SQLite in-memory, no Postgres/Telegram token needed — see tests/conftest.py)
pytest
pytest tests/test_subject_service.py                              # one file
pytest tests/test_subject_service.py::test_get_attendance_info_ok_status  # one test
```

There is no linter/formatter configured in this repo.

### Configuration

`bot/core/settings.py` reads env vars at import time (via `.env`, loaded with `python-dotenv`) and **raises immediately** if required ones are missing. This means importing almost anything under `bot/` requires these to already be set:

- `TELEGRAM_TOKEN` — required.
- `DATABASE_URL`, or the pair `DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`/`DB_NAME` — required (Postgres in production).
- `ADMIN_USER_IDS` — comma-separated Telegram user IDs; if empty, **all** admin commands are denied (fails closed, see `bot/decorators.py`).
- `TIMEZONE_NAME` — optional, defaults to `America/Sao_Paulo`.
- `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_SENDER`/`EMAIL_SENDER_PASSWORD`/`EMAIL_RECEIVER` — optional, only needed for `/bug` reports to actually send.

`tests/conftest.py` sets safe defaults for these via `os.environ.setdefault(...)` at the very top of the file, before any `bot.*` import, specifically so the test suite doesn't need a real `.env`.

See `docs/ROADMAP.md` for what's already been implemented, known gaps/bugs, and suggested next steps — keep it updated when you finish or defer something.

## Architecture

Layered: **Handlers** (`bot/handlers/`) receive Telegram updates and call **Services** (`bot/services/`), which hold all business logic and DB queries against **Models** (`bot/db/models.py`). Services never import `telegram` or `bot.core.dialogs` — they take a SQLAlchemy `Session` as their first argument and return plain model objects/dicts. All user-facing text lives in `bot/core/dialogs.py` as module-level string constants (grouped by feature in commented sections); handlers format and send these, never hardcode text inline.

### Conversation handler pattern

Every multi-step flow (`/addmateria`, `/faltei`, `/lembrar`, `/fatec`, etc.) is a `ConversationHandler` with a consistent shape — copy this shape when adding a new one:

- **Dual entry points**: a `CommandHandler` for the slash command *and* a `CallbackQueryHandler` (pattern-matched `callback_data`) for the equivalent inline-menu button, both routed to the same start function. That function checks `update.callback_query` vs `update.message` to decide whether to `edit_message_text` or `reply_text`/`reply_html`.
- **State constants** are module-level ints from `range(...)`. Each handler file claims its own numeric block (e.g. `subject_handler.py` uses `range(8)` then `range(10, 14)` then `20`; `activity_handler.py` uses `range(20, 24)` then `range(30, 34)`; `absence_handler.py` uses `range(40, 44)` then `range(44, 49)`; `grade_handler.py` uses `range(50, 53)` then `range(53, 58)`) purely as a convention to keep them visually distinct across files — when adding a new conversation, pick an unused block rather than reusing `0`-`N`.
- **`fallbacks=[CommandHandler("cancelar", xxx_cancel)]`** — `xxx_cancel` must be an actual async function. Passing a `dialogs.*` string directly as the callback was a real bug fixed 3 times (`admin_handler.py`, `reminder_handler.py`, `bug_report_handler.py`) — `CommandHandler` calls its callback, so a string blows up with `TypeError: 'str' object is not callable`.
- **`states` always includes `ConversationHandler.TIMEOUT: [TypeHandler(Update, notify_conversation_timeout)]`**, and the handler is built with `conversation_timeout=CONVERSATION_TIMEOUT_SECONDS` (both from `bot/core/conversation_timeout.py`). Without this, an abandoned conversation stays stuck in its state forever and unrelated commands sent afterward get silently swallowed.
- **Reloading a menu after an in-place edit**: never fabricate a fake `Update`/`CallbackQuery` object to re-invoke another handler function (`type('CallbackQuery', (), {...})()` — this was a real, repeated bug: the faked object lacks real methods like `edit_message_text`, and `await fake.answer()` on a plain lambda raises `TypeError` since it's not a coroutine). Instead, extract a `build_xxx_view(...) -> (text, reply_markup)` helper (see `build_subject_edit_view` in `subject_handler.py`, `build_activity_edit_view` in `activity_handler.py`, `build_grades_list_view` in `grade_handler.py`) and call it directly from both the original render path and the reload-after-edit path.

### Cross-cutting pieces

- **`user_service.get_or_create_user(db, telegram_user.id, first_name, username)`** is called at the top of nearly every handler — Telegram's user ID is the only stable identity, so the local `User` row is lazily provisioned on first contact.
- **Timezone**: `bot/core/settings.TIMEZONE` is applied globally via `Defaults(tzinfo=TIMEZONE)` on the `Application` in `main.py`, so naive `datetime.time`/`datetime.datetime` values passed to `job_queue.run_daily`/`run_once` are interpreted in that zone automatically. `dateparser` (used in `reminder_handler.py` to parse free-text times like "amanhã às 14h") does *not* know about PTB's `Defaults`, so it's called with an explicit `settings={'TIMEZONE': ..., 'TO_TIMEZONE': ..., 'RETURN_AS_TIMEZONE_AWARE': True}`.
- **Reminder persistence**: `Reminder` rows (`bot/db/models.py`) only exist while pending — the delivery job deletes its own row immediately after sending. `bot/handlers/reminder_handler.py:schedule_reminder()` is the single function used both when a user creates a reminder *and* by `main.py:reschedule_pending_reminders()` at startup, because `JobQueue`/APScheduler jobs live only in memory and are lost on every process restart.
- **`CourseSubject` vs `Subject`**: `CourseSubject` is a shared, global catalog table (course/shift/semester → subject template) populated by `seed_db.py` from `data/courses.json`, used only by the `/fatec` onboarding (`fatec_handler.py` + `course_service.py`) to bulk-create a specific student's real, per-user `Subject` rows via `subject_service.bulk_create_from_course_subjects`. Don't confuse the two.
- **Admin commands** (`/broadcast`, `/enviar`) are gated by `@admin_only` (`bot/decorators.py`), which checks membership in `ADMIN_USER_IDS`.

### Migrations (Alembic)

Schema changes go through Alembic (`migrations/`), not `Base.metadata.create_all()` — `main.py` no longer calls it. `migrations/env.py` imports `bot.db.base.Base` + `bot.db.models` and sets `sqlalchemy.url` from `bot.core.settings.DATABASE_URL` at runtime (nothing hardcoded in `alembic.ini`), so it always uses the same env vars as the app itself.

- After changing a model in `bot/db/models.py`: `alembic revision --autogenerate -m "..."`, review the generated file in `migrations/versions/` (autogenerate misses some things — renames look like drop+add, server-side defaults, etc.), then `alembic upgrade head`.
- Adopting Alembic on a database that already has the tables (created before this existed, via the old `create_all()`): run `alembic stamp head` once instead of `upgrade head` — it marks the DB as current without re-running `CREATE TABLE` on tables that already exist. Confirmed working end-to-end against a real Postgres container (autogenerate → upgrade → `alembic check` reports no drift → downgrade to base cleanly → simulate a pre-Alembic DB via `create_all()` → `stamp head` leaves data untouched and `alembic check` still reports no drift).
- `seed_db.py` no longer calls `create_all()` either — it assumes migrations have already been run.

### Testing gotchas

- `bot/db/base.py`'s exact `create_engine(DATABASE_URL, pool_pre_ping=True)` call works fine against `sqlite:///:memory:` for tests — SQLAlchemy auto-selects `SingletonThreadPool` for in-memory SQLite, so state persists across multiple `SessionLocal()` calls within the same thread/test.
- SQLite does **not** preserve `tzinfo` on `DateTime(timezone=True)` columns (Postgres does, via `TIMESTAMPTZ`); tests touching `Reminder.remind_at` compare with `.replace(tzinfo=None)` on both sides to sidestep this SQLite-only quirk.
- No local Postgres binary in this environment, but `docker run postgres:16-alpine` works and is the way to validate anything migration/Postgres-type-related for real instead of trusting SQLite's looser typing.

### Editor tooling gotcha

- The file-write tool preserves an existing file's on-disk encoding when overwriting it — editing `requirements.txt` (historically UTF-16, likely from `pip freeze` on Windows PowerShell) through it silently re-wrote UTF-16 even with UTF-8 content, which breaks `pip` (`Invalid requirement` with literal `\x00` bytes in the error). It was converted to plain UTF-8 when Alembic was added (git history has both versions if you need to compare). If a similar non-UTF-8 file ever needs an encoding fix, overwrite it via a shell heredoc (`cat > file << 'EOF' ... EOF`) instead of the normal edit path, then verify with `file <path>`.
