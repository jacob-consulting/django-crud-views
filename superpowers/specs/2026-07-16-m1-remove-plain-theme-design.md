# M1 — Remove `crud_views_plain` + examples groundwork (→ 0.13.0)

**Date:** 2026-07-16
**Status:** Approved design — ready for implementation plan.
**Milestone:** M1 of `superpowers/notes/2026-07-16-release-1-milestone.md` (road to 1.0.0).
**Ships as:** 0.13.0 (breaking removal, no deprecation period).

## Goal

The plain theme (`crud_views_plain`) and its example are gone; theme **pluggability**
survives as a documented, first-class feature with a new reference page; `examples/shared/`
is dissolved. This is a mechanical removal plus one new doc — **no behavior change** to the
bootstrap5 (`crud_views`) theme.

## Why

`crud_views_plain` is unused (not even by the maintainer), undocumented, untested at the
behavior level, unmaintained, and it clutters `examples/`. Removing it before the 1.0.0 road
clears the ground for the API-stability (M2) and examples-rewrite (M3) work. It ships in a
0.x minor so 1.0.0 itself is not a bundle of removals.

## Grounding facts (verified 2026-07-16, re-verify at implementation time)

- **Theme trees are fully parallel.** Every template in *both* `crud_views` and
  `crud_views_plain` renders `{% extends cv_extends %}` — where `cv_extends` resolves to the
  *project's* base template, never a cross-theme extend. Theming is pure override-by-name via
  `INSTALLED_APPS` ordering (the app listed first wins). Nothing in the bootstrap5 theme or
  the test suite inherits from a plain template. Removal is clean.
- **The only code coupling** in the test suite is `tests/test1/test_assets.py`: one
  `import crud_views_plain` and one test (`test_plain_theme_content_templates_render_form_media`).
- **The theme-override mechanism is undocumented.** `docs/reference/templates.md` documents
  `cv_extends` (which base template CRUD pages extend) — a *different* concept.
  `crud_views_plain` is currently the mechanism's *only living example*, and the one code spot
  that references it is the `W110` system-check hint in `src/crud_views/lib/settings.py:81`
  (*"e.g. crud_views_plain"*).
- **`examples/shared/` is wired by symlinks**, and the picture differs from the milestone
  note. All three items under `examples/shared/` are symlink targets:

  | `examples/shared/` item | Consumed by (symlink) | After plain removal |
  |---|---|---|
  | `models.py` | **only** `examples/plain/app/models.py` | **orphaned** — bootstrap5 has its own real `app/models/` package |
  | `migrations/` | the shared models (plain only) | **orphaned** |
  | `taskfile.yaml` | **both** `examples/plain/taskfile.yaml` and `examples/bootstrap5/taskfile.yaml` | one consumer (bootstrap5) |

  So this is **not** a "fold models + migrations + taskfile into bootstrap5": the models and
  migrations are plain-only and get deleted with plain; only the taskfile needs to survive,
  inlined into bootstrap5.
- **No CI / nox / conftest coupling.** `grep -ri plain` over `noxfile.py`, `.github/`,
  `pytest.ini`, `tox.ini`, and `tests/test1/conftest.py` returns nothing.

## Scope

### 1. Deletions

- `src/crud_views_plain/` — the whole app (`apps.py`, `__init__.py`,
  `static/crud_views/css/crud_views.css`, and 25 HTML templates under
  `templates/crud_views/`).
- `examples/plain/` — the whole example project.
- `tests/test1/test_assets.py` — remove `import crud_views_plain` (line 7) and delete
  `test_plain_theme_content_templates_render_form_media` (lines 105–129). The 8
  asset-registry tests in the same file stay untouched.

### 2. `examples/shared/` dissolution

- Delete `examples/shared/models.py` and `examples/shared/migrations/` — orphaned once plain
  is removed.
- Replace `examples/bootstrap5/taskfile.yaml` (currently a symlink →
  `../shared/taskfile.yaml`) with a **real file** of identical content.
