# API (`api/`)

A FastAPI app that exposes `bot/services/` over HTTP, for the web site
(`web/`) and the (future) React Native app — it's a second, independent
consumer of the same services layer that `bot/handlers/` already uses, not a
rewrite of anything. `api/main.py` is the ASGI app; `api/deps.py` has the two
shared dependencies (`get_db`, `get_current_user`); `api/routers/*.py` are one
file per resource; `api/schemas.py` has the Pydantic response models (kept
separate from `bot/db/models.py` on purpose, so a DB column change doesn't
silently change the API contract).

- **Two ways to get a Bearer token**: a personal access token
  (`/tokendeacesso` in the bot, `bot/handlers/user_settings_handler.py`, via
  `access_token_service.create_access_token` — meant for the app/personal
  use), or the Telegram Login Widget (`POST /auth/telegram`, meant for the
  site — see `docs/specs/api-design.md` and
  `docs/specs/frontend-web-and-app.md`). Both end up as the same kind of
  `AccessToken` row; only its SHA-256 hash is stored
  (`AccessToken.token_hash`), so a personal-access-token plaintext is shown
  exactly once and can't be recovered — `/revogartokens` deletes all of a
  user's tokens if one leaks. Send it as `Authorization: Bearer <token>`;
  `api/deps.get_current_user` resolves it back to a `User` via
  `access_token_service.get_user_by_token`.
- Adding an endpoint = add a Pydantic schema in `api/schemas.py`, a router
  function in `api/routers/` that takes `user: User = Depends(get_current_user)`
  (and `db: Session = Depends(get_db)` if it needs to query more than `user`
  itself), call the matching `bot/services/*` function, and
  `include_router(...)` it in `api/main.py`.
- **CORS**: `api/main.py` adds `CORSMiddleware` allowing the origins in
  `bot/core/settings.FRONTEND_ORIGINS` (env var, default
  `http://localhost:5173`). No `allow_credentials` — auth is
  Bearer-token-in-header, not cookie-based, so the browser doesn't need
  cross-origin credentialed requests.
