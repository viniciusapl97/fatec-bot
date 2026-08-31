# Configuration

`bot/core/settings.py` reads env vars at import time (via `.env`, loaded with
`python-dotenv`) and **raises immediately** if required ones are missing.
This means importing almost anything under `bot/` requires these to already
be set:

- `TELEGRAM_TOKEN` — required.
- `DATABASE_URL`, or the pair `DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`/`DB_NAME`
  — required (Postgres in production).
- `ADMIN_USER_IDS` — comma-separated Telegram user IDs; if empty, **all**
  admin commands are denied (fails closed, see `bot/decorators.py`).
- `TIMEZONE_NAME` — optional, defaults to `America/Sao_Paulo`.
- `EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_SENDER`/`EMAIL_SENDER_PASSWORD`/`EMAIL_RECEIVER`
  — optional, only needed for `/bug` reports to actually send.
- `FRONTEND_ORIGINS` — optional, comma-separated list of origins allowed by
  the API's CORS middleware (`api/main.py`); defaults to
  `http://localhost:5173` (the Vite dev server).

For local testing without Postgres or a real Telegram bot,
`DATABASE_URL=sqlite:///./dev.db` works (`bot/db/base.py` switches pool
settings for sqlite) and `TELEGRAM_TOKEN` just needs to be non-empty — it's
only actually called against the Telegram API by the bot process and by
`/auth/telegram`'s signature check, not by anything else.

`tests/conftest.py` sets safe defaults for these via
`os.environ.setdefault(...)` at the very top of the file, before any `bot.*`
import, specifically so the test suite doesn't need a real `.env`.
