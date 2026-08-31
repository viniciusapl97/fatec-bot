# Architecture — deep-dive docs

This folder holds the detailed, per-area reference that used to live entirely
inside `CLAUDE.md`. `CLAUDE.md` (repo root) keeps only what every session
needs regardless of task; these files are the "read only if you're touching
this area" layer, kept out of the always-loaded context on purpose (token
economy — a session doing web frontend work shouldn't pay for the Telegram
conversation-handler pattern, and vice versa).

Everything under `docs/` is in English (token economy — English tokenizes
more efficiently for LLMs than Portuguese for the same content, and it's the
language every other doc here — `CLAUDE.md`, `docs/roadmap-*.md`,
`docs/specs/`, `docs/features/` — already uses). The bot's actual
user-facing text and commands (`bot/core/dialogs.py`, `/addmateria`, etc.)
stay in Portuguese, since that's the product's real language — only the
documentation *about* the code is in English.

- [`bot.md`](bot.md) — layering, the `ConversationHandler` pattern, cross-cutting
  bot pieces (timezone, reminders, `CourseSubject` vs `Subject`, admin gating).
- [`api.md`](api.md) — `api/` (FastAPI): auth, adding an endpoint, CORS.
- [`web.md`](web.md) — `web/` (Vite + React): API client, auth, page pattern, tests.
- [`data.md`](data.md) — Alembic migrations workflow + testing gotchas
  (SQLite `StaticPool`, tzinfo, `autouse` table creation).
- [`configuration.md`](configuration.md) — env vars read by `bot/core/settings.py`.
- [`glossary.md`](glossary.md) — domain-term disambiguation (`CourseSubject` vs
  `Subject`, `Activity` types, `AccessToken` origins, etc.).
- [`tooling-gotchas.md`](tooling-gotchas.md) — editor/tooling quirks unrelated to
  the app's own architecture (e.g. file-encoding on overwrite).

Update the relevant file here when you change how something in that area
works — same rule as `docs/roadmap-*.md`, just for "how it works" instead of
"what's been done".
