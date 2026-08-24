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

# Run the API locally (needs the same .env as the bot)
uvicorn api.main:app --reload   # docs at http://localhost:8000/docs

# Web frontend (web/) — Vite + React + TypeScript, needs the API running
# (see above) and its own web/.env (copy web/.env.example)
cd web && npm install
npm run dev     # dev server at http://localhost:5173
npm run build   # tsc -b && vite build
npm run test    # vitest run — see "Web frontend tests" below
npm run test:watch
```

There is no linter/formatter configured in this repo (the `web/` frontend has `oxlint` from the Vite scaffold, but it isn't wired into any workflow).

### Configuration

`bot/core/settings.py` reads env vars at import time (via `.env`, loaded with `python-dotenv`) and **raises immediately** if required ones are missing. This means importing almost anything under `bot/` requires these to already be set:

- `TELEGRAM_TOKEN` — required.
- `DATABASE_URL`, or the pair `DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`/`DB_NAME` — required (Postgres in production).
- `ADMIN_USER_IDS` — comma-separated Telegram user IDs; if empty, **all** admin commands are denied (fails closed, see `bot/decorators.py`).
- `TIMEZONE_NAME` — optional, defaults to `America/Sao_Paulo`.
- `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_SENDER`/`EMAIL_SENDER_PASSWORD`/`EMAIL_RECEIVER` — optional, only needed for `/bug` reports to actually send.
- `FRONTEND_ORIGINS` — optional, comma-separated list of origins allowed by the API's CORS middleware (`api/main.py`); defaults to `http://localhost:5173` (the Vite dev server).

For local testing without Postgres or a real Telegram bot, `DATABASE_URL=sqlite:///./dev.db` works (`bot/db/base.py` switches pool settings for sqlite) and `TELEGRAM_TOKEN` just needs to be non-empty — it's only actually called against the Telegram API by the bot process and by `/auth/telegram`'s signature check, not by anything else.

`tests/conftest.py` sets safe defaults for these via `os.environ.setdefault(...)` at the very top of the file, before any `bot.*` import, specifically so the test suite doesn't need a real `.env`.

See `docs/ROADMAP.md` for an index into per-area roadmaps (`docs/roadmap-bot.md`, `-api.md`, `-app.md`, `-hosting.md`) and design specs (`docs/specs/`) — what's already been implemented, known gaps, and next steps for each area. Update the relevant roadmap file when you finish or defer something; write a new spec only for a genuinely non-obvious design decision, not for mechanical additions.

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

### API (`api/`)

A FastAPI app that exposes `bot/services/` over HTTP, for the web site (`web/`, below) and the (future) React Native app — it's a second, independent consumer of the same services layer that `bot/handlers/` already uses, not a rewrite of anything. `api/main.py` is the ASGI app; `api/deps.py` has the two shared dependencies (`get_db`, `get_current_user`); `api/routers/*.py` are one file per resource; `api/schemas.py` has the Pydantic response models (kept separate from `bot/db/models.py` on purpose, so a DB column change doesn't silently change the API contract).

- **Two ways to get a Bearer token**: a personal access token (`/tokendeacesso` in the bot, `bot/handlers/user_settings_handler.py`, via `access_token_service.create_access_token` — meant for the app/personal use), or the Telegram Login Widget (`POST /auth/telegram`, meant for the site — see `docs/specs/api-design.md` and `docs/specs/frontend-web-and-app.md`). Both end up as the same kind of `AccessToken` row; only its SHA-256 hash is stored (`AccessToken.token_hash`), so a personal-access-token plaintext is shown exactly once and can't be recovered — `/revogartokens` deletes all of a user's tokens if one leaks. Send it as `Authorization: Bearer <token>`; `api/deps.get_current_user` resolves it back to a `User` via `access_token_service.get_user_by_token`.
- Adding an endpoint = add a Pydantic schema in `api/schemas.py`, a router function in `api/routers/` that takes `user: User = Depends(get_current_user)` (and `db: Session = Depends(get_db)` if it needs to query more than `user` itself), call the matching `bot/services/*` function, and `include_router(...)` it in `api/main.py`.
- **CORS**: `api/main.py` adds `CORSMiddleware` allowing the origins in `bot/core/settings.FRONTEND_ORIGINS` (env var, default `http://localhost:5173`). No `allow_credentials` — auth is Bearer-token-in-header, not cookie-based, so the browser doesn't need cross-origin credentialed requests.

### Web frontend (`web/`)

