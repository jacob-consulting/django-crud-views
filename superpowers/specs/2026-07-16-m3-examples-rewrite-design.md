# M3 — Examples Rewrite: Design Spec

**Date:** 2026-07-16
**Status:** Approved design — ready for implementation planning
**Source:** `superpowers/notes/2026-07-16-release-1-milestone.md` (M3 section), brainstormed 2026-07-16
**Ships as:** merge to main only — **no PyPI release** (examples are not part of the wheel)

## Goal

Replace the organically grown `examples/bootstrap5/app/` monolith with didactically clean
examples: one self-contained Django app per feature inside the single runnable
`examples/bootstrap5/` project. Real-life domains, English only, tested in CI, and structured
so the M4 docs tutorial can follow `library/` step by step.

## Decisions made in this brainstorm

1. **App mapping:** `library/` absorbs the tutorial arc (CRUD, tables, filters, permissions,
   ordered up/down). One extra app `showcase/` demos the presentation extras (cards,
   fieldsets, custom actions, context buttons). 8 feature apps total.
2. **Domains:** see table below; guardian uses the milestone's "documents shared per-user"
   scenario.
3. **Landing-page code snippets:** runtime reading of whole source files via a project-level
   template tag with pygments highlighting (example-only dependency). No markers, no
   duplication — apps must keep files small enough to read whole.
4. **Tests:** pytest, second target next to `tests/test1/`, wired into nox/CI on the full
   matrix. Example tests do NOT count toward the package coverage gate.
5. **Seed data:** one idempotent `manage.py seed` command calling per-app `seed()` functions.
   Committed `db.sqlite3` deleted and gitignored.
6. **Execution:** single branch `m3-examples`, one PR, squash-merge (like M2). Per-app tasks
   inside the branch are independent and parallelizable.
7. **English only:** `locale/de/` removed; i18n-as-a-demonstrated-feature is explicitly a
   separate future decision, not part of M3.

## Target layout

```
examples/bootstrap5/
  manage.py
  taskfile.yaml            # dev / run / test / seed tasks
  project/
    settings.py            # English-only (en-us), no LocaleMiddleware
    urls.py                # home + auth + include() per feature app
    views.py               # home page view
    templatetags/          # {% source_code %} snippet tag (pygments)
    templates/project/     # base.html, home.html, snippet partial
  library/  nested/  formsets/  workflow/
  polymorphic/  guardian/  resources/  showcase/
```

- **Home page** (`/`): a card per feature app — name, one-line description, link.
- **Each app is fully self-contained:** own `models.py`, `views.py`, `urls.py`,
  `templates/<app>/`, `seed.py`, `tests.py`, fresh `migrations/0001_initial.py`.
  Apps import only from `crud_views*` and Django/third-party — never from each other.
- **Landing page pattern:** each app's list view page = intro text ("About this example")
  + the list view itself + collapsible pygments-highlighted panels rendering the app's
  actual `models.py` / `views.py` at runtime (`{% source_code "library/views.py" %}`).
- **Auth:** seeded demo users (`admin` superuser, `alice`, `bob`); credentials displayed on
  the login page and home page.
- **URLs:** each app mounted under its own prefix (`/library/`, `/nested/`, …). ViewSet
  names are globally unique across apps.

## Feature → app mapping

| App | Domain / models | Demonstrates |
|---|---|---|
| `library/` | Author, Book | CRUD, django-tables2 tables, django-filter filters, crispy forms, `*PermissionRequired`, ordered up/down (OrderedModel). **The M4 tutorial app** — follows the tutorial arc exactly. Book→Author is a plain FK (column/filter), NOT URL-nested. |
| `nested/` | Company → Department → Employee, plus Company → Office | `ParentViewSet`, nested URLs, queryset auto-filtering to parent, `CreateViewParentMixin`, two children on one parent + a grandchild chain. Replaces foo/bar/baz/qux 1:1. |
| `formsets/` | Survey: Questionnaire → Question → Choice | ONE clean inline-formset demo (`FormSetMixin`), deliberately simplified vs today's parent/one/two/three matrix. Formsets stay documented-as-internal per M2 — show the supported pattern only. |
| `workflow/` | Campaign (draft → active → closed, + cancel) | `FSMField` + `wf_` transitions as form actions (`WorkflowViewPermissionRequired`), `WorkflowModelMixin` audit history on detail page. |
| `polymorphic/` | Vehicles: Car / Truck / Motorcycle | `PolymorphicCreateSelectView` type picker → per-type `PolymorphicCreateView` (`polymorphic_forms`), polymorphic list. |
| `guardian/` | Documents shared per-user | `GuardianViewSet` + `Guardian*PermissionRequired`; alice owns documents, shares one with bob; list visibly differs per user. Replaces group/members AND book_review as the guardian story. |
| `resources/` | Faked S3-style bucket listing (in-memory, no boto3) | Non-ORM data via `Resource` / `ResourceViewMixin`. |
| `showcase/` | Recipes | Card list view, detail-page fieldsets (simplified vs today's `detail.py` — current version is too complex), custom `CardAction` / context buttons, `MessageMixin`. |

Every current demo maps to exactly one new app; every shipped feature is covered by exactly
one app.

## Seed data & tooling

- `manage.py seed` (project-level management command) calls each app's `seed()` in order.
  Idempotent (`get_or_create` everywhere). Creates: demo users with known passwords,
  model-permission groups where needed, per-app demo records, guardian object permissions,
  campaigns in several workflow states.
- `taskfile.yaml`: `task run` = migrate + seed + runserver; `task test` = pytest;
  `task seed` standalone. (README wiring is M5.)
- **Deletions:** committed `db.sqlite3` (gitignore it), `locale/` entirely,
  `app/management/` (`setup_guardian_demo.py` superseded by guardian `seed()`,
  `bs5_test.py` by the real test suite).
- One shared sqlite DB for all apps; guardian/workflow specialness lives in their `seed()`.

## Testing & CI

- Per-app `tests.py` via Django test client against the example project settings:
  CRUD round-trips + the app's specialty (nested: child list filtered to parent; guardian:
  alice sees hers, bob doesn't; workflow: transition changes state + writes audit history;
  polymorphic: select→create flow; resources: non-ORM list renders; snippets: landing pages
  return 200 with highlighted source).
