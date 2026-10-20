# Task 8 report: buttons verification (2026-10-20)

Branch `feat/button-variants-and-leaves` (merge base 440ac55, HEAD 03b145b). No source code changed.

## Step 1: suites
- `uv run pytest tests -q`: 1498 passed, 3 skipped.
- `cd examples/bootstrap5 && uv run pytest -q`: collection ERROR, `ModuleNotFoundError: django_ratelimit` (project/ratelimit.py, imported by project/test_ratelimit.py). Environment, not this change: the root venv lacks `django-ratelimit` (listed in `requirements/demo.txt`). Re-run with `uv run --with django-ratelimit pytest -q`: 300 passed, 1 skipped, 41 subtests passed.
- vitest (Node 22): 8 files, 106 tests passed.
- `uv run ruff format --check .`: 423 files formatted; `uv run ruff check .`: all passed; `uvx "ruff>=0.16,<0.17" format --check .`: 483 files already formatted.
- nox (Python 3.12):
  - `examples-3.12(django='6.0')`: passed (301 passed, 6 warnings).
  - `tests-3.12(django='4.2')`: FAILED, 1 failed / 1502 passed / 1 skipped.
  - `tests-3.12(django='6.0')`: FAILED, 1 failed / 1503 passed.
  - Both failures are the same test, `tests/test1/test_button_classes_templates.py::test_no_button_class_literal_in_shipped_templates_python_or_js`: "Left contains 23 more items, first extra item: ('crispy_forms/bootstrap.py', 'btn')". Diagnosis: the test sets `SRC = Path(crud_views.__file__).resolve().parent.parent` and globs `**/*.py` under it. In the editable dev venv that is `src/`; in nox the package is installed non-editable, so `SRC` is `site-packages` and the glob scans every installed third-party package (crispy_forms etc.), whose `btn` tokens are reported as offenders. A defect in the guard test (the CI matrix will fail), not in shipped code. Not fixed here (read-only task).

## Step 2: grep gates
- Guard test in the dev venv passes (part of the 1498).
- `grep -rn "btn" src/ --include=*.html --include=*.js --include=*.py | grep -v button_classes.py | grep -v btn-close`: no output.
- `FILTER_RESET_BUTTON_CSS_CLASS` in src/docs/examples: only `REMOVED_SETTINGS` entry in `src/crud_views/lib/button_classes.py:47`, `docs/reference/buttons.md` (migration note, E360 row) and `docs/reference/settings.md:89`. Allowed (the changelog is not in those trees).
- `cv_toggle_class|cv_menu_wrapper_class|_ACTIONS_MENU_STYLE` in src docs: empty.

## Step 3: golden diff
- `git diff 440ac55 -- tests/test1/golden` was not separately enumerated; the post-canonicalisation diff below is the one that carries real DOM changes.
- `git diff 92ff7d2 -- tests/test1/golden`: 6 files, 1 line each, all mapped:
  - `cards_author_disabled.html`: card row gains `cv-card-container="true"`; both buttons gain `cv-key` (detail, update).
  - `cards_author_full.html`: same, plus keys delete/ping; the POST action is `<button type="button" cv-key="ping" data-cv-action="submit-form" data-cv-target=...>` without `href` (was `<a href="#">`).
  - `cards_publisher_child.html`: `cv-card-container="true"`, `cv-key` detail and book.
  - `toolbar_detail_disabled.html`, `toolbar_detail_full.html`: `aria-current="page"` on the active detail action.
  - `toolbar_publisher_list.html`: `aria-current="page"` on the active list action.
- Verdict: only the four allowed changes; nothing else. (The menu-item form relocation row of the spec does not appear because no golden has a card menu.)

## Step 4: spec walk
- "Templates to change": every row is present in `git diff 440ac55 --stat -- src` (context_action, list_action, card_action, actions_menu_item, actions_menu_item_label, context_actions, columns/actions, card, actions_menu, actions_menu_toggle, context_action_filter, formsets/control, card_order, language_selector, button_submit/cancel/delete removed, object-detail card-rows property, new button/action, menu_item, container). Plus formset.js.
- Check ids: `viewset.E209` (lib/view/variant.py), `crud_views.E360/E361/W362` (lib/button_classes.py, registered in checks.py). All found.
- Contract keys: all 15 spec keys (cv_location, cv_tag, cv_href, cv_submit_target, cv_modal, cv_modal_size, cv_disabled, cv_disabled_reason, cv_active, cv_key, cv_label, cv_label_visible, cv_title, cv_icon, cv_variant, cv_flex) are in `LEAF_KEYS`, plus `cv_short_label` from the builder check. 17 entries in total.
- Tabler check: needs no code; `fieldset.btn-list` remains unverified (theme migration is a follow-up).

## Step 5: browser check (example project, Chromium via chrome-devtools MCP, port 8000, alice/alice)
Performed interactively where noted; seed run first (`migrate`, `seed`).
- Author list toolbar: `btn btn-outline-primary btn-lg` with `active` last, filter toggle, create, manage; row buttons `btn-xs`; overflow menu dropdowns present.
- Action-menus chore cards: row buttons and menu with 20 hidden `form.d-none`, POST up/down are `<button>` with `data-cv-action="submit-form"`.
- Recipe cards: `btn btn-primary btn-sm flex-grow-1` detail, secondary edit, POST Favorite as `<button ... submit-form>`, outline delete.
- Create and delete forms: submit `btn btn-primary` (delete too, per table `form:delete`), cancel `btn btn-secondary` with `data-cv-cancel-url`. Filter form: Apply `btn btn-primary`, Reset `btn btn-secondary`.
- Formset page (`/formsets/questionnaire/1/update/`): delete control carries `data-cv-class="btn btn-light"` and `data-cv-class-danger="btn btn-danger"`; clicking it toggled `btn-light` -> `btn-danger` -> `btn-light`. Interactive.
- Card order: only the signed combo exists in the examples (recipes); changing it navigated (reordered page). The unsigned direction toggle (`card-order:toggle`) is not rendered by any example page, so its click behaviour was NOT checked in a browser (covered by pytest only).
- Console: no JS errors; a single issue notice (autocomplete attribute on the login form).
- Not exercised interactively: modal delete flow (not part of this change). The Chrome page on 8766 and the runserver on 9000 are pre-existing and untouched.
- Server on 8000 stopped.

## Findings
1. `test_no_button_class_literal_in_shipped_templates_python_or_js` fails under nox (non-editable install scans site-packages); needs `SRC` derived from the repo or package files rather than the parent of the package dir.
   Fixed in the Task 5 fix round (commit: see `git log`, "fix(tests): button class guard scans the repository src tree, not the installed package"): `SRC` is now `Path(__file__).resolve().parents[2] / "src"`; `uv run nox -r -s "tests-3.12(django='6.0')"` passes (1504 passed).
2. Examples suite needs `django-ratelimit` in the root venv (use `requirements/demo.txt`); passes with it.
3. Unsigned card-order toggle is unreachable in the examples project.
