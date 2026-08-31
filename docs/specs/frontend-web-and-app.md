# Spec: Web frontend + Android/iOS app

Discussed and decided on 2026-08-21. See
[`roadmap-app.md`](../roadmap-app.md) for status/next steps, and
[`roadmap-api.md`](../roadmap-api.md) for the backend that supports both.

The idea evolved over the course of the conversation: started as "just a
site" → then "site + Android widget" → final decision "site + full app
(React Native), with a home-screen widget, iOS maybe someday".

## The foundation: an API over `bot/services/`

All the business logic is already isolated in `bot/services/`, with no
dependency on Telegram — those same services can be exposed behind an API
(FastAPI, `api/`) without rewriting the logic. **That's what the site and
the app have in common** — each one's UI is separate (see stack below),
only the API is shared. See [`specs/api-design.md`](api-design.md).

## Chosen stack

- **Site**: React.
- **App**: React Native, via Expo (makes a local build/sideload without a
  developer account easier). Android first; iOS "someday" becomes much
  cheaper to add later since it's already on React Native, instead of
  starting from scratch in Swift down the line.
- **React Native Web** is an option to unify the UI code between the site
  and the app (used in production by large apps, e.g. the new X/Twitter) —
  but it's not the recommended starting point. Starting with plain React on
  the site and React Native on the app (sharing only the API types/calls)
  is simpler; migrating to RN Web later is an option, not a requirement.

## Home-screen widget (the original reason a native app was considered)

React Native's JS engine runs inside the app's process — a widget is
rendered by the *operating system* outside that process, so it **always
needs a native piece**, even with React Native:
- **Android**: the
  [`react-native-android-widget`](https://github.com/sAleksovski/react-native-android-widget)
  library — draws the widget layout in JSX, it compiles to native views at
  build time. It's the best current option for this scenario — not "run JS
  inside the widget".
- **iOS** (if it ever happens): Apple requires SwiftUI for widgets, no
  exceptions — there's no React Native bridge for this. There's no way
  around Swift for this specific part, even with the whole app in React
  Native.

## Authentication — different for the site and the app

- **Site**: since the bot serves any Telegram user (not just personal
  use), the right approach is the **Telegram Login Widget** — the user
  clicks "Log in with Telegram", Telegram authenticates them and returns a
  signed payload (`user_id`, name, username, photo) for the backend to
  validate the hash. Zero new password to manage, and `user_id` already
  matches `User.user_id` in the database. **Already implemented in the
  backend** (`POST /auth/telegram`, see
  [`specs/api-design.md`](api-design.md)) — built ahead of the site
  existing; only the button/flow on the frontend is left, once the site
  starts.
- **App/widget**: since this app is only for personal use (sideload, no
  store), it's not worth replicating the Login Widget flow — simpler is a
  **personal access token** tied to `user_id`, pasted once into the app's
  settings. **Already implemented** — see
  [`specs/api-design.md`](api-design.md).

## Estimate by ambition level

- Read-only MVP (login + view schedule/grades/absences/attendance/
  calendar), site only: a few weekends.
- Full parity (create/edit/delete everything, same as the bot) on the site
  and/or the app: several weeks, part-time — the app adds extra time if
  React Native/Expo is new territory.
- Working Android widget (`react-native-android-widget`): small scope once
  the API already exists — doesn't need to wait for the whole app to be
  ready to build the widget.
- Custom design + progress charts + iOS + real-time ("really ambitious"):
  months — the most open-ended part, no ceiling.

## Recommended order

1. API first (FastAPI over `bot/services/`) — **in progress**, see
   [`roadmap-api.md`](../roadmap-api.md).
2. Android app (React Native/Expo) with the essentials (view/manage
   schedule, activities, absences, grades) + the widget — the reason this
   conversation started, so it's what pays off fastest.
3. Site as an additional consumer of the same API, when it makes sense.
4. iOS and UI unification (React Native Web) only after validating the
   rest.
