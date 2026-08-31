# Migrations & testing gotchas

## Migrations (Alembic)

Schema changes go through Alembic (`migrations/`), not
`Base.metadata.create_all()` — `main.py` no longer calls it.
`migrations/env.py` imports `bot.db.base.Base` + `bot.db.models` and sets
`sqlalchemy.url` from `bot.core.settings.DATABASE_URL` at runtime (nothing
hardcoded in `alembic.ini`), so it always uses the same env vars as the app
itself.

- After changing a model in `bot/db/models.py`: `alembic revision
  --autogenerate -m "..."`, review the generated file in
  `migrations/versions/` (autogenerate misses some things — renames look
  like drop+add, server-side defaults, etc.), then `alembic upgrade head`.
- Adopting Alembic on a database that already has the tables (created before
  this existed, via the old `create_all()`): run `alembic stamp head` once
  instead of `upgrade head` — it marks the DB as current without re-running
  `CREATE TABLE` on tables that already exist. Confirmed working end-to-end
  against a real Postgres container (autogenerate → upgrade → `alembic
  check` reports no drift → downgrade to base cleanly → simulate a
  pre-Alembic DB via `create_all()` → `stamp head` leaves data untouched and
  `alembic check` still reports no drift).
- `seed_db.py` no longer calls `create_all()` either — it assumes migrations
  have already been run.

Full background/rationale: [`../specs/alembic-migrations.md`](../specs/alembic-migrations.md).

## Testing gotchas

- `bot/db/base.py` forces `poolclass=StaticPool` +
  `connect_args={"check_same_thread": False}` whenever `DATABASE_URL` starts
  with `sqlite` (tests only — Postgres in production is unaffected). Without
  this, SQLite's default per-thread pool gives FastAPI's `TestClient` (which
  runs the ASGI app in its own thread) a completely separate, empty
  in-memory database from the one the test's `db` fixture set up — surfaces
  as `sqlite3.OperationalError: no such table: ...` from inside API test
  requests, not from the fixture itself. `StaticPool` makes every thread
  share the one connection instead.
- SQLite does **not** preserve `tzinfo` on `DateTime(timezone=True)` columns
  (Postgres does, via `TIMESTAMPTZ`); tests touching `Reminder.remind_at`
  compare with `.replace(tzinfo=None)` on both sides to sidestep this
  SQLite-only quirk.
- No local Postgres binary in this environment, but `docker run
  postgres:16-alpine` works and is the way to validate anything
  migration/Postgres-type-related for real instead of trusting SQLite's
  looser typing.
- `api/` tests use FastAPI's `TestClient` (`tests/test_api.py`) — real HTTP
  requests through the actual ASGI app, reusing the same `db`/`user`
  fixtures as the service tests. No mocking needed, unlike the Telegram
  handlers.
- Table creation (`Base.metadata.create_all`) is a **session-scoped
  `autouse` fixture** (`tests/conftest.py:_create_tables`), not something
  only the `db` fixture does. It used to live inside `db`, which broke any
  test that hits the database without requesting `db` itself — e.g. an API
  test that only checks "invalid token → 401" never triggers `db`, so run
  alone (or before any `db`-using test) it hit a SQLite database with no
  tables yet at all. Session-scoped `autouse` guarantees tables exist before
  the first test regardless of which tests ran or in what order.
