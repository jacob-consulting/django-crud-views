---
status: resolved
phase: "06.41"
gap_id: G-06.41-1
---

# Bulk Cancel without JavaScript

## Symptoms

UAT test 6: user reported "the cancel button does not work without javascript".
Expected: leave a bulk review/form without executing its action, returning to the source.

## Evidence and root cause

- `CrispyFormMixin.get_cancel_button_kwargs()` supplies `data_cv_cancel_url`, with no explicit tag.
- The class-table default `form:cancel-tag` is `button` (`src/crud_views/lib/button_classes.py`).
- The form leaf renders that as `<button type="button" data-cv-cancel-url="...">`.
- The delegated click listener in `viewset.js` supplies navigation. Without JavaScript, that
  button has no navigation behavior. The URL resolver is not the defect.
- The Bootstrap example settings do not opt into native Cancel links.
- `tests/test1/test_bulk_return.py` verifies the data attribute and manually GETs its URL;
  that does not verify the browser can follow Cancel without scripting.
- The limitation is documented in `docs/reference/bulk_actions.md` and the existing opt-in
  is documented in `docs/reference/buttons.md#cancel-links`.

## Confirmatory experiment

Command: `PYTHONPATH=src:. .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_crispy_buttons.py::test_configured_cancel_renders_one_native_link tests/test1/test_crispy_buttons.py::test_unconfigured_cancel_stays_the_original_button -q`
Result: 2 passed in 0.22s. Serial because this is a tiny two-test rendering probe.
The configured case asserts an anchor with a real href and no delegated-handler marker;
its submit control stays a submit button. The unconfigured case proves the default is a button.
This confirms rendering behavior, not a completed browser cancellation run.

## Bounded fix direction

Enable the existing project-level native-link option in the Bootstrap example settings,
show the same option beside the bulk guide's JavaScript limitation, and exercise real rendered
bulk Cancel hrefs in example tests for table/card, eligible/mixed/all-blocked and invalid forms.
Retest in a browser with JavaScript disabled. Do not alter the library default, URL policy,
permission checks, form lifecycle, or introduce another return protocol.

Diagnosis performed inline; no subagents dispatched. Implementation belongs to plan 14.

## Resolution — 2026-11-21

Plan 06.41-14 enabled the existing native Cancel link setting in the Bootstrap example and documented it. Automated regression and 18 browser scenarios pass. The user confirmed the no-JavaScript defect retest with “yes”; UAT G-06.41-1 is resolved.