- One project-level test: home page links to every feature app and every link resolves.
- pytest runner mirroring `tests/test1/` (`pytest-django`,
  `DJANGO_SETTINGS_MODULE=project.settings`); `cd examples/bootstrap5 && pytest` works.
- New `examples` session in `noxfile.py` + GitHub Actions workflow, full matrix by default
  (constrain rather than fight if an example-only dep misbehaves on a combo).
- Package coverage gate (`fail_under = 88`) stays scoped to `src/` via `tests/test1/`.

## Execution order (branch `m3-examples`, one PR, squash-merge)

1. **Scaffold:** `project/` (settings, home, base template, snippet templatetag), taskfile,
   seed command skeleton, pytest wiring. Delete `db.sqlite3` + `locale/` up front. Remove
   old `app/` from `INSTALLED_APPS`/urls NOW (it lingers as dead files until step 3) — this
   avoids ViewSet-name collisions (`author`, `book`, `campaign`, …) with the new apps.
2. **One task per app** (independent, parallelizable under SDD): models + migrations +
   views + templates + `seed()` + tests. Each lands green.
3. **Delete `examples/bootstrap5/app/`**; grep-verify no references remain.
4. **CI wiring** (nox session + workflow), CHANGELOG entry, milestone doc M3 marked done.

## Acceptance ("done when")

- Layout matches the target above; every shipped feature has exactly one example app.
- `task run` from a fresh clone yields a populated, navigable example.
- All example tests green in CI on the matrix.
- Zero German strings (`grep -ri` for "Vorname", "Autor", "Titel", verbose_name checks).
- Home page navigates to every feature app.
- Merged to main; no PyPI release; milestone doc status updated.

---

## Hand-over notes for a fresh implementing session

Read these before writing the implementation plan or any code.

**Process:** This project uses superpowers SDD. Next step after this spec is the
`superpowers:writing-plans` skill → plan at `superpowers/plans/2026-07-16-m3-examples.md`,
then execution on branch `m3-examples`, PR, wait for CI green, squash-merge to main, wait
for main CI (see project memory `pr-wait-for-ci-fix-ruff`). No version bump, no PyPI
publish for M3.

**Where things are today (verify with fresh grep before deleting):**
- The monolith: `examples/bootstrap5/app/` — models in `app/models/` (`__init__.py` has
  Author/Book/BookReview/Foo/Bar/Baz/Qux/Detail/Group/Person; `campaign.py`, `poly.py`,
  `questions.py`), views in `app/views/` (one module per ViewSet + `formset/`, `poly/`
  packages), templates in `app/templates/app/`, 11 migrations.
- Project config: `examples/bootstrap5/project/settings.py` (has `LocaleMiddleware` +
  `de` bits to remove, custom `test_runner.py` — check if still needed),
  `project/urls.py` is currently trivial (urls live in `app/urls.py` — the new design
  moves aggregation to `project/urls.py` with per-app `include()`).
- German strings live in model `verbose_name`s (e.g. Book.title has `_("Titel")`) and
  `locale/de/`.
- Root `taskfile.yaml` (repo root) has `run` targets pointing into examples — update those
  alongside `examples/bootstrap5/taskfile.yaml`.
- CI: `.github/workflows/` + `noxfile.py` at repo root run `tests/` only today.

**Known constraints & gotchas:**
- ViewSet names must be globally unique in the project — old `app/` must leave
  `INSTALLED_APPS` before new apps that reuse names (`author`, `book`, `campaign`) land.
- `crud_views` system checks validate ViewSet/CrudView config at startup — new apps must
  pass them (naming conventions, template existence).
- Author/Book use UUID PKs and `OrderedModel` today; keep UUID PK on at least one library
  model (shows PK-type auto-discovery) — Publisher/Book in `tests/test1` cover int PKs,
  and `nested/` models can use default int PKs for contrast.
- `django_object_detail` is an example dependency used by today's `detail.py` — decide in
  the plan whether `showcase/` keeps it or drops it; don't cargo-cult it in.
- Formsets API is semi-private per M2 decision — `formsets/` app shows only the supported
  `FormSetMixin` pattern, nothing exotic.
- pygments is a NEW dependency for examples only — add to the examples/dev dependency
  group, NOT to package dependencies in `pyproject.toml`'s `[project]` table.
- The M2 stability statement is at `docs/development/stability.md` — examples must only
  use public API listed there (they double as public-API smoke tests).
- Downstream repo `django-crud-views-extensions` is unaffected (examples only), no
  compatibility check needed for M3.

**Follow-ups that are NOT M3:** tutorial rewrite against `library/` (M4), README
run-instructions + screenshots (M5), i18n demo app (unscheduled, explicit non-goal).
