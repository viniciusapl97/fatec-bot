# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

It's kept intentionally short — it's loaded in full every session regardless
of task. Deep, per-area detail lives in `docs/architecture/` and is meant to
be read on demand, only when you're actually touching that area.

## Commands

```bash
# Setup
pip install -r requirements.txt          # runtime deps only
pip install -r requirements-dev.txt      # runtime deps + pytest, for local dev

# Create/update the schema (Alembic — see docs/architecture/data.md). Required
# before first run and after pulling any migration that isn't applied yet.
alembic upgrade head

# Run the bot (needs a .env — see docs/architecture/configuration.md)
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
npm run test    # vitest run — see docs/architecture/web.md
npm run test:watch
```

There is no linter/formatter configured in this repo (the `web/` frontend has `oxlint` from the Vite scaffold, but it isn't wired into any workflow).

## Documentation map

| Need | Doc |
|---|---|
| Env vars / `.env` | [`docs/architecture/configuration.md`](docs/architecture/configuration.md) |
| Bot handlers/conversations, cross-cutting bot pieces | [`docs/architecture/bot.md`](docs/architecture/bot.md) |
| API (`api/`) — auth, adding an endpoint, CORS | [`docs/architecture/api.md`](docs/architecture/api.md) |
| Web frontend (`web/`) — API client, auth, pages, tests | [`docs/architecture/web.md`](docs/architecture/web.md) |
| Migrations (Alembic) & testing gotchas | [`docs/architecture/data.md`](docs/architecture/data.md) |
| Domain terms (`CourseSubject` vs `Subject`, etc.) | [`docs/architecture/glossary.md`](docs/architecture/glossary.md) |
| Editor/tooling quirks (file encoding, etc.) | [`docs/architecture/tooling-gotchas.md`](docs/architecture/tooling-gotchas.md) |
| What's built, what's next, per area | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Non-obvious design decisions | [`docs/specs/`](docs/specs/) |
| **Planning a new feature** (spec → plan → tasks) | [`docs/features/README.md`](docs/features/README.md) |

Update the relevant `docs/roadmap-*.md` when you finish or defer something.
Write a new file in `docs/specs/` only for a genuinely non-obvious design
decision (not for mechanical additions), and update the matching
`docs/architecture/*.md` file whenever you change how something already
documented there works. For anything more than a one-file change, start from
`docs/features/README.md` instead of jumping straight to code — it links a
worked example.

## Architecture

Layered: **Handlers** (`bot/handlers/`) receive Telegram updates and call
**Services** (`bot/services/`), which hold all business logic and DB queries
against **Models** (`bot/db/models.py`). Services never import `telegram` or
`bot.core.dialogs` — they take a SQLAlchemy `Session` as their first argument
and return plain model objects/dicts. All user-facing bot text lives in
`bot/core/dialogs.py`. `api/` (FastAPI) and the future React Native app are
additional consumers of the same `bot/services/` — not a rewrite of
anything. `web/` (Vite + React) consumes `api/`. See the table above for
per-area detail.

### Rules that always apply, regardless of area

- **Conversation handler fallback**: `fallbacks=[CommandHandler("cancelar",
  xxx_cancel)]` — `xxx_cancel` must be an actual async function, never a
  `dialogs.*` string. Passing a string directly was a real bug fixed 3 times
  across different handlers — `CommandHandler` calls its callback, so a
  string blows up with `TypeError: 'str' object is not callable`.
- **Never fabricate a fake `Update`/`CallbackQuery`** object to reload a menu
  after an in-place edit — this was a real, repeated bug (the faked object
  lacks real methods like `edit_message_text`). Extract a `build_xxx_view(...)`
  helper instead and call it from both render paths. Details:
  [`docs/architecture/bot.md`](docs/architecture/bot.md).
- **Admin commands** (`/broadcast`, `/enviar`) are gated by `@admin_only`
  (`bot/decorators.py`) — fails closed if `ADMIN_USER_IDS` is empty.
- **`ConversationHandler`s always need `ConversationHandler.TIMEOUT`** wired
  to `notify_conversation_timeout`, or an abandoned conversation stays stuck
  forever. Details: [`docs/architecture/bot.md`](docs/architecture/bot.md).
