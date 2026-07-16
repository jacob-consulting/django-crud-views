# M1 — Remove `crud_views_plain` + examples groundwork — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the unused `crud_views_plain` theme app and its example, dissolve `examples/shared/`, and document the surviving theme-override mechanism in a new reference page — shipping as breaking release 0.13.0.

**Architecture:** Pure mechanical removal plus one new doc. Theming in this package is template-override-by-name (`INSTALLED_APPS` ordering); the bootstrap5 theme (`crud_views`) is untouched. No behavior change — verification is "existing suite stays green, build/grep clean, docs build clean."

**Tech Stack:** Django 4.2/5.2/6.0 × Python 3.12/3.13/3.14, hatchling build, pytest + nox, mkdocs (readthedocs theme, awesome-pages), bump-my-version, uv, go-task.

## Global Constraints

- **Release:** ships as **0.13.0** (breaking removal, **no deprecation period** — the theme is unused).
- **Version bump:** `0.12.1 → 0.13.0`.
- **Do not touch** the bootstrap5 theme's templates, static assets, or rendering behavior.
- **Out of scope (guards):** the German→English example sweep (M3/M5) and any didactic restructuring of `examples/bootstrap5/` (M3). This plan only de-symlinks and deletes.
- **Leave historical files as-is:** `AUDIT.md`, prior `CHANGELOG.md` entries, all of `superpowers/**`. The "no grep hits" bar excludes these.
- **Commits:** use explicit pathspecs — the untracked `cred.prompt.md` must never be committed.
- **Line length:** 120 chars; double quotes; ruff-format runs on commit.

---

## File Structure

Files touched, grouped by task:

- **Task 1 (code/config):** delete `src/crud_views_plain/`; edit `tests/test1/test_assets.py`, `pyproject.toml`, `src/crud_views/lib/settings.py`, `CLAUDE.md`.
- **Task 2 (examples):** delete `examples/plain/`, `examples/shared/`; convert `examples/bootstrap5/taskfile.yaml` from symlink to real file.
- **Task 3 (docs):** create `docs/reference/theme.md`; edit `docs/index.md`, `docs/reference/modals.md`, `docs/reference/.pages`.
- **Task 4 (changelog + PR):** edit `CHANGELOG.md`; open PR; merge to main.
- **Task 5 (release):** `bump-my-version`, tag, push, verify PyPI + extensions repo.

---

## Task 1: Remove the `crud_views_plain` package and its code/config references

**Files:**
- Delete: `src/crud_views_plain/` (entire directory — `apps.py`, `__init__.py`, `static/`, 25 templates)
- Modify: `tests/test1/test_assets.py` (remove import line 7 + test at lines 105–129)
- Modify: `pyproject.toml` (packages ~L97, coverage ~L114, bumpversion stanza ~L136–140)
- Modify: `src/crud_views/lib/settings.py:81` (W110 hint text)
- Modify: `CLAUDE.md:10` (app list bullet)

**Interfaces:**
- Consumes: nothing.
- Produces: a repo where `import crud_views_plain` fails and the package is no longer built. Later tasks assume the app is gone.

**Note on test safety:** the only test coupling is `tests/test1/test_assets.py`. `tests/test1/test_settings_checks.py:49` asserts on the check **message** (`"CRUD_VIEWS_THEME"`), **not** the W110 hint text — so editing the hint (Step 5) does not affect it. The test project's `INSTALLED_APPS` (`conftest.py`) never listed `crud_views_plain`.

- [ ] **Step 1: Create the feature branch**

```bash
git checkout -b m1-remove-plain-theme
```

- [ ] **Step 2: Remove the plain-theme coupling from the asset test**

In `tests/test1/test_assets.py`, delete the import at line 7:

```python
import crud_views_plain
```

and delete the entire trailing test function (lines 105–129), which begins:

```python
def test_plain_theme_content_templates_render_form_media():
    """Regression guard for the plain theme's widget-media bug.
    ...
    """
    base = Path(crud_views_plain.__file__).parent / "templates" / "crud_views"
    for name in (
        "view_create.content.html",
        "view_update.content.html",
        "view_custom_form.content.html",
        "view_delete.content.html",
    ):
        source = (base / name).read_text()
        assert "{{ form.media }}" in source, f"plain theme {name} must render {{{{ form.media }}}}"
```

The 8 asset-registry tests above it stay. `from pathlib import Path` (line 1) is still used by other tests — keep it.

- [ ] **Step 3: Run the asset tests to confirm the suite is still green (app still present)**

