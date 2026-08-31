# Roadmap — Index

Map of everything that exists, to keep context across sessions. Each area
has its own roadmap file (what's already done, what's left); design
decisions with real ambiguity (not mechanical changes) become a spec in
`specs/`, referenced from the roadmap of the matching area.

Update the roadmap of whichever area you touched when you finish or decide
to defer something. Only create a new spec when the decision isn't obvious
from the code — things like "why this lib and not that one", "why this
auth model", not "added one more endpoint that just mirrors a service that
already existed".

To plan a new feature before writing code, use [`features/`](features/)
(spec → plan → tasks) — see [`features/README.md`](features/README.md). To
understand how an existing area of the code already works (technical
reference), use [`architecture/`](architecture/).

Last reorganized: 2026-08-31 (added the `architecture/` and `features/`
folders, and moved all of `docs/` to English for token economy — see
`git log -- docs/` if you need the earlier history).

## Roadmaps by area

- [`roadmap-bot.md`](roadmap-bot.md) — the Telegram bot itself. 18 items
  delivered, 1 long-term pending item (handler/integration tests).
- [`roadmap-api.md`](roadmap-api.md) — HTTP API (`api/`) over
  `bot/services/`. Full CRUD (reads, attendance/average, writes) for the
  4 entities, plus the Telegram Login Widget (`POST /auth/telegram`) for
  the site; only pagination is left to decide.
- [`roadmap-app.md`](roadmap-app.md) — site (React) and Android/iOS app
  (React Native + widget). Not started yet; the API is what unblocks it.
- [`roadmap-hosting.md`](roadmap-hosting.md) — deployment. Still running
  locally; the combined plan is AWS free tier (EC2 + RDS), paused for now.

## Specs (design decisions)

- [`specs/alembic-migrations.md`](specs/alembic-migrations.md) — why
  Alembic, how to adopt it on a database that already exists, validation
  performed.
- [`specs/api-design.md`](specs/api-design.md) — API authentication
  (personal token vs. Login Widget), `api/schemas.py` vs.
  `bot/db/models.py` separation, testing gotchas found.
- [`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md) —
  chosen stack (React / React Native / Expo), why a home-screen widget
  always needs a native piece, site vs. app authentication.

## Features in planning (spec-driven development)

- [`features/api-pagination/`](features/api-pagination/) — pagination for the
  API's listing endpoints (`Draft`, see "Next steps" in
  [`roadmap-api.md`](roadmap-api.md)).
- [`features/discord-bot/`](features/discord-bot/) — a `discord_bot/`
  package as a second direct consumer of `bot/services/`, alongside `api/`.
  Full design closed in a `/grill-with-docs` planning session (`Draft`,
  ready for implementation): read-only v1, `discord.py`, and a
  `telegram_id`/`discord_id` identity model that lets a `User` originate
  on either platform and optionally link the other, without touching the
  6 tables that FK into `users.user_id` today. No `roadmap-discord.md` yet
  — gets created once the first slice ships (see the feature's `tasks.md`).

## Technical reference by area

- [`architecture/`](architecture/) — how each layer works today (bot, API,
  web, migrations/testing, configuration, domain glossary), loaded on
  demand instead of all at once in `CLAUDE.md`.
