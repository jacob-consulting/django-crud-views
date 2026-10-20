# Task 8 report: verification (2026-10-20)

## Step 1: suites
- `.venv/bin/pytest tests -q`: 1422 passed, 3 skipped.
- vitest (Node 22 via npx): 8 files, 94 tests passed.
- `.venv/bin/ruff check .`: all checks passed. `uvx ruff@0.16.0 format --check .`: 471 files already formatted.
- `examples/bootstrap5 manage.py check`: no issues (no E250).

## Step 2: Bootstrap example without jQuery (Chromium via chrome-devtools MCP, 2026-10-20, port 8765, login alice/alice from `seed`)
jQuery tag removed from base.html (typeof jQuery === undefined, bootstrap present). Results:
- Showcase recipe list: delete modal opens; data-cv-modal-dismiss close button hides it; reopened; empty submit gave a 422 and the modal re-rendered with "This field is required."; confirm gave 204 and redirect to list (recipe removed).
- Tooltip: object-detail card-rows page, 15 `[data-cv-tooltip]`, hover shows `.tooltip.show` ("Product name").
- Filter toggle (library/author): aria-expanded false->true, panel `collapse show`; after reload still open; toggled closed, after reload false (persisted).
- POST list action (Favorite, `submit-form`): POST /showcase/recipe/4/favorite/ -> 302, page reloaded.
- Cancel: `/library/author/<id>/update/?cv_from=list` data-cv-cancel-url click navigated to the list.
- Card order combo (`submit-on-change`): navigated to `?order=title`, cards re-ordered.
- Console: no script errors. Only: favicon 404 (server log), browser-logged 422 network line from the deliberate validation test, and a Bootstrap aria-hidden/focus warning on modal close.
- Formset page (`/formsets/questionnaire/1/update/`): exactly one console.error: "crud_views formset.js: pages with formsets need jQuery; load it before DOMContentLoaded."
- base.html restored with `git checkout -- <file>`.

## Step 3: Tabler without shim or jQuery
Did NOT touch the tabler-test tree. Instead copied it (without .venv/.git/.run) to the scratchpad, ran it with its own venv and `PYTHONPATH=<this repo>/src` so the local crud_views was used (no reinstall; installed version stays 0.29.4), port 8766, throwaway superuser in the copy's DB. Copy edits: `shared/js.html` = core loop + one deferred `crud_views_tabler/adapters.js` containing `Object.assign(cv.adapters, cv.bootstrapAdapters(() => globalThis.tabler));`; no jQuery, no bootstrap-shim. Copy deleted afterwards.
- Finding (theme, not this change): tabler-test's `tags/list_filter.inner.html` uses `{% cv_filter_icon %}`, removed earlier (#198), so /customer/ raised TemplateSyntaxError. Patched in the copy to `{% cv_icon "filter" %}` only to continue.
- Page state: jQuery undefined, window.bootstrap undefined, tabler defined, cv.adapters = modal, tooltip, collapse; scripts all deferred.
- Modal delete opens; 422 re-render with error; close via theme `.btn-close` (data-bs-dismiss, handled by Tabler's own data API) closes; `data-cv-modal-dismiss` (adapter hide) closes; confirm gave 204 and redirect to list.
- Filter toggle: panel opens (`collapse show`, aria-expanded true). Theme's toggle override has no aria-expanded initially (theme markup predates this change).
- `cv.adapters.tooltip.init` on a titled button: `.tooltip.show` appears. Theme templates use `data-bs-toggle="tooltip"` (Tabler-owned) rather than `data-cv-tooltip`, so the theme has no data-cv-tooltip triggers.
- Cancel (`data-cv-cancel-url`) navigated to /customer/.
- Card order combo and `submit-form`: theme's unsigned combo has no `data-cv-action`, so verified with synthetic attributes (change navigated to ?order=revenue; submit-form anchor submitted a GET form). Theme has no POST list action; synthetic only.
- Console errors/warnings: none (one browser "autocomplete attribute" issue notice on login form).
- Not exercised on Tabler: formset page (no formset view in tabler-test).

## Step 4: grep
`grep -nE '\bbootstrap\b|\bjQuery\b|\$\(|\$\.' viewset.js modal.js list.filter.js tooltip.js` -> no output (exit 1).

## Acceptance checklist
- [x] Bootstrap, no jQuery: modals open/422/dismiss/redirect, tooltips, filter toggle + persistence, POST list action, cancel, card order combo, no console errors
- [x] Same with a formset: exactly one jQuery console error, rest works
- [x] Tabler, adapters line, no jQuery, no shim, deferred: all above (caveats: theme templates need fixes noted above; combo/POST action synthetic; no formset page)
- [x] `cv_modal_size = "modal-lg"` -> E250 with hint; "lg" passes (covered by pytest suite, tests/test1/test_modal.py, passing; not re-run by hand through `manage.py check`)
- [x] Default DOM equals 0.30.0 except the listed deltas (covered by golden fixtures in pytest; not diffed by hand)
- [x] grep: no bootstrap/$/jQuery tokens in the four scripts

## Restoration
- django-crud-views `git status --short`: empty.
- tabler-test `git status --short`: `?? .run/` (identical to recorded); installed crud_views still 0.29.4; nothing changed there.
- All servers (8765, 8766) stopped.