Run: `cd tests && pytest test1/test_assets.py -v`
Expected: PASS — 8 tests pass, `test_plain_theme_content_templates_render_form_media` no longer collected.

- [ ] **Step 4: Delete the plain-theme app**

```bash
git rm -r src/crud_views_plain
```

- [ ] **Step 5: Remove the packaging, coverage, and bump references from `pyproject.toml`**

Delete the `"src/crud_views_plain",` line from the `packages` array (~L97). After:

```toml
packages = [
    "src/crud_views",
    "src/crud_views_workflow",
    "src/crud_views_polymorphic",
```

Remove `"crud_views_plain"` from `[tool.coverage.run] source` (~L114). After:

```toml
source = ["crud_views", "crud_views_polymorphic", "crud_views_workflow"]
```

Delete the entire `[[tool.bumpversion.files]]` stanza targeting the plain `__init__.py` (~L136–140):

```toml
[[tool.bumpversion.files]]
filename = "src/crud_views_plain/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

- [ ] **Step 6: Rewrite the W110 system-check hint in `src/crud_views/lib/settings.py:81`**

Change the hint so it no longer names the deleted app and points at the new doc. Before:

```python
                    hint=(
                        "Theming is done by overriding templates, not via a setting. Ship templates "
                        "under the crud_views/ namespace and list your app (e.g. crud_views_plain) "
                        "before crud_views in INSTALLED_APPS. Remove CRUD_VIEWS_THEME."
                    ),
```

After:

```python
                    hint=(
                        "Theming is done by overriding templates, not via a setting. Ship templates "
                        "under the crud_views/ namespace and list your theme app (e.g. myapp_theme) "
                        "before crud_views in INSTALLED_APPS (see docs/reference/theme.md). "
                        "Remove CRUD_VIEWS_THEME."
                    ),
```

- [ ] **Step 7: Remove the app bullet from `CLAUDE.md:10`**

Delete this line:

```markdown
- `crud_views_plain` — plain HTML theme override (no CSS framework)
```

The header on line 7 already reads "ships as **four** separate Django apps" while the list showed five — this deletion makes the count correct. No other wording change.

- [ ] **Step 8: Verify the removal — suite green, grep clean, build clean**

Run: `cd tests && pytest`
Expected: PASS — full suite green (same count minus the one deleted test).

Run: `cd /home/alex/projects/alex/django-crud-views && grep -rin "crud_views_plain" src/ tests/ pyproject.toml CLAUDE.md`
Expected: **no output** (exit 1).

Run: `uv build 2>&1 | tail -5 && python -c "import zipfile,glob; w=sorted(glob.glob('dist/*.whl'))[-1]; print(w); assert not any('crud_views_plain' in n for n in zipfile.ZipFile(w).namelist()), 'plain still in wheel'; print('wheel clean')"`
Expected: prints the wheel path then `wheel clean`.

- [ ] **Step 9: Commit**

```bash
git add tests/test1/test_assets.py pyproject.toml src/crud_views/lib/settings.py CLAUDE.md
git commit -m "refactor: remove crud_views_plain package and its code references"
```

(The `git rm` from Step 4 is already staged; it is included in this commit.)

---

## Task 2: Dissolve the `examples/plain` and `examples/shared` trees

**Files:**
- Delete: `examples/plain/` (entire project)
- Delete: `examples/shared/` (entire directory, after inlining its taskfile)
- Modify: `examples/bootstrap5/taskfile.yaml` (symlink → real file)

**Interfaces:**
- Consumes: Task 1's removal (the plain app no longer exists, so its example is dead).
- Produces: a self-contained `examples/bootstrap5/` with a real `taskfile.yaml`; no `examples/shared/`.

**Why this shape:** `examples/shared/models.py` and `examples/shared/migrations/` were symlinked **only** by `examples/plain/` — they die with it. `examples/shared/taskfile.yaml` was symlinked by **both** plain and bootstrap5; after plain is gone, bootstrap5 is its only consumer, so it becomes a real file in bootstrap5 and `examples/shared/` is deleted whole. `examples/bootstrap5/app/models/` is real (not symlinked) and never used the shared models.

- [ ] **Step 1: Delete the plain example project**

```bash
git rm -r examples/plain
```

- [ ] **Step 2: Replace the bootstrap5 taskfile symlink with a real file**

`examples/bootstrap5/taskfile.yaml` is currently a symlink to `../shared/taskfile.yaml`. Remove the symlink and write a real file with the **identical** content:

```bash
git rm examples/bootstrap5/taskfile.yaml
```

Then create `examples/bootstrap5/taskfile.yaml` with exactly:

```yaml
version: '3'

