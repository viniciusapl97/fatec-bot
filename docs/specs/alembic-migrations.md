# Spec: Migrations with Alembic

Decision made on 2026-08-21. See the matching item in
[`roadmap-bot.md`](../roadmap-bot.md) for the status/changelog summary.

## Problem

The bot created/updated tables with `Base.metadata.create_all(bind=engine)`
every time it started up (`main.py`) or `seed_db.py` ran. That works for
creating tables that don't exist, but **does not migrate columns on tables
that already exist** — every schema change in production depended on
someone remembering to run a manual `ALTER TABLE`. Two such pending changes
had already piled up (`notifications_enabled`, `notification_hour`) before
this was fixed for good.

## Decision

Adopt [Alembic](https://alembic.sqlalchemy.org/) as the owner of the
schema. `Base.metadata.create_all()` was removed from `main.py` and
`seed_db.py` — migrations are now the only way to create/alter tables.

- `migrations/env.py` imports `bot.db.base.Base` + `bot.db.models` (so
  `Base.metadata` contains every table) and sets `sqlalchemy.url` at
  runtime from `bot.core.settings.DATABASE_URL` — the same environment
  variables as the rest of the project, nothing duplicated/hardcoded in
  `alembic.ini`.
- The baseline migration (`migrations/versions/6cde7bf58518_*.py`) covers
  the 7 tables that existed at adoption time.

## Adopting on a database that already exists (dev or production)

A database created before Alembic existed (via `create_all()`, like the
one you're already running locally) **should not run `alembic upgrade
head` directly** — that would try to `CREATE TABLE` on tables that already
exist and fail.

```bash
# Once, on the database that already exists:
alembic stamp head

# From then on, always:
alembic upgrade head
```

`stamp head` marks the database as "already at the latest version" without
running any DDL — since the baseline migration already includes
`notifications_enabled` and `notification_hour`, this single step also
resolves the two manual `ALTER TABLE` items that were pending.

## Validation

Tested end-to-end against a real Postgres (Docker container
`postgres:16-alpine`, discarded afterward — no new dependency for the
project):
1. `alembic upgrade head` from scratch → tables created correctly.
2. `alembic check` → no pending difference between the models and the
   database.
3. `alembic downgrade base` → clean, removes everything.
4. Simulated the user's actual state: tables created via `create_all()`
   (without Alembic) → `alembic stamp head` → data intact, `alembic check`
   still reports no difference.
5. Ran real `services/` operations (create user, subject, activity,
   absence, grade, reminder, compute attendance) directly against the
   schema created by the migration — everything working.

The pytest suite (SQLite) doesn't use `main.py`/`seed_db.py` directly, so
it was unaffected by these changes.

## Side effect: `requirements.txt` was in UTF-16

When trying to just add the `alembic` line to `requirements.txt`, the edit
tool preserved the file's original encoding — which had always been
UTF-16 (probably generated via `pip freeze` on Windows PowerShell; that's
why `cat`/`grep` always showed it "spaced out" whenever someone looked at
the file from a Linux/macOS terminal). The result was a UTF-16
`requirements.txt` with the new line added, which breaks `pip` (`ERROR:
Invalid requirement` with literal `\x00` bytes in the middle of the package
name).

Fixed by rewriting the whole file via a shell heredoc
(`cat > requirements.txt << 'EOF' ... EOF`), which forces UTF-8 regardless
of what was already in the file. This is the method to use whenever a
non-UTF-8 file's encoding needs fixing — a normal edit preserves the
original encoding.
