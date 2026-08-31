# Web frontend (`web/`)

A Vite + React + TypeScript SPA consuming `api/` — the site half of
`docs/specs/frontend-web-and-app.md` (the React Native app hasn't been
started). No UI component library; plain CSS (`src/index.css`) with CSS
custom properties for light/dark.

- **`src/api/`**: `types.ts` mirrors `api/schemas.py` by hand (kept as a
  separate contract on purpose, same reasoning as the schemas/models split in
  the backend); `client.ts` is a thin `fetch` wrapper that attaches
  `Authorization: Bearer <token>` from `localStorage` and throws `ApiError`
  on non-2xx (message pulled from the response's `detail`); `resources.ts`
  has one function per `api/routers/*.py` endpoint. Adding a backend endpoint
  = add its type(s) to `types.ts` and a function to `resources.ts`.
- **Auth** (`src/auth/`): `AuthContext` holds `user`/`login`/`logout`, backed
  by the token in `localStorage`. `client.ts` dispatches a
  `jovis:unauthorized` `window` event on any `401`; `AuthContext` listens for
  it and clears `user`, which `RequireAuth` (route wrapper) turns into a
  redirect to `/login`. `TelegramLoginButton` injects the official Telegram
  widget `<script>` tag pointed at `VITE_TELEGRAM_BOT_USERNAME` and wires its
  callback to `AuthContext.login`, which calls `POST /auth/telegram` and
  stores the returned token — same flow as the backend's Login Widget
  support.
- **Pages** (`src/pages/`): one per resource (`Subjects`, `Activities`,
  `Absences`, `Grades`) follow the same shape — a list (TanStack Query
  `useQuery`) plus an inline create/edit `<form class="panel">` (not a
  modal) toggled by local `editingId: number | 'new' | null` state, with
  `useMutation` invalidating the list query on success. Copy this shape for a
  new resource page. Backend validation errors (e.g. the `409` schedule
  conflict on `Subjects`) surface via `ApiError.message` in an `ErrorBanner`
  scoped to the form, not the whole page.
- **Config**: `web/.env` (gitignored, copy from `.env.example`) needs
  `VITE_API_URL` (the FastAPI base URL) and `VITE_TELEGRAM_BOT_USERNAME` (the
  bot's `@username`, without the `@`, for the Login Widget).

## Testes

Vitest + React Testing Library + jsdom (`web/vite.config.ts`'s `test` block,
`web/src/test/setup.ts` for jest-dom matchers and per-test
`localStorage`/DOM cleanup). `web/.env.test` pins
`VITE_API_URL`/`VITE_TELEGRAM_BOT_USERNAME` to fixed dummy values so tests
don't depend on a developer's local `web/.env` — Vitest defaults to Vite's
`test` mode, which loads `.env.test` automatically.

Coverage is intentionally not exhaustive across the 4 CRUD pages
(Matérias/Atividades/Faltas/Notas share one list+inline-form shape — see
"Pages" above): `src/api/client.test.ts` covers the `fetch` wrapper (auth
header, 401 → clear token + `UNAUTHORIZED_EVENT`, error `detail` parsing, 204
handling); `src/auth/AuthContext.test.tsx` covers the login/logout/
session-refresh state machine; `src/pages/Subjects.test.tsx` is a full
component test of the list+form+delete pattern, including the `409`
schedule-conflict path, and stands in as the reference for testing another
page the same way — it isn't duplicated onto Activities/Absences/Grades. All
three files `vi.mock('../api/resources')` rather than mocking `fetch`
directly, so tests assert on which resource function was called with which
payload, not on request wiring.