env:
  PYTHONPATH: ../../.

tasks:

  init:
    cmds:
      - task: migrate
      - task: superuser

  migrations:
    cmds:
      - ./manage.py makemigrations
    silent: true

  migrate:
    cmds:
      - ./manage.py migrate
    silent: true

  superuser:
    cmds:
      - ./manage.py createsuperuser --noinput
    silent: true
    env:
      DJANGO_SUPERUSER_USERNAME: admin
      DJANGO_SUPERUSER_PASSWORD: foobar4711
      DJANGO_SUPERUSER_EMAIL: admin@example.org

  shell:
    cmds:
      - ./manage.py shell
    silent: true

  run:
    cmds:
      - uv run manage.py runserver 0.0.0.0:8000

  makemessages:
    cmd: uv run manage.py makemessages -l de

  compilemessages:
    cmd: uv run manage.py compilemessages

  setup_guardian_demo:
    cmd: uv run manage.py setup_guardian_demo
```

(Content copied verbatim from the shared taskfile. The German `makemessages -l de` line stays — the English/i18n sweep is M3/M5, not this plan.)

- [ ] **Step 3: Delete the shared directory**

```bash
git rm -r examples/shared
```

- [ ] **Step 4: Smoke-test the bootstrap5 example still checks out**

Run: `cd /home/alex/projects/alex/django-crud-views/examples/bootstrap5 && PYTHONPATH=../../. uv run python manage.py check`
Expected: exits 0 with "System check identified no issues" (warnings, if any, are pre-existing and fine — there must be **no errors** and no `ModuleNotFoundError`).

- [ ] **Step 5: Verify no stray references and no dangling symlinks**

Run: `cd /home/alex/projects/alex/django-crud-views && test ! -e examples/shared && test ! -e examples/plain && test -f examples/bootstrap5/taskfile.yaml && ! test -L examples/bootstrap5/taskfile.yaml && echo OK`
Expected: `OK` (shared/plain gone; bootstrap5 taskfile is a real file, not a symlink).

Run: `find examples -xtype l`
Expected: **no output** (no broken symlinks left).

- [ ] **Step 6: Commit**

```bash
git add examples/bootstrap5/taskfile.yaml
git commit -m "refactor(examples): remove plain example, dissolve examples/shared into bootstrap5"
```

(The three `git rm` operations are already staged and included in this commit.)

---

## Task 3: Document the theme-override mechanism and clean doc references

**Files:**
- Create: `docs/reference/theme.md`
- Modify: `docs/index.md:34` (features list)
- Modify: `docs/reference/modals.md:30` (generic wording)
- Modify: `docs/reference/.pages` (nav — insert `theme.md`)

**Interfaces:**
- Consumes: nothing from earlier tasks (docs-only).
- Produces: `docs/reference/theme.md` — the canonical "bring your own theme" page referenced by the W110 hint (Task 1, Step 6) and the CHANGELOG (Task 4).

- [ ] **Step 1: Create `docs/reference/theme.md`**

Write the file with exactly this content:

````markdown
# Custom themes (bring your own theme)

crud_views ships one theme, **bootstrap5** (the `crud_views` app). The look and feel is
defined entirely by templates under the `crud_views/` template namespace, and you can replace
any of them by shipping a **theme app** of your own. There is no theme *setting* — theming is
template override by name, resolved through Django's app template loader.

!!! note "Two different mechanisms"
    This page is about replacing crud_views' **own** templates (buttons, list/detail/form
    partials) to restyle the framework. To choose which **base template** your CRUD pages
    extend (your site chrome), use `cv_extends` instead — see
    [Base template](templates.md).

## How resolution works

Every crud_views template lives under a `crud_views/` directory, e.g.
`crud_views/view_list_table.html`, `crud_views/tags/button_submit.html`. Django's
`app_directories` template loader searches each app in `INSTALLED_APPS` **in order** and
returns the first template matching a given name.

So to override a template, an app earlier in `INSTALLED_APPS` ships a template with the
**same name** under its own `templates/crud_views/` directory. That copy wins; crud_views'
own copy is the fallback for every template the theme app does not override.

## What a theme app must provide

A theme app is an ordinary Django app:

1. An `AppConfig` (so it can appear in `INSTALLED_APPS`).
2. A `templates/crud_views/` directory containing the same-named templates you want to
   override. You only need to ship the templates you actually change — anything you omit
   falls through to bootstrap5.
3. Optionally, static assets under `static/` (register JS/CSS via the asset registry — see
   [Assets](assets.md) — if your theme needs its own).

## INSTALLED_APPS ordering (the one rule that matters)

Your theme app **must be listed before `crud_views`** so its templates are found first:

```python
INSTALLED_APPS = [
    # ...
    "myapp_theme.apps.MyAppThemeConfig",   # <-- before crud_views
    "crud_views.apps.CrudViewsConfig",
    # ...
]
```

If it is listed *after* `crud_views`, crud_views' own templates are found first and your
overrides never render.

!!! warning "`CRUD_VIEWS_THEME` is not a setting"
    There is no theme setting. If `CRUD_VIEWS_THEME` is set, crud_views' system checks emit
    `crud_views.W110` and ignore it. Do theming with a template-override app as described
    here.

## Worked example: restyle the submit button

Give your theme app a template at
`myapp_theme/templates/crud_views/tags/button_submit.html`:

```html
<button type="submit" class="my-fancy-button">{{ label }}</button>
```

With `myapp_theme` listed before `crud_views` in `INSTALLED_APPS`, every crud_views form now
renders your button, while all other templates keep the bootstrap5 defaults.
````

- [ ] **Step 2: Add `theme.md` to the reference nav**

In `docs/reference/.pages`, insert `- theme.md` immediately after `- templates.md`:

```yaml
    - templates.md
    - theme.md
    - settings.md
    - ...
