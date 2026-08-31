# Bot architecture (`bot/`)

Layered: **Handlers** (`bot/handlers/`) receive Telegram updates and call
**Services** (`bot/services/`), which hold all business logic and DB queries
against **Models** (`bot/db/models.py`). Services never import `telegram` or
`bot.core.dialogs` — they take a SQLAlchemy `Session` as their first argument
and return plain model objects/dicts. All user-facing text lives in
`bot/core/dialogs.py` as module-level string constants (grouped by feature in
commented sections); handlers format and send these, never hardcode text
inline.

## Conversation handler pattern

Every multi-step flow (`/addmateria`, `/faltei`, `/lembrar`, `/fatec`, etc.)
is a `ConversationHandler` with a consistent shape — copy this shape when
adding a new one:

- **Dual entry points**: a `CommandHandler` for the slash command *and* a
  `CallbackQueryHandler` (pattern-matched `callback_data`) for the equivalent
  inline-menu button, both routed to the same start function. That function
  checks `update.callback_query` vs `update.message` to decide whether to
  `edit_message_text` or `reply_text`/`reply_html`.
- **State constants** are module-level ints from `range(...)`. Each handler
  file claims its own numeric block (e.g. `subject_handler.py` uses `range(8)`
  then `range(10, 14)` then `20`; `activity_handler.py` uses `range(20, 24)`
  then `range(30, 34)`; `absence_handler.py` uses `range(40, 44)` then
  `range(44, 49)`; `grade_handler.py` uses `range(50, 53)` then
  `range(53, 58)`) purely as a convention to keep them visually distinct
  across files — when adding a new conversation, pick an unused block rather
  than reusing `0`-`N`.
- **`fallbacks=[CommandHandler("cancelar", xxx_cancel)]`** — `xxx_cancel`
  must be an actual async function. Passing a `dialogs.*` string directly as
  the callback was a real bug fixed 3 times (`admin_handler.py`,
  `reminder_handler.py`, `bug_report_handler.py`) — `CommandHandler` calls its
  callback, so a string blows up with `TypeError: 'str' object is not
  callable`.
- **`states` always includes `ConversationHandler.TIMEOUT:
  [TypeHandler(Update, notify_conversation_timeout)]`**, and the handler is
  built with `conversation_timeout=CONVERSATION_TIMEOUT_SECONDS` (both from
  `bot/core/conversation_timeout.py`). Without this, an abandoned
  conversation stays stuck in its state forever and unrelated commands sent
  afterward get silently swallowed.
- **Reloading a menu after an in-place edit**: never fabricate a fake
  `Update`/`CallbackQuery` object to re-invoke another handler function
  (`type('CallbackQuery', (), {...})()` — this was a real, repeated bug: the
  faked object lacks real methods like `edit_message_text`, and `await
  fake.answer()` on a plain lambda raises `TypeError` since it's not a
  coroutine). Instead, extract a `build_xxx_view(...) -> (text,
  reply_markup)` helper (see `build_subject_edit_view` in
  `subject_handler.py`, `build_activity_edit_view` in `activity_handler.py`,
  `build_grades_list_view` in `grade_handler.py`) and call it directly from
  both the original render path and the reload-after-edit path.

## Cross-cutting pieces

- **`user_service.get_or_create_user(db, telegram_user.id, first_name,
  username)`** is called at the top of nearly every handler — Telegram's
  user ID is the only stable identity, so the local `User` row is lazily
  provisioned on first contact.
- **Timezone**: `bot/core/settings.TIMEZONE` is applied globally via
  `Defaults(tzinfo=TIMEZONE)` on the `Application` in `main.py`, so naive
  `datetime.time`/`datetime.datetime` values passed to
  `job_queue.run_daily`/`run_once` are interpreted in that zone
  automatically. `dateparser` (used in `reminder_handler.py` to parse
  free-text times like "amanhã às 14h") does *not* know about PTB's
  `Defaults`, so it's called with an explicit `settings={'TIMEZONE': ...,
  'TO_TIMEZONE': ..., 'RETURN_AS_TIMEZONE_AWARE': True}`.
- **Reminder persistence**: `Reminder` rows (`bot/db/models.py`) only exist
  while pending — the delivery job deletes its own row immediately after
  sending. `bot/handlers/reminder_handler.py:schedule_reminder()` is the
  single function used both when a user creates a reminder *and* by
  `main.py:reschedule_pending_reminders()` at startup, because
  `JobQueue`/APScheduler jobs live only in memory and are lost on every
  process restart.
- **`CourseSubject` vs `Subject`**: see `glossary.md`.
- **Admin commands** (`/broadcast`, `/enviar`) are gated by `@admin_only`
  (`bot/decorators.py`), which checks membership in `ADMIN_USER_IDS`.