A Vite + React + TypeScript SPA consuming `api/` — the site half of `docs/specs/frontend-web-and-app.md` (the React Native app hasn't been started). No UI component library; plain CSS (`src/index.css`) with CSS custom properties for light/dark.

- **`src/api/`**: `types.ts` mirrors `api/schemas.py` by hand (kept as a separate contract on purpose, same reasoning as the schemas/models split in the backend); `client.ts` is a thin `fetch` wrapper that attaches `Authorization: Bearer <token>` from `localStorage` and throws `ApiError` on non-2xx (message pulled from the response's `detail`); `resources.ts` has one function per `api/routers/*.py` endpoint. Adding a backend endpoint = add its type(s) to `types.ts` and a function to `resources.ts`.
- **Auth** (`src/auth/`): `AuthContext` holds `user`/`login`/`logout`, backed by the token in `localStorage`. `client.ts` dispatches a `jovis:unauthorized` `window` event on any `401`; `AuthContext` listens for it and clears `user`, which `RequireAuth` (route wrapper) turns into a redirect to `/login`. `TelegramLoginButton` injects the official Telegram widget `<script>` tag pointed at `VITE_TELEGRAM_BOT_USERNAME` and wires its callback to `AuthContext.login`, which calls `POST /auth/telegram` and stores the returned token — same flow as the backend's Login Widget support.
- **Pages** (`src/pages/`): one per resource (`Subjects`, `Activities`, `Absences`, `Grades`) follow the same shape — a list (TanStack Query `useQuery`) plus an inline create/edit `<form class="panel">` (not a modal) toggled by local `editingId: number | 'new' | null` state, with `useMutation` invalidating the list query on success. Copy this shape for a new resource page. Backend validation errors (e.g. the `409` schedule conflict on `Subjects`) surface via `ApiError.message` in an `ErrorBanner` scoped to the form, not the whole page.
- **Config**: `web/.env` (gitignored, copy from `.env.example`) needs `VITE_API_URL` (the FastAPI base URL) and `VITE_TELEGRAM_BOT_USERNAME` (the bot's `@username`, without the `@`, for the Login Widget).

#### Web frontend tests

Vitest + React Testing Library + jsdom (`web/vite.config.ts`'s `test` block, `web/src/test/setup.ts` for jest-dom matchers and per-test `localStorage`/DOM cleanup). `web/.env.test` pins `VITE_API_URL`/`VITE_TELEGRAM_BOT_USERNAME` to fixed dummy values so tests don't depend on a developer's local `web/.env` — Vitest defaults to Vite's `test` mode, which loads `.env.test` automatically.

Coverage is intentionally not exhaustive across the 4 CRUD pages (Matérias/Atividades/Faltas/Notas share one list+inline-form shape — see "Pages" above): `src/api/client.test.ts` covers the `fetch` wrapper (auth header, 401 → clear token + `UNAUTHORIZED_EVENT`, error `detail` parsing, 204 handling); `src/auth/AuthContext.test.tsx` covers the login/logout/session-refresh state machine; `src/pages/Subjects.test.tsx` is a full component test of the list+form+delete pattern, including the `409` schedule-conflict path, and stands in as the reference for testing another page the same way — it isn't duplicated onto Activities/Absences/Grades. All three files `vi.mock('../api/resources')` rather than mocking `fetch` directly, so tests assert on which resource function was called with which payload, not on request wiring.

Schema changes go through Alembic (`migrations/`), not `Base.metadata.create_all()` — `main.py` no longer calls it. `migrations/env.py` imports `bot.db.base.Base` + `bot.db.models` and sets `sqlalchemy.url` from `bot.core.settings.DATABASE_URL` at runtime (nothing hardcoded in `alembic.ini`), so it always uses the same env vars as the app itself.

- After changing a model in `bot/db/models.py`: `alembic revision --autogenerate -m "..."`, review the generated file in `migrations/versions/` (autogenerate misses some things — renames look like drop+add, server-side defaults, etc.), then `alembic upgrade head`.
- Adopting Alembic on a database that already has the tables (created before this existed, via the old `create_all()`): run `alembic stamp head` once instead of `upgrade head` — it marks the DB as current without re-running `CREATE TABLE` on tables that already exist. Confirmed working end-to-end against a real Postgres container (autogenerate → upgrade → `alembic check` reports no drift → downgrade to base cleanly → simulate a pre-Alembic DB via `create_all()` → `stamp head` leaves data untouched and `alembic check` still reports no drift).
- `seed_db.py` no longer calls `create_all()` either — it assumes migrations have already been run.

### Testing gotchas

- `bot/db/base.py` forces `poolclass=StaticPool` + `connect_args={"check_same_thread": False}` whenever `DATABASE_URL` starts with `sqlite` (tests only — Postgres in production is unaffected). Without this, SQLite's default per-thread pool gives FastAPI's `TestClient` (which runs the ASGI app in its own thread) a completely separate, empty in-memory database from the one the test's `db` fixture set up — surfaces as `sqlite3.OperationalError: no such table: ...` from inside API test requests, not from the fixture itself. `StaticPool` makes every thread share the one connection instead.
- SQLite does **not** preserve `tzinfo` on `DateTime(timezone=True)` columns (Postgres does, via `TIMESTAMPTZ`); tests touching `Reminder.remind_at` compare with `.replace(tzinfo=None)` on both sides to sidestep this SQLite-only quirk.
- No local Postgres binary in this environment, but `docker run postgres:16-alpine` works and is the way to validate anything migration/Postgres-type-related for real instead of trusting SQLite's looser typing.
- `api/` tests use FastAPI's `TestClient` (`tests/test_api.py`) — real HTTP requests through the actual ASGI app, reusing the same `db`/`user` fixtures as the service tests. No mocking needed, unlike the Telegram handlers.
- Table creation (`Base.metadata.create_all`) is a **session-scoped `autouse` fixture** (`tests/conftest.py:_create_tables`), not something only the `db` fixture does. It used to live inside `db`, which broke any test that hits the database without requesting `db` itself — e.g. an API test that only checks "invalid token → 401" never triggers `db`, so run alone (or before any `db`-using test) it hit a SQLite database with no tables yet at all. Session-scoped `autouse` guarantees tables exist before the first test regardless of which tests ran or in what order.

### Editor tooling gotcha

- The file-write tool preserves an existing file's on-disk encoding when overwriting it — editing `requirements.txt` (historically UTF-16, likely from `pip freeze` on Windows PowerShell) through it silently re-wrote UTF-16 even with UTF-8 content, which breaks `pip` (`Invalid requirement` with literal `\x00` bytes in the error). It was converted to plain UTF-8 when Alembic was added (git history has both versions if you need to compare). If a similar non-UTF-8 file ever needs an encoding fix, overwrite it via a shell heredoc (`cat > file << 'EOF' ... EOF`) instead of the normal edit path, then verify with `file <path>`.
