# Glossary format (this repo: `docs/architecture/glossary.md`)

Adapted from upstream's `CONTEXT.md` format to match the bullet-list style
already in use in this repo — don't switch to the heading-per-term style
below, follow the existing file's format instead.

## Structure (as already used in `docs/architecture/glossary.md`)

```md
- **`Term`** — one or two sentence definition. What it IS, not what it does.
  Cross-reference the file/model it lives in if that's not obvious
  (e.g. `bot/db/models.py`).
```

Example, straight from the existing file:

```md
- **`CourseSubject` vs `Subject`** — `CourseSubject` is a shared, global
  catalog table (course/shift/semester → subject template), populated by
  `seed_db.py` from `data/courses.json`, used only by the `/fatec`
  onboarding... Everything else in the app operates on `Subject`, never
  `CourseSubject`.
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and note the alternative to avoid inline, in prose (no separate `_Avoid_` line needed — keep the existing file's one-bullet-per-term shape).
- **Keep definitions tight.** One or two sentences for the core definition; a following sentence for cross-references is fine.
- **Only include terms specific to this project's domain.** General programming concepts don't belong even if used extensively. Ask: is this a concept unique to this app (`CourseSubject`, `Activity` types, `AccessToken` origins), or a general one? Only the former belongs.
- **This repo is single-context.** No `CONTEXT-MAP.md`/multi-glossary split — everything goes in the one `docs/architecture/glossary.md`.
