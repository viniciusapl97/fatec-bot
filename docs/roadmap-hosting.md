# Roadmap — Hosting

See [`ROADMAP.md`](ROADMAP.md) for the general index across areas.

Last updated: 2026-08-21.

## Status: still running locally

Open decision (2026-08-21): the user wants to use this as an opportunity to
learn AWS, using the free tier (EC2 t2/t3.micro + RDS Postgres
t3/t4g.micro, both eligible for 12 months on a new account). Not started
yet — said "not for now" when asked whether they wanted to proceed with the
setup.

## Combined plan, when resumed

1. Create a budget alert first (before any resource).
2. A dedicated IAM user (not the root account).
3. VPC/Security Groups (the default VPC is fine to start).
4. EC2 — run the bot as a `systemd` service.
5. RDS Postgres — migrate from the local database to it (`alembic upgrade
   head` on the new database, see
   [`specs/alembic-migrations.md`](specs/alembic-migrations.md)).
6. CloudWatch for logs.

## Note for when the API/site/app go to production

This plan only covers the bot. When the API (`api/`) also goes to
production, it can run on the same EC2 instance (another process, e.g. via
`systemd`/`nginx` in front) or somewhere else — not decided yet, not urgent
while only the bot is in production.
