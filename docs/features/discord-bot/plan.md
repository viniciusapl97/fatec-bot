# Plan: Discord bot (`discord_bot/`)

Prerequisite: [`spec.md`](spec.md).

## Layers affected

- [ ] `bot/db/models.py` — `User` gains `telegram_id` (nullable, unique,
      `BigInteger`) and `discord_id` (nullable, unique, `BigInteger`).
      `user_id` is unchanged in shape (`NOT NULL`, `unique`, still the FK
      target for the other 6 tables) — see "Identity model" below for what
      it holds going forward.
- [ ] Migration: add the two columns + backfill `telegram_id = user_id` for
      every existing row (safe: every existing row is Telegram-origin).
- [ ] `bot/services/user_service.py` — new `get_or_create_discord_user(db,
      discord_id, display_name)`, alongside the existing
      `get_or_create_user` (kept for Telegram; decide at implementation
      time whether renaming it to `get_or_create_telegram_user` is worth
      touching its ~13 call sites for symmetry, or whether a doc comment is
      enough — leaning towards leaving the name as-is).
- [ ] New `bot/services/account_link_service.py` — generate/redeem linking
      codes.
- [ ] New `AccountLinkCode` model + migration (ephemeral, same spirit as
      `Reminder`: a row exists only while the code is pending).
- [ ] New `discord_bot/` package (sibling to `bot/`, `api/`): its own
      entrypoint, `discord_bot/core/dialogs.py` (Discord-appropriate
      text/embeds, same voice as `bot/core/dialogs.py` but not
      copy-pasted — Discord's formatting/embed model differs from
      Telegram's `parse_mode`), slash commands calling straight into
      `bot/services/*`.
- [ ] `bot/core/settings.py` — new optional `DISCORD_BOT_TOKEN` env var
      (mirrors `TELEGRAM_TOKEN`'s pattern; optional so the bot/API keep
      working with zero Discord config, same spirit as `FRONTEND_ORIGINS`
      being optional).
- [ ] No changes needed to `api/`, `web/`, or any of the ~13 existing call
      sites that pass `user.user_id` around — that's the point of the
      design below.

## Design

### Identity model: `telegram_id` / `discord_id` alongside the existing `user_id`

`User.user_id` today is simultaneously (a) the Telegram numeric ID, (b) the
FK target for `Subject`/`Activity`/`Absence`/`Grade`/`Reminder`/
`AccessToken` (6 tables), and (c) the value threaded through ~13 files
across `bot/handlers/`, `bot/services/`, `api/`. Rebuilding all of that to
key off `User.id` instead is a real, separate, invasive project — explicitly
out of scope here (see `spec.md`).

Instead:

- `User` gains two new nullable, unique `BigInteger` columns: `telegram_id`,
  `discord_id` — always the real value, never synthetic. Every future
  lookup ("does this Telegram/Discord account already have a `User`?")
  queries these, not `user_id`.
- `user_id` keeps its existing `NOT NULL` + `unique` + FK role exactly as
  today, filled in at creation time only:
  - Telegram-origin signup: `user_id = telegram_id` (unchanged from
    today's behavior).
  - Discord-origin signup: `user_id = -discord_id` (negative). Telegram
    never issues a negative ID, so this can never collide with a real
    Telegram-origin row **by construction** — not by hoping the numeric
    ranges happen to stay disjoint.
- `user_id` is **never mutated** after a row is created — linking a second
  platform later only fills in whichever of `telegram_id`/`discord_id` was
  still `NULL`. This keeps the 6 existing FKs permanently valid without an
  `ON UPDATE CASCADE` or any migration on those child tables.
- Existing rows (all Telegram-origin, before Discord existed): the
  migration backfills `telegram_id = user_id`, `discord_id = NULL` — fully
  retroactive, no behavior change for any existing user.
- `user_id` becomes, going forward, an internal/legacy compatibility value.
  New code should read `telegram_id`/`discord_id` for identity, not infer
  platform origin from `user_id`'s sign anywhere except the one place that
  needs it (row creation) — centralize that in `user_service.py` so it's
  not scattered.

This is a non-obvious decision (hard to reverse once rows exist with a
negative `user_id`; surprising without this context; a real trade-off
against the "do it properly" FK-repoint alternative) — **write it up as
`docs/specs/discord-identity-model.md` once implemented** (see
`tasks.md`), using this section as the source material.

### Account linking

Bidirectional, code-based:

- Either platform can generate a one-time code for the account the
  requester is currently authenticated as (`/vincular` on Telegram, the
  equivalent slash command on Discord).
- `AccountLinkCode` row: `id`, `user_id` (the initiating `User.id`
  surrogate key, not the legacy `user_id` column), `code` (short random
  string), `created_at`. Ephemeral — deleted on redemption or once expired
  (10 min TTL, same order of magnitude as `CONVERSATION_TIMEOUT_SECONDS`).
- Redeeming on the other platform: if that platform identity
  (`telegram_id`/`discord_id`) is already attached to a *different*
  `User`, reject with a clear error — never silently merge or overwrite.
  Two real people redeeming into the same slot is a data-integrity bug,
  not an edge case to paper over.
- On success: set the still-`NULL` `telegram_id`/`discord_id` column on the
  initiating `User` row, delete the code.

### Discord-side interaction

- Library: `discord.py`, native slash commands (`app_commands`).
- v1 command set (read-only, mirrors existing bot commands 1:1 via the same
  services): today (`/hoje`), week (`/semana`), schedule (`/grade`),
  attendance (`/faltas`), grades (`/notas`). Exact Discord command names
  (English-style `/today` etc. vs. keeping the bot's Portuguese names for
  voice consistency) — an implementation-time call, not a design fork
  worth its own round.
- No `ConversationHandler`-equivalent needed for v1: every v1 command is a
  single-shot read. The multi-step-flow question (modals vs. a lightweight
  pending-interaction state store) is deferred to whichever v2 slice adds
  create/edit — not designed prematurely here.

## Non-obvious decisions

- **Identity model** (above) → `docs/specs/discord-identity-model.md`, to
  be written once implemented.
- **Direct `bot/services/` consumption over the HTTP API** — mirrors the
  reasoning already in `docs/specs/api-design.md`'s "why an API on top of
  `bot/services/`", so it's a straightforward extension of an
  already-documented pattern rather than a new call. A short paragraph
  added to `docs/architecture/bot.md` once implemented is enough; no new
  spec file needed for this one.

## Risks / trade-offs

- `user_id`'s meaning gets subtler (real Telegram ID, or a negative
  Discord placeholder) — mitigated by centralizing the encode/decode logic
  in one place and documenting it loudly in the eventual spec and in
  `docs/architecture/glossary.md`'s "User identity" entry (it currently
  says "Telegram's numeric user ID is the only stable identity" — that
  becomes wrong the moment this ships and must be updated then).
- The negative-number encoding is a real but unconventional pattern —
  worth a code comment at the exact line that does it, matching
  `CLAUDE.md`'s own bar for comments ("a hidden constraint, a subtle
  invariant").
- Deferring the `users.id`-based FK repoint means this workaround is
  likely permanent, not a stepping stone — worth being explicit about in
  the eventual spec so a future reader doesn't assume it's temporary.
