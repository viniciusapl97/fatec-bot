# Spec: Pagination for the API's listing endpoints

**Status:** Draft
**Area:** api
**Related roadmap:** [`../../roadmap-api.md`](../../roadmap-api.md) — "Next steps"

## Problem / motivation

`GET /subjects`, `/activities`, `/absences`, and `/grades` return the
user's entire list at once. The API doesn't have Telegram's 4096-character
limit (which already forced pagination on the bot — see
`docs/architecture/bot.md`), but a user with many subjects/activities
accumulated across several semesters can still generate a payload large
enough to weigh on the site (`web/`) and any future app.

## Requirements

- The 4 listing endpoints (`/subjects`, `/activities`, `/absences`,
  `/grades`) accept pagination via query params.
- Without the params, current behavior (full list) doesn't change — avoids
  breaking any existing consumer overnight.
- The pagination shape is the same across all 4 endpoints (a consumer
  implements it once, reuses it 4 times).

## Acceptance criteria

- [ ] `GET /subjects?page=2&page_size=20` returns items 21-40 (or fewer, on
      the last page) inside an envelope with the total item count.
- [ ] Omitting `page`/`page_size` keeps current behavior (full list, no
      envelope) — confirmed by the "Open question" below before leaving
      Draft.
- [ ] Invalid `page`/`page_size` (≤0, `page_size` above a cap) return 422,
      not a silent 500.
- [ ] Tests covering: full page, partial last page, page past the total
      (empty list, not an error), invalid params.

## Out of scope

- Cursor-based pagination (offset/limit is enough for the expected volume
  per user — tens to a few hundred rows, not thousands).
- Changing the bot's existing pagination (`/grade`, `/calendario` —
  pagination by Telegram character count, a completely different
  mechanism, not touched).

## Open questions

- Envelope always present (a contract change for every consumer, including
  the 3 that already exist) vs. only when `page`/`page_size` are sent
  (keeps backward compatibility, but two possible response shapes for the
  same endpoint)? **Decide before leaving Draft** — `plan.md` already
  assumes the second option as the recommendation, but it isn't confirmed.
- Cap on `page_size` (`plan.md` suggests 100)?
