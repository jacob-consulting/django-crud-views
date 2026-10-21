# Acceptance: drop django-bootstrap5 (#221)

Plan: `superpowers/plans/2026-10-21-drop-django-bootstrap5.md` (committed on `main` as a0e5756).
Branch: `feat/drop-django-bootstrap5` — 3ccf145 (icons), 130c9e2 (`{% cv_messages %}`), f6861b8 (dependency removal).

## Acceptance criteria from #221

| Criterion | Command | Result |
|---|---|---|
| `django-bootstrap5` in no section of `pyproject.toml` | `task build` + `Requires-Dist` of the built wheel | `crispy-bootstrap5>=2023.10` and `django-crispy-forms>=2.0` present, no `django-bootstrap5` in any extra |
| No `django_bootstrap5` / `{% bootstrap` reference survives | `pytest tests/test1/test_no_django_bootstrap5.py` | 591 passed (one case per scanned file) |
| `{% cv_messages %}` renders Bootstrap 5 alert markup, `info` + `error` covered | `pytest tests/test1/test_messages.py` | 20 passed |
| The example app still shows flash messages after a redirect | `cd examples/bootstrap5 && pytest` | 300 passed, 1 skipped, 41 subtests — includes `test_demo_pages_render_german` and `test_demo_chrome_renders_german`, which render the rewritten base template |
| Full suite green | `pytest tests -n auto` | 2310 passed, 2 skipped |
| Lint | `task check && task format` | all checks passed; 492 files left unchanged |
| i18n untouched | `pytest tests/test1/test_i18n.py` | 7 passed, no `.po`/`.mo` edit — `{% translate 'Close' %}` reuses the existing `msgid "Close"` → `"Schließen"` |

## Deliberate deviations

- **`DEBUG → alert-secondary`**, where django-bootstrap5's `{% bootstrap_messages %}` mapped `DEBUG → warning`.
  A debug message is not a warning, and the default `MESSAGE_LEVEL` hides debug messages anyway, so this only
  surfaces in a project that lowers it. Documented in `docs/reference/messages.md`.
- **`data-bs-dismiss="alert"` rather than a new `cv.adapters` entry.** Bootstrap dismisses alerts declaratively, so
  an adapter would add a JS file and an adapter surface for behaviour that needs neither. This follows the dominant
  pattern in shipped templates (`data-bs-toggle` in `actions_menu_toggle.html`, `language_selector.html`, the
  object-detail accordion and tabs layouts); the modal's `data-cv-modal-dismiss` is the exception, needed only
  because crud_views' own JS opens modals. Consequence, unchanged from before: the X is inert without Bootstrap's
  JS bundle.
- **The guard test does not scan `docs/` or `CHANGELOG.md`**, narrowing #221's acceptance grep. Both name the
  package in migration prose on purpose — `docs/reference/messages.md` compares the `DEBUG` mapping, and the
  CHANGELOG carries the breaking-change bullet. The tutorial's mention was removed as required.

## Notes for the reviewer

- **The local dev venv still has `django_bootstrap5` installed** — removing a dependency does not uninstall it — so
  no `ImportError` would ever prove the removal here. `tests/test1/test_no_django_bootstrap5.py` is the contract.
  In CI it is also enforced structurally: the nox `tests` session installs `.[polymorphic,workflow,ordered,test]`
  and `examples` installs `.[all,test,examples]`, so any surviving `{% load django_bootstrap5 %}` or
  `INSTALLED_APPS` entry fails at `django.setup()`.
- `tests/test1/conftest.py:36` carried `"django_bootstrap5"` in `INSTALLED_APPS` as well as the example's
  `settings.py`; both were removed. Missing the conftest one was the single way this change could pass locally and
  fail every CI session.
- Two venv-only fixes were needed to run the verification, neither part of the change: `requirements/demo.txt`
  (`django-ratelimit`, without which the example suite cannot collect `project/test_ratelimit.py`) and `polib`
  (without which `test_no_empty_or_fuzzy_msgstr` silently skips). `task dev` installs both.