```

- [ ] **Step 3: Clean the plain-theme mention in `docs/index.md`**

Replace the "Themes are pluggable" bullet and its two sub-bullets (around lines 32–34):

```markdown
- Themes are pluggable, so you can easily customize the look and feel to your needs, includes themes
    - `bootstrap5` with Bootstrap 5 (default)
    - `plain` no CSS, minimal HTML and JavaScript (install `crud_views_plain` to override)
```

with:

```markdown
- Themes are pluggable — `bootstrap5` (Bootstrap 5) ships as the default, and you can
  [bring your own theme](reference/theme.md) to customize the look and feel
```

- [ ] **Step 4: Generalize the plain-theme mention in `docs/reference/modals.md:30`**

Replace:

```markdown
- Progressive enhancement: direct links, middle-click, disabled JavaScript and non-Bootstrap
  themes (e.g. `crud_views_plain`) all render the normal full page.
```

with:

```markdown
- Progressive enhancement: direct links, middle-click, disabled JavaScript and custom themes
  that ship no modal JavaScript all render the normal full page.
```

- [ ] **Step 5: Build the docs to verify they render**

Run: `cd /home/alex/projects/alex/django-crud-views && uv run mkdocs build --strict 2>&1 | tail -15`
Expected: `INFO - Documentation built in ...` with no `WARNING`/`ERROR` about `theme.md`, broken links, or missing nav entries. (`--strict` turns nav/link warnings into failures.)

- [ ] **Step 6: Verify no live doc still advertises the plain theme**

Run: `cd /home/alex/projects/alex/django-crud-views && grep -rin "crud_views_plain" docs/`
Expected: **no output** (exit 1).

- [ ] **Step 7: Commit**

```bash
git add docs/reference/theme.md docs/reference/.pages docs/index.md docs/reference/modals.md
git commit -m "docs: add theme-override reference, drop plain-theme mentions"
```

---

## Task 4: CHANGELOG entry, PR, and merge to main

**Files:**
- Modify: `CHANGELOG.md` (new `## 0.13.0` section at the top)

**Interfaces:**
- Consumes: Tasks 1–3 (all changes present on the branch).
- Produces: a merged `main` with all M1 code/doc changes, CI green — the state Task 5 releases from.

- [ ] **Step 1: Add the 0.13.0 CHANGELOG section**

Insert a new section directly under the `# Django CRUD Views - Changelog` title, above `## 0.12.1`:

```markdown
## 0.13.0

### Removed
- **Breaking:** the `crud_views_plain` theme app has been removed. It was unused and
  undocumented, so there is no deprecation period. Theme pluggability is unchanged — ship your
  own template-override theme app (see the new `docs/reference/theme.md`). `bootstrap5` remains
  the only bundled theme.

### Changed
- The `examples/plain/` project and the `examples/shared/` directory were removed;
  `examples/bootstrap5/` is now self-contained.
```

- [ ] **Step 2: Commit the CHANGELOG**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): 0.13.0 — remove crud_views_plain theme (breaking)"
```

- [ ] **Step 3: Push the branch and open the PR**

```bash
git push -u origin m1-remove-plain-theme
gh pr create --title "M1: remove crud_views_plain theme (0.13.0)" \
  --body "Removes the unused crud_views_plain theme app and its example, dissolves examples/shared/, and documents the surviving theme-override mechanism in docs/reference/theme.md. Breaking; ships as 0.13.0. Spec: superpowers/specs/2026-07-16-m1-remove-plain-theme-design.md"
