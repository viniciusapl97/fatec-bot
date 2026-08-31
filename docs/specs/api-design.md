# Spec: API design (`api/`)

Decisions made on 2026-08-21, when starting the API implementation. See
[`roadmap-api.md`](../roadmap-api.md) for the status/changelog summary
(what's already been built, what's left).

## Why an API on top of `bot/services/`

All the bot's business logic already lives in `bot/services/`, with no
dependency on Telegram at all (no `import telegram`, no `import dialogs` —
see [`../architecture/bot.md`](../architecture/bot.md)). The API is just
another "client" of these services, the same way `bot/handlers/` already
is — it doesn't duplicate any logic, and the bot keeps working entirely
independently of whether the API exists or not.

## Authentication: personal access token (not the Telegram Login Widget)

There are two planned consumers of the API, with different needs (see
[`specs/frontend-web-and-app.md`](frontend-web-and-app.md)):
- **Site**: serves any bot user → needs real login → the **Telegram Login
  Widget** is the right path (not implemented yet).
- **Personal app (React Native, sideload)**: personal use only, no store →
  not worth replicating the Login Widget's OAuth-like flow.

For this second case, a **personal access token** was implemented:
- `AccessToken` (`bot/db/models.py`) stores only the **SHA-256 hash** of
  the token — never the plaintext value. Like a password, minus the
  username.
- `/tokendeacesso` on the bot (`bot/handlers/user_settings_handler.py`)
  generates a token with `secrets.token_urlsafe(32)` and shows it to the
  user **exactly once** — after that, only the hash exists, there's no way
  to recover the original value (if lost, generate another one).
- `/revogartokens` deletes all of a user's tokens at once — meant for the
  case where a token leaks.
- The API validates via the `Authorization: Bearer <token>` header —
  `api/deps.get_current_user` hashes the received token and looks it up in
  the database (`access_token_service.get_user_by_token`), 401 if not
  found.

## Telegram Login Widget (`POST /auth/telegram`) — for the site

Decided on 2026-08-21, while implementing it. The widget returns a signed
payload to the frontend (`id`, `first_name`, `last_name?`, `username?`,
`photo_url?`, `auth_date`, `hash`) — see
[the official algorithm](https://core.telegram.org/widgets/login#checking-authorization).
`api/routers/auth.py` reproduces that algorithm: builds the
"data-check-string" (every field except `hash`, and except any that came
back `None`, as `key=value` sorted by key and joined with `\n`), computes
`HMAC-SHA256` of it using `SHA256(TELEGRAM_TOKEN)` as the key, and compares
with `hmac.compare_digest` (avoids timing attacks). It also rejects an
`auth_date` older than 24h (`TELEGRAM_AUTH_MAX_AGE_SECONDS`), so an old
login link doesn't stay valid forever.

**Important decision: this is not a separate authentication scheme.**
Instead of inventing a session/JWT just for the site, the endpoint only
validates the signature, resolves the user via
`user_service.get_or_create_user` (the same function any bot handler
already uses), and issues a regular **personal access token**
(`access_token_service.create_access_token` — the same mechanism as the
bot's `/tokendeacesso`). The site receives that token, stores it (where,
still to be decided — see `roadmap-app.md`), and authenticates exactly like
the app already does, via `Authorization: Bearer <token>`. This means `/me`
and every other endpoint neither knows nor needs to know whether the token
came from the bot or from the widget — it's the same `AccessToken` in the
same table.

Consciously accepted trade-off: since `AccessToken` has neither expiration
nor rotation (only `/revogartokens` on the bot deletes all of them at
once), every widget login creates a new row in that table — there's no
token reuse across logins. That's acceptable for an MVP (there's nothing
sensitive besides the user's own data, and the owner can always revoke
everything via the bot); if it accumulates too much clutter, the next step
is either reusing an existing token per user, or giving tokens issued by
the widget specifically an expiration (without affecting the app's
personal token).

## Separation between `api/schemas.py` and `bot/db/models.py`

The Pydantic response models (`api/schemas.py`) are deliberately a
**separate** contract from the SQLAlchemy models, even though they mirror
the same fields in most cases. This is intentional: a database column
change doesn't accidentally leak into the API's public contract. Endpoints
that join data from more than one table (e.g. `ActivityOut`/`AbsenceOut`/
`GradeOut` embedding `subject_name`, which isn't a direct model attribute)
are assembled by hand in the router, not via Pydantic's automatic
`from_attributes`.

## Testing gotchas found along the way

### `StaticPool` for the tests' SQLite

Testing the API with FastAPI's `TestClient` against the tests' in-memory
SQLite produced `sqlite3.OperationalError: no such table: ...` even though
the table existed. Cause: `TestClient` runs the ASGI app on a thread
separate from the test's thread, and SQLite's default pool
(`SingletonThreadPool`) creates a **new, empty in-memory database per
thread**.

Fixed in `bot/db/base.py`: when `DATABASE_URL` starts with `sqlite`, it
forces `poolclass=StaticPool` + `connect_args={"check_same_thread": False}`
— every thread now shares the same connection/database. Only applies to
SQLite; production Postgres is unaffected (still uses SQLAlchemy's default
pool).

### Table creation needs to be `autouse`, not just inside the `db` fixture

API tests that don't request the `db` fixture (e.g. "invalid token → 401",
which doesn't need to insert anything into the database) never triggered
`Base.metadata.create_all()`, which used to live only inside the `db`
fixture. Running the whole suite this went unnoticed (some other test file,
run earlier, had already created the tables), but running just `pytest
tests/test_api.py` alone broke with `no such table`.

Fixed by moving table creation to an `autouse=True`, `scope="session"`
fixture in `tests/conftest.py` — runs once before any test, regardless of
which ones request `db`.

## Validation

Each batch of endpoints was tested against a real Postgres (Docker
container `postgres:16-alpine`, discarded afterward) in addition to the
automated tests: generate a token via the bot → authenticate against the
API → endpoints returning the correct data, scoped only to the token's
owner → invalid/missing token rejected (401/403) → revoking invalidates
immediately. Also run with real `uvicorn` (not just `TestClient`),
including `/docs` (Swagger), which comes free with FastAPI.
