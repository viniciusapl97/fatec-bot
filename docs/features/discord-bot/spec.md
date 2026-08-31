# Spec: Discord bot (`discord_bot/`)

**Status:** Draft
**Area:** bot (new: discord) — no `roadmap-discord.md` yet, see `docs/ROADMAP.md` → "Features in planning"

## Problem / motivation

The bot only exists on Telegram today. Some people the app should reach — a
class/course Discord server, someone who doesn't use Telegram at all — can't
use it without first getting on Telegram. `bot/services/` is already
Telegram-agnostic (no `import telegram`, no `import dialogs` — see
`docs/architecture/bot.md`), so a Discord surface is a second consumer of
that same layer, the same way `api/` already is.

## Requirements

- New `discord_bot/` package, sibling to `bot/` and `api/`, consuming
  `bot/services/` directly — no HTTP hop through `api/` (see `plan.md`).
- Runs as its own process (its own entrypoint + its own token env var), same
  pattern as `api/` running as its own `uvicorn` process alongside the
  bot's `main.py`.
- Built on `discord.py`, using native slash commands (`app_commands`).
- v1 scope is read-only: today / week / schedule / attendance / grades — no
  create/edit/delete yet, mirroring the phased approach already used for
  the site's MVP (see `docs/specs/frontend-web-and-app.md`).
- A person ends up at the exact same account (`User` row) whether they
  started via Telegram, started via Discord, or use both — via account
  linking. Three valid shapes, all supported:
  1. Telegram-only (today's behavior, unchanged).
  2. Discord-only (new).
  3. Both, linked together (new).

## Acceptance criteria

- [ ] A person who has never used the bot can start using it directly from
      Discord — a slash command auto-provisions a `User` row, same spirit
      as `get_or_create_user` today.
- [ ] A linking slash command on either platform, given a valid,
      unexpired, single-use code generated from the *other* platform,
      links to the account that already exists there.
- [ ] Linking to a platform identity that's already attached to a
      *different* `User` is rejected with a clear message, never silently
      overwritten or merged.
- [ ] A linking code expires after 10 minutes and can't be reused after
      expiring or after one successful redemption.
- [ ] Discord equivalents of `/hoje`, `/semana`, `/grade`, `/faltas`,
      `/notas` (read-only) return the same underlying data as their
      Telegram counterparts, via the same `bot/services/*` calls.
- [ ] Existing Telegram users, existing `Subject`/`Activity`/`Absence`/
      `Grade`/`Reminder`/`AccessToken` rows, and the API are completely
      unaffected — this is additive only.

## Out of scope

- Create/edit/delete flows on Discord (v2+, once the essential read-only
  slice ships and the interaction pattern — modals vs. a multi-step
  pending-state flow — is decided; not designed prematurely here).
- Consuming `api/` instead of `bot/services/` directly (decided against —
  see `plan.md`).
- Repointing `Subject`/`Activity`/`Absence`/`Grade`/`Reminder`/
  `AccessToken`'s foreign keys from `users.user_id` to `users.id`. That's
  the "do it properly" alternative to this feature's identity model
  (see `plan.md`) — a real, separate, invasive project touching ~13 files,
  deliberately deferred indefinitely, not bundled into this slice.
- A home-screen widget, voice features, or anything beyond text/slash
  commands.

## Open questions

None — the design was fully agreed in the planning session behind this
spec (see `plan.md`). Ready to break down into tasks.
