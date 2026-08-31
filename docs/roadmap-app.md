# Roadmap — Site + Android/iOS App

See [`ROADMAP.md`](ROADMAP.md) for the general index across areas, and
[`specs/frontend-web-and-app.md`](specs/frontend-web-and-app.md) for the
full decision (stack, authentication, estimates, reasoning behind each
choice).

Last updated: 2026-08-24.

## Status: 🚧 site has full CRUD parity; app not started yet

The idea evolved over the course of the 2026-08-21 conversation: started as
"just a site" → then "site + Android widget" → final decision "site + full
app (React Native), with a home-screen widget, iOS maybe someday". The
original recommended order was Android app first — revised on 2026-08-24:
the site was started first, by explicit request.

## ✅ Done

1. **React site** (`web/`, 2026-08-24) — Vite + React + TypeScript,
   React Router, TanStack Query. Full CRUD parity with the bot:
   - Login via Telegram Login Widget (`POST /auth/telegram`, already
     existed in the backend) — token stored in `localStorage`, a `401`
     from the API clears the session and redirects to `/login`
     (`src/api/client.ts`).
   - Subjects: list + create/edit/delete, with schedule-conflict detection
     (`409`) shown in the form; detail page (`/subjects/:id`) with the
     subject's attendance and grades.
   - Activities: list with assignment/exam filter, create/edit/delete
     (`activity_type` fixed at creation, not editable — same rule as the
     bot).
   - Absences: list, create/delete, edit only the quantity (same
     limitation as the bot).
   - Grades: list, create/edit/delete.
   - No UI library — plain, functional CSS; a custom design is deferred to
     a separate future phase (see spec).
   - `api/main.py` gained `CORSMiddleware` (didn't exist — the API never
     had a browser consumer before); new optional env var
     `FRONTEND_ORIGINS` in `bot/core/settings.py`.
   - Manually validated end-to-end against the local API (SQLite):
     login/logout, CRUD for the 4 entities, schedule conflict, 401 →
     redirect.
2. **Automated site tests** (2026-08-24) — Vitest + React Testing
   Library + jsdom. Deliberately non-exhaustive coverage: `client.ts`
   (auth header, 401, error parsing, 204), `AuthContext` (login/
   logout/session refresh), and one full component test
   (list+form+409 conflict+delete) in `Subjects.test.tsx`, which serves as
   the reference pattern for the other 3 pages rather than being copied
   1:1 onto them. Details in
   [`../architecture/web.md`](../architecture/web.md) → "Tests".
3. **Visual redesign + mobile navigation** (2026-08-24) — dark
   "dashboard"-style theme (Inter + Space Grotesk, purple/blue gradient
   accent, `lucide-react` for icons), sidebar with icon navigation on
   desktop. On mobile (`≤780px`): a thin top bar + a fixed bottom nav bar
   (native-app style) instead of the sidebar; listing tables
   (`≤720px`) become a card list instead of a horizontally-cut table.
4. **"What grade do I need" calculator** (2026-08-24) — on
   `/subjects/:id`, given a subject's grades already entered, calculates
   the average needed on the remaining grades to hit a target average.
   100% client-side calculation (same formula as
   `grade_service.get_average` — simple arithmetic mean), no new
   endpoint.
5. **Attendance-risk banner on the Dashboard** (2026-08-24)
   — `GET /subjects` now embeds the same computed fields as
   `GET /subjects/{id}/attendance` (`percent`, `remaining_allowed`,
   `at_risk`, `failed`) directly in `SubjectOut`, so at-risk subjects can be
   listed on the home screen without an extra call per subject. Backend
   change in `api/routers/subjects.py`/`api/schemas.py`
   (`SubjectCreate`/`Update` unchanged), 2 new tests in
   `tests/test_api.py`.

## 🎯 Next steps

- Android app (React Native/Expo) — see "Recommended order" below.
- Component tests for the remaining pages (Activities/Absences/Grades), if
  a real bug shows up in them or the pattern needs re-validating — not
  required right now (same shape as `Subjects.test.tsx`).
- Site deployment (depends on `roadmap-hosting.md`, still local/paused).

## Recommended order (updated)

1. ~~API first~~ — **done**, see [`roadmap-api.md`](roadmap-api.md).
2. ~~Site (React)~~ — **done** (full CRUD parity, see above).
3. Android app (React Native/Expo) with the essentials (view/manage
   schedule, activities, absences, grades) + the home-screen widget
   (`react-native-android-widget`) — the original reason for this
   conversation, not started yet.
4. iOS and UI unification (React Native Web) only after validating the
   rest.
