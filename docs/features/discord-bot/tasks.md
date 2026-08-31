# Tasks: Discord bot (`discord_bot/`)

Prerequisite: [`plan.md`](plan.md).

- [ ] Migration: add `User.telegram_id`, `User.discord_id` (nullable,
      unique, `BigInteger`) + backfill `telegram_id = user_id` for
      existing rows. `alembic revision --autogenerate -m "..."`, review,
      `alembic upgrade head`.
- [ ] `bot/services/user_service.py`: `get_or_create_discord_user(db,
      discord_id, display_name)` + tests.
- [ ] New `bot/services/account_link_service.py` + `AccountLinkCode`
      model/migration + tests: generate code, redeem code, expiry,
      collision rejection (redeeming into an already-linked identity).
- [ ] `bot/core/settings.py`: optional `DISCORD_BOT_TOKEN`.
- [ ] New `discord_bot/` package: entrypoint, `discord_bot/core/dialogs.py`,
      slash command registration boilerplate (`app_commands`).
- [ ] v1 read-only commands: today, week, schedule, attendance, grades —
      each a thin slash-command wrapper calling the matching
      `bot/services/*` function, no new business logic.
- [ ] Linking slash command on the Discord side + `/vincular` (or
      equivalent) on the Telegram side, if it doesn't already exist.
- [ ] Tests: `tests/test_account_link_service.py`, the Discord-origin path
      through `user_service` (including the `user_id = -discord_id`
      encoding).
- [ ] `docs/specs/discord-identity-model.md`: write up the identity-model
      decision from `plan.md`, once implemented. Link it from
      `docs/ROADMAP.md`'s "Specs" section.
- [ ] `docs/roadmap-discord.md`: new roadmap file for this area (mirrors
      `roadmap-bot.md`/`roadmap-api.md`), once the first slice ships. Add
      it to `docs/ROADMAP.md`'s "Roadmaps by area", and remove this
      feature's entry from "Features in planning" once it's tracked there
      instead.
- [ ] `docs/architecture/bot.md`: add a short paragraph on `discord_bot/`
      as a second direct consumer of `bot/services/`, mirroring how
      `api/` is already described.
- [ ] `docs/architecture/glossary.md`: update the "User identity" entry —
      it currently says the Telegram ID is the only stable identity;
      that becomes inaccurate once this ships.
- [ ] Update `Status` in `spec.md`/`plan.md`/`tasks.md` to `Done` (or
      `In Progress` once work starts).