```

- [ ] **Step 4: Wait for PR CI to go green; fix ruff if it complains**

Run: `gh pr checks --watch`
Expected: all checks pass. If ruff-format/ruff-check fails, run `uv run ruff format . && uv run ruff check --fix .`, commit, and push; re-watch.

- [ ] **Step 5: Squash-merge to main and wait for main CI**

```bash
gh pr merge --squash --delete-branch
git checkout main && git pull
gh run watch "$(gh run list --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
```

Expected: post-merge main CI green.

---

## Task 5: Release 0.13.0

**Files:**
- Modified by `bump-my-version`: `pyproject.toml`, `src/crud_views/__init__.py`, `docs/index.md`, `README.md` (**4 files** — the fifth, `src/crud_views_plain/__init__.py`, was removed from the bump config in Task 1).

**Interfaces:**
- Consumes: merged, green `main` from Task 4.
- Produces: `v0.13.0` tag, PyPI release, verified downstream.

**Note:** the release runs directly on `main` (see project memory `release-process`). bump-my-version does **not** edit `CHANGELOG.md` — that was done in Task 4.

- [ ] **Step 1: Confirm you are on clean, up-to-date main**

Run: `git checkout main && git pull && git status`
Expected: on `main`, up to date, clean tree (no untracked `cred.prompt.md` staged).

- [ ] **Step 2: Bump the version (commits + tags automatically)**

Run: `uv run bump-my-version bump minor`
Expected: version `0.12.1 → 0.13.0` across the 4 configured files; a `Bump version: 0.12.1 → 0.13.0` commit; a `v0.13.0` tag created.

Run: `git show --stat HEAD` and `git tag --list v0.13.0`
Expected: the 4 files changed; tag `v0.13.0` present. Confirm `src/crud_views_plain/__init__.py` is **not** in the diff (it no longer exists).

- [ ] **Step 3: Push main and the tag (the tag push triggers publish.yml → PyPI)**

```bash
git push origin main && git push origin v0.13.0
```

- [ ] **Step 4: Watch the publish workflow**

Run: `gh run watch "$(gh run list --workflow publish.yml --limit 1 --json databaseId --jq '.[0].databaseId')"`
Expected: tests (3.12/3.13/3.14) + docs + lint pass, then the `publish` job uploads to PyPI via trusted publishing.

- [ ] **Step 5: Verify the release is live on PyPI**

Run: `curl -s https://pypi.org/pypi/django-crud-views/json | jq -r .info.version`
Expected: `0.13.0`.

- [ ] **Step 6: Verify `django-crud-views-extensions` is green against 0.13.0**

In the sibling `django-crud-views-extensions` repo, install against `django-crud-views==0.13.0` and run its test suite.

Run: `pip install 'django-crud-views==0.13.0' && python -m pytest` (from the extensions repo checkout)
Expected: install resolves 0.13.0 and the extensions test suite passes. (Extensions does not use the plain theme, but this confirms the downstream contract.)

---

## Self-Review

**Spec coverage** (against `superpowers/specs/2026-07-16-m1-remove-plain-theme-design.md`):

- Deletions — plain app, plain example, test coupling → Task 1 (Steps 4, 2), Task 2 (Step 1). ✓
- `examples/shared/` dissolution (delete models+migrations, inline taskfile, delete dir) → Task 2. ✓
- Code edits — pyproject ×3, settings W110 hint, CLAUDE.md → Task 1 (Steps 5–7). ✓
- Docs — new `theme.md`, index, modals, nav → Task 3. ✓
- Release — CHANGELOG, bump, tag, publish, extensions verify → Tasks 4–5. ✓
- "Done when" — grep clean (T1S8, T2S5, T3S6), examples gone (T2S5), wheel clean (T1S8), suite green (T1S8), theme.md in nav (T3S5), 0.13.0 on PyPI (T5S5), extensions green (T5S6). ✓
- Out-of-scope guards (German sweep, bootstrap5 restructure) — stated in Global Constraints and Task 2 Step 2. ✓

**Placeholder scan:** no TBD/TODO; every code/edit step shows exact before/after content; theme.md content is complete. ✓

**Type/name consistency:** no cross-task code interfaces (mechanical removal); the W110 hint references `docs/reference/theme.md`, which Task 3 creates at that exact path; the CHANGELOG references the same path. Branch name `m1-remove-plain-theme` and tag `v0.13.0` used consistently across Tasks 1/4/5. ✓