- Delete `examples/shared/` entirely.
- **No content changes to the taskfile.** Its German `makemessages -l de` and any other
  German artifacts belong to the M3/M5 English sweep, not to M1.

### 3. Code edits

- `pyproject.toml`:
  - Remove `"src/crud_views_plain"` from `packages` (~line 97).
  - Remove `crud_views_plain` from `[tool.coverage.run] source` (~line 114).
  - Delete the 4-line `[[tool.bumpversion.files]]` stanza targeting
    `src/crud_views_plain/__init__.py` (~lines 136–140).
- `src/crud_views/lib/settings.py:81` — the `W110` check hint currently reads *"…list your
  app (e.g. crud_views_plain) before crud_views in INSTALLED_APPS."* Rewrite to a generic
  example name (e.g. `myapp_theme`) and point at the new `docs/reference/theme.md`.
- `CLAUDE.md:10` — remove the `crud_views_plain` bullet. Note: the header already says
  "ships as **four** separate Django apps" while currently listing **five** — removing this
  bullet fixes that pre-existing count mismatch (no wording change needed beyond the deletion).

### 4. Documentation

- **New `docs/reference/theme.md`** — the "bring your own theme" reference page. Covers:
  - how template resolution finds theme templates (override-by-name under the `crud_views/`
    namespace);
  - what a theme app must provide (same-named templates, an `AppConfig`, optional static
    assets);
  - `INSTALLED_APPS` ordering — your theme app must be listed **before** `crud_views`;
  - a short worked example of overriding one template.

  It is cross-linked with `docs/reference/templates.md` (which stays scoped to `cv_extends`)
  and added to the `reference/` nav (`.pages`).
- `docs/index.md:34` — remove the `plain` sub-bullet; keep the "Themes are pluggable" parent
  bullet and reword it to point at `theme.md`.
- `docs/reference/modals.md:30` — reword "other themes (e.g. `crud_views_plain`)" to a
  generic "custom themes that ship no modal JS".
- **Left as-is** (historical record, matches the "no grep hits outside CHANGELOG/history"
  bar): `AUDIT.md`, prior `CHANGELOG.md` entries, and all of `superpowers/**` (specs, plans,
  prompts, notes).

### 5. Release

- CHANGELOG `0.13.0` entry, flagged **Breaking**: `crud_views_plain` removed (no deprecation
  — the theme was unused). Note that theme pluggability is retained and now documented at
  `docs/reference/theme.md`.
- Bump `0.12.1 → 0.13.0` via bump-my-version, tag, publish to PyPI (existing release process
  — see project memory `release-process`).
- Verify `django-crud-views-extensions` still installs and passes against 0.13.0. It does not
  use the plain theme, but it is the downstream contract and must be confirmed green.

## Explicitly out of scope (guards)

- The German-string → English sweep of the examples (that is M3/M5).
- Any didactic restructuring of `examples/bootstrap5/` — one-app-per-feature, real-life
  domains, rendered code snippets (that is M3). M1 only de-symlinks and deletes; the
  bootstrap5 example is otherwise left exactly as it is.
- Any change to the bootstrap5 theme's templates, static assets, or rendering behavior.

## Done when

- `grep -ri crud_views_plain` over the repo returns hits **only** in `CHANGELOG.md`,
  `AUDIT.md`, and `superpowers/**` history.
- `examples/shared/` no longer exists; `examples/bootstrap5/taskfile.yaml` is a real file, not
  a symlink.
- `uv build` produces a wheel that does not contain the `crud_views_plain` package.
- The full test suite is green across the nox matrix (Python 3.12/3.13/3.14 × Django
  4.2/5.2/6.0), with coverage still above `fail_under = 88`.
- `docs/reference/theme.md` exists, renders in the docs nav, and no doc mentions the removed
  plain theme as a shipped feature.
- 0.13.0 is live on PyPI and `django-crud-views-extensions` is green against it.
